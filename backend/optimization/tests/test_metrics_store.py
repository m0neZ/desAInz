"""Tests for :class:`backend.optimization.storage.MetricsStore`."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backend.optimization.metrics import ResourceMetric
from backend.optimization.storage import MetricsStore


def test_sqlite_metrics_store(tmp_path: Path) -> None:
    """Verify metrics are persisted in a temporary SQLite database."""
    store = MetricsStore(f"sqlite:///{tmp_path/'metrics.db'}")
    metric = ResourceMetric(
        datetime.now(timezone.utc), 50.0, 128.0, disk_usage_mb=256.0
    )
    store.add_metric(metric)
    metrics = store.get_metrics()
    assert len(metrics) == 1
    assert metrics[0].cpu_percent == 50.0
    assert metrics[0].memory_mb == 128.0
    assert metrics[0].disk_usage_mb == 256.0
