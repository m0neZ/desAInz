"""Test the Timescale metrics storage utilities."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from contextlib import contextmanager

import fakeredis

import pytest
import psycopg2

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
        idea_id=1, timestamp=datetime.utcnow().replace(tzinfo=UTC), score=0.8
    )
    store.add_score(score_metric)
    latency_metric = PublishLatencyMetric(
        idea_id=1,
        timestamp=datetime.utcnow().replace(tzinfo=UTC),
        latency_seconds=2.5,
    )
    store.add_latency(latency_metric)
    # create aggregate should not fail on SQLite
    store.create_hourly_continuous_aggregate()
    assert (
        store.get_active_users(
            datetime.utcnow().replace(tzinfo=UTC) - timedelta(hours=1)
        )
        == 1
    )


def test_pool_used_for_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure a connection pool is created for PostgreSQL URLs."""
    created: dict[str, str] = {}

    class DummyPool:
        def __init__(self, _minconn: int, maxconn: int, dsn: str) -> None:
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


def test_postgresql_metrics(
    postgresql: psycopg2.extensions.connection,
) -> None:
    """Verify metrics operations work with PostgreSQL."""
    store = TimescaleMetricsStore(postgresql.info.dsn)
    metric = ScoreMetric(
        idea_id=2, timestamp=datetime.utcnow().replace(tzinfo=UTC), score=0.9
    )
    store.add_score(metric)
    latency_metric = PublishLatencyMetric(
        idea_id=2,
        timestamp=datetime.utcnow().replace(tzinfo=UTC),
        latency_seconds=1.2,
    )
    store.add_latency(latency_metric)
    since = datetime.utcnow().replace(tzinfo=UTC) - timedelta(minutes=5)
    assert store.get_active_users(since) == 1


def test_active_users_cached(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Active user aggregation should be cached and invalidated."""
    db = tmp_path / "metrics.db"
    store = TimescaleMetricsStore(f"sqlite:///{db}")
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(metrics_store, "sync_get", lambda key: fake.get(key))
    monkeypatch.setattr(
        metrics_store,
        "sync_set",
        lambda key, value, ttl=None: (
            fake.setex(key, ttl, value) if ttl else fake.set(key, value)
        ),
    )
    monkeypatch.setattr(metrics_store, "sync_delete", lambda key: fake.delete(key))
    metric = ScoreMetric(
        idea_id=3, timestamp=datetime.utcnow().replace(tzinfo=UTC), score=0.8
    )
    store.add_score(metric)

    calls: list[int] = []
    orig_get_conn = store._get_conn

    @contextmanager
    def counting_conn():
        calls.append(1)
        with orig_get_conn() as conn:
            yield conn

    monkeypatch.setattr(store, "_get_conn", counting_conn)
    since = datetime.utcnow().replace(tzinfo=UTC) - timedelta(hours=1)
    assert store.get_active_users(since) == 1
    assert store.get_active_users(since) == 1
    assert len(calls) == 1


def test_cache_invalidated_on_new_score(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Adding a new score should clear cached aggregations."""
    db = tmp_path / "metrics.db"
    store = TimescaleMetricsStore(f"sqlite:///{db}")
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(metrics_store, "sync_get", lambda key: fake.get(key))
    monkeypatch.setattr(
        metrics_store,
        "sync_set",
        lambda key, value, ttl=None: (
            fake.setex(key, ttl, value) if ttl else fake.set(key, value)
        ),
    )
    monkeypatch.setattr(metrics_store, "sync_delete", lambda key: fake.delete(key))
    metric = ScoreMetric(
        idea_id=4, timestamp=datetime.utcnow().replace(tzinfo=UTC), score=0.8
    )
    store.add_score(metric)
    since = datetime.utcnow().replace(tzinfo=UTC) - timedelta(hours=1)
    assert store.get_active_users(since) == 1
    assert fake.get(metrics_store.ACTIVE_USERS_CACHE_KEY) is not None
    metric2 = ScoreMetric(
        idea_id=5, timestamp=datetime.utcnow().replace(tzinfo=UTC), score=0.7
    )
    store.add_score(metric2)
    assert fake.get(metrics_store.ACTIVE_USERS_CACHE_KEY) is None
