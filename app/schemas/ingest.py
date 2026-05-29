from typing import Optional
from pydantic import BaseModel, HttpUrl


# ── Requests ──────────────────────────────────────────────────────────────────

class IngestTextRequest(BaseModel):
    text: str
    source_name: str = "manual_input"
    project_id: Optional[int] = None


class IngestUrlRequest(BaseModel):
    url: HttpUrl
    project_id: Optional[int] = None


# ── Responses ─────────────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    chunks_stored: int
    source: str
    collection: str


class DocumentChunk(BaseModel):
    id: str
    source: str
    preview: str          # first 120 chars of the chunk
    project_id: Optional[int]