from app.services.vector_store import (
    search_by_symbol
)


def find_symbol_chunks(
    symbol_name: str
):
    """
    Exact symbol lookup.

    Examples:
    APIRouter
    APIRouter.get
    add_api_route
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