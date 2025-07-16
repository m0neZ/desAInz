"""Integration test covering the full pipeline with metrics verification."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "backend" / "signal-ingestion" / "src"))
sys.path.append(str(ROOT / "backend" / "scoring-engine"))
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend" / "mockup-generation"))

import kafka  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402
from types import ModuleType, SimpleNamespace  # noqa: E402

diffusers_stub = ModuleType("diffusers")
setattr(diffusers_stub, "StableDiffusionXLPipeline", object)
sys.modules.setdefault("diffusers", diffusers_stub)

torch_stub = ModuleType("torch")
setattr(torch_stub, "cuda", SimpleNamespace(is_available=lambda: False))
sys.modules.setdefault("torch", torch_stub)

kafka_producer_mock = MagicMock(
    return_value=SimpleNamespace(send=lambda *a, **k: None, flush=lambda: None)
)
kafka.KafkaProducer = kafka_producer_mock

import psutil  # noqa: E402
import time  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)  # noqa: E402

from signal_ingestion import ingestion, publisher  # noqa: E402
from signal_ingestion import database as ing_db  # noqa: E402
from mockup_generation.generator import MockupGenerator  # noqa: E402
from scoring_engine import weight_repository  # noqa: E402
import importlib  # noqa: E402
from typing import Any, cast  # noqa: E402

opt_api = cast(Any, importlib.import_module("backend.optimization.api"))
from backend.optimization.storage import MetricsStore  # noqa: E402


class DummyAdapter:
    """Simplified adapter returning static signals."""

    async def fetch(self) -> list[dict[str, str]]:
        """Return a single dummy signal."""
        return [{"id": "1"}]


@pytest.mark.asyncio()
async def test_pipeline_with_metrics(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Run ingestion, generation, publishing and metrics collection."""
    proc = psutil.Process()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(ing_db, "engine", engine)
    monkeypatch.setattr(ing_db, "SessionLocal", session_factory)
    await ing_db.init_db()

    ingestion.ADAPTERS = [DummyAdapter()]

    async def patched_ingest(session: AsyncSession) -> None:
        for adapter in ingestion.ADAPTERS:
            rows = await adapter.fetch()
            for row in rows:
                key = f"{adapter.__class__.__name__}:{row['id']}"
                if ingestion.is_duplicate(key):
                    continue
                ingestion.add_key(key)
                signal = models.Signal(
                    source=adapter.__class__.__name__,
                    content=str(row),
                    timestamp=datetime.now(timezone.utc),
                )
                session.add(signal)
                await session.commit()
                publisher.publish("signals", key)

    monkeypatch.setattr(ingestion, "ingest", patched_ingest)
    import signal_ingestion.models as models

    monkeypatch.setattr(
        models,
        "datetime",
        SimpleNamespace(utcnow=lambda: datetime.now(timezone.utc)),
    )

    sent: list[str] = []

    def fake_send(topic: str, message: bytes | str) -> object:
        sent.append(message.decode() if isinstance(message, bytes) else message)
        return SimpleNamespace(get=lambda *a, **k: None)

    monkeypatch.setattr(publisher.producer, "send", fake_send)
    monkeypatch.setattr(publisher.producer, "flush", lambda: None)

    def fake_load(self) -> None:  # type: ignore[no-untyped-def]
        self.pipeline = None

    monkeypatch.setattr(MockupGenerator, "load", fake_load)
    monkeypatch.setattr(
        MockupGenerator,
        "_fallback_api",
        staticmethod(lambda p: SimpleNamespace(save=lambda pth: Path(pth).touch())),
    )

    store = set()
    monkeypatch.setattr(ingestion, "is_duplicate", lambda key: key in store)
    monkeypatch.setattr(ingestion, "add_key", lambda key: store.add(key))

    weight_repository.update_weights(
        freshness=1.0,
        engagement=1.0,
        novelty=1.0,
        community_fit=1.0,
        seasonality=1.0,
    )

    thresholds = {
        "ingest": 5.0,
        "generate": 5.0,
        "publish": 1.0,
        "metrics": 2.0,
        "memory_mb": 300.0,
    }

    async with session_factory() as session:
        start = time.perf_counter()
        await ingestion.ingest(session)
        ingest_time = time.perf_counter() - start
    assert ingest_time < thresholds["ingest"]
    assert proc.memory_info().rss / 1024**2 < thresholds["memory_mb"]

    generator = MockupGenerator()
    start = time.perf_counter()
    result = generator.generate("cat", str(tmp_path / "img.png"), num_inference_steps=1)
    gen_time = time.perf_counter() - start
    assert Path(result.image_path).exists()
    assert gen_time < thresholds["generate"]
    assert proc.memory_info().rss / 1024**2 < thresholds["memory_mb"]

    start = time.perf_counter()
    publisher.publish("signals", "done")
    pub_time = time.perf_counter() - start
    assert sent
    assert pub_time < thresholds["publish"]

    monkeypatch.setattr(opt_api, "store", MetricsStore(str(tmp_path / "metrics.db")))
    client = TestClient(opt_api.app)
    metric = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": 10,
        "memory_mb": 100,
    }
    start = time.perf_counter()
    response = client.post("/metrics", json=metric)
    assert response.status_code == 200
    response = client.get("/optimizations")
    assert response.status_code == 200
    metrics_time = time.perf_counter() - start
    assert len(opt_api.store.get_metrics()) == 1
    assert metrics_time < thresholds["metrics"]
    assert proc.memory_info().rss / 1024**2 < thresholds["memory_mb"]
