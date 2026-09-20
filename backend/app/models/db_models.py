"""
Purpose:
Defines the relational PostgreSQL schema and SQLAlchemy ORM models for CodeGraphAI multi-tenancy.

Models:
- User: Multi-tenant user entity with bcrypt password hash and subscription tier.
- Repository: Git repositories registered/indexed by a tenant.
- Conversation: Multi-turn chat session sandboxed to a user and repository.
- Message: Individual turn in a chat conversation with retrieval strategy metadata & token counts.
- CodeSymbol: AST/Tree-sitter extracted symbol identifiers mapped to graph nodes & vector points.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    JSON
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    tier = Column(String(32), default="free", nullable=False)  # 'free', 'pro', 'enterprise'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    repositories = relationship("Repository", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    git_url = Column(String(1024), nullable=False)
    is_private = Column(Boolean, default=False, nullable=False)
    commit_hash = Column(String(64), nullable=True)
    indexed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="repositories")
    conversations = relationship("Conversation", back_populates="repository", cascade="all, delete-orphan")
    code_symbols = relationship("CodeSymbol", back_populates="repository", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Conversation", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="conversations")
    repository = relationship("Repository", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # 'user' | 'assistant' | 'system'
    content = Column(Text, nullable=False)
    retrieval_strategy = Column(Text, nullable=True)  # 'hybrid', 'graph_only', 'vector_only', or multi-step pipeline
    sources = Column(JSON, default=list, nullable=True)  # List of retrieved chunks, file paths, citations
    token_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class CodeSymbol(Base):
    __tablename__ = "code_symbols"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(1024), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    qualified_name = Column(String(512), nullable=False)
    symbol_type = Column(String(64), nullable=False)  # 'function', 'class', 'method', 'variable'
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)

    # Relationships
    repository = relationship("Repository", back_populates="code_symbols")
