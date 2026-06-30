"""
Purpose:
Coordinates codebase context retrieval by delegating to the Intent-Aware Retrieval Orchestrator.

Role in CodeGraphAI:
Exposes the entrypoint for context retrieval in the GraphRAG pipeline. It routes queries through the
orchestration service to perform intent classification, specialized strategy execution, and context ranking.

GraphRAG Workflow:

Question
│
▼
Intent Detection
│
▼
Retrieval Orchestrator
│
┌──────┼─────────────┐
│      │             │
▼      ▼             ▼
Symbol  Call Graph    Architecture
Strategy Strategy     Strategy
│      │             │
└──────┴─────────────┘
│
▼
Context Ranking
│
▼
Prompt Builder
│
▼
Groq LLM
│
▼
Source-Grounded Answer
"""

from app.services.retrieval_orchestrator import RetrievalOrchestrator

# Instantiate a single global orchestrator instance
orchestrator = RetrievalOrchestrator()


def hybrid_retrieve(question: str):
    """
    Executes intent-aware retrieval for a query, returning only the ranked context.
    This remains fully backward compatible with the original signature.

    Args:
        question (str): User's natural language question.

    Returns:
        list of dict: Ranked and deduplicated code context chunks.
    """
    context, _, _ = orchestrator.orchestrate(question)
    return context


def hybrid_retrieve_detailed(question: str) -> tuple:
    """
    Executes intent-aware retrieval for a query, returning the ranked context along with
    the detected intent and the list of retrieval strategies executed.

    Args:
        question (str): User's natural language question.

    Returns:
        tuple: (context: list of dict, intent: str, strategies_used: list of str)
    """
    return orchestrator.orchestrate(question)