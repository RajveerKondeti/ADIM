from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    All SQLAlchemy models inherit from this class.
    DeclarativeBase is the modern Pydantic v2 / SQLAlchemy 2.x style.
    """
    pass