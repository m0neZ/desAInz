"""Database session management."""

from __future__ import annotations

import os
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/publisher"
)

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)  # type: ignore[call-overload]


async def get_session() -> AsyncIterator[AsyncSession]:
    """Provide an async database session."""
    async with AsyncSessionLocal() as session:
        yield session
