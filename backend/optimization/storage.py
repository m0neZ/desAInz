"""SQLite-based storage for resource metrics."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator, List

from .metrics import ResourceMetric


class MetricsStore:
    """Store and retrieve resource metrics."""

    def __init__(self, db_path: str = "metrics.db") -> None:
        """Initialize the store and ensure the table exists."""
        self.db_path = db_path
        with self._get_connection() as conn:
            conn.execute(
                (
                    "CREATE TABLE IF NOT EXISTS metrics (timestamp TEXT, "
                    "cpu REAL, memory REAL)"
                )
            )

    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager returning a SQLite connection."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.commit()
            conn.close()

    def add_metric(self, metric: ResourceMetric) -> None:
        """Add a metric entry to the database."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO metrics VALUES (?, ?, ?)",
                (metric.timestamp.isoformat(), metric.cpu_percent, metric.memory_mb),
            )

    def get_metrics(self) -> List[ResourceMetric]:
        """Retrieve all stored metrics."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT timestamp, cpu, memory FROM metrics").fetchall()
        return [
            ResourceMetric(
                timestamp=datetime.fromisoformat(ts),
                cpu_percent=cpu,
                memory_mb=memory,
            )
            for ts, cpu, memory in rows
        ]
