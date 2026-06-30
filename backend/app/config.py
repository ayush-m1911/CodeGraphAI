"""
Purpose:
Defines system configurations and environment variables schema.

Role in CodeGraphAI:
Provides config and settings variables to all parts of the application. It loads settings from the environment
or a local `.env` file and binds them to a validated config object.

Key Responsibilities:
* Declare Settings class inheriting from Pydantic BaseSettings.
* Bind environment properties (`qdrant_url`, `collection_name`, `groq_api_key`) with validation.
* Initialize a global settings instance for import throughout the backend.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    qdrant_url: str
    collection_name: str
    groq_api_key: str

    class Config:
        env_file = ".env"


settings = Settings()