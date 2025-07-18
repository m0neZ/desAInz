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

from apscheduler.triggers.interval import IntervalTrigger  # noqa: E402

from signal_ingestion.scheduler import create_scheduler  # noqa: E402
from signal_ingestion.settings import settings  # noqa: E402


def test_ingest_job_scheduled() -> None:
    """The scheduler configures the ingest job with the correct interval."""
    scheduler = create_scheduler()
    job = scheduler.get_job("ingest")
    assert job is not None
    assert isinstance(job.trigger, IntervalTrigger)
    assert job.trigger.interval.total_seconds() == settings.ingest_interval_minutes * 60
