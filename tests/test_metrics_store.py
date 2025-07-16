"""Test the Timescale metrics storage utilities."""

from datetime import datetime, timezone
from pathlib import Path

from backend.monitoring.src.monitoring.metrics_store import (
    PublishLatencyMetric,
    ScoreMetric,
    TimescaleMetricsStore,
)


def test_metrics_insertion(tmp_path: Path) -> None:
    """Verify that metrics can be stored without error."""
    db = tmp_path / "metrics.db"
    store = TimescaleMetricsStore(f"sqlite:///{db}")
    score_metric = ScoreMetric(
        idea_id=1, timestamp=datetime.now(timezone.utc), score=0.8
    )
    store.add_score(score_metric)
    latency_metric = PublishLatencyMetric(
        idea_id=1,
        timestamp=datetime.now(timezone.utc),
        latency_seconds=2.5,
    )
    store.add_latency(latency_metric)
    # create aggregate should not fail on SQLite
    store.create_hourly_continuous_aggregate()
