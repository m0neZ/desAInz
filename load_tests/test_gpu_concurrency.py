"""Test GPU slot contention with multiple Celery workers."""

from __future__ import annotations

import sys
import time
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import AsyncIterator, Iterator

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend" / "mockup-generation"))

import importlib
import types

import fakeredis
import pytest
from celery import Celery
from celery.contrib.testing.worker import start_worker

APP = Celery("test", broker="memory://", backend="cache+memory://")
celery_stub = types.ModuleType("mockup_generation.celery_app")
celery_stub.app = APP  # type: ignore[attr-defined]
sys.modules.setdefault("mockup_generation.celery_app", celery_stub)

diffusers_mod = types.ModuleType("diffusers")
diffusers_mod.StableDiffusionXLPipeline = object  # type: ignore[attr-defined]
sys.modules.setdefault("diffusers", diffusers_mod)
torch_mod = types.ModuleType("torch")
setattr(torch_mod, "nn", types.ModuleType("nn"))
setattr(torch_mod.nn, "Module", object)
setattr(torch_mod, "cuda", types.ModuleType("cuda"))
setattr(torch_mod.cuda, "is_available", lambda: False)
sys.modules.setdefault("torch", torch_mod)
sys.modules.setdefault("torch.nn", torch_mod.nn)
db_mod = types.ModuleType("backend.shared.db")
db_mod.engine = object()  # type: ignore[attr-defined]


@contextmanager
def _scope() -> Iterator[object]:
    yield object()


db_mod.session_scope = _scope  # type: ignore[attr-defined]
sys.modules.setdefault("backend.shared.db", db_mod)
base_mod = types.ModuleType("backend.shared.db.base")
setattr(
    base_mod,
    "Base",
    type(
        "Base",
        (),
        {"metadata": type("MD", (), {"create_all": lambda *a, **k: None})()},
    ),
)
sys.modules.setdefault("backend.shared.db.base", base_mod)
models_mod = types.ModuleType("backend.shared.db.models")


class _AIModel:
    model_id = "id"
    is_default = True


class _GeneratedMockup:
    id = 1
    prompt = ""
    num_inference_steps = 1
    seed = 0


setattr(models_mod, "AIModel", _AIModel)
setattr(models_mod, "GeneratedMockup", _GeneratedMockup)
sys.modules.setdefault("backend.shared.db.models", models_mod)
pgv_mod = types.ModuleType("pgvector.sqlalchemy")
setattr(pgv_mod, "Vector", object)
sys.modules.setdefault("pgvector.sqlalchemy", pgv_mod)
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
yaml_mod = types.ModuleType("yaml")
setattr(yaml_mod, "safe_load", lambda *_args, **_kwargs: {})
sys.modules.setdefault("yaml", yaml_mod)
sys.modules.setdefault("open_clip", types.ModuleType("open_clip"))
cache_mod = types.ModuleType("backend.shared.cache")
cache_mod.SyncRedis = fakeredis.FakeRedis  # type: ignore[attr-defined]
cache_mod.get_sync_client = lambda: fakeredis.FakeRedis()  # type: ignore[attr-defined]
sys.modules.setdefault("backend.shared.cache", cache_mod)
model_repo_mod = types.ModuleType("mockup_generation.model_repository")
model_repo_mod.get_default_model_id = lambda: "model"  # type: ignore[attr-defined]
model_repo_mod.save_generated_mockup = lambda *a, **k: 1  # type: ignore[attr-defined]
sys.modules.setdefault("mockup_generation.model_repository", model_repo_mod)

tasks = importlib.import_module("mockup_generation.tasks")


class DummyGenerator:
    """Quickly create a dummy file and return its path."""

    def generate(
        self, prompt: str, output: str, model_identifier: str | None = None
    ) -> object:
        Path(output).write_text("x")
        time.sleep(0.1)
        return type("R", (), {"image_path": output})()

    def cleanup(self) -> None:
        return None


class DummyListingGen:
    """Return constant listing metadata."""

    def generate(self, keywords: list[str]) -> object:
        return type("Listing", (), {"title": "t", "description": "d", "tags": ["a"]})()


class DummyClient:
    """Collect upload calls without performing network IO."""

    def upload_file(self, src: str, bucket: str, obj: str) -> None:
        return None


@pytest.fixture()
def celery_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[Celery]:
    """Yield a Celery app patched into the tasks module."""

    monkeypatch.setattr(tasks, "app", APP)
    yield APP


@pytest.fixture()
def patched_tasks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub out heavy components in :mod:`tasks`."""

    fake = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr(tasks, "redis_client", fake)
    monkeypatch.setattr(tasks, "async_redis_client", fake)
    monkeypatch.setattr(tasks, "get_gpu_slots", lambda: 1)
    monkeypatch.setattr(tasks, "generator", DummyGenerator())
    monkeypatch.setattr(tasks, "ListingGenerator", lambda: DummyListingGen())

    @asynccontextmanager
    async def _client() -> AsyncIterator[DummyClient]:
        yield DummyClient()

    monkeypatch.setattr(tasks, "_get_storage_client", _client)
    monkeypatch.setattr(tasks, "remove_background", lambda img: img)
    monkeypatch.setattr(tasks, "convert_to_cmyk", lambda img: img)
    monkeypatch.setattr(tasks, "ensure_not_nsfw", lambda img: None)
    monkeypatch.setattr(tasks, "validate_dpi_image", lambda img: True)
    monkeypatch.setattr(tasks, "validate_color_space", lambda img: True)
    monkeypatch.setattr(tasks, "validate_dimensions", lambda img: True)
    monkeypatch.setattr(tasks, "compress_lossless", lambda img, path: None)
    monkeypatch.setattr(tasks, "validate_file_size", lambda path: True)
    monkeypatch.setattr(
        tasks.model_repository, "save_generated_mockup", lambda *a, **k: 1
    )
    tasks.settings.s3_bucket = "b"
    tasks.settings.s3_endpoint = "http://test"


def test_slot_contention(
    celery_app: Celery, patched_tasks: None, tmp_path: Path
) -> None:
    """Run two tasks concurrently and observe lock metrics."""

    queues = ["q1", "q2"]
    workers = [
        start_worker(celery_app, perform_ping_check=False, pool="solo", queues=[q])
        for q in queues
    ]
    for w in workers:
        w.__enter__()
    try:
        res1 = celery_app.send_task(
            "mockup_generation.tasks.generate_mockup",
            args=[["a"], str(tmp_path)],
            queue="q1",
        )
        res2 = celery_app.send_task(
            "mockup_generation.tasks.generate_mockup",
            args=[["b"], str(tmp_path)],
            queue="q2",
        )
        start = time.perf_counter()
        res1.get(timeout=5)
        res2.get(timeout=5)
        duration = time.perf_counter() - start
    finally:
        for w in reversed(workers):
            w.__exit__(None, None, None)

    assert duration >= 0.2
    assert tasks.GPU_SLOT_ACQUIRE_TOTAL._value.get() == 2
    assert tasks.GPU_SLOTS_IN_USE._value.get() == 0
