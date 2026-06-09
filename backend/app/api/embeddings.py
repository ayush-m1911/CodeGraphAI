from fastapi import APIRouter
from app.services.embeddings import embedding_model

router = APIRouter()

@router.get("/embed")
def embed():

    vector = embedding_model.embed_query(
        "How does authentication work?"
    )

    return {
        "dimensions": len(vector),
        "sample": vector[:10]
    }