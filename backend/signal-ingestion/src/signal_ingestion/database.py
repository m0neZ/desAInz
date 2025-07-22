"""Database session utilities."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.shared.config import settings
from backend.shared.db import register_pool_metrics

from .models import Base

DATABASE_URL = str(settings.effective_database_url)
engine = create_async_engine(DATABASE_URL, echo=False)
register_pool_metrics(engine)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a new ``AsyncSession``."""
    async with SessionLocal() as session:
        yield session
