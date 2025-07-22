"""Storage backend for resource metrics."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator, List, Tuple

import psycopg2
from urllib.parse import urlparse

from .metrics import ResourceMetric


class MetricsStore:
    """Store and retrieve resource metrics in SQLite or TimescaleDB."""

    def __init__(self, db_url: str | None = None) -> None:
        """Initialize the store and ensure the table exists."""
        self.db_url = db_url or os.environ.get(
            "METRICS_DB_URL", f"sqlite:///{os.path.abspath('metrics.db')}"
        )
        parsed = urlparse(self.db_url)
        self._use_sqlite = str(parsed.scheme).startswith("sqlite")
        if self._use_sqlite:
            self.db_path = parsed.path
            with self._get_sqlite_conn() as conn:
                conn.execute(
                    (
                        "CREATE TABLE IF NOT EXISTS metrics (timestamp TEXT, "
                        "cpu REAL, memory REAL, disk REAL)"
                    )
                )
        else:
            with self._get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        (
                            "CREATE TABLE IF NOT EXISTS metrics (timestamp "
                            "TIMESTAMPTZ, cpu DOUBLE PRECISION, memory DOUBLE "
                            "PRECISION, disk DOUBLE PRECISION)"
                        )
                    )
                    conn.commit()

    @contextmanager
    def _get_sqlite_conn(self) -> Iterator[sqlite3.Connection]:
        """Yield a SQLite connection."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.commit()
            conn.close()

    @contextmanager
    def _get_pg_conn(self) -> Iterator[psycopg2.extensions.connection]:
        """Yield a PostgreSQL connection."""
        conn = psycopg2.connect(self.db_url)
        try:
            yield conn
        finally:
            conn.close()

    def add_metric(self, metric: ResourceMetric) -> None:
        """Add a metric entry to the database."""
        if self._use_sqlite:
            with self._get_sqlite_conn() as conn:
                conn.execute(
                    "INSERT INTO metrics VALUES (?, ?, ?, ?)",
                    (
                        metric.timestamp.isoformat(),
                        metric.cpu_percent,
                        metric.memory_mb,
                        metric.disk_usage_mb,
                    ),
                )
        else:
            with self._get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO metrics VALUES (%s, %s, %s, %s)",
                        (
                            metric.timestamp.isoformat(),
                            metric.cpu_percent,
                            metric.memory_mb,
                            metric.disk_usage_mb,
                        ),
                    )
                    conn.commit()

    def get_metrics(self) -> List[ResourceMetric]:
        """Retrieve all stored metrics."""
        if self._use_sqlite:
            with self._get_sqlite_conn() as conn:
                rows = conn.execute(
                    "SELECT timestamp, cpu, memory, disk FROM metrics"
                ).fetchall()
        else:
            with self._get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT timestamp, cpu, memory, disk FROM metrics")
                    rows = cur.fetchall()
        result: List[ResourceMetric] = []
        for ts, cpu, memory, disk in rows:
            if isinstance(ts, datetime):
                timestamp = ts
            else:
                timestamp = datetime.fromisoformat(str(ts))
            result.append(
                ResourceMetric(
                    timestamp=timestamp,
                    cpu_percent=cpu,
                    memory_mb=memory,
                    disk_usage_mb=disk,
                )
            )
        return result

    def get_recent_metrics(self, limit: int) -> List[ResourceMetric]:
        """Return the most recent ``limit`` metrics ordered oldest to newest."""
        if self._use_sqlite:
            with self._get_sqlite_conn() as conn:
                rows = conn.execute(
                    "SELECT timestamp, cpu, memory, disk FROM metrics"
                    " ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        else:
            with self._get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT timestamp, cpu, memory, disk FROM metrics"
                        " ORDER BY timestamp DESC LIMIT %s",
                        (limit,),
                    )
                    rows = cur.fetchall()
        return list(reversed(self._rows_to_metrics(rows)))

    def get_metrics_since(self, since: datetime) -> List[ResourceMetric]:
        """Return metrics recorded at or after ``since``."""
        if self._use_sqlite:
            with self._get_sqlite_conn() as conn:
                rows = conn.execute(
                    "SELECT timestamp, cpu, memory, disk FROM metrics"
                    " WHERE timestamp >= ? ORDER BY timestamp",
                    (since.isoformat(),),
                ).fetchall()
        else:
            with self._get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT timestamp, cpu, memory, disk FROM metrics"
                        " WHERE timestamp >= %s ORDER BY timestamp",
                        (since.isoformat(),),
                    )
                    rows = cur.fetchall()
        return self._rows_to_metrics(rows)

    def _rows_to_metrics(
        self, rows: list[Tuple[str | datetime, float, float, float | None]]
    ) -> List[ResourceMetric]:
        """Convert database rows to :class:`ResourceMetric` objects."""
        result: List[ResourceMetric] = []
        for ts, cpu, memory, disk in rows:
            if isinstance(ts, datetime):
                timestamp = ts
            else:
                timestamp = datetime.fromisoformat(str(ts))
            result.append(
                ResourceMetric(
                    timestamp=timestamp,
                    cpu_percent=cpu,
                    memory_mb=memory,
                    disk_usage_mb=disk,
                )
            )
        return result

    def create_hourly_continuous_aggregate(self) -> None:
        """Create an hourly materialized view when using PostgreSQL."""
        if self._use_sqlite:
            return

        stmt_ts = (
            "CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_hourly "
            "WITH (timescaledb.continuous) AS "
            "SELECT time_bucket('1 hour', timestamp) AS bucket, "
            "AVG(cpu) AS avg_cpu, AVG(memory) AS avg_memory, "
            "AVG(disk) AS avg_disk "
            "FROM metrics GROUP BY bucket"
        )
        fallback_stmt = (
            "CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_hourly AS "
            "SELECT date_trunc('hour', timestamp) AS bucket, "
            "AVG(cpu) AS avg_cpu, AVG(memory) AS avg_memory, "
            "AVG(disk) AS avg_disk "
            "FROM metrics GROUP BY bucket"
        )
        with self._get_pg_conn() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(stmt_ts)
                except psycopg2.Error:
                    cur.execute(fallback_stmt)
                conn.commit()
