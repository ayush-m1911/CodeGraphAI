"""
Purpose:
Manages connections and operations for the Qdrant vector database.

Responsibilities:
* Initialize the QdrantClient with connection limits.
* Support dynamic fallback to local persistent filesystem storage (path="qdrant_storage") if the Docker server is unavailable.
* Create and reset collection schemas with Cosine similarity metrics.
* Upsert chunks containing text, file path, chunk type, and symbol name payload properties.
* Execute semantic similarity vector queries.
* Query the database using scroll filters for exact matches on symbol names.

Interaction with other modules:
* Reads configuration variables (`qdrant_url`, `collection_name`) from `config.py`.
* Driven by `indexing_service.py` to store computed code embeddings.
* Queried by `retriever.py` and `symbol_retriever.py` to retrieve code contexts.

How it contributes to the production architecture:
Decouples vector search from hardcoded database collections. By allowing dynamic `collection_name` parameters,
the service supports multi-tenant isolation (e.g. separate collections per repository), preparing the system
for scale and integration with relational databases like PostgreSQL.
"""

import logging
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.config import settings

logger = logging.getLogger("codegraphai.vector_store")

try:
    # Attempt connecting to Docker Qdrant service
    client = QdrantClient(
        url=settings.qdrant_url,
        timeout=3.0
    )
    client.get_collections()
    logger.info(f"Successfully connected to Qdrant server at {settings.qdrant_url}")
except Exception as e:
    # Safe fallback to local persistent storage or in-memory if locked
    logger.warning(
        f"Could not connect to Qdrant server at {settings.qdrant_url}: {e}. "
        "Falling back to local persistent storage Qdrant client (path='qdrant_storage')."
    )
    try:
        client = QdrantClient(path="qdrant_storage")
    except Exception:
        logger.warning("Local storage locked; initializing in-memory Qdrant client.")
        client = QdrantClient(":memory:")

COLLECTION_NAME = settings.collection_name



def create_collection(vector_size: int, collection_name: str = None):
    """
    Creates a new collection in Qdrant with the specified vector dimension, using Cosine distance.

    Parameters:
        vector_size (int): The dimensions of the input vectors (e.g. 384 for bge-small).
        collection_name (str, optional): Overrides the default collection name for tenancy.

    Returns:
        None

    Execution Flow:
        1. Determine the target collection name.
        2. Query current collections from the Qdrant client.
        3. Create a new collection configured with Cosine distance if it doesn't already exist.
    """
    col_name = collection_name if collection_name else COLLECTION_NAME
    collections = client.get_collections()
    existing = [c.name for c in collections.collections]

    if col_name in existing:
        logger.info(f"Qdrant collection '{col_name}' already exists.")
        return

    logger.info(f"Creating new Qdrant collection: '{col_name}' (dim={vector_size})")
    client.create_collection(
        collection_name=col_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )


def store_chunks(
    chunks: list,
    embeddings: list,
    collection_name: str = None,
    user_id: str = None,
    repository_id: str = None
):
    """
    Upserts a batch of code chunks and their computed vectors into the active Qdrant collection,
    tagging each vector point with tenant isolation metadata (user_id, repository_id) and unified entity UUIDs.
    """
    col_name = collection_name if collection_name else COLLECTION_NAME
    points = []

    for chunk, vector in zip(chunks, embeddings):
        metadata = chunk.get("metadata", {})
        # Unified Entity UUID: Use assigned symbol_id or existing id or generate new UUID
        point_id = chunk.get("symbol_id") or metadata.get("symbol_id") or str(uuid.uuid4())

        payload = {
            "text": chunk.get("text", ""),
            "file_path": metadata.get("file_path", ""),
            "chunk_type": metadata.get("chunk_type", ""),
            "symbol_name": metadata.get("symbol_name", ""),
            "user_id": str(user_id) if user_id else "",
            "repository_id": str(repository_id) if repository_id else "",
            "symbol_id": str(point_id)
        }

        points.append(
            PointStruct(
                id=str(point_id),
                vector=vector,
                payload=payload
            )
        )

    logger.info(f"Upserting {len(points)} vectors to Qdrant collection '{col_name}' for tenant {user_id}/{repository_id}")
    client.upsert(
        collection_name=col_name,
        points=points
    )


def search_chunks(
    query_vector: list,
    limit: int = 5,
    collection_name: str = None,
    user_id: str = None,
    repository_id: str = None
) -> list:
    """
    Performs a semantic similarity vector search in the active collection,
    enforcing strict multi-tenant payload filtering when tenant coordinates are provided.
    """
    col_name = collection_name if collection_name else COLLECTION_NAME
    
    query_filter = None
    filter_conditions = []

    if user_id:
        filter_conditions.append(
            FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))
        )
    if repository_id:
        filter_conditions.append(
            FieldCondition(key="repository_id", match=MatchValue(value=str(repository_id)))
        )

    if filter_conditions:
        query_filter = Filter(must=filter_conditions)

    results = client.query_points(
        collection_name=col_name,
        query=query_vector,
        query_filter=query_filter,
        limit=limit
    )
    return results.points


def search_by_symbol(
    symbol_name: str,
    collection_name: str = None,
    user_id: str = None,
    repository_id: str = None
) -> list:
    """
    Performs an exact filtering lookup for a symbol name with mandatory tenant isolation.
    """
    col_name = collection_name if collection_name else COLLECTION_NAME
    filter_conditions = [
        FieldCondition(
            key="symbol_name",
            match=MatchValue(value=symbol_name)
        )
    ]

    if user_id:
        filter_conditions.append(
            FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))
        )
    if repository_id:
        filter_conditions.append(
            FieldCondition(key="repository_id", match=MatchValue(value=str(repository_id)))
        )

    result = client.scroll(
        collection_name=col_name,
        scroll_filter=Filter(must=filter_conditions),
        limit=5
    )
    return result[0]

