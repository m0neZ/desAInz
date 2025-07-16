"""SQLAlchemy base declarative class."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):  # type: ignore[misc]
    """Base class for all ORM models."""
