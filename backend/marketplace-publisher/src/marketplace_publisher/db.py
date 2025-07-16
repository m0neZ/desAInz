"""Database models and helpers for tracking publishing state."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
import json

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    Integer,
    String,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .settings import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class Marketplace(str, Enum):
    """Supported marketplaces."""

    redbubble = "redbubble"
    amazon_merch = "amazon_merch"
    etsy = "etsy"


class PublishStatus(str, Enum):
    """Status values for a publish task."""

    pending = "pending"
    in_progress = "in_progress"
    success = "success"
    failed = "failed"


class PublishTask(Base):
    """Database model representing a publish task."""

    __tablename__ = "publish_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marketplace: Mapped[Marketplace] = mapped_column(
        SqlEnum(Marketplace), nullable=False
    )
    design_path: Mapped[str] = mapped_column(String, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(String)
    status: Mapped[PublishStatus] = mapped_column(
        SqlEnum(PublishStatus), default=PublishStatus.pending, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


engine = create_async_engine(settings.database_url, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_task(session: AsyncSession, **kwargs: Any) -> PublishTask:
    """Persist a new ``PublishTask`` instance."""
    if isinstance(kwargs.get("metadata_json"), (dict, list)):
        kwargs["metadata_json"] = json.dumps(kwargs["metadata_json"])
    task = PublishTask(**kwargs)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def update_task_status(
    session: AsyncSession, task_id: int, status: PublishStatus
) -> None:
    """Update task status in the database."""
    await session.execute(
        update(PublishTask)
        .where(PublishTask.id == task_id)
        .values(status=status, updated_at=datetime.utcnow())
    )
    await session.commit()


async def increment_attempts(session: AsyncSession, task_id: int) -> None:
    """Increment the attempt count for a task."""
    await session.execute(
        update(PublishTask)
        .where(PublishTask.id == task_id)
        .values(attempts=PublishTask.attempts + 1, updated_at=datetime.utcnow())
    )
    await session.commit()


async def get_task(session: AsyncSession, task_id: int) -> PublishTask | None:
    """Retrieve a task by ID."""
    return await session.get(PublishTask, task_id)
