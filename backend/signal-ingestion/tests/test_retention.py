"""Tests for signal retention routines."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from signal_ingestion import database
from signal_ingestion.models import Signal
from signal_ingestion.retention import purge_old_signals


@pytest.mark.asyncio()
async def test_purge_old_signals() -> None:
    """Remove signals older than the retention threshold."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    database.engine = engine
    database.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    await database.init_db()

    async with database.SessionLocal() as session:
        old_ts = datetime.now(timezone.utc) - timedelta(days=100)
        new_ts = datetime.now(timezone.utc)
        session.add_all(
            [
                Signal(
                    source="t",
                    content="{}",
                    timestamp=old_ts,
                    embedding=[0.0, 0.0],
                ),
                Signal(
                    source="t",
                    content="{}",
                    timestamp=new_ts,
                    embedding=[0.0, 0.0],
                ),
            ]
        )
        await session.commit()
        await purge_old_signals(session, 90)
        remaining = (await session.execute(select(Signal))).scalars().all()
        assert len(remaining) == 1
        assert remaining[0].timestamp == new_ts.replace(tzinfo=None)
