"""
Purpose:
Exposes API endpoints for interacting with the codebase using hybrid chat retrieval.

Role in CodeGraphAI:
Connects the user's natural language queries with the backend's GraphRAG hybrid retrieval system and LLM generation pipeline.
It orchestrates retrieval of source contexts and queries the LLM for source-grounded answers.

Key Responsibilities:
* Expose POST /chat endpoint.
* Invoke hybrid retrieve services to fetch relevant AST chunks, symbol lookup, and knowledge graph expansions.
* Pass retrieved contexts along with the user's question to the LLM backend.
* Return structured response containing the generated text and referenced source blocks (with text, scores, and metadata) to the frontend.
"""

from fastapi import APIRouter

from app.models.schemas import (
    QuestionRequest
)

from app.services.hybrid_retriever import hybrid_retrieve_detailed
from app.services.llm import (
    generate_answer
)


router = APIRouter()


@router.post("/chat")
def chat(
    payload: QuestionRequest
):
    """
    Handles user queries about the code repository, executes hybrid context retrieval, and generates responses.

    Workflow:
    1. Extract question from request payload.
    2. Invoke Intent-Aware Retrieval Orchestrator via hybrid_retrieve_detailed.
    3. Feed context chunks, question, intent, and strategies to LLM generator.
    4. Compile list of sources indicating file path, symbol, type, relation, score, and code text.
    5. Return finalized answer, intent, strategies, and source blocks.

    Args:
        payload (QuestionRequest): Payload containing the user's question.

    Returns:
        dict: A dictionary containing "answer" (str), "intent" (str), "retrieval_strategy" (list of str), and "sources" (list of dicts).
    """

    context, intent, strategies_used, confidence = hybrid_retrieve_detailed(
        payload.question
    )

    answer = generate_answer(
        context,
        payload.question,
        intent=intent,
        strategies_used=strategies_used
    )

    return {
    "answer": answer,
    "intent": intent,
    "retrieval_strategy": strategies_used,
    "confidence": confidence,

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


