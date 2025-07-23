"""Tests for automatic metrics ingestion."""

from pathlib import Path

from backend.optimization.api import record_resource_usage
from backend.optimization.storage import MetricsStore


def test_record_resource_usage(tmp_path: Path) -> None:
    """Metrics are captured and stored using the helper function."""
    store = MetricsStore(f"sqlite:///{tmp_path/'metrics.db'}")
    assert list(store.get_metrics()) == []
    record_resource_usage(store)
    metrics = list(store.get_metrics())
    assert len(metrics) == 1
    assert metrics[0].timestamp.tzinfo is not None
    assert metrics[0].disk_usage_mb is not None
