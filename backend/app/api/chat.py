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

from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from app.models.schemas import QuestionRequest
from app.models.db_models import User
from app.api.auth_deps import get_current_user_optional
from app.services.hybrid_retriever import hybrid_retrieve_detailed
from app.services.llm import generate_answer
from app.services.memory_service import (
    get_conversation_history,
    contextualize_query,
    async_save_chat_turn
)

router = APIRouter()


@router.post("/chat")
def chat(
    payload: QuestionRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Handles multi-turn conversational code queries:
    1. Retrieves sliding window history (K=6 turns) from PostgreSQL.
    2. Resolves co-references and contextualizes query for vector & graph retrieval.
    3. Executes multi-tenant hybrid retrieval and LLM generation.
    4. Persists the question/answer turn asynchronously into PostgreSQL.
    """
    user_id = str(current_user.id) if current_user else None
    repo_id = payload.repository_id
    conversation_id = payload.conversation_id

    # 1. Multi-Turn History Retrieval (K=6)
    history = []
    search_query = payload.question
    if conversation_id:
        history = get_conversation_history(conversation_id, k=6)
        # 2. Co-Reference Resolution
        search_query = contextualize_query(history, payload.question)

    # 3. Hybrid Vector & Graph Retrieval
    context, intent, strategies_used, confidence = hybrid_retrieve_detailed(
        search_query,
        user_id=user_id,
        repository_id=repo_id
    )

    # 4. LLM Generation Grounded in Context + Multi-Turn History
    answer = generate_answer(
        context,
        payload.question,
        intent=intent,
        strategies_used=strategies_used,
        history=history
    )

    sources = [
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

    # 5. Non-blocking Asynchronous Persistence into PostgreSQL
    if conversation_id:
        background_tasks.add_task(
            async_save_chat_turn,
            conversation_id=conversation_id,
            user_question=payload.question,
            assistant_answer=answer,
            retrieval_strategy=", ".join(strategies_used) if strategies_used else "hybrid",
            sources=sources,
            token_count=len(answer.split())
        )

    return {
        "answer": answer,
        "intent": intent,
        "retrieval_strategy": strategies_used,
        "confidence": confidence,
        "contextualized_query": search_query,
        "sources": sources
    }



