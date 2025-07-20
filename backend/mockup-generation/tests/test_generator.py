"""Tests for :mod:`mockup_generation.generator`."""

from __future__ import annotations

import sys
from pathlib import Path
import types
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))  # noqa: E402

diffusers_mod = types.ModuleType("diffusers")
diffusers_mod.StableDiffusionXLPipeline = object  # type: ignore[attr-defined]
sys.modules.setdefault("diffusers", diffusers_mod)
torch_mod = types.ModuleType("torch")
torch_mod.cuda = types.ModuleType("cuda")
torch_mod.cuda.is_available = lambda: False
sys.modules.setdefault("torch", torch_mod)
sys.modules.setdefault("pgvector.sqlalchemy", types.ModuleType("pgvector.sqlalchemy"))
sys.modules["pgvector.sqlalchemy"].Vector = lambda *a, **k: object()
model_repo_mod = types.ModuleType("mockup_generation.model_repository")
model_repo_mod.get_default_model_id = lambda: "model"
sys.modules.setdefault("mockup_generation.model_repository", model_repo_mod)

from mockup_generation import generator as gen_mod  # noqa: E402


class DummySession:
    """Session raising ``RequestException`` for all requests."""

    def post(self, *args: object, **kwargs: object) -> None:
        raise gen_mod.requests.RequestException("boom")

    def get(self, *args: object, **kwargs: object) -> None:  # pragma: no cover
        raise gen_mod.requests.RequestException("boom")


def test_fallback_api_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """`GenerationError` is raised when the provider fails."""
    monkeypatch.setattr(gen_mod.settings, "fallback_provider", "stability")
    monkeypatch.setattr(gen_mod.requests, "Session", lambda: DummySession())
    import time

    monkeypatch.setattr(time, "sleep", lambda *_: None)
    gen = gen_mod.MockupGenerator()
    with pytest.raises(gen_mod.GenerationError):
        gen._fallback_api("test")


class DummyPipeline:
    """Pipeline that always fails."""

    def __call__(self, *args: object, **kwargs: object) -> types.SimpleNamespace:
        raise RuntimeError("fail")


def test_generate_propagates_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """`GenerationError` from fallback should propagate."""
    gen = gen_mod.MockupGenerator()
    monkeypatch.setattr(gen, "load", lambda *a, **k: None)
    gen.pipeline = DummyPipeline()
    monkeypatch.setattr(
        gen_mod.MockupGenerator,
        "_fallback_api",
        lambda self, p: (_ for _ in ()).throw(gen_mod.GenerationError("x")),
    )
    with pytest.raises(gen_mod.GenerationError):
        gen.generate("p", str(Path("/tmp/img.png")), num_inference_steps=1)
