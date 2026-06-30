"""
Purpose:
Constructs prompt context from neighboring symbols in the knowledge graph.

Role in CodeGraphAI:
Translates logical graph node entities retrieved during neighborhood expansion into actual, human-readable source code.
It maps each neighbor symbol name back to its corresponding source-code chunk definition, building a graph-enriched code context.

Key Responsibilities:
* Retrieve neighboring nodes and edges for a given symbol name.
* Look up code chunks from the vector database for each neighbor symbol node.
* Formulate context records containing symbol names, structural relationships (e.g. calls, contains), target files, chunk types, and raw code text.
"""

from app.services.graph_retriever import (
    get_neighbors
)

from app.services.symbol_retriever import (
    find_symbol_chunks
)


def build_graph_context(
    symbol_name: str,
    max_neighbors: int = 10
):
    """
    Builds context chunks for neighboring nodes connected to a target symbol.

    Args:
        symbol_name (str): Fully qualified symbol name to expand from.
        max_neighbors (int): Maximum number of neighbors to query (defaults to 10).

    Returns:
        list of dict: Graph-expanded source context chunks with relation and source fields.
    """

    neighbors = get_neighbors(
        symbol_name,
        max_neighbors
    )

    graph_context = []

    for neighbor in neighbors:

        node_name = neighbor.get(
            "node"
        )

        relation = neighbor.get(
            "relation"
        )

        symbol_chunks = (
            find_symbol_chunks(
                node_name
            )
        )

        for chunk in symbol_chunks:

            graph_context.append(
                {
                    "symbol_name": node_name,
                    "relation": relation,
                    "graph_source": symbol_name,
                    "file_path": chunk[
                        "file_path"
                    ],
                    "chunk_type": chunk[
                        "chunk_type"
                    ],
                    "text": chunk[
                        "text"
                    ]
                }
            )

    return graph_context