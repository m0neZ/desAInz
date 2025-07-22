"""Tests for duplicate detection logic."""

import os
import sys
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from signal_ingestion import database, tasks
from signal_ingestion.adapters.base import BaseAdapter
from signal_ingestion.models import Signal


class DummyAdapter(BaseAdapter):
    """Simple adapter returning one signal for testing."""

    def __init__(self) -> None:
        super().__init__(base_url="")

    async def fetch(self) -> list[dict[str, object]]:
        return [{"id": 1, "title": "a", "url": "u"}]


@pytest.mark.asyncio()
async def test_duplicate_rows_are_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip ingestion when adapter returns already ingested signals."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    database.engine = engine
    database.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    await database.init_db()

    called = []
    monkeypatch.setattr(tasks, "publish", lambda *a, **k: called.append(a))
    monkeypatch.setattr(tasks, "is_duplicate", lambda key: True)
    monkeypatch.setattr(tasks, "add_key", lambda key: None)
    monkeypatch.setattr(tasks, "store_keywords", lambda *a, **k: None)

    async with database.SessionLocal() as session:
        await tasks._ingest_from_adapter(session, DummyAdapter())
        row = (await session.execute(select(Signal))).scalars().first()

    assert row is None
    assert called == []
