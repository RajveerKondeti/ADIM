from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# pool_pre_ping=True — before handing a connection from the pool to a request,
# SQLAlchemy sends a lightweight "SELECT 1" to confirm the connection is alive.
# This is what fixes the "connection already closed" error after uvicorn reloads.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,       # Connections kept open in the pool
    max_overflow=20,    # Extra connections allowed when pool is exhausted
    pool_timeout=30,    # Seconds to wait for a connection before raising
    echo=settings.DEBUG,  # Log SQL queries only in debug mode
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a DB session and guarantees cleanup.

    The yield-based pattern means the session is closed AFTER the response
    is sent, including in error cases (the finally block always runs).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()