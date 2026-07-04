"""
Purpose:
Defines Celery background tasks used by CodeGraphAI to process codebases asynchronously.

Responsibilities:
* Exposes the index_repository_task wrapper.
* Handles progress state tracking via Celery's `self.update_state()`.
* Implements automatic retries with exponential backoff on common failures.

Interaction with other modules:
* Triggered by `index.py` POST endpoints.
* Calls `indexing_service.py` to drive the actual code analysis.
* Interacts with Redis to store state.

How it contributes to the production architecture:
Maintains application resilience. By implementing exponential backoff retries for transient errors
(e.g., git cloning limits, network timeouts, embedding API failures), it prevents pipeline crashes
in production environments.
"""

import logging
from app.workers.celery_app import celery_app
from app.services.indexing_service import index_repository as service_index_repo

logger = logging.getLogger("codegraphai.tasks")


@celery_app.task(name="app.tasks.index_repository", bind=True, max_retries=3)
def index_repository_task(self, repo_url: str, repo_id: str = None, repository_path: str = None) -> dict:
    """
    Asynchronously executes the repository indexing pipeline.

    Parameters:
        self: The Celery task instance bind context.
        repo_url (str): The public GitHub URL of the repository.
        repo_id (str, optional): A unique identifier for the repository.
        repository_path (str, optional): Custom path to clone the repository.

    Returns:
        dict: Ingestion metrics summary.

    Execution Flow:
        1. Define progress_callback to translate indexing updates into Celery task states.
        2. Execute service layer indexing coordination.
        3. Catch failures (e.g. Git clone, network, API limits) and trigger retries with exponential backoff.
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
        # Calculate exponential backoff countdown: 5s, 10s, 20s
        countdown = (2 ** self.request.retries) * 5
        logger.error(
            f"[Indexing] Attempt {attempt} failed for {repo_url}: {exc}. "
            f"Retrying in {countdown}s..."
        )
        raise self.retry(exc=exc, countdown=countdown)
