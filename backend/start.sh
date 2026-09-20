#!/usr/bin/env bash
set -e

# Prevent PyTorch / OpenBLAS / Tokenizers from allocating multi-core memory caches
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false

# Start background Celery ingestion worker with solo pool to prevent forking overhead
celery -A app.workers.celery_app:celery_app worker --loglevel=info --pool=solo &

# Start FastAPI web service on Render's assigned port with single worker
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
