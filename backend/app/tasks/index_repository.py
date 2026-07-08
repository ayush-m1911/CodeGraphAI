"""
Purpose:
Defines Celery background tasks used by CodeGraphAI to process codebases asynchronously.

Responsibilities:
* Exposes the index_repository_task wrapper.
* Handles progress state tracking via Celery's `self.update_state()`.
* Implements robust retry filters ensuring retries occur only on transient failures (git clone, network, DB limits).
* Prevents infinite retry loops on syntax errors or code execution bugs.

Failure handling:
* Differentiates transient and non-transient exceptions.
* deterministic bugs (KeyError, ValueError, syntax error) fail cleanly with reported diagnostic logs without retrying.

Inputs:
* Repository URL path, owner ID slug, and filesystem parameters.

Outputs:
* dict: Consolidated ingestion statistics.

Interaction with other modules:
* Triggered by index API endpoints.
* Invokes `indexing_service.py` to run repository ingestion.
"""

import logging
import socket
from app.workers.celery_app import celery_app
from app.services.indexing_service import index_repository as service_index_repo

logger = logging.getLogger("codegraphai.tasks")


def is_transient_failure(exc: Exception) -> bool:
    """
    Checks if an exception is a transient infrastructure or connection failure.
    Deterministic codebase parsing errors or coding bugs return False.
    """
    err_str = str(exc).lower()
    
    # Deterministic parser or python bugs - do not retry
    non_transient_keywords = [
        "keyerror", "parser", "syntaxerror", "indentationerror", 
        "unsupported syntax", "attributeerror", "valueerror", "typeerror",
        "assertionerror", "indexerror"
    ]
    if any(k in err_str for k in non_transient_keywords):
        return False
        
    if isinstance(exc, (KeyError, ValueError, TypeError, AttributeError, SyntaxError, IndexError, AssertionError)):
        return False
        
    # Standard connection exceptions are transient
    if isinstance(exc, (ConnectionError, TimeoutError, socket.timeout, socket.error)):
        return True
        
    # Infrastructure transient triggers
    transient_keywords = [
        "clone", "git", "network", "connection", "timeout", "unavailable", 
        "redis", "qdrant", "groq", "rate limit", "http", "socket"
    ]
    if any(k in err_str for k in transient_keywords):
        return True
        
    return False


@celery_app.task(name="app.tasks.index_repository", bind=True, max_retries=3)
def index_repository_task(self, repo_url: str, repo_id: str = None, repository_path: str = None) -> dict:
    """
    Asynchronously executes the repository indexing pipeline.
    """
    attempt = self.request.retries + 1
    logger.info(f"[Indexing] Starting async indexing task for: {repo_url} (Attempt {attempt}/3)")
    
    # Progress callback function mapped to Celery update_state
    def progress_callback(percent: int, description: str):
        self.update_state(
            state="PROGRESS",
            meta={
                "percent": percent,
                "description": description
            }
        )
        logger.info(f"[Indexing] Progress {percent}%: {description}")

    try:
        summary = service_index_repo(
            repo_url=repo_url,
            repo_id=repo_id,
            repository_path=repository_path,
            progress_callback=progress_callback
        )
        logger.info(f"[Indexing] Completed indexing task successfully for: {repo_url}")
        return summary
    except Exception as exc:
        # Determine whether to retry or fail gracefully
        if is_transient_failure(exc):
            countdown = (2 ** self.request.retries) * 5
            logger.error(
                f"[Indexing] Attempt {attempt} failed with transient error: {exc}. "
                f"Retrying in {countdown}s..."
            )
            raise self.retry(exc=exc, countdown=countdown)
        else:
            logger.error(
                f"[Indexing] Attempt {attempt} failed with non-transient, deterministic error: {exc}. "
                "Failing task gracefully without retry to avoid clogging background workers."
            )
            # Record diagnostics summary
            raise exc
