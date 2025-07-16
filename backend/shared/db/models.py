"""Shared SQLAlchemy models used across services."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Idea(Base):
    """Represents a generated idea."""

    __tablename__ = "ideas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(UTC))
    signals: Mapped[list["Signal"]] = relationship(back_populates="idea")
    mockups: Mapped[list["Mockup"]] = relationship(back_populates="idea")


class Signal(Base):
    """Metric signal associated with an idea."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    engagement_rate: Mapped[float] = mapped_column(Float)
    details: Mapped[str | None] = mapped_column(String, nullable=True)

    idea: Mapped[Idea] = relationship(back_populates="signals")


class Mockup(Base):
    """Visual mockup for an idea."""

    __tablename__ = "mockups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id"))
    image_url: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    idea: Mapped[Idea] = relationship(back_populates="mockups")
    listings: Mapped[list["Listing"]] = relationship(back_populates="mockup")


class Listing(Base):
    """Marketplace listing for a mockup."""

    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mockup_id: Mapped[int] = mapped_column(ForeignKey("mockups.id"))
    price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mockup: Mapped[Mockup] = relationship(back_populates="listings")
    tests: Mapped[list["ABTest"]] = relationship(back_populates="listing")


class Weights(Base):
    """Scoring weight parameters."""

    __tablename__ = "weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    freshness: Mapped[float] = mapped_column(Float, default=1.0)
    engagement: Mapped[float] = mapped_column(Float, default=1.0)
    novelty: Mapped[float] = mapped_column(Float, default=1.0)
    community_fit: Mapped[float] = mapped_column(Float, default=1.0)
    seasonality: Mapped[float] = mapped_column(Float, default=1.0)


class ABTest(Base):
    """A/B test configuration."""

    __tablename__ = "ab_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    variant: Mapped[str] = mapped_column(String(50))
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)

    listing: Mapped[Listing] = relationship(back_populates="tests")


class AuditLog(Base):
    """Audit log entry for administrator actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
