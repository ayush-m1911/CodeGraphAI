"""
Purpose:
Multi-tenant Neo4j graph database driver and partitioned Cypher traversal service.

Responsibilities:
- Manage resilient connection pool to Neo4j graph database.
- Enforce tenant isolation by strictly partitioning every node and relationship with (user_id, repo_id).
- Upsert AST symbols using PostgreSQL code_symbols.id as the canonical Node ID (Unified Entity UUID).
- Execute sandboxed Cypher queries for caller/callee discovery and graph traversal.
"""

import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver
from app.config import settings

logger = logging.getLogger("codegraphai.neo4j")

_driver: Optional[Driver] = None


def get_neo4j_driver() -> Optional[Driver]:
    """
    Returns the singleton Neo4j driver instance, initializing lazily.
    Returns None with a logged warning if connection fails.
    """
    global _driver
    if _driver is not None:
        return _driver

    try:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_lifetime=30 * 60,
            max_connection_pool_size=50,
            connection_acquisition_timeout=5.0
        )
        # Verify connectivity
        _driver.verify_connectivity()
        logger.info(f"Connected to Neo4j database at {settings.neo4j_uri}")
        _init_constraints(_driver)
        return _driver
    except Exception as e:
        logger.warning(f"Neo4j driver connection unavailable at {settings.neo4j_uri}: {e}")
        return None


def _init_constraints(driver: Driver):
    """
    Creates composite uniqueness and search indexes on (user_id, repo_id, id).
    """
    queries = [
        """
        CREATE CONSTRAINT symbol_tenant_unique IF NOT EXISTS
        FOR (s:Symbol) REQUIRE (s.user_id, s.repo_id, s.id) IS UNIQUE
        """,
        """
        CREATE INDEX symbol_tenant_name_idx IF NOT EXISTS
        FOR (s:Symbol) ON (s.user_id, s.repo_id, s.name)
        """
    ]
    with driver.session() as session:
        for q in queries:
            try:
                session.run(q)
            except Exception as ex:
                logger.debug(f"Constraint setup notice: {ex}")


def sync_graph_to_neo4j(
    user_id: str,
    repo_id: str,
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]]
) -> bool:
    """
    Upserts graph nodes and relationships in Neo4j with strict tenant partitioning.
    Uses Unified Entity UUID (PostgreSQL code_symbols.id) as the Node id.
    """
    driver = get_neo4j_driver()
    if not driver:
        logger.warning("Neo4j driver unavailable; skipping graph database sync.")
        return False

    with driver.session() as session:
        # 1. Upsert Nodes in Batches
        node_query = """
        UNWIND $batch AS node
        MERGE (s:Symbol {id: node.id, user_id: $user_id, repo_id: $repo_id})
        SET s.name = node.name,
            s.qualified_name = node.qualified_name,
            s.file_path = node.file_path,
            s.symbol_type = node.symbol_type,
            s.start_line = node.start_line,
            s.end_line = node.end_line
        """
        batch_nodes = []
        for n in nodes:
            batch_nodes.append({
                "id": str(n.get("id")),
                "name": str(n.get("name", "")),
                "qualified_name": str(n.get("qualified_name", n.get("name", ""))),
                "file_path": str(n.get("file_path", "")),
                "symbol_type": str(n.get("symbol_type", "function")),
                "start_line": int(n.get("start_line", 1)),
                "end_line": int(n.get("end_line", 1))
            })

        if batch_nodes:
            session.run(node_query, batch=batch_nodes, user_id=user_id, repo_id=repo_id)

        # 2. Upsert Relationships
        edge_query = """
        UNWIND $batch AS edge
        MATCH (source:Symbol {name: edge.source, user_id: $user_id, repo_id: $repo_id})
        MATCH (target:Symbol {name: edge.target, user_id: $user_id, repo_id: $repo_id})
        MERGE (source)-[r:CALLS]->(target)
        """
        batch_edges = []
        for e in edges:
            batch_edges.append({
                "source": str(e.get("source")),
                "target": str(e.get("target"))
            })

        if batch_edges:
            session.run(edge_query, batch=batch_edges, user_id=user_id, repo_id=repo_id)

    logger.info(f"[Neo4j] Synced {len(batch_nodes)} nodes and {len(batch_edges)} edges for tenant {user_id}/{repo_id}")
    return True


def get_callees_cypher(user_id: str, repo_id: str, symbol_name: str) -> List[Dict[str, Any]]:
    """
    Queries callees of a symbol scoped strictly to the tenant's repository.
    """
    driver = get_neo4j_driver()
    if not driver:
        return []

    query = """
    MATCH (s:Symbol {name: $name, user_id: $user_id, repo_id: $repo_id})-[:CALLS]->(target:Symbol)
    WHERE target.user_id = $user_id AND target.repo_id = $repo_id
    RETURN target.id AS id, target.name AS name, target.file_path AS file_path, target.symbol_type AS symbol_type
    """
    with driver.session() as session:
        result = session.run(query, name=symbol_name, user_id=user_id, repo_id=repo_id)
        return [record.data() for record in result]


def get_callers_cypher(user_id: str, repo_id: str, symbol_name: str) -> List[Dict[str, Any]]:
    """
    Queries callers of a symbol scoped strictly to the tenant's repository.
    """
    driver = get_neo4j_driver()
    if not driver:
        return []

    query = """
    MATCH (caller:Symbol)-[:CALLS]->(s:Symbol {name: $name, user_id: $user_id, repo_id: $repo_id})
    WHERE caller.user_id = $user_id AND caller.repo_id = $repo_id
    RETURN caller.id AS id, caller.name AS name, caller.file_path AS file_path, caller.symbol_type AS symbol_type
    """
    with driver.session() as session:
        result = session.run(query, name=symbol_name, user_id=user_id, repo_id=repo_id)
        return [record.data() for record in result]
