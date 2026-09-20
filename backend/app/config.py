"""
Purpose:
Defines system configurations, environment variables schema, and connection variables.

Responsibilities:
* Declare Settings class inheriting from Pydantic BaseSettings.
* Bind environment properties (`qdrant_url`, `collection_name`, `groq_api_key`, `redis_url`) with validation.
* Initialize a global settings instance for import throughout the backend.

Interaction with other modules:
* Read by `celery_app.py` to establish Redis connections.
* Read by `vector_store.py` to connect to the Qdrant instance.
* Read by `llm.py` to authenticate with Groq's APIs.

How it contributes to the production architecture:
Centralizes variable binding and type casting. In production, variables are loaded from the running environment 
(e.g., Docker Compose environment configurations), decoupling hardcoded credentials and addresses from application code.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    qdrant_url: str
    collection_name: str
    groq_api_key: str
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql://codegraph:codegraph_password@localhost:5432/codegraph_db"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "codegraph_password"
    jwt_secret_key: str = "codegraph_super_secret_jwt_key_2026"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    llm_model: str = "openai/gpt-oss-120b"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extraneous environment variables during container orchestration



# Global settings singleton used by the API and worker containers
settings = Settings()

