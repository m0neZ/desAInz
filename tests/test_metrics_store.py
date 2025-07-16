"""Tests for metrics storage and downsampling."""

from datetime import datetime, timedelta

from backend.shared.metrics_store import (
    InMemoryMetricsStore,
    ScoreRecord,
    PublishLatencyRecord,
)


def test_downsampling() -> None:
    """Metrics should be grouped by minute."""
    store = InMemoryMetricsStore()
    now = datetime.utcnow()
    store.add_score(ScoreRecord(timestamp=now, score=1.0))
    store.add_score(ScoreRecord(timestamp=now + timedelta(seconds=30), score=3.0))
    result = store.query_scores(1)
    assert len(result) == 1
    assert abs(result[0][1] - 2.0) < 1e-6
    store.add_publish_latency(PublishLatencyRecord(timestamp=now, latency_ms=10))
    store.add_publish_latency(
        PublishLatencyRecord(timestamp=now + timedelta(seconds=30), latency_ms=30)
    )
    lat = store.query_latency(1)
    assert len(lat) == 1
    assert abs(lat[0][1] - 20.0) < 1e-6
