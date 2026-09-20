"""
Purpose:
Database connection and session factory for PostgreSQL relational storage in CodeGraphAI.

Responsibilities:
* Create SQLAlchemy engine connected to configured database_url.
* Provide scoped SessionLocal sessions.
* Define Base model class for declarative mapping.
* Provide get_db dependency for FastAPI routes.
* Provide init_db() to initialize relational tables on startup.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# In case PostgreSQL URL starts with postgres:// (older Heroku/Supabase format), normalize to postgresql://
db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Configure connection pooling
engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a transactional database session per request,
    ensuring proper cleanup when the request cycle finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initializes database schema and tables defined in db_models.
    Safe to call on application startup.
    """
    # Import all models to ensure they are registered with Base.metadata
    import app.models.db_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
