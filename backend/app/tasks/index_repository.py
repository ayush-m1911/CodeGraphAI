"""
Purpose:
Defines Celery background tasks used by CodeGraphAI to process codebases asynchronously.

Responsibilities:
* Exposes the index_repository_task wrapper.
* Invokes the internal Indexing Service without duplicating parsing logic.
* Relays task completion statuses back to the Celery executor.

How it communicates with Redis:
When a task is queued, Celery serializes the arguments and pushes them to Redis.
Once executed, the worker writes the task execution summary (files/chunks counts)
back to Redis under the task ID key.

How it communicates with Celery:
Uses the @celery_app.task decorator to register the function as a Celery-managed task execution unit.
"""

from app.workers.celery_app import celery_app
from app.services.indexing_service import index_repository as service_index_repo


@celery_app.task(name="app.tasks.index_repository", bind=True)
def index_repository_task(self, repo_url: str) -> dict:
    """
    Asynchronously executes the repository indexing pipeline.

    Inputs:
        self: The Celery task instance bind context.
        repo_url (str): The public GitHub URL of the repository.

    Outputs:
        dict: Ingestion metrics summary containing counts of files, chunks, nodes, and edges indexed.

    Responsibilities:
        * Delegates repository cloning, parsing, indexing, and uploads to the service layer.
        * Propagates service response values or raises exceptions on failure to Celery worker handlers.
    """
    print(f"Starting async indexing job for: {repo_url}")
    summary = service_index_repo(repo_url)
    print(f"Finished async indexing job for: {repo_url}")
    return summary
