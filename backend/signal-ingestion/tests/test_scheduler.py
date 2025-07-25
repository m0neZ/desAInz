"""Tests for the ingestion scheduler."""

from __future__ import annotations

import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)  # noqa: E402
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)  # noqa: E402
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"  # noqa: E402
os.environ["KAFKA_SKIP"] = "1"  # noqa: E402


class _DummyBloom:
    def create(self, *args, **kwargs) -> None:
        """Do nothing."""

    def exists(self, *args, **kwargs) -> bool:
        return False

    def add(self, *args, **kwargs) -> None:
        pass


class _DummyRedis:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def bf(self) -> _DummyBloom:
        return _DummyBloom()

    def exists(self, *args, **kwargs) -> bool:
        return False

    def expire(self, *args, **kwargs) -> None:
        pass

    @classmethod
    def from_url(cls, *args, **kwargs) -> "_DummyRedis":
        return cls()


import redis  # noqa: E402

redis.Redis = _DummyRedis  # type: ignore[attr-defined]

from types import SimpleNamespace
import pytest
from apscheduler.triggers.cron import CronTrigger  # noqa: E402
from apscheduler.triggers.interval import IntervalTrigger  # noqa: E402

sys.modules.setdefault(
    "signal_ingestion.database",
    SimpleNamespace(SessionLocal=lambda: None),
)

from signal_ingestion import scheduler  # noqa: E402
from signal_ingestion.settings import settings  # noqa: E402


def test_ingest_job_scheduled() -> None:
    """The scheduler configures the ingest job with the correct interval."""
    sched = scheduler.create_scheduler()
    job = sched.get_job("ingest")
    assert job is not None
    assert isinstance(job.trigger, IntervalTrigger)
    assert job.trigger.interval.total_seconds() == settings.ingest_interval_minutes * 60


def test_ingest_job_scheduled_cron(monkeypatch: pytest.MonkeyPatch) -> None:
    """A cron expression configures a ``CronTrigger`` for ingestion."""
    monkeypatch.setattr(settings, "ingest_cron", "*/5 * * * *")
    sched = scheduler.create_scheduler()
    job = sched.get_job("ingest")
    assert isinstance(job.trigger, CronTrigger)


def test_ingest_job_enqueues(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ingestion job sends tasks for each enabled adapter."""

    class DummyApp:
        def __init__(self) -> None:
            self.sent: list[tuple[str, list[str], str | None]] = []

        def send_task(
            self, name: str, args: list[str] | None = None, queue: str | None = None
        ) -> None:
            self.sent.append((name, args or [], queue))

    dummy = DummyApp()
    monkeypatch.setattr(scheduler.tasks, "app", dummy)
    monkeypatch.setattr(scheduler.tasks, "ADAPTERS", {"foo": object(), "bar": object()})
    monkeypatch.setattr(settings, "enabled_adapters", ["foo", "bar"])
    scheduler.ingest_job()
    assert dummy.sent == [
        ("signal_ingestion.ingest_adapter", ["foo"], scheduler.tasks.queue_for("foo")),
        ("signal_ingestion.ingest_adapter", ["bar"], scheduler.tasks.queue_for("bar")),
    ]
