"""Tests for memory usage when fetching metrics."""

from __future__ import annotations

import gc
from datetime import UTC, datetime
from pathlib import Path

import psutil

from backend.optimization.metrics import ResourceMetric
from backend.optimization.storage import MetricsStore


def test_get_metrics_memory_usage(tmp_path: Path) -> None:
    """Ensure get_metrics does not load all rows into memory at once."""
    store = MetricsStore(f"sqlite:///{tmp_path/'metrics.db'}")
    for i in range(5000):
        store.add_metric(
            ResourceMetric(
                timestamp=datetime.now(UTC),
                cpu_percent=float(i),
                memory_mb=float(i),
                disk_usage_mb=float(i),
            )
        )

    proc = psutil.Process()
    before = proc.memory_info().rss
    count = 0
    for _ in store.get_metrics(batch_size=250):
        count += 1
    gc.collect()
    after = proc.memory_info().rss
    assert count == 5000
    assert after - before < 5 * 1024 * 1024
