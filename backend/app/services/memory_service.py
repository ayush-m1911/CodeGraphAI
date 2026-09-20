"""
Purpose:
Conversational Memory Engine for multi-turn chat sessions in CodeGraphAI.

Responsibilities:
- Retrieve the sliding window buffer (K=6 turns) from PostgreSQL.
- Perform fast LLM-based co-reference resolution and query contextualization.
- Asynchronously persist user questions and assistant answers (with token count and sources metadata).
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from groq import Groq

from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.models.db_models import Conversation, Message

logger = logging.getLogger("codegraphai.memory")

# Initialize Groq client
try:
    groq_client = Groq(api_key=settings.groq_api_key)
except Exception as e:
    logger.warning(f"Groq client initialization warning: {e}")
    groq_client = None


def get_conversation_history(
    conversation_id: str,
    k: int = 6,
    db: Optional[Session] = None
) -> List[Dict[str, str]]:
    """
    Retrieves the last K message turns (chronological order) for the given conversation.
    """
    if not conversation_id:
        return []

    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        # Fetch the last K messages ordered by creation time descending, then reverse for chronological order
        recent_messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(k).all()

        chronological = list(reversed(recent_messages))
        return [
            {"role": msg.role, "content": msg.content}
            for msg in chronological
        ]
    except Exception as e:
        logger.error(f"Failed to fetch conversation history for {conversation_id}: {e}")
        return []
    finally:
        if should_close:
            db.close()


def contextualize_query(history: List[Dict[str, str]], latest_question: str) -> str:
    """
    Resolves co-references and contextualizes the latest user query given conversation history.
    E.g., "What does that function return?" -> "What does calculate_tax in billing.py return?"
    """
    if not history or len(history) == 0:
        return latest_question

    if not groq_client:
        return latest_question

    system_prompt = (
        "You are a code query contextualization and co-reference resolution engine. "
        "Given the conversation history between a developer and an AI assistant about a software codebase, "
        "and the developer's latest question which may contain ambiguous pronouns, co-references, follow-up questions, "
        "or implicit mentions (e.g., 'that function', 'the method above', 'why does it fail?', 'what parameters does it accept?', 'summarize earlier answers'), "
        "re-write the question into a standalone, fully-qualified search query that can be understood in isolation while preserving the user's intent. "
        "Do NOT answer the question. Only output the reformulated question string without quotes or preamble. "
        "If the question is already self-contained or is a meta conversational request, return a clear standalone question."
    )

    formatted_history = "\n".join([f"{turn['role'].upper()}: {turn['content']}" for turn in history])
    user_prompt = f"CONVERSATION HISTORY:\n{formatted_history}\n\nLATEST QUESTION: {latest_question}\n\nSTANDALONE QUERY:"

    try:
        # Try configured openai/gpt-oss-120b model with fast fallback candidates
        primary_model = getattr(settings, "llm_model", "openai/gpt-oss-120b")
        model_candidates = [primary_model, "openai/gpt-oss-120b", "llama-3.1-8b-instant", "llama3-8b-8192", "llama-3.3-70b-versatile"]
        unique_models = []
        for m in model_candidates:
            if m not in unique_models:
                unique_models.append(m)

        completion = None
        for model_name in unique_models:
            try:
                completion = groq_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,
                    max_tokens=150
                )
                if completion and completion.choices:
                    break
            except Exception:
                continue

        if completion and completion.choices:
            reformulated = completion.choices[0].message.content.strip()
            if reformulated:
                logger.info(f"[Co-Reference] Reformulated '{latest_question}' -> '{reformulated}'")
                return reformulated
        return latest_question
    except Exception as e:
        logger.warning(f"Co-reference resolution notice: {e}; returning raw question.")
        return latest_question



def async_save_chat_turn(
    conversation_id: str,
    user_question: str,
    assistant_answer: str,
    retrieval_strategy: Optional[str] = "hybrid",
    sources: Optional[List[Dict[str, Any]]] = None,
    token_count: int = 0,
    db: Optional[Session] = None
):
    """
    Persists the user question and assistant answer turn into PostgreSQL.
    Executed as a non-blocking background task.
    """
    if not conversation_id:
        return

    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        from datetime import timedelta
        base_time = datetime.utcnow()

        # Check last message timestamp to guarantee strict chronological progression
        last_msg = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).first()
        if last_msg and last_msg.created_at and last_msg.created_at >= base_time:
            base_time = last_msg.created_at + timedelta(milliseconds=10)

        # 1. Update conversation timestamp and title if default
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.updated_at = base_time
            default_titles = [
                "New Conversation", "New Chat", "Initial Analysis", 
                "Initial Workspace Analysis", "Untitled Thread", ""
            ]
            if conv.title in default_titles or not conv.title:
                clean_title = user_question.strip().replace("\n", " ")
                conv.title = clean_title[:45].strip() + ("..." if len(clean_title) > 45 else "")

        # 2. Add user message
        user_msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=user_question,
            retrieval_strategy=None,
            sources=[],
            token_count=len(user_question.split()),
            created_at=base_time
        )
        db.add(user_msg)

        # 3. Add assistant message (created at base_time + 1 microsecond to guarantee ordering)
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_answer,
            retrieval_strategy=retrieval_strategy,
            sources=sources or [],
            token_count=token_count if token_count > 0 else len(assistant_answer.split()),
            created_at=base_time + timedelta(milliseconds=1)
        )
        db.add(assistant_msg)

        db.commit()
        logger.info(f"[Memory] Persisted chat turn for conversation {conversation_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist chat turn for {conversation_id}: {e}")
    finally:
        if should_close:
            db.close()


