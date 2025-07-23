"""Tests for :mod:`backend.optimization.metrics`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backend.optimization.metrics import MetricsAnalyzer, ResourceMetric
from backend.optimization.storage import MetricsStore
import pytest


def test_average_cpu_memory() -> None:
    """Validate average CPU and memory calculations."""
    metrics = [
        ResourceMetric(
            timestamp=datetime.now(UTC) - timedelta(minutes=i),
            cpu_percent=10 * i,
            memory_mb=256.0,
            disk_usage_mb=1024.0,
        )
        for i in range(4)
    ]
    analyzer = MetricsAnalyzer(metrics)
    assert analyzer.average_cpu() == sum(10 * i for i in range(4)) / 4
    assert analyzer.average_memory() == 256.0
    assert analyzer.average_disk_usage() == 1024.0


def test_top_recommendations() -> None:
    """Ensure prioritized recommendations are returned."""
    metrics = [
        ResourceMetric(
            timestamp=datetime.now(UTC) - timedelta(minutes=i),
            cpu_percent=90,
            memory_mb=2048,
            disk_usage_mb=12 * 1024.0,
        )
        for i in range(15)
    ]
    analyzer = MetricsAnalyzer(metrics)
    recs = analyzer.top_recommendations()
    assert recs
    assert any("CPU" in r for r in recs)
    assert any("Disk usage" in r for r in recs)
    assert len(recs) <= 3


def test_trend_calculation() -> None:
    """Verify trend slopes for CPU, memory and disk."""
    now = datetime.now(UTC)
    metrics = [
        ResourceMetric(
            timestamp=now - timedelta(minutes=5 - i),
            cpu_percent=10 * i,
            memory_mb=100 * i,
            disk_usage_mb=200 * i,
        )
        for i in range(6)
    ]
    analyzer = MetricsAnalyzer(metrics)
    assert analyzer.cpu_trend() > 0
    assert analyzer.memory_trend() > 0
    assert analyzer.disk_usage_trend() > 0


def test_recommendations_for_high_usage() -> None:
    """Recommendations should mention scaling when usage is high."""
    now = datetime.now(UTC)
    metrics = [
        ResourceMetric(
            timestamp=now - timedelta(minutes=20 - i),
            cpu_percent=85 + i,
            memory_mb=1500 + 10 * i,
            disk_usage_mb=11 * 1024 + 50 * i,
        )
        for i in range(20)
    ]
    analyzer = MetricsAnalyzer(metrics)
    recs = analyzer.recommend_optimizations()
    assert any("CPU usage is trending upward" in r for r in recs)
    assert any("Disk usage exceeds" in r for r in recs)


def test_monthly_cost_estimate() -> None:
    """Compute a positive monthly cost from metrics."""
    metrics = [
        ResourceMetric(
            timestamp=datetime.now(UTC) - timedelta(minutes=i),
            cpu_percent=50.0,
            memory_mb=1024.0,
            disk_usage_mb=10 * 1024.0,
        )
        for i in range(30)
    ]
    analyzer = MetricsAnalyzer(metrics)
    cost = analyzer.monthly_cost_estimate()
    assert cost > 0


def test_cost_alerts_trigger() -> None:
    """Cost alerts should fire when thresholds are exceeded."""
    metrics = [
        ResourceMetric(
            timestamp=datetime.now(UTC) - timedelta(minutes=i),
            cpu_percent=95.0,
            memory_mb=8 * 1024.0,
            disk_usage_mb=60 * 1024.0,
        )
        for i in range(15)
    ]
    analyzer = MetricsAnalyzer(metrics)
    alerts = analyzer.cost_alerts()
    assert any("CPU usage" in a for a in alerts)
    assert any("Disk usage" in a for a in alerts)


def test_from_store_since(tmp_path):
    """`MetricsAnalyzer.from_store` filters metrics by timestamp."""
    store = MetricsStore(f"sqlite:///{tmp_path/'metrics.db'}")
    now = datetime.now(UTC)
    metrics = [
        ResourceMetric(
            timestamp=now - timedelta(minutes=i),
            cpu_percent=float(i),
            memory_mb=float(i),
            disk_usage_mb=float(i),
        )
        for i in range(10)
    ]
    store.add_metrics(metrics)

    since = now - timedelta(minutes=5)
    analyzer = MetricsAnalyzer.from_store(store, since=since)
    assert analyzer.average_cpu() == pytest.approx(sum(range(6)) / 6)
