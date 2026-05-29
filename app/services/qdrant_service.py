"""
qdrant_service.py — all Qdrant operations live here.

Responsibilities:
  - Create the collection if it doesn't exist (called on startup)
  - Upsert chunks with their vectors + metadata
  - Search for semantically similar chunks at query time
"""
import logging
import uuid
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

# Matches all-MiniLM-L6-v2 output size — must match the embedding model.
VECTOR_SIZE = 384


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


def ensure_collection_exists() -> None:
    """
    Called once on startup. Creates the Qdrant collection if it doesn't exist.
    Safe to call multiple times — idempotent.
    """
    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]

    if settings.QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,   # Best for semantic similarity
            ),
        )
        logger.info(f"✅ Created Qdrant collection: '{settings.QDRANT_COLLECTION}'")
    else:
        logger.info(f"✅ Qdrant collection '{settings.QDRANT_COLLECTION}' already exists.")


def upsert_chunks(
    chunks: list[str],
    vectors: list[list[float]],
    source: str,
    user_id: int,
    project_id: Optional[int] = None,
) -> int:
    """
    Store text chunks + their embedding vectors in Qdrant.

    Each point stores:
      - The vector (for similarity search)
      - The original text chunk (returned with results)
      - Metadata: source filename/URL, who uploaded it, which project
    """
    client = get_qdrant_client()
    ensure_collection_exists()

    points = [
        PointStruct(
            id=str(uuid.uuid4()),       # Random UUID for each chunk
            vector=vector,
            payload={
                "text": chunk,
                "source": source,
                "user_id": user_id,
                "project_id": project_id,
                "chunk_index": i,
            },
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]

    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    logger.info(f"Stored {len(points)} chunks from '{source}' into Qdrant.")
    return len(points)


def search_similar(
    query_vector: list[float],
    limit: int = 3,
    project_id: Optional[int] = None,
) -> list[str]:
    """
    Find the top-k chunks most semantically similar to the query.

    If project_id is provided, results are scoped to that project's documents.
    This is important: user A's data never leaks into user B's agent context.
    """
    client = get_qdrant_client()

    # Optional filter: scope results to a specific project
    query_filter = None
    if project_id:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=project_id),
                )
            ]
        )

    results = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=limit,
        query_filter=query_filter,
    )

    points: list[ScoredPoint] = result.points  # type: ignore[assignment]
    return [p.payload["text"] for p in points if p.payload and p.payload.get("text")]