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

    with open(
        "repositories/fastapi/fastapi/routing.py",
        encoding="utf8"
    ) as f:

        code = f.read()

    chunks = (
        extract_python_chunks(code)
    )

    return {
        "total": len(chunks),
        "sample": chunks[:3]
    }


@router.get("/code-chunks")
def code_chunks():

    chunks = create_code_chunks(
        "repositories/fastapi"
    )

    return {
        "total_chunks": len(chunks),
        "sample": chunks[:5]
    }

@router.get("/graph")
def graph():

    graph = build_repository_graph(
        "repositories/fastapi"
    )

    save_graph(graph)

    return {
        "nodes": len(
            graph["nodes"]
        ),
        "edges": len(
            graph["edges"]
        ),
        "sample_nodes":
        graph["nodes"][:10],
        "sample_edges":
        graph["edges"][:10]
    }

from fastapi import Query

@router.get("/graph-neighbors")
def graph_neighbors(
    symbol: str = Query(...)
):

    result = get_neighbors(
        symbol
    )

    return {
        "symbol": symbol,
        "neighbors": result
    }

@router.get("/hybrid")
def hybrid():

    result = hybrid_retrieve(
        "How does APIRouter work?"
    )

    return result



@router.get("/symbol")
def symbol_lookup():

    result = find_symbol_chunks(
        "APIRouter"
    )

    return result