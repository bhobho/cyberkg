"""
database.py — Neo4j connection manager.
Provides a single driver instance reused across all requests.
"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
USER     = os.getenv("NEO4J_USER",     "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def get_session():
    """Return a new Neo4j session. Always close it after use."""
    return driver.session()


def close():
    driver.close()


def run_query(query: str, params: dict = None):
    """Helper: run a Cypher query and return all records as dicts."""
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]
