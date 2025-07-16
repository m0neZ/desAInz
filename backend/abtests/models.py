"""Models for A/B testing service."""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.db.base import Base


class ABTest(Base):
    """Represents an A/B test variant."""

    __tablename__ = "ab_tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_name: Mapped[str] = mapped_column(nullable=False)
    variant: Mapped[str] = mapped_column(nullable=False)
    metrics: Mapped[dict[str, float] | None] = mapped_column(JSON)
