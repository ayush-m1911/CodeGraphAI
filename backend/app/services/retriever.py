import re

from app.services.embeddings import (
    embedding_model
)

from app.services.vector_store import (
    search_chunks,
    search_by_symbol
)


def retrieve_context(
    question: str,
    top_k: int = 3
):
    contexts = []

    # -------------------------
    # SYMBOL-AWARE RETRIEVAL
    # -------------------------

    match = re.search(
        r"([A-Z][A-Za-z0-9_]*)",
        question
    )

    if match:

        symbol = match.group(1)

        symbol_results = search_by_symbol(
            symbol
        )

        if symbol_results:

            for result in symbol_results:

                contexts.append({
                    "text": result.payload["text"],
                    "file_path": result.payload["file_path"],
                    "symbol_name": result.payload.get(
                        "symbol_name"
                    ),
                    "chunk_type": result.payload.get(
                        "chunk_type"
                    ),
                    "score": getattr(
                        result,
                        "score",
                        1.0
                    )
                })

            return contexts

    # -------------------------
    # VECTOR SEARCH FALLBACK
    # -------------------------

    query_vector = (
        embedding_model.embed_query(
            question
        )
    )

    results = search_chunks(
        query_vector,
        limit=top_k
    )

    for result in results:

        contexts.append({
            "text": result.payload["text"],
            "file_path": result.payload["file_path"],
            "symbol_name": result.payload.get(
                "symbol_name"
            ),
            "chunk_type": result.payload.get(
                "chunk_type"
            ),
            "score": result.score
        })

    return contexts