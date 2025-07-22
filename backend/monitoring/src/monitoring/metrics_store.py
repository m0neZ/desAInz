"""TimescaleDB storage for scores and publish latency metrics."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, MutableMapping, cast

from backend.shared.cache import sync_delete

import requests
from backend.shared.http import request_with_retry

import sqlite3
import psycopg2
from psycopg2.pool import SimpleConnectionPool

LATENCY_CACHE_KEY = "monitoring:latency_avg"


def invalidate_latency_cache() -> None:
    """Remove cached average latency from Redis."""
    try:
        sync_delete(LATENCY_CACHE_KEY)
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
        env_url = os.environ.get("METRICS_DB_URL", "postgresql://localhost/metrics")
        self.db_url: str = db_url or env_url
        self.loki_url = loki_url or os.environ.get("LOKI_URL")
        self._session = requests.Session()

        self._use_sqlite = self.db_url.startswith("sqlite://")
        if self._use_sqlite:
            self.db_path = self.db_url.replace("sqlite://", "")
            self._pool: SimpleConnectionPool | None = None
        else:
            maxconn = int(os.environ.get("METRICS_DB_POOL_SIZE", "5"))
            self._pool = SimpleConnectionPool(1, maxconn, dsn=self.db_url)

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

    def __del__(self) -> None:
        """Close the connection pool when the store is garbage-collected."""
        pool = getattr(self, "_pool", None)
        if pool is not None:
            pool.closeall()
        self._session.close()

    def _send_loki_log(
        self, message: str, labels: MutableMapping[str, str] | None = None
    ) -> None:
        """Send a log line to Loki if configured."""
        loki_url = self.loki_url or os.environ.get("LOKI_URL")
        if not loki_url:
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
            request_with_retry(
                "POST",
                f"{loki_url}/loki/api/v1/push",
                json=payload,
                timeout=2,
                session=self._session,
            )
        except requests.RequestException:
            pass

    @contextmanager
    def _get_conn(
        self,
    ) -> Iterator[psycopg2.extensions.connection | sqlite3.Connection]:
        """Yield a database connection."""
        if self._use_sqlite:
            conn = sqlite3.connect(self.db_path)
            try:
                yield conn
            finally:
                conn.commit()
                conn.close()
        else:
            assert self._pool is not None
            conn = self._pool.getconn()
            try:
                yield conn
            finally:
                self._pool.putconn(conn)

    def add_score(self, metric: ScoreMetric) -> None:
        """Insert a score metric row."""
        with self._get_conn() as conn:
            if self._use_sqlite:
                conn.execute(
                    "INSERT INTO scores VALUES (?, ?, ?)",
                    (metric.idea_id, metric.timestamp.isoformat(), metric.score),
                )
            else:
                pg_conn = cast(psycopg2.extensions.connection, conn)
                with pg_conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO scores VALUES (%s, %s, %s)",
                        (metric.idea_id, metric.timestamp, metric.score),
                    )
                    pg_conn.commit()
        self._send_loki_log(
            "score_metric", {"idea_id": str(metric.idea_id), "type": "score"}
        )

    def add_latency(self, metric: PublishLatencyMetric) -> None:
        """Insert a publish latency metric row."""
        with self._get_conn() as conn:
            if self._use_sqlite:
                conn.execute(
                    "INSERT INTO publish_latency VALUES (?, ?, ?)",
                    (
                        metric.idea_id,
                        metric.timestamp.isoformat(),
                        metric.latency_seconds,
                    ),
                )
            else:
                pg_conn = cast(psycopg2.extensions.connection, conn)
                with pg_conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO publish_latency VALUES (%s, %s, %s)",
                        (metric.idea_id, metric.timestamp, metric.latency_seconds),
                    )
                    pg_conn.commit()
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
        if self._use_sqlite:
            return
        with self._get_conn() as conn:
            pg_conn = cast(psycopg2.extensions.connection, conn)
            with pg_conn.cursor() as cur:
                cur.execute(stmt)
                pg_conn.commit()
        self._send_loki_log("continuous_aggregate_created")

    def get_active_users(self, since: datetime) -> int:
        """Return the number of ideas with a recent score."""
        with self._get_conn() as conn:
            if self._use_sqlite:
                cur = conn.execute(
                    "SELECT COUNT(*) FROM ("
                    "SELECT idea_id, MAX(timestamp) AS ts FROM scores GROUP BY idea_id"
                    ") WHERE ts >= ?",
                    (since.isoformat(),),
                )
                row = cur.fetchone()
                return int(row[0] if row is not None else 0)
            pg_conn = cast(psycopg2.extensions.connection, conn)
            with pg_conn.cursor() as cur:
                cur.execute(
                    (
                        "SELECT COUNT(*) FROM ("
                        "SELECT idea_id, MAX(timestamp) AS ts FROM scores GROUP BY idea_id"
                        ") s WHERE ts >= %s"
                    ),
                    (since,),
                )
                result = cur.fetchone()
            return int(result[0] if result is not None else 0)

    def get_error_rate(self, since: datetime) -> float:
        """Return fraction of latest scores below ``0.5`` since ``since``."""
        with self._get_conn() as conn:
            if self._use_sqlite:
                cur = conn.execute(
                    (
                        "SELECT SUM(CASE WHEN s.score < 0.5 THEN 1 ELSE 0 END), "
                        "COUNT(*) FROM scores s "
                        "JOIN (SELECT idea_id, MAX(timestamp) ts FROM scores GROUP BY idea_id) m "
                        "ON s.idea_id = m.idea_id AND s.timestamp = m.ts "
                        "WHERE s.timestamp >= ?"
                    ),
                    (since.isoformat(),),
                )
                errors, total = cur.fetchone() or (0, 0)
            else:
                pg_conn = cast(psycopg2.extensions.connection, conn)
                with pg_conn.cursor() as cur:
                    cur.execute(
                        (
                            "SELECT SUM(CASE WHEN score < 0.5 THEN 1 ELSE 0 END), COUNT(*) "
                            "FROM (SELECT DISTINCT ON (idea_id) score, timestamp FROM scores "
                            "ORDER BY idea_id, timestamp DESC) s WHERE timestamp >= %s"
                        ),
                        (since,),
                    )
                    result = cur.fetchone()
                    errors, total = result if result is not None else (0, 0)
        return 0.0 if total == 0 else float(errors) / float(total)
