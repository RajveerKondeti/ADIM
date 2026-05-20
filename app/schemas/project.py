from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Request schemas ───────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)


# ── Response schemas ──────────────────────────────────────────────────────────

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}