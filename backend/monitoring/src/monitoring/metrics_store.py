"""TimescaleDB storage for scores and publish latency metrics."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, MutableMapping

from backend.shared.cache import get_sync_client

import requests

import psycopg2

LATENCY_CACHE_KEY = "monitoring:latency_avg"


def invalidate_latency_cache() -> None:
    """Remove cached average latency from Redis."""
    try:
        client = get_sync_client()
        client.delete(LATENCY_CACHE_KEY)
    except Exception:  # pragma: no cover - redis optional
        pass


@dataclass
class ScoreMetric:
    """Score metric for a design idea."""

    idea_id: int
    timestamp: datetime
    score: float


@dataclass
class PublishLatencyMetric:
    """Publish latency metric for a design idea."""

    idea_id: int
    timestamp: datetime
    latency_seconds: float


class TimescaleMetricsStore:
    """Store and downsample metrics in TimescaleDB and log to Loki."""

    def __init__(self, db_url: str | None = None, loki_url: str | None = None) -> None:
        """Initialize the store, ensure tables exist and configure logging."""
        self.db_url = db_url or os.environ.get(
            "METRICS_DB_URL", "postgresql://localhost/metrics"
        )
        self.loki_url = loki_url or os.environ.get("LOKI_URL")
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                (
                    "CREATE TABLE IF NOT EXISTS scores (idea_id INTEGER, "
                    "timestamp TIMESTAMPTZ, score DOUBLE PRECISION)"
                )
            )
            cur.execute(
                (
                    "CREATE TABLE IF NOT EXISTS publish_latency (idea_id "
                    "INTEGER, timestamp TIMESTAMPTZ, latency_seconds DOUBLE "
                    "PRECISION)"
                )
            )
            conn.commit()

    def _send_loki_log(
        self, message: str, labels: MutableMapping[str, str] | None = None
    ) -> None:
        """Send a log line to Loki if configured."""
        if not self.loki_url:
            return
        payload = {
            "streams": [
                {
                    "stream": labels or {"app": "monitoring"},
                    "values": [
                        [str(int(datetime.utcnow().timestamp() * 1e9)), message]
                    ],
                }
            ]
        }
        try:
            requests.post(f"{self.loki_url}/loki/api/v1/push", json=payload, timeout=2)
        except requests.RequestException:
            pass

    @contextmanager
    def _get_conn(self) -> Iterator[psycopg2.extensions.connection]:
        """Yield a database connection."""
        conn = psycopg2.connect(self.db_url)
        try:
            yield conn
        finally:
            conn.close()

    def add_score(self, metric: ScoreMetric) -> None:
        """Insert a score metric row."""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO scores VALUES (%s, %s, %s)",
                    (metric.idea_id, metric.timestamp, metric.score),
                )
                conn.commit()
        self._send_loki_log(
            "score_metric", {"idea_id": str(metric.idea_id), "type": "score"}
        )

    def add_latency(self, metric: PublishLatencyMetric) -> None:
        """Insert a publish latency metric row."""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO publish_latency VALUES (%s, %s, %s)",
                    (metric.idea_id, metric.timestamp, metric.latency_seconds),
                )
                conn.commit()
        invalidate_latency_cache()
        self._send_loki_log(
            "latency_metric",
            {"idea_id": str(metric.idea_id), "type": "publish_latency"},
        )

    def create_hourly_continuous_aggregate(self) -> None:
        """Create an hourly downsampled view for latency metrics."""
        stmt = (
            "CREATE MATERIALIZED VIEW IF NOT EXISTS latency_hourly "
            "WITH (timescaledb.continuous) AS "
            "SELECT time_bucket('1 hour', timestamp) AS bucket, "
            "AVG(latency_seconds) AS avg_latency "
            "FROM publish_latency GROUP BY bucket"
        )
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(stmt)
                conn.commit()
        self._send_loki_log("continuous_aggregate_created")
