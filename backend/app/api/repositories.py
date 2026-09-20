"""
Purpose:
Multi-tenant repository management API router.

Responsibilities:
- Manage repository records linked to the authenticated user.
- Query user-scoped repository list and details.
- Provide isolation so users cannot view or delete another tenant's repositories.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import User, Repository
from app.models.auth_schemas import RepositoryCreate, RepositoryResponse
from app.api.auth_deps import get_current_user

router = APIRouter(prefix="/api/repositories", tags=["Repositories"])


@router.get("", response_model=List[RepositoryResponse])
def list_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns all repositories indexed by or registered to the active user.
    """
    repos = db.query(Repository).filter(Repository.user_id == current_user.id).order_by(Repository.indexed_at.desc()).all()
    return repos


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def create_repository(
    payload: RepositoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registers a new repository linked directly to current_user.id.
    """
    existing_repo = db.query(Repository).filter(
        Repository.user_id == current_user.id,
        Repository.git_url == payload.git_url
    ).first()

    if existing_repo:
        return existing_repo

    repo = Repository(
        user_id=current_user.id,
        name=payload.name,
        git_url=payload.git_url,
        is_private=payload.is_private or False,
        commit_hash=payload.commit_hash
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


@router.get("/{repo_id}", response_model=RepositoryResponse)
def get_repository(
    repo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetches details of a specific repository owned by the active user.
    """
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.user_id == current_user.id
    ).first()

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found or access denied."
        )

    return repo


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(
    repo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a repository and cascades deletion of its conversations and symbols.
    """
    repo = db.query(Repository).filter(
        Repository.id == repo_id,
        Repository.user_id == current_user.id
    ).first()

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found or access denied."
        )

    db.delete(repo)
    db.commit()
    return None
