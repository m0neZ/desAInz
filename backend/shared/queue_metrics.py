"""Prometheus collector for Celery queue lengths."""

from __future__ import annotations

import os
from typing import Iterable

import redis
from prometheus_client import REGISTRY
from prometheus_client.core import GaugeMetricFamily


class RedisQueueLengthCollector:
    """Collect queue length metrics from Redis."""

    def __init__(self, broker_url: str, queues: Iterable[str]) -> None:
        """Store ``broker_url`` and ``queues`` for metric collection."""
        self.broker_url = broker_url
        self.queues = list(queues)

    def collect(self) -> Iterable[GaugeMetricFamily]:
        """Yield a gauge with LLEN values for each queue."""
        client = redis.Redis.from_url(self.broker_url)
        metric = GaugeMetricFamily(
            "celery_queue_length",
            "Number of pending tasks per Celery queue",
            labels=["queue"],
        )
        try:
            for queue in self.queues:
                metric.add_metric([queue], client.llen(queue))
        finally:
            client.close()
        yield metric


def register_redis_queue_collector(
    queues: Iterable[str] | None = None, broker_url: str | None = None
) -> None:
    """Register ``RedisQueueLengthCollector`` with the Prometheus registry."""
    url = broker_url or os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    queue_names = list(
        filter(None, (queues or os.getenv("CELERY_QUEUES", "celery").split(",")))
    )
    try:
        REGISTRY.register(RedisQueueLengthCollector(url, queue_names))
    except ValueError:  # pragma: no cover - already registered
        pass
