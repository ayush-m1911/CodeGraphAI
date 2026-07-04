"""
Purpose:
Configures and initializes the Celery application instance for CodeGraphAI.

Responsibilities:
* Instantiates the Celery class with application identifiers.
* Configures broker and backend connection strings using Redis.
* Customizes data serialization protocols (JSON) and timezone parameters.
* Performs task discovery to load asynchronous handlers.

Interaction with other modules:
* Reads configuration parameters from `config.py`.
* Discovers and registers task definitions declared in `app.tasks.*`.
* Queried by `index.py` endpoints to instantiate `AsyncResult` wrappers.

How it contributes to the production architecture:
Provides the central Celery task queue controller. By binding to external Redis instances dynamically 
through the central configuration parameters, it supports horizontal worker scaling across containers.
"""

from celery import Celery
from app.config import settings

# Instantiate the Celery app instance using the centralized settings
celery_app = Celery(
    "codegraphai_workers",
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Celery Application Configurations
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Discover tasks under app.tasks
    imports=["app.tasks.index_repository"]
)
