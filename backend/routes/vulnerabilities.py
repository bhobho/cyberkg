"""
vulnerabilities.py — CVE-centric queries.

Answer: "Which malware families exploit this CVE, and what assets are at risk?"
"""
from fastapi import APIRouter, Query, HTTPException
from database import run_query

router = APIRouter(prefix="/api/vulnerabilities", tags=["Vulnerabilities"])


@router.get("")
def get_vulnerability(cve: str = Query(..., description="CVE ID, e.g. CVE-2017-0144")):
    """
    Given a CVE ID, returns:
    - CVE details (CVSS score, description)
    - Techniques that exploit it
    - Malware families that use those techniques
    - Assets affected by this CVE
    """
    query = """
    MATCH (c:CVE)
    WHERE toLower(c.id) CONTAINS toLower($cve)

    OPTIONAL MATCH (t:Technique)-[:EXPLOITS]->(c)
    OPTIONAL MATCH (m:Malware)-[:USES_TECHNIQUE]->(t)
    OPTIONAL MATCH (c)-[:AFFECTS]->(a:Asset)

    RETURN
      c.id          AS cve_id,
      c.cvss        AS cvss,
      c.description AS description,
      collect(DISTINCT t.name) AS techniques,
      collect(DISTINCT m.name) AS malware_families,
      collect(DISTINCT {name: a.name, type: a.type}) AS affected_assets
    """
    rows = run_query(query, {"cve": cve})

    if not rows or rows[0]["cve_id"] is None:
        raise HTTPException(status_code=404, detail=f"CVE '{cve}' not found")

    return rows[0]


@router.get("/list")
def list_cves():
    """Returns all CVEs ordered by CVSS score descending."""
    return run_query("""
        MATCH (c:CVE)
        RETURN c.id AS id, c.cvss AS cvss, c.description AS description
        ORDER BY c.cvss DESC
    """)


@router.get("/malware/{malware_name}")
def get_malware_detail(malware_name: str):
    """
    Given a malware name, returns all techniques it uses and CVEs it can exploit.
    """
    query = """
    MATCH (m:Malware)
    WHERE toLower(m.name) CONTAINS toLower($name)

    OPTIONAL MATCH (m)-[:USES_TECHNIQUE]->(t:Technique)
    OPTIONAL MATCH (t)-[:EXPLOITS]->(c:CVE)
    OPTIONAL MATCH (m)-[:TARGETS]->(a:Asset)

    RETURN
      m.name        AS malware,
      m.type        AS malware_type,
      m.description AS description,
      collect(DISTINCT {id: t.id, name: t.name, tactic: t.tactic}) AS techniques,
      collect(DISTINCT c.id) AS cves,
      collect(DISTINCT a.name) AS targets
    """
    rows = run_query(query, {"name": malware_name})
    if not rows or rows[0]["malware"] is None:
        raise HTTPException(status_code=404, detail=f"Malware '{malware_name}' not found")
    return rows[0]


@router.get("/malware")
def list_malware():
    """Returns all malware nodes."""
    return run_query("MATCH (m:Malware) RETURN m.id AS id, m.name AS name, m.type AS type ORDER BY m.name")
