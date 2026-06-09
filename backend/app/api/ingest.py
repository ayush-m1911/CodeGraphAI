from fastapi import APIRouter, HTTPException

from app.models.schemas import RepoRequest
from app.services.github_loader import clone_repository

router = APIRouter()


@router.post("/ingest")
def ingest_repository(payload: RepoRequest):

    try:

        result = clone_repository(
            payload.repo_url
        )

        return {
            "status": "success",
            "repository": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )