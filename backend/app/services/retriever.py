"""
Purpose:
Implements retrieval strategies for obtaining codebase context.

Role in CodeGraphAI:
Decides whether to perform an exact symbol lookup or fallback to semantic vector search based on the query structure.
It bridges raw user input to the database level, retrieving initial source-code anchors.

Key Responsibilities:
* Parse questions with regex to extract capitalised words (PascalCase symbols).
* Check the vector database for exact symbol payload matching.
* If symbol matching succeeds, return the exact definition chunks immediately.
* If no exact match is found, compute query vector embeddings and perform standard semantic cosine similarity search.

Interview Readiness Note:
- Why exact symbol lookup complements vector search: Pure vector similarity models (like BGE or Ada) can fail on specific, short,
  or similarly-spelled identifier strings (e.g. distinguishing `APIRouter` vs `APIRoute` vs `add_api_route`). Exact symbol retrieval guarantees
  that the exact AST node chunk for the class/function of interest is pulled directly, bypassing embedding retrieval noise.
"""

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
    top_k: int = 3,
    user_id: str = None,
    repository_id: str = None
):
    """
    Retrieves code chunks using symbol-aware matching or semantic vector search fallback,
    strictly partitioned by tenant user_id and repository_id.

    Args:
        question (str): User's natural language query.
        top_k (int): Number of chunks to retrieve if falling back to vector search.
        user_id (str, optional): Tenant user UUID.
        repository_id (str, optional): Repository ID.

    Returns:
        list of dict: Retrieved code context chunks containing text, file path, symbol name, and score.
    """
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
            symbol,
            user_id=user_id,
            repository_id=repository_id
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
        limit=top_k,
        user_id=user_id,
        repository_id=repository_id
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
