from fastapi import APIRouter

from app.models.schemas import (
    QuestionRequest
)

from app.services.hybrid_retriever import hybrid_retrieve
from app.services.llm import (
    generate_answer
)


router = APIRouter()


@router.post("/chat")
def chat(
    payload: QuestionRequest
):

    context = hybrid_retrieve(
        payload.question
    )

    answer = generate_answer(
        context,
        payload.question
    )

    return {
    "answer": answer,

    "sources": [
        {
            "file_path": c["file_path"],
            "symbol_name": c.get("symbol_name"),
            "chunk_type": c.get("chunk_type"),
            "relation": c.get("relation"),
            "score": c.get("score", "graph"),
            "text": c.get("text", "")
        }
        for c in context
    ]
}
