from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class TimestampMixin:
    """
    Add created_at and updated_at to any model.

    Usage:
        class User(Base, TimestampMixin):
            ...

    created_at: set once by the DB on INSERT, never changes.
    updated_at: set on INSERT, automatically updated on every UPDATE.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )