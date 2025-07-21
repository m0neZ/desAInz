"""Database models and helpers for tracking publishing state."""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any

from backend.shared.db import models as shared_models

from sqlalchemy import DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, Integer, String, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.shared.db import async_engine, AsyncSessionLocal, session_scope
from .settings import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class Marketplace(str, Enum):
    """Supported marketplaces."""

    redbubble = "redbubble"
    amazon_merch = "amazon_merch"
    etsy = "etsy"
    society6 = "society6"
    zazzle = "zazzle"


class PublishStatus(str, Enum):
    """Status values for a publish task."""

    pending = "pending"
    in_progress = "in_progress"
    success = "success"
    failed = "failed"


class PublishTask(Base):
    """Database model representing a publish task."""

    __tablename__ = "publish_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # noqa: A003
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


class WebhookEvent(Base):
    """Webhook event received from a marketplace."""

    __tablename__ = "webhook_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # noqa: A003
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("publish_task.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    task: Mapped["PublishTask"] = relationship("PublishTask", backref="events")


class OAuthToken(Base):
    """OAuth credentials for a marketplace."""

    __tablename__ = "oauth_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # noqa: A003
    marketplace: Mapped[Marketplace] = mapped_column(
        SqlEnum(Marketplace), nullable=False, unique=True
    )
    access_token: Mapped[str | None] = mapped_column(String, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


engine = async_engine
SessionLocal = AsyncSessionLocal


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


async def create_webhook_event(
    session: AsyncSession, task_id: int, status: str
) -> None:
    """Persist a ``WebhookEvent`` row and update the task status."""
    event = WebhookEvent(task_id=task_id, status=status)
    session.add(event)
    await session.execute(
        update(PublishTask)
        .where(PublishTask.id == task_id)
        .values(status=status, updated_at=datetime.utcnow())
    )
    await session.commit()


async def get_task(session: AsyncSession, task_id: int) -> PublishTask | None:
    """Retrieve a task by ID."""
    result = await session.execute(select(PublishTask).where(PublishTask.id == task_id))
    return result.scalars().first()


async def get_listing(
    session: AsyncSession, listing_id: int
) -> shared_models.Listing | None:
    """Return listing with ``listing_id``."""
    result = await session.execute(
        select(shared_models.Listing).where(shared_models.Listing.id == listing_id)
    )
    return result.scalars().first()


async def update_listing(session: AsyncSession, listing_id: int, **values: Any) -> None:
    """Update listing attributes using provided keyword ``values``."""
    if not values:
        return
    await session.execute(
        update(shared_models.Listing)
        .where(shared_models.Listing.id == listing_id)
        .values(**values)
    )
    await session.commit()


async def get_oauth_token(
    session: AsyncSession, marketplace: Marketplace
) -> OAuthToken | None:
    """Return stored token for ``marketplace`` if available."""
    result = await session.execute(
        select(OAuthToken).where(OAuthToken.marketplace == marketplace)
    )
    return result.scalars().first()


async def upsert_oauth_token(
    session: AsyncSession,
    marketplace: Marketplace,
    access_token: str | None,
    refresh_token: str | None,
    expires_at: datetime | None,
) -> None:
    """Insert or update token information."""
    token = await get_oauth_token(session, marketplace)
    if token is None:
        token = OAuthToken(
            marketplace=marketplace,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        session.add(token)
    else:
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.expires_at = expires_at
    await session.commit()


def get_oauth_token_sync(marketplace: Marketplace) -> OAuthToken | None:
    """Return stored token row for ``marketplace``."""
    with session_scope() as session:
        return (
            session.query(OAuthToken)
            .filter(OAuthToken.marketplace == marketplace)
            .first()
        )


def upsert_oauth_token_sync(
    marketplace: Marketplace,
    access_token: str | None,
    refresh_token: str | None,
    expires_at: datetime | None,
) -> None:
    """Store token details synchronously."""
    with session_scope() as session:
        token = (
            session.query(OAuthToken)
            .filter(OAuthToken.marketplace == marketplace)
            .first()
        )
        if token is None:
            token = OAuthToken(
                marketplace=marketplace,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )
            session.add(token)
        else:
            token.access_token = access_token
            token.refresh_token = refresh_token
            token.expires_at = expires_at
        session.commit()
