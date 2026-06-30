"""
Purpose:
Implements exact symbol lookup in the vector store database.

Role in CodeGraphAI:
Enables direct, exact lookups for fully-qualified class, method, or top-level function names, bypassing semantic search completely
when a user queries specific identifiers (e.g. APIRouter).

Key Responsibilities:
* Encapsulate exact match queries against Qdrant database payload filters.
* Map database payload results to formatted dictionary representations including text, file path, symbol name, and score.
"""

from app.services.vector_store import (
    search_by_symbol
)


def find_symbol_chunks(
    symbol_name: str
):
    """
    Looks up code chunks by exact symbol matching in the vector database.

    Args:
        symbol_name (str): Fully qualified symbol name (e.g. APIRouter, APIRouter.get).

    Returns:
        list of dict: Matching chunk records with details (text, file_path, symbol_name, chunk_type, score).
    """

    results = search_by_symbol(
        symbol_name
    )

    chunks = []

    for result in results:

        payload = result.payload

        chunks.append(
            {
                "text":
                    payload["text"],

                "file_path":
                    payload["file_path"],

                "symbol_name":
                    payload.get(
                        "symbol_name"
                    ),

                "chunk_type":
                    payload.get(
                        "chunk_type"
                    ),

                "score":
                    1.0
            }
        )

    return chunks