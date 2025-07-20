"""Integration tests for the resource MetricsStore."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.optimization.storage import MetricsStore
from backend.optimization.metrics import ResourceMetric
import psycopg2


@pytest.mark.parametrize(
    "url",
    [
        None,  # default sqlite
        "postgresql://postgres:postgres@localhost/test_metrics",
    ],
)
def test_add_and_get_metrics(url: str | None, tmp_path: Path) -> None:
    """Ensure metrics are persisted and fetched using different backends."""
    if url is None:
        db_path = tmp_path / "metrics.db"
        store = MetricsStore(f"sqlite:///{db_path}")
    else:
        try:
            with psycopg2.connect(url) as conn:
                with conn.cursor() as cur:
                    cur.execute("TRUNCATE metrics")
                conn.commit()
        except psycopg2.OperationalError:
            pytest.skip("PostgreSQL not available")
        store = MetricsStore(url)

    metric = ResourceMetric(
        timestamp=datetime.now(timezone.utc), cpu_percent=1.0, memory_mb=2.0
    )
    store.add_metric(metric)
    metrics = store.get_metrics()
    assert len(metrics) == 1
    assert metrics[0].cpu_percent == 1.0
    assert metrics[0].memory_mb == 2.0
