"""Test scheduling of ingestion tasks across queues."""

from __future__ import annotations

from signal_ingestion import database, tasks
from signal_ingestion.normalization import NormalizedSignal
from signal_ingestion.adapters.base import BaseAdapter
from signal_ingestion.models import Signal
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import select
import pytest


class DummyApp:
    """Collect Celery send_task calls."""

    def __init__(self) -> None:
        """Initialize storage for sent tasks."""
        self.sent: list[tuple[str, list[str], str | None]] = []

    def send_task(
        self, name: str, args: list[str] | None = None, queue: str | None = None
    ) -> None:
        """Record a send_task call."""
        self.sent.append((name, args or [], queue))


def test_schedule_ingestion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure each adapter is dispatched to its own queue."""
    dummy = DummyApp()
    monkeypatch.setattr(tasks, "app", dummy)
    tasks.schedule_ingestion(["tiktok", "instagram"])
    assert dummy.sent == [
        ("signal_ingestion.ingest_adapter", ["tiktok"], tasks.queue_for("tiktok")),
        (
            "signal_ingestion.ingest_adapter",
            ["instagram"],
            tasks.queue_for("instagram"),
        ),
    ]


@pytest.mark.asyncio()
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_ingest_from_adapter_publishes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Publish normalized rows to Kafka topics."""

    class DummyAdapter(BaseAdapter):
        def __init__(self) -> None:
            super().__init__(base_url="")

        async def fetch(self) -> list[dict[str, object]]:
            return [{"id": 1, "foo": "bar"}]

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    database.engine = engine
    database.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    await database.init_db()

    published: list[tuple[str, str]] = []

    def dummy_publish(topic: str, message: str) -> None:
        published.append((topic, message))

    monkeypatch.setattr(tasks, "publish", dummy_publish)
    monkeypatch.setattr(tasks, "is_duplicate", lambda key: False)
    monkeypatch.setattr(tasks, "add_key", lambda key: None)

    async with database.SessionLocal() as session:
        await tasks._ingest_from_adapter(session, DummyAdapter())
        row = (await session.execute(select(Signal))).scalars().first()

    assert row is not None
    assert isinstance(row.embedding, list)

    assert ("signals", "DummyAdapter:1") in published
    assert ("signals.ingested", '{"id": 1, "foo": "bar"}') in published


@pytest.mark.asyncio()
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_ingest_from_adapter_redacts_pii(monkeypatch: pytest.MonkeyPatch) -> None:
    """Emails and phone numbers are removed before persisting signals."""

    class DummyAdapter(BaseAdapter):
        def __init__(self) -> None:
            super().__init__(base_url="")

        async def fetch(self) -> list[dict[str, object]]:
            return [
                {
                    "id": 1,
                    "title": "Contact user@example.com or 123-456-7890",
                    "url": "https://example.com",
                }
            ]

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    database.engine = engine
    database.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    await database.init_db()

    monkeypatch.setattr(tasks, "publish", lambda *args, **kwargs: None)
    monkeypatch.setattr(tasks, "is_duplicate", lambda key: False)
    monkeypatch.setattr(tasks, "add_key", lambda key: None)
    monkeypatch.setattr(tasks, "store_keywords", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        tasks,
        "normalize",
        lambda source, row: NormalizedSignal(
            id=str(row["id"]), title=row.get("title"), url=row.get("url"), source=source
        ),
    )

    async with database.SessionLocal() as session:
        await tasks._ingest_from_adapter(session, DummyAdapter())
        row = (await session.execute(select(Signal))).scalars().first()

    assert row is not None
    assert "user@example.com" not in row.content
    assert "123-456-7890" not in row.content
    assert "[REDACTED]" in row.content
