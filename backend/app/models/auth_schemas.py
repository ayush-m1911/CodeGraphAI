"""
Purpose:
Pydantic schema definitions for authentication, multi-tenant repositories, conversations, and chat history.
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field


# ---------------------- AUTH SCHEMAS ----------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="User password (minimum 6 characters)")
    tier: Optional[str] = "free"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    tier: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str
    email: Optional[str] = None
    tier: Optional[str] = None
    exp: Optional[int] = None


# ---------------------- REPOSITORY SCHEMAS ----------------------

class RepositoryCreate(BaseModel):
    name: str
    git_url: str
    is_private: Optional[bool] = False
    commit_hash: Optional[str] = None


class RepositoryResponse(BaseModel):
    id: str
    user_id: str
    name: str
    git_url: str
    is_private: bool
    commit_hash: Optional[str] = None
    indexed_at: datetime

    class Config:
        from_attributes = True


# ---------------------- CONVERSATION & MESSAGE SCHEMAS ----------------------

class ConversationCreate(BaseModel):
    repository_id: str
    title: Optional[str] = "New Chat"


class ConversationUpdate(BaseModel):
    title: str


class MessageCreate(BaseModel):
    role: str = "user"  # 'user' or 'assistant'
    content: str
    retrieval_strategy: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = []
    token_count: Optional[int] = 0


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    retrieval_strategy: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = []
    token_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    repository_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageResponse]] = []

    class Config:
        from_attributes = True
