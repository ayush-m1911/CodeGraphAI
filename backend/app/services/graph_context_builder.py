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