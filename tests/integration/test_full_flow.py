"""Integration test orchestrating signal to publish with metrics update."""

# mypy: ignore-errors

from __future__ import annotations

import sys
from datetime import UTC, datetime
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
import warnings

import pytest
import vcr
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# stub external dependencies before importing services
from backend.shared.kafka import utils as kafka_utils
from backend.shared.kafka import schema_registry as kafka_schema
from backend.shared.config import settings as shared_settings
import redis
import sqlalchemy

_orig_async_engine = sqlalchemy.ext.asyncio.create_async_engine
sqlalchemy.ext.asyncio.create_async_engine = lambda url, *a, **k: _orig_async_engine(
    str(url), *a, **k
)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
shared_settings.database_url = "sqlite+aiosqlite:///:memory:"
shared_settings.pgbouncer_url = None
shared_settings.schema_registry_url = "http://localhost:8081"
shared_settings.redis_url = "redis://localhost:6379/0"

kafka_utils.KafkaProducer = MagicMock(
    return_value=SimpleNamespace(send=lambda *a, **k: None, flush=lambda: None)
)
kafka_schema.SchemaRegistryClient.register = MagicMock()
kafka_schema.SchemaRegistryClient.fetch = MagicMock(return_value={})
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=pytest.PytestRemovedIn9Warning)
pytestmark = pytest.mark.filterwarnings("ignore::pytest.PytestRemovedIn9Warning")


redis.Redis.from_url = lambda *a, **k: SimpleNamespace(
    exists=lambda *args, **kwargs: False,
    bf=lambda: SimpleNamespace(
        create=lambda *args, **kwargs: None,
        exists=lambda *args, **kwargs: False,
        add=lambda *args, **kwargs: None,
    ),
    expire=lambda *args, **kwargs: None,
)

sys.modules.setdefault(
    "diffusers",
    SimpleNamespace(StableDiffusionXLPipeline=object),
)
sys.modules.setdefault(
    "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "backend" / "signal-ingestion" / "src"))
sys.path.append(str(ROOT / "backend" / "scoring-engine"))
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend" / "mockup-generation"))

from signal_ingestion import ingestion, publisher
from signal_ingestion import database as ing_db
from signal_ingestion.adapters.tiktok import TikTokAdapter
from mockup_generation.generator import MockupGenerator
from scoring_engine import scoring, weight_repository
import importlib
from backend.optimization.storage import MetricsStore

opt_api = importlib.import_module("backend.optimization.api")


@vcr.use_cassette(
    "tests/integration/cassettes/full_flow.yaml", record_mode="new_episodes"
)
@pytest.mark.asyncio()
async def test_full_flow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Run ingestion, scoring, generation, publishing and metrics update."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(ing_db, "engine", engine)
    monkeypatch.setattr(ing_db, "SessionLocal", session_factory)
    await ing_db.init_db()

    ingestion.ADAPTERS = [TikTokAdapter()]

    sent: list[dict] = []

    def fake_produce(topic: str, message: dict) -> None:
        sent.append(message)

    monkeypatch.setattr(publisher.producer, "produce", fake_produce)

    class DummyPipe:
        def __call__(self, **kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(
                images=[SimpleNamespace(save=lambda p: Path(p).touch())]
            )

    def fake_load(self, *args: object, **kwargs: object) -> None:
        self.pipeline = DummyPipe()

    monkeypatch.setattr(MockupGenerator, "load", fake_load)

    async def _fallback(_: str) -> SimpleNamespace:  # pragma: no cover
        return SimpleNamespace(save=lambda pth: Path(pth).touch())

    monkeypatch.setattr(
        MockupGenerator,
        "_fallback_api",
        staticmethod(_fallback),
    )

    import signal_ingestion.dedup as dedup

    store = set()
    monkeypatch.setattr(dedup, "is_duplicate", lambda key: key in store)
    monkeypatch.setattr(dedup, "add_key", lambda key: store.add(key))

    monkeypatch.setattr(weight_repository, "update_weights", lambda **k: None)
    sig = scoring.Signal(
        source="global",
        timestamp=datetime.utcnow().replace(tzinfo=UTC),
        engagement_rate=1.0,
        embedding=[0.1, 0.2],
        metadata={},
    )
    score = scoring.calculate_score(sig, 0.5, [])
    assert isinstance(score, float)

    gen = MockupGenerator()
    result = gen.generate("cat", str(tmp_path / "img.png"), num_inference_steps=1)
    assert Path(result.image_path).exists()

    publisher.publish("signals", "done")
    assert sent

    monkeypatch.setattr(
        opt_api,
        "store",
        MetricsStore(f"sqlite:///{tmp_path / 'metrics.db'}"),
    )
    client = TestClient(opt_api.app)
    metric = {
        "timestamp": datetime.utcnow().replace(tzinfo=UTC).isoformat(),
        "cpu_percent": 10,
        "memory_mb": 100,
    }
    response = client.post("/metrics", json=metric)
    assert response.status_code == 200
    response = client.get("/optimizations")
    assert response.status_code == 200
    assert len(opt_api.store.get_metrics()) == 1
