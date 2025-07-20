"""Tests for :mod:`mockup_generation.generator` failure modes."""

from __future__ import annotations

import sys
from pathlib import Path
import types
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))  # noqa: E402

# Stub heavy dependencies used by generator
sys.modules.setdefault("diffusers", types.ModuleType("diffusers"))
sys.modules["diffusers"].StableDiffusionXLPipeline = object
sys.modules.setdefault("torch", types.ModuleType("torch"))
sys.modules["torch"].cuda = types.SimpleNamespace(is_available=lambda: False)
sys.modules.setdefault("torch.nn", types.ModuleType("nn"))

from mockup_generation.generator import MockupGenerator, GenerationError  # noqa: E402


class DummySession:
    """HTTP client that always raises ``RequestException``."""

    def post(self, *a, **k):
        from requests.exceptions import RequestException

        raise RequestException("boom")

    def get(self, *a, **k):
        from requests.exceptions import RequestException

        raise RequestException("boom")


def test_fallback_api_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fallback API should raise :class:`GenerationError` after retries."""
    monkeypatch.setattr("requests.Session", lambda: DummySession())
    monkeypatch.setattr("time.sleep", lambda *_: None)
    gen = MockupGenerator()
    with pytest.raises(GenerationError):
        gen._fallback_api("prompt")
