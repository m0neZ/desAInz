"""Models for signals service."""

from __future__ import annotations

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.db.base import Base


class Signal(Base):
    """Represents a signal."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    data: Mapped[str | None] = mapped_column(Text)
