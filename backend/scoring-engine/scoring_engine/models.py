"""SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import Float, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for ORM models."""


class Weights(Base):
    """Model storing scoring weights."""

    __tablename__ = "weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    freshness: Mapped[float] = mapped_column(Float, default=1.0)
    engagement: Mapped[float] = mapped_column(Float, default=1.0)
    novelty: Mapped[float] = mapped_column(Float, default=1.0)
    community_fit: Mapped[float] = mapped_column(Float, default=1.0)
    seasonality: Mapped[float] = mapped_column(Float, default=1.0)
