"""Test purging of PII from stored signals."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from signal_ingestion import database
from signal_ingestion.models import Signal
from signal_ingestion.purge_pii import purge_pii


@pytest.mark.asyncio()
async def test_purge_pii() -> None:
    """Ensure stored rows are cleaned."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    database.engine = engine
    database.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    await database.init_db()

    async with database.SessionLocal() as session:
        session.add(Signal(source="t", content="Contact me at user@example.com"))
        await session.commit()
        await purge_pii(session)
        row = (await session.execute(select(Signal))).scalars().first()
        assert "[REDACTED]" in row.content
