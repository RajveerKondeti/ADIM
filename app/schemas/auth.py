from pydantic import BaseModel, EmailStr, Field


# ── Request schemas (what the client sends) ───────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ── Response schemas (what we send back) ──────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str

    model_config = {"from_attributes": True}  # Allows reading from SQLAlchemy models


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"