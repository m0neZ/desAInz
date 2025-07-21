from __future__ import annotations

import importlib
import sys
from pathlib import Path
import types

import fakeredis
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))  # noqa: E402

# Patch heavy deps before importing the module under test
sys.modules.setdefault("diffusers", types.ModuleType("diffusers"))
sys.modules["diffusers"].StableDiffusionXLPipeline = object  # type: ignore[attr-defined]
sys.modules.setdefault("torch", types.ModuleType("torch"))
sys.modules["torch"].cuda = types.SimpleNamespace(is_available=lambda: False)  # type: ignore[attr-defined]

import redis  # noqa: E402


@pytest.mark.usefixtures("monkeypatch")  # type: ignore[misc]
def test_gpu_queue_metric(monkeypatch: pytest.MonkeyPatch) -> None:
    """Metric reflects pending tasks in Redis."""
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(redis.Redis, "from_url", lambda *a, **k: fake)

    stub_tasks = types.ModuleType("mockup_generation.tasks")
    stub_tasks.get_gpu_slots = lambda: 1  # type: ignore[attr-defined]
    stub_tasks.queue_for_gpu = lambda idx: f"gpu-{idx}"  # type: ignore[attr-defined]
    sys.modules["mockup_generation.tasks"] = stub_tasks

    from mockup_generation import celery_app  # noqa: E402

    importlib.reload(celery_app)
    fake.rpush(stub_tasks.queue_for_gpu(0), b"job")
    collector = celery_app.GPUQueueCollector()
    metric = next(iter(collector.collect()))
    assert metric.samples[0].value == 1
