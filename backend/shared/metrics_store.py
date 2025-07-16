"""Metrics storage utilities using ClickHouse."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Tuple
from abc import ABC, abstractmethod

import clickhouse_connect


@dataclass
class ScoreRecord:
    """A scored signal entry."""

    timestamp: datetime
    score: float


@dataclass
class PublishLatencyRecord:
    """A single publish latency entry."""

    timestamp: datetime
    latency_ms: float


class BaseMetricsStore(ABC):
    """Abstract metrics storage interface."""

    @abstractmethod
    def add_score(self, record: ScoreRecord) -> None:
        """Store a score metric."""

    @abstractmethod
    def add_publish_latency(self, record: PublishLatencyRecord) -> None:
        """Store a publish latency metric."""

    @abstractmethod
    def query_scores(self, interval_minutes: int) -> List[Tuple[datetime, float]]:
        """Return average score per ``interval_minutes``."""

    @abstractmethod
    def query_latency(self, interval_minutes: int) -> List[Tuple[datetime, float]]:
        """Return average latency per ``interval_minutes``."""


class InMemoryMetricsStore(BaseMetricsStore):
    """Store metrics in memory for testing."""

    def __init__(self) -> None:
        """Initialize empty in-memory storage."""
        self.scores: List[ScoreRecord] = []
        self.latencies: List[PublishLatencyRecord] = []

    def add_score(self, record: ScoreRecord) -> None:
        """Add a scoring metric."""
        self.scores.append(record)

    def add_publish_latency(self, record: PublishLatencyRecord) -> None:
        """Add a publish latency metric."""
        self.latencies.append(record)

    def _downsample(
        self, data: Iterable[Tuple[datetime, float]], interval_minutes: int
    ) -> List[Tuple[datetime, float]]:
        """Aggregate ``data`` by ``interval_minutes``."""
        buckets: Dict[datetime, List[float]] = {}
        for ts, value in data:
            bucket = ts.replace(
                second=0,
                microsecond=0,
                minute=(ts.minute // interval_minutes) * interval_minutes,
            )
            buckets.setdefault(bucket, []).append(value)
        return [
            (ts, sum(values) / len(values)) for ts, values in sorted(buckets.items())
        ]

    def query_scores(self, interval_minutes: int) -> List[Tuple[datetime, float]]:
        """Return average score per ``interval_minutes`` from memory."""
        return self._downsample(
            [(r.timestamp, r.score) for r in self.scores], interval_minutes
        )

    def query_latency(self, interval_minutes: int) -> List[Tuple[datetime, float]]:
        """Return average latency per ``interval_minutes`` from memory."""
        return self._downsample(
            [(r.timestamp, r.latency_ms) for r in self.latencies], interval_minutes
        )


class ClickHouseMetricsStore(BaseMetricsStore):
    """Store metrics in ClickHouse."""

    def __init__(self, url: str) -> None:
        """Connect to ClickHouse at ``url`` and create tables if needed."""
        host, port = url.split(":") if ":" in url else (url, "8123")
        self.client = clickhouse_connect.get_client(host=host, port=int(port))
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create tables for metrics if they do not exist."""
        self.client.command(
            """
            CREATE TABLE IF NOT EXISTS scores(
                timestamp DateTime,
                score Float32
            ) ENGINE=MergeTree ORDER BY timestamp
            """
        )
        self.client.command(
            """
            CREATE TABLE IF NOT EXISTS publish_latency(
                timestamp DateTime,
                latency_ms Float32
            ) ENGINE=MergeTree ORDER BY timestamp
            """
        )

    def add_score(self, record: ScoreRecord) -> None:
        """Insert a score record into ClickHouse."""
        self.client.insert(
            "scores",
            [[record.timestamp, record.score]],
            column_names=["timestamp", "score"],
        )

    def add_publish_latency(self, record: PublishLatencyRecord) -> None:
        """Insert a publish latency record into ClickHouse."""
        self.client.insert(
            "publish_latency",
            [[record.timestamp, record.latency_ms]],
            column_names=["timestamp", "latency_ms"],
        )

    def _query(self, table: str, interval_minutes: int) -> List[Tuple[datetime, float]]:
        """Return averages over ``interval_minutes`` for ``table``."""
        query = (
            "SELECT toStartOfInterval(timestamp, INTERVAL "
            f"{interval_minutes} minute) AS ts, avg(value) "
            f"FROM (SELECT timestamp, {{column}} AS value FROM {table})"
            " GROUP BY ts ORDER BY ts"
        )
        column = "score" if table == "scores" else "latency_ms"
        result = self.client.query(query.format(column=column))
        return [(row[0], row[1]) for row in result.result_rows]

    def query_scores(self, interval_minutes: int) -> List[Tuple[datetime, float]]:
        """Query averaged scores."""
        return self._query("scores", interval_minutes)

    def query_latency(self, interval_minutes: int) -> List[Tuple[datetime, float]]:
        """Query averaged publish latency."""
        return self._query("publish_latency", interval_minutes)


def get_metrics_store() -> BaseMetricsStore:
    """Return a metrics store based on ``CLICKHOUSE_URL``."""
    url = os.environ.get("CLICKHOUSE_URL")
    if url:
        try:
            return ClickHouseMetricsStore(url)
        except Exception:  # pragma: no cover - fallback when DB unavailable
            return InMemoryMetricsStore()
    return InMemoryMetricsStore()


METRICS_STORE = get_metrics_store()
