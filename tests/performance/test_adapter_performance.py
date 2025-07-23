"""Performance tests for signal ingestion adapters."""

# mypy: ignore-errors

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import importlib

import types

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
import math

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "backend" / "signal-ingestion" / "src"))
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

# Use a patched ``create_async_engine`` that ignores unsupported arguments.
import sqlalchemy.ext.asyncio as sa_async

_real_create_async_engine = sa_async.create_async_engine


def _patched_create_async_engine(url: str, *args: object, **kwargs: object) -> Any:
    kwargs.pop("pool_size", None)
    return _real_create_async_engine(url, *args, **kwargs)


sa_async.create_async_engine = _patched_create_async_engine  # type: ignore[assignment]

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type checking only
    shared_config: Any = None
else:  # pragma: no cover - runtime import and reload
    shared_config = importlib.import_module("backend.shared.config")  # type: ignore[assignment]
    importlib.reload(shared_config)  # type: ignore[arg-type]

from signal_ingestion import database as database_mod, tasks as tasks_mod  # noqa: E402
from signal_ingestion.adapters.base import BaseAdapter  # noqa: E402
from signal_ingestion.models import Signal as DBSignal  # noqa: E402

database = importlib.reload(database_mod)
tasks = importlib.reload(tasks_mod)


class BulkAdapter(BaseAdapter):  # type: ignore[misc]
    """Adapter returning a large batch of signals."""

    def __init__(self, size: int) -> None:
        super().__init__(base_url="")
        self.size = size

    async def fetch(self) -> list[dict[str, object]]:
        return [
            {"id": i, "title": f"title-{i}", "url": "https://example.com"}
            for i in range(self.size)
        ]


@pytest.mark.asyncio()
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_ingest_large_volume(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ingest a large number of rows within a time threshold."""
    engine: AsyncEngine = create_async_engine("sqlite+aiosqlite:///:memory:")
    database.engine = engine  # type: ignore[attr-defined]
    database.SessionLocal = async_sessionmaker(  # type: ignore[attr-defined]
        engine, expire_on_commit=False
    )
    await database.init_db()

    monkeypatch.setattr(tasks, "publish", lambda *a, **k: None)
    monkeypatch.setattr(tasks, "is_duplicate", lambda _k: False)
    monkeypatch.setattr(tasks, "add_key", lambda _k: None)
    monkeypatch.setattr(tasks, "store_keywords", lambda *a, **k: None)
    monkeypatch.setattr(tasks, "extract_keywords", lambda _t: [])
    monkeypatch.setattr(
        tasks,
        "generate_embeddings",
        lambda texts: [[0.0] * 2 for _ in texts],
    )
    monkeypatch.setattr(
        tasks,
        "normalize",
        lambda src, row: tasks.NormalizedSignal(
            id=str(row["id"]), title=row.get("title"), url=row.get("url"), source=src
        ),
    )

    commit_count = 0
    orig_commit = AsyncSession.commit

    async def counting_commit(self: AsyncSession) -> None:
        nonlocal commit_count
        await orig_commit(self)
        commit_count += 1

    monkeypatch.setattr(AsyncSession, "commit", counting_commit)

    adapter = BulkAdapter(1000)
    start = time.perf_counter()
    async with database.SessionLocal() as session:
        await tasks._ingest_from_adapter(session, adapter)
        rows = (await session.execute(select(DBSignal))).scalars().all()
    duration = time.perf_counter() - start

    assert len(rows) == 1000
    assert duration < 5.0
    expected_commits = math.ceil(adapter.size / tasks.EMBEDDING_CHUNK_SIZE)
    assert commit_count == expected_commits

    await engine.dispose()
