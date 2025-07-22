"""Stress test concurrent scoring and generation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import sys

import fakeredis.aioredis
from PIL import Image

from fastapi.testclient import TestClient
import pytest
import warnings

# Ensure the scoring engine package can be imported when running this test alone.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "scoring-engine"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend" / "mockup-generation"))
warnings.filterwarnings("ignore", category=DeprecationWarning)
from scoring_engine.app import app as scoring_app
import scoring_engine.app as scoring_module
from scoring_engine.weight_repository import get_weights, update_weights
from mockup_generation.generator import MockupGenerator


def _setup_scoring(redis_client: fakeredis.aioredis.FakeRedis) -> ThreadPoolExecutor:
    scoring_module.redis_client = redis_client
    get_weights()  # ensure weight row exists with defaults
    update_weights(
        freshness=1.0,
        engagement=1.0,
        novelty=1.0,
        community_fit=1.0,
        seasonality=1.0,
    )
    return ThreadPoolExecutor(max_workers=5)


class _DummyPipeline:
    """Lightweight stub for the diffusion pipeline."""

    def __call__(self, prompt: str, num_inference_steps: int = 30):
        """Return a simple result with a dummy image."""

        class _Result:
            def __init__(self) -> None:
                self.images = [Image.new("RGB", (1, 1))]

        return _Result()


def _fake_load(self: MockupGenerator) -> None:  # noqa: D401 - short helper
    """Patch pipeline with a dummy implementation."""

    self.pipeline = _DummyPipeline()


def _worker(client, gen: MockupGenerator, tmp: Path, idx: int) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engagement_rate": 1.0,
        "embedding": [1.0, 0.0],
        "metadata": {},
    }
    client.post("/score", json=payload)
    gen.generate("test", str(tmp / f"{idx}.png"), num_inference_steps=1)


def test_parallel_services(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fake_redis: fakeredis.aioredis.FakeRedis,
) -> None:
    """Run scoring and generation concurrently without errors."""
    executor = _setup_scoring(fake_redis)
    gen = MockupGenerator()
    monkeypatch.setattr(MockupGenerator, "load", _fake_load)

    client = TestClient(scoring_app)
    with executor:
        list(executor.map(lambda i: _worker(client, gen, tmp_path, i), range(10)))
