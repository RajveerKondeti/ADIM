"""
ingest.py — HTTP endpoints for the document ingestion pipeline.

POST /api/v1/ingest/text   → paste raw text
POST /api/v1/ingest/file   → upload .pdf or .txt
POST /api/v1/ingest/url    → scrape a webpage
GET  /api/v1/ingest/status → check collection stats
"""
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.ingest import IngestResponse, IngestTextRequest, IngestUrlRequest
from app.services.ingestion import (
    chunk_text,
    embed_texts,
    extract_pdf_text,
    fetch_url_text,
)
from app.services.qdrant_service import get_qdrant_client, upsert_chunks

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Ingest raw text ───────────────────────────────────────────────────────────

@router.post(
    "/text",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest plain text into the knowledge base",
)
def ingest_text(
    body: IngestTextRequest,
    current_user: User = Depends(get_current_user),
) -> IngestResponse:
    """
    Paste any text — meeting notes, reports, documentation, operational data.
    The system chunks it, embeds it, and stores it in Qdrant.
    The agent can now answer questions grounded in this content.
    """
    chunks = chunk_text(body.text)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text is too short or empty to ingest.",
        )

    vectors = embed_texts(chunks)
    count = upsert_chunks(
        chunks=chunks,
        vectors=vectors,
        source=body.source_name,
        user_id=current_user.id,
        project_id=body.project_id,
    )

    return IngestResponse(
        chunks_stored=count,
        source=body.source_name,
        collection=settings.QDRANT_COLLECTION,
    )


# ── Ingest file upload ────────────────────────────────────────────────────────

@router.post(
    "/file",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a .pdf or .txt file into the knowledge base",
)
async def ingest_file(
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(default=None),
    current_user: User = Depends(get_current_user),
) -> IngestResponse:
    filename = file.filename or "unknown_file"

    if not (filename.endswith(".pdf") or filename.endswith(".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .pdf and .txt files are supported.",
        )

    content = await file.read()

    try:
        if filename.endswith(".pdf"):
            text = extract_pdf_text(content)
        else:
            text = content.decode("utf-8", errors="ignore")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract usable text from this file.",
        )

    vectors = embed_texts(chunks)
    count = upsert_chunks(
        chunks=chunks,
        vectors=vectors,
        source=filename,
        user_id=current_user.id,
        project_id=project_id,
    )

    return IngestResponse(
        chunks_stored=count,
        source=filename,
        collection=settings.QDRANT_COLLECTION,
    )


# ── Ingest URL ────────────────────────────────────────────────────────────────

@router.post(
    "/url",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Scrape a URL and ingest its content",
)
async def ingest_url(
    body: IngestUrlRequest,
    current_user: User = Depends(get_current_user),
) -> IngestResponse:
    url_str = str(body.url)

    try:
        text = await fetch_url_text(url_str)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract usable text from this URL.",
        )

    vectors = embed_texts(chunks)
    count = upsert_chunks(
        chunks=chunks,
        vectors=vectors,
        source=url_str,
        user_id=current_user.id,
        project_id=body.project_id,
    )

    return IngestResponse(
        chunks_stored=count,
        source=url_str,
        collection=settings.QDRANT_COLLECTION,
    )


# ── Collection status ─────────────────────────────────────────────────────────

@router.get(
    "/status",
    summary="Check how many documents are stored in the knowledge base",
)
def collection_status(
    current_user: User = Depends(get_current_user),
) -> dict:
    client = get_qdrant_client()
    info = client.get_collection(settings.QDRANT_COLLECTION)

    # vectors config is Union[VectorParams, Dict[str, VectorParams], None]
    vectors_config = info.config.params.vectors
    if isinstance(vectors_config, dict):
        # named vectors — grab the first one
        vector_size = next(iter(vectors_config.values())).size
    elif vectors_config is not None:
        # unnamed single vector (our case)
        vector_size = vectors_config.size
    else:
        vector_size = "unknown"

    return {
        "collection": settings.QDRANT_COLLECTION,
        "total_chunks": info.points_count,
        "vector_size": vector_size,
        "status": str(info.status),
    }