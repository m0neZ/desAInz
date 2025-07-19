"""Tests for GPU slot locking."""

from __future__ import annotations

import sys
from pathlib import Path
import contextlib

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

import types  # noqa: E402

diffusers_mod = types.ModuleType("diffusers")
diffusers_mod.StableDiffusionXLPipeline = object  # type: ignore[attr-defined]
sys.modules.setdefault("diffusers", diffusers_mod)
torch_mod = types.ModuleType("torch")
torch_mod.nn = types.ModuleType("nn")
torch_mod.nn.Module = object
torch_mod.cuda = types.ModuleType("cuda")
torch_mod.cuda.is_available = lambda: False
sys.modules.setdefault("torch", torch_mod)
sys.modules.setdefault("torch.nn", torch_mod.nn)
fastapi_mod = types.ModuleType("fastapi")
fastapi_mod.FastAPI = object
fastapi_mod.Request = object
fastapi_mod.Response = object
fastapi_mod.HTTPException = Exception
responses_mod = types.ModuleType("fastapi.responses")
responses_mod.JSONResponse = object
sys.modules.setdefault("fastapi.responses", responses_mod)
fastapi_mod.responses = responses_mod
sys.modules.setdefault("fastapi", fastapi_mod)
model_repo_mod = types.ModuleType("mockup_generation.model_repository")
model_repo_mod.get_default_model_id = lambda: "model"
sys.modules.setdefault("mockup_generation.model_repository", model_repo_mod)
for name in [
    "opentelemetry",
    "opentelemetry.instrumentation.fastapi",
    "opentelemetry.instrumentation.flask",
    "opentelemetry.sdk.resources",
    "opentelemetry.sdk.trace",
    "opentelemetry.sdk.trace.export",
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    "sentry_sdk",
    "sentry_sdk.integrations.asgi",
    "backend.shared.db",
    "backend.shared.tracing",
    "backend.shared.logging",
    "backend.shared.sentry",
    "backend.shared.feature_flags",
    "backend.shared.errors",
]:
    sys.modules.setdefault(name, types.ModuleType(name))
db_mod = sys.modules.setdefault(
    "backend.shared.db", types.ModuleType("backend.shared.db")
)
db_mod.engine = object()


class _DummySession:
    def scalar(self, *args, **kwargs):
        return None


@contextlib.contextmanager
def _scope():
    yield _DummySession()


db_mod.session_scope = _scope
sys.modules.setdefault(
    "backend.shared.db.base", types.ModuleType("backend.shared.db.base")
)
sys.modules.setdefault(
    "backend.shared.db.models", types.ModuleType("backend.shared.db.models")
)
base_mod = sys.modules.setdefault(
    "backend.shared.db.base", types.ModuleType("backend.shared.db.base")
)


class _Base:
    metadata = type("metadata", (), {"create_all": lambda *args, **kwargs: None})


base_mod.Base = _Base
models_mod = sys.modules["backend.shared.db.models"]


class _AIModel:
    model_id = "id"
    is_default = True


class _GeneratedMockup:
    id = 1
    prompt = ""
    num_inference_steps = 1
    seed = 0


models_mod.AIModel = _AIModel
models_mod.GeneratedMockup = _GeneratedMockup
open_clip_mod = types.ModuleType("open_clip")
open_clip_mod.tokenize = lambda *args, **kwargs: type(
    "T", (), {"to": lambda self, *a, **k: self}
)()
sys.modules.setdefault("open_clip", open_clip_mod)
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
flask_mod = types.ModuleType("flask")
flask_mod.Flask = object
flask_mod.request = object()
flask_mod.jsonify = lambda *args, **kwargs: ""
sys.modules.setdefault("flask", flask_mod)
sys.modules.setdefault("fastapi", types.ModuleType("fastapi"))
sys.modules.setdefault(
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    types.ModuleType("opentelemetry.exporter.otlp.proto.http.trace_exporter"),
)

import threading  # noqa: E402
import fakeredis  # noqa: E402
import pytest  # noqa: E402

from mockup_generation import tasks  # noqa: E402


def test_gpu_slot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lock is acquired and released using the context manager."""
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(tasks, "redis_client", fake)
    monkeypatch.setattr(tasks, "get_gpu_slots", lambda: 1)

    with tasks.gpu_slot():
        assert fake.lock("gpu_slot:0").locked()
    assert not fake.lock("gpu_slot:0").locked()


def test_gpu_slot_contention(monkeypatch: pytest.MonkeyPatch) -> None:
    """Multiple workers should acquire the lock sequentially."""
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(tasks, "redis_client", fake)
    monkeypatch.setattr(tasks, "get_gpu_slots", lambda: 1)

    order: list[str] = []

    def worker(label: str) -> None:
        with tasks.gpu_slot():
            order.append(label)

    t1 = threading.Thread(target=worker, args=("a",))
    t2 = threading.Thread(target=worker, args=("b",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert order == ["a", "b"] or order == ["b", "a"]
