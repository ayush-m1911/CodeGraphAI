from fastapi import APIRouter

from app.services.parser import parse_repository
from app.services.chunker import create_chunks
from app.services.embeddings import embedding_model

from app.services.vector_store import (
    create_collection,
    store_chunks
)

router = APIRouter()


@router.get("/index")
def index_repo():

    from app.services.repository_chunker import (
    create_code_chunks
)
    docs = parse_repository(
    "repositories/fastapi"
)
    print("TOTAL DOCS:", len(docs))

    for doc in docs[:50]:
     print(doc["file_path"])
    chunks = create_code_chunks(
    "repositories/fastapi"
)
    for doc in docs:
     if "routing.py" in doc["file_path"]:
        print("ROUTING EXISTS")
    texts = [
    chunk["text"]
    for chunk in chunks
]

    vectors = embedding_model.embed_documents(
    texts
)

    create_collection(
        len(vectors[0])
    )

    store_chunks(
        chunks,
        vectors
    )

    return {
        "documents": len(docs),
        "chunks": len(chunks),
        "indexed": len(vectors)
    }