"""
init_db.py — runs once on application startup.

Responsibility:
  1. Verify the database is reachable.
  2. Create all tables that don't yet exist (idempotent — safe to run repeatedly).

NOT responsible for:
  - Running Alembic migrations (that's alembic upgrade head, done in CI/CD)
  - Seeding data (see scripts/seed.py)
"""
import logging

from sqlalchemy.exc import OperationalError

from app.db.base import Base
from app.db.session import engine

# Import every model so Base.metadata knows about them before create_all().
# If a model isn't imported here, its table won't be created.
from app.models import project, user  # noqa: F401

logger = logging.getLogger(__name__)


def init_db() -> None:
    try:
        # create_all is idempotent — skips tables that already exist.
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables verified/created.")
    except OperationalError as e:
        logger.error(
            "❌ Cannot connect to the database. "
            "Is Docker running? Is the DATABASE_URL in .env correct?\n"
            f"Error: {e}"
        )
        raise