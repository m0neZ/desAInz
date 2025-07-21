"""Tests for /search endpoint."""

# mypy: ignore-errors

from pathlib import Path
import os
import sys
import importlib
from unittest import mock
import warnings

from fastapi.testclient import TestClient


class DummyRedis:
    """Simple async Redis mock."""

    def __init__(self) -> None:
        import fakeredis

        self._client = fakeredis.FakeRedis()

    async def get(self, key: str) -> bytes | None:
        return self._client.get(key)

    async def setex(self, key: str, ttl: int, value: float) -> None:
        self._client.setex(key, ttl, value)

    async def incr(self, key: str) -> None:
        self._client.incr(key)


sys.path.append(str(Path(__file__).resolve().parents[1] / "backend" / "scoring-engine"))
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("KAFKA_SKIP", "1")
warnings.filterwarnings("ignore", category=DeprecationWarning)
with mock.patch("backend.shared.cache.get_async_client", return_value=DummyRedis()):
    scoring_module = importlib.import_module("scoring_engine.app")
scoring_module.settings.redis_url = "redis://localhost:6379/0"
scoring_module.redis_client = DummyRedis()
app = scoring_module.app
from backend.shared.db import session_scope
from backend.shared.db.models import Embedding


def test_search_returns_result() -> None:
    """Search returns at least one matching embedding."""
    vec = [1.0] + [0.0] * 767
    with session_scope() as session:
        session.add(Embedding(source="src", embedding=vec))
        session.flush()
    client = TestClient(app)
    resp = client.post("/search", json={"embedding": vec, "limit": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) >= 1
