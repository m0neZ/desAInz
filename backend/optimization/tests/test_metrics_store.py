"""Tests for :class:`backend.optimization.storage.MetricsStore`."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from backend.optimization.metrics import ResourceMetric
from backend.optimization.storage import MetricsStore


def test_sqlite_metrics_store(tmp_path: Path) -> None:
    """Verify metrics are persisted in a temporary SQLite database."""
    store = MetricsStore(f"sqlite:///{tmp_path/'metrics.db'}")
    metric = ResourceMetric(datetime.now(UTC), 50.0, 128.0, disk_usage_mb=256.0)
    store.add_metric(metric)
    metrics = list(store.get_metrics())
    assert len(metrics) == 1
    assert metrics[0].cpu_percent == 50.0
    assert metrics[0].memory_mb == 128.0
    assert metrics[0].disk_usage_mb == 256.0


def test_add_metrics_batch(tmp_path: Path) -> None:
    """Verify multiple metrics can be inserted efficiently."""
    store = MetricsStore(f"sqlite:///{tmp_path/'metrics.db'}")
    metrics = [ResourceMetric(datetime.now(UTC), float(i), float(i)) for i in range(3)]
    store.add_metrics(metrics)
    retrieved = list(store.get_metrics())
    assert len(retrieved) == 3
