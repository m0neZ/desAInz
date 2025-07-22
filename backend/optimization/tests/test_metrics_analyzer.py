"""Tests for :mod:`backend.optimization.metrics`."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend.optimization.metrics import MetricsAnalyzer, ResourceMetric


def test_average_cpu_memory() -> None:
    """Validate average CPU and memory calculations."""
    metrics = [
        ResourceMetric(
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=i),
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
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=i),
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
    now = datetime.now(timezone.utc)
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
    now = datetime.now(timezone.utc)
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
