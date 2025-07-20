"""Tests for metrics analysis utilities."""

from datetime import datetime, timedelta, timezone

from backend.optimization.metrics import MetricsAnalyzer, ResourceMetric


def test_average_cpu_memory() -> None:
    """Validate average calculations for CPU and memory."""
    metrics = [
        ResourceMetric(
            datetime.now(timezone.utc) - timedelta(minutes=i),
            50 + i,
            512,
            disk_usage_mb=1024.0,
        )
        for i in range(5)
    ]
    analyzer = MetricsAnalyzer(metrics)
    assert analyzer.average_cpu() > 50
    assert analyzer.average_memory() == 512


def test_top_recommendations() -> None:
    """Ensure top recommendations are returned in priority order."""
    metrics = [
        ResourceMetric(
            datetime.now(timezone.utc) - timedelta(minutes=i),
            90,
            2048,
            disk_usage_mb=11 * 1024.0,
        )
        for i in range(20)
    ]
    analyzer = MetricsAnalyzer(metrics)
    recs = analyzer.top_recommendations()
    assert recs != []
    assert len(recs) <= 3
    assert any("Average CPU" in r for r in recs)


def test_trend_methods() -> None:
    """Check that trend utilities return positive slopes."""
    now = datetime.now(timezone.utc)
    metrics = [
        ResourceMetric(
            now - timedelta(minutes=5 - i),
            cpu_percent=20 * i,
            memory_mb=128 * i,
            disk_usage_mb=256 * i,
        )
        for i in range(6)
    ]
    analyzer = MetricsAnalyzer(metrics)
    assert analyzer.cpu_trend() > 0
    assert analyzer.memory_trend() > 0
    assert analyzer.disk_usage_trend() > 0
