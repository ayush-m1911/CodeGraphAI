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

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from celery.result import AsyncResult
from app.models.schemas import RepoRequest
from app.workers.celery_app import celery_app

router = APIRouter()


@router.post("/repositories/index")
def index_repo(payload: RepoRequest):
    """
    HTTP POST endpoint to queue a repository indexing task.

    Inputs:
        payload (RepoRequest): Request payload containing the GitHub repo_url.

    Outputs:
        dict: A dictionary containing the job_id and queued status.

    Responsibilities:
        1. Receive and validate request payload containing the target repo URL.
        2. Queue the indexing task in the Celery worker queue.
        3. Return immediately with the job ID and status.
    """
    # Trigger the task asynchronously
    task = celery_app.send_task("app.tasks.index_repository", args=[payload.repo_url])
    return {
        "job_id": task.id,
        "status": "queued"
    }


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """
    HTTP GET endpoint to track the status and progress of a repository indexing task.

    Parameters:
        job_id (str): The unique identifier of the Celery task.

    Returns:
        dict: A dictionary containing the current task status and results/metadata:
              - status: Current state (PENDING, STARTED, PROGRESS, SUCCESS, FAILURE, RETRY).
              - progress: If in PROGRESS, contains {"percent": int, "description": str}.
              - result: If in SUCCESS, contains the indexing metrics.
              - error: If in FAILURE, contains error details.

    Execution Flow:
        1. Initialize Celery AsyncResult client querying by task ID.
        2. Query task state from Redis.
        3. Map state keys and build client response payload.
    """
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
        # Include retry details in the payload if they are captured
        response_data["error"] = str(result.info)

    return response_data