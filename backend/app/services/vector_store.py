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
    client = QdrantClient(
        url=settings.qdrant_url,
        timeout=3.0
    )
    client.get_collections()
    print(f"Successfully connected to Qdrant server at {settings.qdrant_url}")
except Exception as e:
    print(f"Could not connect to Qdrant server at {settings.qdrant_url}: {e}")
    print("Falling back to local persistent storage Qdrant client (path='qdrant_storage').")
    client = QdrantClient(path="qdrant_storage")

COLLECTION_NAME = settings.collection_name


def create_collection(vector_size: int):

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
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit
    )

    return results.points

def search_by_symbol(
    symbol_name
):

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