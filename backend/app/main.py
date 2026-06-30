"""
Purpose:
Entry point and application setup for the CodeGraphAI FastAPI backend.

Role in CodeGraphAI:
Bootstraps the web application service, configures middleware (CORS settings for the React frontend),
and aggregates all modular api routes (chat, index, tree, parsing, embedding, etc.) to expose them as web endpoints.

Key Responsibilities:
* Initialize FastAPI app with title and version settings.
* Enable CORS middleware configuration for safe frontend cross-origin requests.
* Include all modular API routers from app/api/*.
* Expose diagnostics endpoints like root check and configuration settings.
"""

from fastapi import FastAPI
from fastapi import APIRouter
from app.config import settings
from app.api.ingest import router as ingest_router
from app.api.parser import router as parser_router
from app.api.chunk import router as chunk_router
from app.api.embeddings import router as embeddings_router
from app.api.qdrant import router as qdrant_router
from app.api.index import router as index_router
from app.api.chat import router as chat_router
from app.api.tree import router as tree_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CodeGraphAI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)
app.include_router(parser_router)
app.include_router(chunk_router)
app.include_router(embeddings_router)
app.include_router(qdrant_router)
app.include_router(index_router)
app.include_router(chat_router)
app.include_router(tree_router)
router = APIRouter()

@app.get("/")
def root():
    """
    Exposes a root health check endpoint to verify that the backend is running.

    Returns:
        dict: A message confirming the backend status.
    """
    return {
        "message": "CodeGraphAI Backend Running"
    }


@app.get("/config")
def show_config():
    """
    Exposes configuration details of the backend's active vector store connections.

    Returns:
        dict: The Qdrant URL and collection name settings loaded in the system.
    """
    return {
        "qdrant_url": settings.qdrant_url,
        "collection": settings.collection_name
    }


