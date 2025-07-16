"""Models for mockups service."""

from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.db.base import Base


class Mockup(Base):
    """Represents a mockup for an idea."""

    __tablename__ = "mockups"

    id: Mapped[int] = mapped_column(primary_key=True)
    idea_id: Mapped[int] = mapped_column(  # noqa: E501
        ForeignKey("ideas.id"), nullable=False
    )
    image_url: Mapped[str] = mapped_column(nullable=True)

    idea = relationship("Idea")
