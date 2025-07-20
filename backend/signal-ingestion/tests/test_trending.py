"""Tests for trending keyword cache."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from pathlib import Path

import fakeredis

import pytest
from fastapi.testclient import TestClient
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="fastapi.*")

from signal_ingestion import trending
from backend.shared.config import settings


def test_store_keywords_sets_ttl(monkeypatch):
    """`store_keywords` refreshes TTL on the sorted set."""
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(trending, "get_sync_client", lambda: fake)
    trending.store_keywords(["foo", "bar"])
    ttl1 = fake.ttl(trending.TRENDING_KEY)
    assert 0 < ttl1 <= settings.trending_ttl
    trending.store_keywords(["foo"])
    ttl2 = fake.ttl(trending.TRENDING_KEY)
    assert ttl2 > 0
    assert ttl2 <= settings.trending_ttl
    assert ttl2 >= ttl1 - 1


def test_get_top_keywords_sorted(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return keywords ordered by score."""
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(trending, "get_sync_client", lambda: fake)
    fake.zadd(trending.TRENDING_KEY, {"foo": 1, "bar": 3, "baz": 2})
    assert trending.get_top_keywords(2) == ["bar", "baz"]


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_trending_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Endpoint returns trending keywords list."""
    sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
    sys.modules.setdefault(
        "pgvector.sqlalchemy", SimpleNamespace(Vector=lambda *a, **k: None)
    )
    sys.modules.setdefault(
        "signal_ingestion.database",
        SimpleNamespace(
            get_session=lambda: None,
            init_db=lambda: None,
            SessionLocal=lambda: None,
        ),
    )
    sys.modules.setdefault(
        "signal_ingestion.models", SimpleNamespace(Base=object, Signal=object)
    )
    sys.modules.setdefault(
        "celery",
        SimpleNamespace(Celery=lambda *a, **k: SimpleNamespace(conf=SimpleNamespace())),
    )
    sys.modules.setdefault(
        "signal_ingestion.scheduler", SimpleNamespace(create_scheduler=lambda: None)
    )
    sys.modules.setdefault(
        "signal_ingestion.ingestion", SimpleNamespace(ingest=lambda *a, **k: None)
    )
    sys.modules.setdefault("signal_ingestion.tasks", SimpleNamespace())
    sys.modules.setdefault(
        "signal_ingestion.publisher", SimpleNamespace(publish=lambda *a, **k: None)
    )
    sys.modules.setdefault(
        "signal_ingestion.dedup",
        SimpleNamespace(
            add_key=lambda *a, **k: None,
            is_duplicate=lambda *a, **k: False,
            initialize=lambda: None,
        ),
    )
    sys.modules.setdefault(
        "backend.shared.kafka.schema_registry",
        SimpleNamespace(SchemaRegistryClient=lambda *a, **k: None),
    )
    sys.modules.setdefault(
        "kafka",
        SimpleNamespace(
            KafkaProducer=lambda *a, **k: SimpleNamespace(
                send=lambda *a, **k: None, flush=lambda: None
            ),
            KafkaConsumer=object,
        ),
    )
    from signal_ingestion import main as main_module

    monkeypatch.setattr(trending, "get_top_keywords", lambda limit=10: ["foo", "bar"])
    client = TestClient(main_module.app)
    resp = client.get("/trending?limit=2")
    assert resp.status_code == 200
    assert resp.json() == ["foo", "bar"]
