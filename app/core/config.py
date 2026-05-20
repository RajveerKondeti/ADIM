from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────
    APP_NAME: str = "ADIM"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # ── Security ───────────────────────────────────────────────────────
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Database ───────────────────────────────────────────────────────
    DATABASE_URL: str

    # ── AI / LLM ──────────────────────────────────────────────────────
    GOOGLE_API_KEY: str

    # ── Vector DB (Qdrant) ────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "adim_docs"

    # ── Graph DB (Neo4j) ──────────────────────────────────────────────
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — reads .env once, reuses everywhere."""
    return Settings()


# Module-level singleton so you can do: from app.core.config import settings
settings = get_settings()