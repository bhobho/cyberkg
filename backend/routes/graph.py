"""
graph.py — Returns the full knowledge graph (nodes + edges) for visualization.
The frontend uses this to render the interactive force-directed graph.
"""
from fastapi import APIRouter
from database import run_query

router = APIRouter(prefix="/api/graph", tags=["Graph"])

# Maps Neo4j label → color used by the frontend
NODE_COLORS = {
    "Malware":   "#ef4444",   # red
    "Technique": "#f97316",   # orange
    "CVE":       "#eab308",   # yellow
    "Asset":     "#3b82f6",   # blue
}


@router.get("")
def get_full_graph():
    """
    Returns all nodes and relationships in a format ready for react-force-graph.
    Response shape: { nodes: [...], links: [...] }
    """
    # Fetch all nodes with their labels
    node_query = """
    MATCH (n)
    RETURN
      id(n)      AS neo_id,
      labels(n)  AS labels,
      properties(n) AS props
    """
    raw_nodes = run_query(node_query)

    nodes = []
    for row in raw_nodes:
        label = row["labels"][0] if row["labels"] else "Unknown"
        props = row["props"]
        nodes.append({
            "id":    props.get("id", str(row["neo_id"])),
            "label": label,
            "name":  props.get("name", props.get("id", "?")),
            "color": NODE_COLORS.get(label, "#888"),
            **props,
        })

    # Fetch all relationships
    edge_query = """
    MATCH (a)-[r]->(b)
    RETURN
      properties(a).id AS source,
      properties(b).id AS target,
      type(r)          AS type
    """
    raw_edges = run_query(edge_query)

    links = [
        {"source": row["source"], "target": row["target"], "type": row["type"]}
        for row in raw_edges
        if row["source"] and row["target"]
    ]

    return {"nodes": nodes, "links": links}


@router.get("/stats")
def get_stats():
    """Returns node and edge counts — used by the dashboard header."""
    counts = run_query("""
        MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count
    """)
    edge_count = run_query("MATCH ()-[r]->() RETURN count(r) AS count")
    return {
        "nodes": {row["label"]: row["count"] for row in counts},
        "edges": edge_count[0]["count"] if edge_count else 0,
    }
