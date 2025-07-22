"""Tests for GPU metrics collection."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

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


def test_gpu_utilization_metric(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gauge is updated using ``torch.cuda.utilization_rate``."""
    util_called: list[float] = []

    torch_mod = types.ModuleType("torch")
    torch_mod.cuda = types.SimpleNamespace(
        is_available=lambda: True,
        utilization_rate=lambda: 42.0,
    )
    sys.modules["torch"] = torch_mod

    gauge = types.SimpleNamespace(set=lambda v: util_called.append(v))

    mock_celery_app = types.ModuleType("mockup_generation.celery_app")

    def _task_decorator(*_a: object, **_kw: object) -> callable:
        def wrapper(func: callable) -> types.SimpleNamespace:
            return types.SimpleNamespace(run=func)

        return wrapper

    mock_celery_app.app = types.SimpleNamespace(task=_task_decorator)
    mock_celery_app.queue_for_gpu = lambda *a, **k: None
    sys.modules["mockup_generation.celery_app"] = mock_celery_app

    client_mod = types.ModuleType("aiobotocore.client")
    client_mod.AioBaseClient = object
    monkeypatch.setitem(sys.modules, "aiobotocore.client", client_mod)
    session_mod = types.ModuleType("aiobotocore.session")
    session_mod.get_session = lambda: None
    monkeypatch.setitem(sys.modules, "aiobotocore.session", session_mod)

    import mockup_generation.tasks as tasks  # noqa: E402

    monkeypatch.setattr(tasks, "GPU_UTILIZATION", gauge)

    tasks._update_gpu_utilization()

    assert util_called == [42.0]
