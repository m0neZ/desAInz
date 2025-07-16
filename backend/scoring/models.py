"""Models for scoring service."""

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float

from backend.shared.db.base import Base


class ScoringWeight(Base):
    """Represents scoring weights."""

    __tablename__ = "scoring_weights"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
