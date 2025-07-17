"""Integration tests for the end-to-end workflow."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
import vcr
from PIL import Image
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Stub external dependencies before importing service modules
import kafka

kafka.KafkaProducer = MagicMock(
    return_value=SimpleNamespace(send=lambda *a, **k: None, flush=lambda: None)
)
sys.modules.setdefault(
    "diffusers",
    SimpleNamespace(StableDiffusionXLPipeline=object),
)
sys.modules.setdefault(
    "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
)

# Extend import path for service packages
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "backend" / "signal-ingestion" / "src"))  # noqa: E402
sys.path.append(str(ROOT / "backend" / "scoring-engine"))
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend" / "mockup-generation"))  # noqa: E402

from signal_ingestion import ingestion, publisher  # type: ignore  # noqa: E402
from signal_ingestion import database as ing_db  # type: ignore  # noqa: E402
from mockup_generation.generator import MockupGenerator  # type: ignore  # noqa: E402
from scoring_engine import scoring, weight_repository  # noqa: E402


@vcr.use_cassette(
    "tests/integration/cassettes/workflow.yaml", record_mode="new_episodes"
)
@pytest.mark.asyncio()
async def test_end_to_end(monkeypatch, tmp_path) -> None:
    """Run ingestion, scoring, generation and publishing together."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(ing_db, "engine", engine)
    monkeypatch.setattr(ing_db, "SessionLocal", session_factory)
    await ing_db.init_db()

    ingestion.ADAPTERS = [ingestion.TikTokAdapter()]

    sent: list[tuple[str, bytes]] = []

    def fake_send(topic: str, message: bytes) -> object:  # pragma: no cover
        sent.append((topic, message))
        return SimpleNamespace(get=lambda *a, **k: None)

    monkeypatch.setattr(publisher.producer, "send", fake_send)
    monkeypatch.setattr(publisher.producer, "flush", lambda: None)

    def fake_load(self) -> None:  # pragma: no cover
        self.pipeline = None

    def fallback(prompt: str) -> Image.Image:  # pragma: no cover
        return Image.new("RGB", (1, 1), color="white")

    monkeypatch.setattr(MockupGenerator, "load", fake_load)
    monkeypatch.setattr(MockupGenerator, "_fallback_api", staticmethod(fallback))
    import signal_ingestion.dedup as dedup

    store = set()
    monkeypatch.setattr(dedup, "is_duplicate", lambda key: key in store)
    monkeypatch.setattr(dedup, "add_key", lambda key: store.add(key))
    monkeypatch.setattr(ingestion, "is_duplicate", lambda key: key in store)
    monkeypatch.setattr(ingestion, "add_key", lambda key: store.add(key))

    weight_repository.update_weights(
        freshness=1.0,
        engagement=1.0,
        novelty=1.0,
        community_fit=1.0,
        seasonality=1.0,
    )
    sig = scoring.Signal(
        timestamp=datetime.now(timezone.utc),
        engagement_rate=1.0,
        embedding=[0.1, 0.2],
        metadata={},
    )
    score = scoring.calculate_score(sig, np.array([0.0, 0.0]), 0.5, [])
    assert isinstance(score, float)

    gen = MockupGenerator()
    result = gen.generate("cat", str(tmp_path / "img.png"), num_inference_steps=1)
    assert Path(result.image_path).exists()

    publisher.publish("signals", "done")
    assert sent
