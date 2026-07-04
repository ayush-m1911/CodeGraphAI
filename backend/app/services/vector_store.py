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
    # Safe fallback to local disk storage if Docker is down
    logger.warning(
        f"Could not connect to Qdrant server at {settings.qdrant_url}: {e}. "
        "Falling back to local persistent storage Qdrant client (path='qdrant_storage')."
    )
    client = QdrantClient(path="qdrant_storage")

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


def store_chunks(chunks: list, embeddings: list, collection_name: str = None):
    """
    Upserts a batch of code chunks and their computed vectors into the active Qdrant collection.

    Parameters:
        chunks (list of dict): AST parsed code chunks with metadata payload.
        embeddings (list of list of float): Dense vector floats generated for the chunks.
        collection_name (str, optional): The collection to store chunks in.

    Returns:
        None

    Execution Flow:
        1. Formulate PointStruct instances for each chunk and embedding pair with a new UUID.
        2. Execute an upsert command targeting the resolved collection name.
    """
    col_name = collection_name if collection_name else COLLECTION_NAME
    points = []

    for chunk, vector in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk["text"],
                    "file_path": chunk["metadata"]["file_path"],
                    "chunk_type": chunk["metadata"]["chunk_type"],
                    "symbol_name": chunk["metadata"]["symbol_name"]
                }
            )
        )

    logger.info(f"Upserting {len(points)} vectors to Qdrant collection '{col_name}'")
    client.upsert(
        collection_name=col_name,
        points=points
    )


def search_chunks(query_vector: list, limit: int = 5, collection_name: str = None) -> list:
    """
    Performs a semantic similarity vector search in the active collection.

    Parameters:
        query_vector (list of float): The query's dense vector embeddings.
        limit (int): Max number of matches to return (defaults to 5).
        collection_name (str, optional): The collection to search.

    Returns:
        list: Matching Points returned by Qdrant, containing scores and payload data.

    Execution Flow:
        1. Query Qdrant vector database using cosine distance metrics.
        2. Extract and return matching points from search results.
    """
    col_name = collection_name if collection_name else COLLECTION_NAME
    results = client.query_points(
        collection_name=col_name,
        query=query_vector,
        limit=limit
    )
    return results.points


def search_by_symbol(symbol_name: str, collection_name: str = None) -> list:
    """
    Performs an exact filtering lookup for a symbol name in the active collection.

    Parameters:
        symbol_name (str): Fully qualified symbol name (e.g. APIRouter or APIRouter.get).
        collection_name (str, optional): The collection to scroll.

    Returns:
        list: Matching Points returned by Qdrant whose symbol_name matches the filter.

    Execution Flow:
        1. Apply FieldCondition matching the exact symbol_name payload value.
        2. Scroll collection entries with limit constraint.
        3. Return list of matching points.
    """
    col_name = collection_name if collection_name else COLLECTION_NAME
    result = client.scroll(
        collection_name=col_name,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="symbol_name",
                    match=MatchValue(value=symbol_name)
                )
            ]
        ),
        limit=5
    )
    return result[0]
