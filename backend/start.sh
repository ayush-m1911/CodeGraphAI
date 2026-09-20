#!/usr/bin/env bash
set -e

# Start background Celery ingestion worker
celery -A app.workers.celery_app:celery_app worker --loglevel=info --concurrency=1 &

# Start FastAPI web service on Render's assigned port
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
