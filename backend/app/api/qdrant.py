from fastapi import APIRouter

from app.services.embeddings import embedding_model
from app.services.vector_store import create_collection

router = APIRouter()


@router.get("/qdrant/init")
def init_qdrant():

    sample_vector = embedding_model.embed_query(
        "hello world"
    )

    create_collection(
        len(sample_vector)
    )

    return {
        "message": "Collection Created",
        "dimensions": len(sample_vector)
    }