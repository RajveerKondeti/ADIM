from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=10_000)
    project_id: Optional[int] = None
    use_rag: bool = False  # RAG disabled until embedding pipeline is wired up


class ChatResponse(BaseModel):
    response: str
    project_context_used: bool = False