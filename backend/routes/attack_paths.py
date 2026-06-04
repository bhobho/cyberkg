"""
attack_paths.py — Finds attack paths that lead to a given asset.

The graph traversal answer: "Which malware families can reach this asset,
and what is the full attack chain from malware → technique → CVE → asset?"
"""
from fastapi import APIRouter, Query, HTTPException
from database import run_query

router = APIRouter(prefix="/api/attack-paths", tags=["Attack Paths"])


@router.get("")
def get_attack_paths(asset: str = Query(..., description="Asset name or ID, e.g. 'Windows Server 2019'")):
    """
    Returns full attack chains targeting the given asset.
    Each chain: Malware → Technique → CVE → Asset
    """
    # Try matching by name first, then by ID
    query = """
    MATCH (a:Asset)
    WHERE toLower(a.name) CONTAINS toLower($search)
       OR toLower(a.id)   CONTAINS toLower($search)

    OPTIONAL MATCH path1 = (m:Malware)-[:USES_TECHNIQUE]->(t:Technique)-[:EXPLOITS]->(c:CVE)-[:AFFECTS]->(a)
    OPTIONAL MATCH (m2:Malware)-[:TARGETS]->(a)

    WITH a,
         collect(DISTINCT {
             malware:   m.name,
             malware_id: m.id,
             technique: t.name,
             technique_id: t.id,
             tactic:    t.tactic,
             cve:       c.id,
             cvss:      c.cvss
         }) AS chains,
         collect(DISTINCT m2.name) AS direct_targets

    RETURN a.name AS asset, a.type AS asset_type, chains, direct_targets
    """
    rows = run_query(query, {"search": asset})

    if not rows or rows[0]["asset"] is None:
        raise HTTPException(status_code=404, detail=f"Asset '{asset}' not found in the graph")

    row = rows[0]
    chains = [c for c in row["chains"] if c.get("malware")]

    return {
        "asset":          row["asset"],
        "asset_type":     row["asset_type"],
        "attack_chains":  chains,
        "direct_targets": row["direct_targets"],
        "risk_score":     _risk_score(chains),
    }


@router.get("/all-assets")
def list_assets():
    """Returns all assets so the frontend can populate a dropdown."""
    rows = run_query("MATCH (a:Asset) RETURN a.id AS id, a.name AS name, a.type AS type ORDER BY a.name")
    return rows


def _risk_score(chains: list) -> str:
    """Rough risk label based on CVSS scores in attack chains."""
    if not chains:
        return "Low"
    scores = [c.get("cvss", 0) or 0 for c in chains]
    max_score = max(scores) if scores else 0
    if max_score >= 9.0:
        return "Critical"
    if max_score >= 7.0:
        return "High"
    if max_score >= 4.0:
        return "Medium"
    return "Low"
