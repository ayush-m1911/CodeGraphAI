from typing import Optional
from pydantic import BaseModel


class RepoRequest(BaseModel):
    repo_url: str
    repo_id: Optional[str] = None


class QuestionRequest(BaseModel):
    question: str
    repository_id: Optional[str] = None
    conversation_id: Optional[str] = None