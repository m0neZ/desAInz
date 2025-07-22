"""Tests for TimescaleMetricsStore with PostgreSQL."""

from __future__ import annotations

import psycopg2
import pytest

from backend.monitoring.src.monitoring.metrics_store import TimescaleMetricsStore


def test_create_continuous_aggregate(
    postgresql: psycopg2.extensions.connection,
) -> None:
    """Ensure continuous aggregate view is created on PostgreSQL."""
    store = TimescaleMetricsStore(postgresql.info.dsn)
    store.create_hourly_continuous_aggregate()
    with postgresql.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_matviews WHERE matviewname='latency_hourly'")
        assert cur.fetchone() is not None
