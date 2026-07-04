"""
Purpose:
Configures and initializes the Celery application instance for CodeGraphAI.

Responsibilities:
* Instantiates the Celery class with application identifiers.
* Configures broker and backend connection strings using Redis.
* Customizes data serialization protocols (JSON) and timezone parameters.
* Performs task discovery to load asynchronous handlers.

How it communicates with Redis:
Establishes a connection pool to Redis (defaulting to redis://localhost:6379/0).
* It writes task payloads to Redis message queues (broker).
* It reads/writes task states and results from/to Redis storage (backend).

How it communicates with Celery:
Acts as the central engine that Celery worker processes boot from. It exposes Celery options
and registers task routes dynamically.
"""

from celery import Celery

# Instantiate the Celery app instance
celery_app = Celery(
    "codegraphai_workers",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
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
