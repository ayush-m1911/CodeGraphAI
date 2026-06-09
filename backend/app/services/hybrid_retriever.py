import re

from app.services.retriever import (
    retrieve_context
)

from app.services.symbol_retriever import (
    find_symbol_chunks
)

from app.services.graph_context_builder import (
    build_graph_context
)


def hybrid_retrieve(
    question: str
):

    expanded_context = []

    seen = set()

    # --------------------------------
    # SYMBOL RETRIEVAL (EXACT MATCH)
    # --------------------------------

    symbols = re.findall(
        r"\b[A-Za-z_][A-Za-z0-9_\.]*\b",
        question
    )

    for symbol in symbols:

        symbol_chunks = find_symbol_chunks(
            symbol
        )

        for chunk in symbol_chunks:

            key = (
                chunk["file_path"],
                chunk.get("symbol_name")
            )

            if key in seen:
                continue

            expanded_context.append(
                chunk
            )

            seen.add(key)

    # --------------------------------
    # VECTOR RETRIEVAL
    # --------------------------------

    vector_context = retrieve_context(
        question,
        top_k=3
    )

    for chunk in vector_context:

        key = (
            chunk["file_path"],
            chunk.get("symbol_name")
        )

        if key in seen:
            continue

        expanded_context.append(
            chunk
        )

        seen.add(key)

    # --------------------------------
    # GRAPH EXPANSION
    # --------------------------------

    processed_symbols = set()

    graph_contexts = []

    for chunk in expanded_context:

        symbol_name = chunk.get(
            "symbol_name"
        )

        if not symbol_name:
            continue

        if symbol_name in processed_symbols:
            continue

        processed_symbols.add(
            symbol_name
        )

        graph_context = build_graph_context(
            symbol_name
        )

        for graph_chunk in graph_context:

            key = (
                graph_chunk["file_path"],
                graph_chunk.get("symbol_name"),
                graph_chunk.get("relation")
            )

            if key in seen:
                continue

            graph_contexts.append(
                graph_chunk
            )

            seen.add(key)

    expanded_context.extend(
        graph_contexts
    )

    return expanded_context