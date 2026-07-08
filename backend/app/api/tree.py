"""
Purpose:
Exposes diagnostic endpoints for testing and validating the parsing, chunking, exact symbol lookup, and knowledge graph components.

Role in CodeGraphAI:
Acts as a diagnostic controller to verify system mechanics (AST parsing correctness, vector store index representation,
active knowledge graph node/edge collections, and isolated retrieval performance) independently of the main chat flow.

Key Responsibilities:
* Provide testing endpoints for parsing individual Python files into AST chunks.
* Expose endpoints to fetch the active repository knowledge graph representation (nodes/edges) for the frontend workspace.
* Provide endpoints to query node neighbors or check hybrid retrieval and exact symbol lookup results.
"""

from fastapi import APIRouter

from app.services.code_chunker import (
    extract_python_chunks,
)
from app.services.repository_chunker import (
    create_code_chunks 
)
from app.services.code_graph import (
    build_repository_graph,
    save_graph
)
from app.services.graph_retriever import (
    get_neighbors
)
from app.services.hybrid_retriever import (
    hybrid_retrieve
)
from app.services.symbol_retriever import (
    find_symbol_chunks
)
router = APIRouter()


@router.get("/tree-test")
def tree_test():
    """
    Parses a sample python file (routing.py) to inspect AST parsing outputs.

    Returns:
        dict: The total count of chunks extracted and a sample of the first 3 chunks.
    """

    with open(
        "repositories/fastapi/fastapi/routing.py",
        encoding="utf8"
    ) as f:

        code = f.read()

    chunks = (
        extract_python_chunks(code, "repositories/fastapi/fastapi/routing.py")
    )

    return {
        "total": len(chunks),
        "sample": chunks[:3]
    }


@router.get("/code-chunks")
def code_chunks():
    """
    Generates AST code chunks for the entire cloned repository to inspect parser results.

    Returns:
        dict: Total chunk count and a sample list of 5 chunks.
    """

    chunks = create_code_chunks(
        "repositories/fastapi"
    )

    return {
        "total_chunks": len(chunks),
        "sample": chunks[:5]
    }

@router.get("/graph")
def graph():
    """
    Exposes the active repository knowledge graph structures (nodes and edges) for frontend rendering.

    Returns:
        dict: Complete list of nodes and edges, or an error payload if retrieval fails.
    """
    from app.services.graph_retriever import load_graph
    try:
        return load_graph()
    except Exception as e:
        return {
            "error": f"Failed to load active graph: {str(e)}",
            "nodes": [],
            "edges": []
        }

from fastapi import Query

@router.get("/graph-neighbors")
def graph_neighbors(
    symbol: str = Query(...)
):
    """
    Inspects neighbors for a given symbol in the knowledge graph.

    Args:
        symbol (str): The name of the class, method, or function symbol.

    Returns:
        dict: The target symbol and its adjacent connected nodes with relation types.
    """

    result = get_neighbors(
        symbol
    )

    return {
        "symbol": symbol,
        "neighbors": result
    }

@router.get("/hybrid")
def hybrid():
    """
    Runs a test of the hybrid retrieval mechanism on a sample query.

    Returns:
        list: Relevant AST and GraphRAG expanded context chunks.
    """

    result = hybrid_retrieve(
        "How does APIRouter work?"
    )

    return result



@router.get("/symbol")
def symbol_lookup():
    """
    Runs a test of the exact symbol lookup logic.

    Returns:
        list: Matching AST chunk references from the vector store collection.
    """

    result = find_symbol_chunks(
        "APIRouter"
    )

    return result


@router.get("/graph/symbol/{symbol_name}")
def get_symbol_graph(symbol_name: str):
    """
    Extracts the symbol node and its incoming/outgoing connections.
    """
    from app.services.graph_retriever import load_graph
    graph = load_graph()
    sub_nodes = []
    sub_edges = []
    seen_node_ids = set()
    
    for edge in graph["edges"]:
        if edge["source"] == symbol_name or edge["target"] == symbol_name:
            sub_edges.append(edge)
            seen_node_ids.add(edge["source"])
            seen_node_ids.add(edge["target"])
            
    for node in graph["nodes"]:
        if node["id"] == symbol_name or node["id"] in seen_node_ids:
            sub_nodes.append(node)
            
    return {"nodes": sub_nodes, "edges": sub_edges}


@router.get("/graph/neighbors/{symbol_name}")
def get_symbol_neighbors(symbol_name: str):
    """
    Returns adjacent neighbors for a symbol to support lazy expansion.
    """
    from app.services.graph_retriever import get_neighbors, load_graph
    neighbors = get_neighbors(symbol_name)
    graph = load_graph()
    
    sub_nodes = []
    sub_edges = []
    neighbor_names = {n["node"] for n in neighbors}
    
    for edge in graph["edges"]:
        if (edge["source"] == symbol_name and edge["target"] in neighbor_names) or \
           (edge["target"] == symbol_name and edge["source"] in neighbor_names):
            sub_edges.append(edge)
            
    for node in graph["nodes"]:
        if node["id"] == symbol_name or node["id"] in neighbor_names:
            sub_nodes.append(node)
            
    return {"nodes": sub_nodes, "edges": sub_edges}


@router.get("/graph/path")
def get_graph_path(question: str):
    """
    Traces a GraphRAG question context to return the nodes and edges that participated in the retrieval path.
    """
    from app.services.graph_retriever import load_graph
    from app.services.retrieval_orchestrator import route_query
    
    # Run intent routing to identify retrieved symbols
    strategy, retrieved_data = route_query(question)
    
    retrieved_symbols = set()
    if retrieved_data:
        for chunk in retrieved_data:
            if isinstance(chunk, dict) and chunk.get("symbol_name"):
                retrieved_symbols.add(chunk["symbol_name"])
            elif hasattr(chunk, "symbol_name"):
                retrieved_symbols.add(chunk.symbol_name)
                
    graph = load_graph()
    sub_nodes = []
    sub_edges = []
    
    for edge in graph["edges"]:
        if edge["source"] in retrieved_symbols or edge["target"] in retrieved_symbols:
            sub_edges.append(edge)
            
    for node in graph["nodes"]:
        is_retrieved = node["id"] in retrieved_symbols
        node_copy = dict(node)
        node_copy["isRetrieved"] = is_retrieved
        if is_retrieved or node["id"] in {e["source"] for e in sub_edges} or node["id"] in {e["target"] for e in sub_edges}:
            sub_nodes.append(node_copy)
            
    return {"nodes": sub_nodes, "edges": sub_edges}
