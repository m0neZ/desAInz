"""Stress test concurrent scoring and generation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import fakeredis
from PIL import Image

from scoring_engine.app import app as scoring_app, redis_client
from scoring_engine.weight_repository import update_weights
from mockup_generation.generator import MockupGenerator


def _setup_scoring() -> ThreadPoolExecutor:
    scoring_app.config.update(TESTING=True)
    redis_client.connection_pool.connection_class = fakeredis.FakeConnection
    update_weights(
        freshness=1.0,
        engagement=1.0,
        novelty=1.0,
        community_fit=1.0,
        seasonality=1.0,
    )
    return ThreadPoolExecutor(max_workers=5)


def _fake_load(self: MockupGenerator) -> None:  # noqa: D401 - short helper
    """Patch pipeline with a dummy implementation."""
    self.pipeline = type(
        "P",
        (),
        {
            "__call__": lambda _self, prompt, num_inference_steps=30: type(
                "R", (), {"images": [Image.new("RGB", (1, 1))]}
            )()
        },
    )()


def _worker(client, gen: MockupGenerator, tmp: Path, idx: int) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engagement_rate": 1.0,
        "embedding": [1.0, 0.0],
        "metadata": {},
    }
    client.post("/score", json=payload)
    gen.generate("test", str(tmp / f"{idx}.png"), num_inference_steps=1)


def test_parallel_services(monkeypatch, tmp_path) -> None:
    """Run scoring and generation concurrently without errors."""
    executor = _setup_scoring()
    gen = MockupGenerator()
    monkeypatch.setattr(MockupGenerator, "load", _fake_load)

    client = scoring_app.test_client()
    with executor:
        list(executor.map(lambda i: _worker(client, gen, tmp_path, i), range(10)))
