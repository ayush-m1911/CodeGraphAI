"""
Purpose:
Manages connections and operations for the Qdrant vector database.

Role in CodeGraphAI:
Serves as the database abstraction layer, handles upserting embedded code chunks,
performing semantic vector similarity searches, and running exact key-value filters on symbol names.

Key Responsibilities:
* Initialize the QdrantClient with connection limits.
* Support dynamic fallback to local persistent filesystem storage (path="qdrant_storage") if the Docker server is unavailable.
* Create and reset collection schemas with Cosine metric similarity metrics.
* Upsert chunks containing text, file path, chunk type, and symbol name payload properties.
* Execute semantic similarity vector queries.
* Query the database using scroll filters for exact matches on symbol names.

Interview Readiness Note:
- Why Qdrant? Qdrant is a highly performant, production-grade vector search engine. It supports complex payloads,
  high-speed similarity queries, and advanced field filtering (such as exact match scrolling on payloads).
- Why dynamic fallback? During local development or interview demonstrations, launching Docker containers can be complex.
  By automatically falling back to an in-memory/disk persistent DB file, the application remains fully functional out-of-the-box.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance
from qdrant_client.models import VectorParams
from qdrant_client.models import PointStruct
from qdrant_client.models import Filter
from qdrant_client.models import FieldCondition
from qdrant_client.models import MatchValue
import uuid
from app.config import settings


try:
    # Attempt connecting to Docker Qdrant service
    client = QdrantClient(
        url=settings.qdrant_url,
        timeout=3.0
    )
    client.get_collections()
    print(f"Successfully connected to Qdrant server at {settings.qdrant_url}")
except Exception as e:
    # Safe fallback to local disk storage if Docker is down
    print(f"Could not connect to Qdrant server at {settings.qdrant_url}: {e}")
    print("Falling back to local persistent storage Qdrant client (path='qdrant_storage').")
    client = QdrantClient(path="qdrant_storage")

COLLECTION_NAME = settings.collection_name


def create_collection(vector_size: int):
    """
    Creates a new collection in Qdrant with the specified vector dimension, using Cosine distance.

    Args:
        vector_size (int): The dimensions of the input vectors (e.g. 384 for bge-small).
    """

    collections = client.get_collections()

    existing = [
        c.name
        for c in collections.collections
    ]

    if COLLECTION_NAME in existing:
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )

def store_chunks(
    chunks,
    embeddings
):
    """
    Upserts a batch of code chunks and their computed vectors into the active Qdrant collection.

    Args:
        chunks (list of dict): AST parsed code chunks with metadata.
        embeddings (list of list of float): Dense vector floats generated for the chunks.
    """

    points = []

    for chunk, vector in zip(
        chunks,
        embeddings
    ):

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

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

def search_chunks(
    query_vector,
    limit=5
):
    """
    Performs a semantic similarity vector search in the active collection.

    Args:
        query_vector (list of float): The query's dense vector embeddings.
        limit (int): Max number of matches to return (defaults to 5).

    Returns:
        list: Matching Points returned by Qdrant, containing scores and payload data.
    """
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit
    )

    return results.points

def search_by_symbol(
    symbol_name
):
    """
    Performs an exact filtering lookup for a symbol name in the active collection.

    Args:
        symbol_name (str): Fully qualified symbol name (e.g. APIRouter or APIRouter.get).

    Returns:
        list: Matching Points returned by Qdrant whose symbol_name matches the filter.
    """

    result = client.scroll(
        collection_name=COLLECTION_NAME,

        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="symbol_name",
                    match=MatchValue(
                        value=symbol_name
                    )
                )
            ]
        ),

        limit=5
    )

    return result[0]