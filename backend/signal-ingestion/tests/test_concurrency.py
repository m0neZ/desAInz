"""Concurrency stress tests for ingestion."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import text

from signal_ingestion import database, ingestion
from signal_ingestion.adapters.base import BaseAdapter
from typing import cast


class _Adapter:
    def __init__(self, name: str, count: int) -> None:
        self._name = name
        self._count = count

    async def fetch(self) -> list[dict[str, int]]:  # pragma: no cover - simple mock
        return [{"id": i} for i in range(self._count)]


@pytest.mark.asyncio()
async def test_ingest_parallel(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ingest many signals concurrently without race conditions."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", session_factory)
    await database.init_db()

    ingestion.ADAPTERS = cast(
        list[BaseAdapter], [_Adapter(f"a{i}", 50) for i in range(5)]
    )

    store: set[str] = set()
    monkeypatch.setattr(ingestion, "is_duplicate", store.__contains__)
    monkeypatch.setattr(ingestion, "add_key", store.add)

    await ingestion.ingest(session_factory())

    async with session_factory() as session:
        result = await session.execute(text("select count(*) from signals"))
        count = result.scalar_one()
    assert count == 250
