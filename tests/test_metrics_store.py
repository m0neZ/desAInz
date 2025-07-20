"""Test the Timescale metrics storage utilities."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

import backend.monitoring.src.monitoring.metrics_store as metrics_store
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


def test_pool_used_for_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure a connection pool is created for PostgreSQL URLs."""
    created: dict[str, str] = {}

    class DummyPool:
        def __init__(self, minconn: int, maxconn: int, dsn: str) -> None:
            created["dsn"] = dsn

        def getconn(self) -> object:  # pragma: no cover - dummy
            class DummyConn:
                def cursor(self) -> object:
                    class DummyCur:
                        def execute(self, *args: object, **kwargs: object) -> None:
                            pass

                    return DummyCur()

                def commit(self) -> None:  # pragma: no cover - dummy
                    pass

            return DummyConn()

        def putconn(self, conn: object) -> None:  # pragma: no cover - dummy
            pass

        def closeall(self) -> None:  # pragma: no cover - dummy
            pass

    monkeypatch.setattr(metrics_store, "SimpleConnectionPool", DummyPool)
    store = TimescaleMetricsStore("postgresql://example/db")
    assert created["dsn"] == "postgresql://example/db"
    assert isinstance(store, TimescaleMetricsStore)
