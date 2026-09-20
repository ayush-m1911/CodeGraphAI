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

import logging
import redis
from celery import Celery
from app.config import settings

logger = logging.getLogger("codegraphai.celery")

# Check if Redis is reachable, otherwise fallback to in-memory eager execution
is_redis_available = False
try:
    r = redis.Redis.from_url(settings.redis_url, socket_timeout=1.0)
    r.ping()
    is_redis_available = True
    logger.info("Successfully connected to Redis broker.")
except Exception as e:
    logger.warning("Redis is not available. Celery will execute tasks locally in eager mode.")

if is_redis_available:
    celery_app = Celery(
        "codegraphai_workers",
        broker=settings.redis_url,
        backend=settings.redis_url
    )
else:
    celery_app = Celery(
        "codegraphai_workers",
        broker="memory://",
        backend="cache+memory://"
    )

# Celery Application Configurations
celery_app.conf.update(
    task_always_eager=not is_redis_available,
    task_eager_propagates=False,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Discover tasks under app.tasks
    imports=["app.tasks.index_repository"]
)

