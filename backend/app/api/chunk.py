from fastapi import APIRouter

from app.services.parser import parse_repository
from app.services.chunker import create_chunks

router = APIRouter()


@router.get("/chunks")
def chunks():

    docs = parse_repository(
        "repositories/fastapi"
    )

    chunks = create_chunks(docs)

    return {
        "documents": len(docs),
        "chunks": len(chunks),
        "sample": {
            "file_path": chunks[0]["metadata"]["file_path"],
            "chunk_id": chunks[0]["metadata"]["chunk_id"],
            "chunk_length": len(chunks[0]["text"]),
            "preview": chunks[0]["text"][:300]
        }
    }