"""Tests for the ingestion scheduler."""

from __future__ import annotations

import importlib
import os
import sys
from typing import Any, Callable, Tuple
from types import ModuleType

import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)  # noqa: E402
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")),
)  # noqa: E402
os.environ["DATABASE_URL"] = "sqlite:///test.db"  # noqa: E402
os.environ["KAFKA_SKIP"] = "1"  # noqa: E402


class _DummyBloom:
    def create(self, *args: Any, **kwargs: Any) -> None:
        """Do nothing."""

    def exists(self, *args: Any, **kwargs: Any) -> bool:
        return False

    def add(self, *args: Any, **kwargs: Any) -> None:
        pass


class _DummyRedis:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def bf(self) -> _DummyBloom:
        return _DummyBloom()

    def exists(self, *args: Any, **kwargs: Any) -> bool:
        return False

    def expire(self, *args: Any, **kwargs: Any) -> None:
        pass

    @classmethod
    def from_url(cls, *args: Any, **kwargs: Any) -> "_DummyRedis":
        return cls()


import redis  # noqa: E402

redis.Redis = _DummyRedis

from apscheduler.triggers.cron import CronTrigger  # noqa: E402
from apscheduler.triggers.interval import IntervalTrigger  # noqa: E402


class DummyApp:
    """Collect Celery send_task calls."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, list[str], str | None]] = []

    def send_task(
        self,
        name: str,
        args: list[str] | None = None,
        queue: str | None = None,
    ) -> None:
        self.sent.append((name, args or [], queue))


from apscheduler.schedulers.base import BaseScheduler
from signal_ingestion.settings import Settings


def _load_scheduler(
    monkeypatch: pytest.MonkeyPatch,
) -> Tuple[Callable[[], BaseScheduler], Settings, DummyApp]:
    import types
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from backend.shared import config as shared_config

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    dummy_db = ModuleType("signal_ingestion.database")
    dummy_db.engine = engine  # type: ignore[attr-defined]
    dummy_db.SessionLocal = async_sessionmaker(  # type: ignore[attr-defined]
        engine, expire_on_commit=False
    )

    async def init_db() -> None:
        pass

    dummy_db.init_db = init_db  # type: ignore[attr-defined]
    sys.modules["signal_ingestion.database"] = dummy_db

    import signal_ingestion.tasks as tasks
    import signal_ingestion.settings as settings_mod
    import signal_ingestion.scheduler as scheduler_mod

    shared_config.settings.database_url = "sqlite:///test.db"
    importlib.reload(settings_mod)
    importlib.reload(tasks)
    importlib.reload(scheduler_mod)

    dummy = DummyApp()
    monkeypatch.setattr(tasks, "app", dummy)
    return scheduler_mod.create_scheduler, settings_mod.settings, dummy


def test_ingest_jobs_interval(monkeypatch: pytest.MonkeyPatch) -> None:
    """Jobs use ``IntervalTrigger`` when no cron schedule is provided."""
    monkeypatch.delenv("INGEST_CRON_SCHEDULE", raising=False)
    create_scheduler, settings, dummy = _load_scheduler(monkeypatch)
    scheduler = create_scheduler()
    jobs = scheduler.get_jobs()
    assert jobs
    for job in jobs:
        assert isinstance(job.trigger, IntervalTrigger)
        job.func(*job.args)
    expected = [
        (
            "signal_ingestion.ingest_adapter",
            [name],
            importlib.import_module("signal_ingestion.tasks").queue_for(name),
        )
        for name in importlib.import_module(
            "signal_ingestion.tasks"
        ).ADAPTERS.keys()
    ]
    assert dummy.sent == expected
    assert (
        job.trigger.interval.total_seconds()
        == settings.ingest_interval_minutes * 60
    )


def test_ingest_jobs_cron(monkeypatch: pytest.MonkeyPatch) -> None:
    """Jobs use ``CronTrigger`` when cron schedule is configured."""
    monkeypatch.setenv("INGEST_CRON_SCHEDULE", "0 0 * * *")
    create_scheduler, _, _ = _load_scheduler(monkeypatch)
    scheduler = create_scheduler()
    jobs = scheduler.get_jobs()
    assert jobs
    assert all(isinstance(job.trigger, CronTrigger) for job in jobs)
