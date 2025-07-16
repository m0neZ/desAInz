"""Database models for marketplace publisher."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as PgEnum
from sqlalchemy import Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()  # type: ignore


class PublishState(str, Enum):
    """Possible states for a publish job."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"


class PublishJob(Base):  # type: ignore
    """Model representing a publishing job."""

    __tablename__ = "publish_jobs"

    id = Column(Integer, primary_key=True)  # type: ignore[assignment]
    marketplace = Column(String, nullable=False)  # type: ignore[assignment]
    listing_id = Column(String, nullable=True)  # type: ignore[assignment]
    state: PublishState = Column(
        PgEnum(PublishState), default=PublishState.PENDING, nullable=False
    )  # type: ignore[assignment]
    attempts = Column(Integer, default=0, nullable=False)  # type: ignore[assignment]
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(  # type: ignore[assignment]
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )
