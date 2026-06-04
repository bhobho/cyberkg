"""
loader.py — Loads data into Neo4j.

Run order:
  1. load_seed_data()    — always works (uses local static data)
  2. enrich_from_mitre() — optional, fetches live MITRE ATT&CK JSON
  3. enrich_from_nvd()   — optional, fetches live NVD CVE data

Run this file directly:  python -m ingest.loader
"""
import os
import asyncio
import httpx
from database import run_query
from ingest.seed_data import (
    MALWARE, TECHNIQUES, CVES, ASSETS,
    MALWARE_USES_TECHNIQUE, TECHNIQUE_EXPLOITS_CVE,
    CVE_AFFECTS_ASSET, MALWARE_TARGETS_ASSET,
)

MITRE_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
NVD_URL   = "https://services.nvd.nist.gov/rest/json/cves/2.0"


# ─── Step 1: Create constraints so duplicate nodes are never created ──────────

def create_constraints():
    print("Creating Neo4j uniqueness constraints...")
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Malware)    REQUIRE m.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Technique)  REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:CVE)        REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Asset)      REQUIRE a.id IS UNIQUE",
    ]
    for c in constraints:
        run_query(c)
    print("  ✓ Constraints ready")


# ─── Step 2: Load static seed data ────────────────────────────────────────────

def load_seed_data():
    print("\nLoading seed data...")

    for m in MALWARE:
        run_query(
            "MERGE (m:Malware {id: $id}) SET m += $props",
            {"id": m["id"], "props": m},
        )
    print(f"  ✓ {len(MALWARE)} malware nodes")

    for t in TECHNIQUES:
        run_query(
            "MERGE (t:Technique {id: $id}) SET t += $props",
            {"id": t["id"], "props": t},
        )
    print(f"  ✓ {len(TECHNIQUES)} technique nodes")

    for c in CVES:
        run_query(
            "MERGE (c:CVE {id: $id}) SET c += $props",
            {"id": c["id"], "props": c},
        )
    print(f"  ✓ {len(CVES)} CVE nodes")

    for a in ASSETS:
        run_query(
            "MERGE (a:Asset {id: $id}) SET a += $props",
            {"id": a["id"], "props": a},
        )
    print(f"  ✓ {len(ASSETS)} asset nodes")

    for mal_id, tech_id in MALWARE_USES_TECHNIQUE:
        run_query(
            """
            MATCH (m:Malware {id: $mal_id}), (t:Technique {id: $tech_id})
            MERGE (m)-[:USES_TECHNIQUE]->(t)
            """,
            {"mal_id": mal_id, "tech_id": tech_id},
        )
    print(f"  ✓ {len(MALWARE_USES_TECHNIQUE)} USES_TECHNIQUE edges")

    for tech_id, cve_id in TECHNIQUE_EXPLOITS_CVE:
        run_query(
            """
            MATCH (t:Technique {id: $tech_id}), (c:CVE {id: $cve_id})
            MERGE (t)-[:EXPLOITS]->(c)
            """,
            {"tech_id": tech_id, "cve_id": cve_id},
        )
    print(f"  ✓ {len(TECHNIQUE_EXPLOITS_CVE)} EXPLOITS edges")

    for cve_id, asset_id in CVE_AFFECTS_ASSET:
        run_query(
            """
            MATCH (c:CVE {id: $cve_id}), (a:Asset {id: $asset_id})
            MERGE (c)-[:AFFECTS]->(a)
            """,
            {"cve_id": cve_id, "asset_id": asset_id},
        )
    print(f"  ✓ {len(CVE_AFFECTS_ASSET)} AFFECTS edges")

    for mal_id, asset_id in MALWARE_TARGETS_ASSET:
        run_query(
            """
            MATCH (m:Malware {id: $mal_id}), (a:Asset {id: $asset_id})
            MERGE (m)-[:TARGETS]->(a)
            """,
            {"mal_id": mal_id, "asset_id": asset_id},
        )
    print(f"  ✓ {len(MALWARE_TARGETS_ASSET)} TARGETS edges")
    print("Seed data loaded successfully.\n")


# ─── Step 3 (optional): Enrich from live MITRE ATT&CK ────────────────────────

async def enrich_from_mitre():
    print("Fetching MITRE ATT&CK data (this may take ~30s)...")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(MITRE_URL)
            resp.raise_for_status()
            bundle = resp.json()
    except Exception as e:
        print(f"  ✗ Could not fetch MITRE data: {e}. Skipping.")
        return

    techniques_added = 0
    for obj in bundle.get("objects", []):
        if obj.get("type") != "attack-pattern":
            continue
        ext = obj.get("external_references", [])
        att_ref = next((r for r in ext if r.get("source_name") == "mitre-attack"), None)
        if not att_ref:
            continue

        tid  = att_ref.get("external_id", "")
        name = obj.get("name", "")
        desc = obj.get("description", "")[:300]
        tactic_list = [p["phase_name"] for p in obj.get("kill_chain_phases", [])]
        tactic = tactic_list[0] if tactic_list else "unknown"

        if not tid.startswith("T"):
            continue

        run_query(
            """
            MERGE (t:Technique {id: $id})
            SET t.name = $name, t.description = $desc, t.tactic = $tactic
            """,
            {"id": tid, "name": name, "desc": desc, "tactic": tactic},
        )
        techniques_added += 1

    print(f"  ✓ Enriched {techniques_added} techniques from MITRE ATT&CK live feed")


# ─── Step 4 (optional): Enrich CVEs from NVD ─────────────────────────────────

async def enrich_from_nvd():
    api_key = os.getenv("NVD_API_KEY", "")
    headers = {"apiKey": api_key} if api_key else {}
    cve_ids = [c["id"] for c in CVES]
    print(f"Enriching {len(cve_ids)} CVEs from NVD...")

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        for cve_id in cve_ids:
            try:
                resp = await client.get(NVD_URL, params={"cveId": cve_id})
                resp.raise_for_status()
                data = resp.json()
                vuln = data.get("vulnerabilities", [])
                if not vuln:
                    continue
                cve_item = vuln[0].get("cve", {})
                metrics   = cve_item.get("metrics", {})
                cvss_data = (
                    metrics.get("cvssMetricV31", [{}])[0]
                    .get("cvssData", {})
                )
                score = cvss_data.get("baseScore", 0.0)
                run_query(
                    "MERGE (c:CVE {id: $id}) SET c.cvss = $score",
                    {"id": cve_id, "score": score},
                )
            except Exception:
                pass  # NVD rate-limits unauthenticated requests — skip silently

    print(f"  ✓ NVD enrichment complete")


# ─── Entry point ──────────────────────────────────────────────────────────────

async def main():
    create_constraints()
    load_seed_data()
    await enrich_from_mitre()
    await enrich_from_nvd()
    print("\nAll data loaded. Knowledge graph is ready!")


if __name__ == "__main__":
    asyncio.run(main())
