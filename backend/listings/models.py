"""Models for listings service."""

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Numeric

from backend.shared.db.base import Base


class Listing(Base):
    """Represents a listing."""

    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(Numeric(scale=2), nullable=False)
