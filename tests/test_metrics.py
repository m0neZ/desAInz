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
            datetime.now(timezone.utc) - timedelta(minutes=1),
            90,
            2048,
        )
    ]
    analyzer = MetricsAnalyzer(metrics)
    recs = analyzer.top_recommendations()
    assert recs != []
    assert len(recs) <= 3
