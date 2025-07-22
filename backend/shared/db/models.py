"""Shared SQLAlchemy models used across services."""

from __future__ import annotations

from datetime import datetime

from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .base import Base


class Idea(Base):
    """Represents a generated idea."""

    __tablename__ = "ideas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
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
    content_hash: Mapped[str] = mapped_column(String(32), unique=True)

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
    state: Mapped[str] = mapped_column(String(50), default="pending")

    mockup: Mapped[Mockup] = relationship(back_populates="listings")
    tests: Mapped[list["ABTest"]] = relationship(back_populates="listing")


class Weights(Base):
    """Scoring weight parameters."""

    __tablename__ = "weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(50), unique=True, default="global")
    freshness: Mapped[float] = mapped_column(Float, default=1.0)
    engagement: Mapped[float] = mapped_column(Float, default=1.0)
    novelty: Mapped[float] = mapped_column(Float, default=1.0)
    community_fit: Mapped[float] = mapped_column(Float, default=1.0)
    seasonality: Mapped[float] = mapped_column(Float, default=1.0)
    centroid: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)


class ABTest(Base):
    """A/B test configuration."""

    __tablename__ = "ab_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    variant: Mapped[str] = mapped_column(String(50))
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)

    listing: Mapped[Listing] = relationship(back_populates="tests")


class ABTestResult(Base):
    """Outcome metrics for an A/B test variant."""

    __tablename__ = "ab_test_results"
    __table_args__ = (Index("ix_ab_test_results_ab_test_id", "ab_test_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ab_test_id: Mapped[int] = mapped_column(ForeignKey("ab_tests.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)

    ab_test: Mapped[ABTest] = relationship()


class MarketplaceMetric(Base):
    """Aggregated metrics for a marketplace listing."""

    __tablename__ = "marketplace_metrics"
    __table_args__ = (Index("ix_marketplace_metrics_listing_id", "listing_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    purchases: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)

    listing: Mapped[Listing] = relationship()


class MarketplacePerformanceMetric(Base):
    """Detailed performance metrics for a listing."""

    __tablename__ = "marketplace_performance_metrics"
    __table_args__ = (Index("ix_marketplace_perf_listing_id", "listing_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    views: Mapped[int] = mapped_column(Integer, default=0)
    favorites: Mapped[int] = mapped_column(Integer, default=0)
    orders: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)

    listing: Mapped[Listing] = relationship()


class Embedding(Base):
    """Content embedding stored as a pgvector."""

    __tablename__ = "embeddings"
    __table_args__ = (
        Index("ix_embeddings_vector", "embedding", postgresql_using="ivfflat"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(50))
    embedding: Mapped[list[float]] = mapped_column(Vector(768))


class UserRole(Base):
    """Association between a username and its role."""

    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    role: Mapped[str] = mapped_column(String(20))


class AuditLog(Base):
    """Record of privileged operations."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AIModel(Base):
    """AI model metadata tracked in the database."""

    __tablename__ = "ai_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(50))
    model_id: Mapped[str] = mapped_column(String, unique=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ScoreMetric(Base):
    """Score metric for a design idea."""

    __tablename__ = "score_metrics"
    __table_args__ = (
        Index("ix_score_metrics_idea_id_timestamp", "idea_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    score: Mapped[float] = mapped_column(Float)

    idea: Mapped[Idea] = relationship()


class PublishLatencyMetric(Base):
    """Publish latency metric for a design idea."""

    __tablename__ = "publish_latency_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("ideas.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    latency_seconds: Mapped[float] = mapped_column(Float)

    idea: Mapped[Idea] = relationship()


class ScoreBenchmark(Base):
    """Benchmark result for the scoring engine."""

    __tablename__ = "score_benchmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    runs: Mapped[int] = mapped_column(Integer)
    uncached_seconds: Mapped[float] = mapped_column(Float)
    cached_seconds: Mapped[float] = mapped_column(Float)


class GeneratedMockup(Base):
    """Parameters used for generating a mockup."""

    __tablename__ = "generated_mockups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prompt: Mapped[str] = mapped_column(String)
    num_inference_steps: Mapped[int] = mapped_column(Integer)
    seed: Mapped[int] = mapped_column(Integer)
    image_uri: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String)
    tags: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RevokedToken(Base):
    """JWT token that has been revoked."""

    __tablename__ = "revoked_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class RefreshToken(Base):
    """Refresh token linked to a username."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
