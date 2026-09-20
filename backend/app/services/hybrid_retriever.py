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


def hybrid_retrieve(question: str, user_id: str = None, repository_id: str = None):
    """
    Executes intent-aware retrieval for a query, returning only the ranked context.
    """
    context, _, _, _ = orchestrator.orchestrate(question, user_id=user_id, repository_id=repository_id)
    return context


def hybrid_retrieve_detailed(
    question: str,
    user_id: str = None,
    repository_id: str = None
) -> tuple:
    """
    Executes intent-aware retrieval for a query with tenant isolation.
    """
    return orchestrator.orchestrate(question, user_id=user_id, repository_id=repository_id)