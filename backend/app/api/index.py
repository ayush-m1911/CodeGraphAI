"""
Purpose:
Exposes HTTP API endpoints to index codebases asynchronously.

Responsibilities:
* Exposes the POST /repositories/index endpoint to queue repository indexing tasks.
* Exposes the GET /jobs/{job_id} endpoint to track background task execution status.
* Interacts with Celery and Redis to dispatch and monitor task states.

How it fits into the overall pipeline:
Acts as the entrypoint for frontend triggers. It schedules heavy repository cloning
and parsing operations on background workers, allowing the API server to remain responsive.
"""

import uuid
import threading
import logging
from typing import Dict, Any
from fastapi import APIRouter
from celery.result import AsyncResult
from app.models.schemas import RepoRequest
from app.workers.celery_app import celery_app, is_redis_available
from app.services.indexing_service import index_repository

logger = logging.getLogger("codegraphai.api.index")
router = APIRouter()

# In-memory status store for standalone / local executions without Redis
_local_jobs: Dict[str, Dict[str, Any]] = {}


def _run_local_indexing(job_id: str, repo_url: str):
    """Executes the repository indexing pipeline in a background thread."""
    def progress_callback(percent: int, description: str):
        _local_jobs[job_id] = {
            "status": "PROGRESS",
            "progress": {
                "percent": percent,
                "description": description
            }
        }
        logger.info(f"[Local Job {job_id[:8]}] Progress {percent}%: {description}")

    try:
        summary = index_repository(
            repo_url=repo_url,
            progress_callback=progress_callback
        )
        _local_jobs[job_id] = {
            "status": "SUCCESS",
            "result": summary
        }
        logger.info(f"[Local Job {job_id[:8]}] Indexing completed successfully.")
    except Exception as exc:
        logger.error(f"[Local Job {job_id[:8]}] Indexing failed: {exc}")
        _local_jobs[job_id] = {
            "status": "FAILURE",
            "error": str(exc)
        }


@router.post("/repositories/index")
def index_repo(payload: RepoRequest):
    """
    HTTP POST endpoint to queue a repository indexing task.
    Uses Celery worker queue if Redis is available, otherwise uses an in-process background worker thread.
    """
    if is_redis_available:
        task = celery_app.send_task("app.tasks.index_repository", args=[payload.repo_url])
        return {
            "job_id": task.id,
            "status": "queued"
        }
    else:
        job_id = str(uuid.uuid4())
        _local_jobs[job_id] = {
            "status": "PROGRESS",
            "progress": {
                "percent": 5,
                "description": "Initializing ingestion pipeline..."
            }
        }
        thread = threading.Thread(
            target=_run_local_indexing,
            args=(job_id, payload.repo_url),
            daemon=True
        )
        thread.start()
        return {
            "job_id": job_id,
            "status": "queued"
        }


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """
    HTTP GET endpoint to track the status and progress of a repository indexing task.
    """
    if job_id in _local_jobs:
        return _local_jobs[job_id]

    result = AsyncResult(job_id, app=celery_app)
    
    response_data = {
        "status": result.state
    }

    if result.state == "SUCCESS":
        response_data["result"] = result.result
    elif result.state == "FAILURE":
        response_data["error"] = str(result.info)
    elif result.state == "PROGRESS":
        response_data["progress"] = result.info
    elif result.state == "RETRY":
        response_data["error"] = str(result.info)

    return response_data