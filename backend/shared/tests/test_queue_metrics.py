"""Tests for Redis queue length metrics collector."""

from __future__ import annotations

from typing import Any

import fakeredis
import redis

from backend.shared import queue_metrics


def test_queue_length_collector(monkeypatch: Any) -> None:
    """Collector reports pending tasks for each queue."""
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(redis.Redis, "from_url", lambda *_a, **_kw: fake)
    fake.rpush("celery", b"job")
    collector = queue_metrics.RedisQueueLengthCollector("redis://localhost", ["celery"])
    metric = next(iter(collector.collect()))
    assert metric.samples[0].value == 1
