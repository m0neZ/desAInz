"""Integration tests for the resource MetricsStore."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from backend.optimization.metrics import ResourceMetric
from backend.optimization.storage import MetricsStore


@pytest.mark.parametrize("use_postgres", [False, True])
def test_add_and_get_metrics(use_postgres: bool, tmp_path: Path, postgresql) -> None:
    """Ensure metrics are persisted and fetched using different backends."""
    if not use_postgres:
        db_path = tmp_path / "metrics.db"
        store = MetricsStore(f"sqlite:///{db_path}")
    else:
        with postgresql.cursor() as cur:
            cur.execute("TRUNCATE metrics")
        postgresql.commit()
        store = MetricsStore(postgresql.info.dsn)

    metric = ResourceMetric(
        timestamp=datetime.utcnow().replace(tzinfo=UTC),
        cpu_percent=1.0,
        memory_mb=2.0,
        disk_usage_mb=3.0,
    )
    store.add_metric(metric)
    metrics = store.get_metrics()
    assert len(metrics) == 1
    assert metrics[0].cpu_percent == 1.0
    assert metrics[0].memory_mb == 2.0
    assert metrics[0].disk_usage_mb == 3.0
