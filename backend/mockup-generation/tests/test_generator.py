"""Tests for :mod:`mockup_generation.generator` failure modes."""

from __future__ import annotations

import sys
from pathlib import Path
import types
from typing import Iterator

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))  # noqa: E402

# Stub heavy dependencies used by generator
sys.modules.setdefault("diffusers", types.ModuleType("diffusers"))
sys.modules["diffusers"].StableDiffusionXLPipeline = object  # type: ignore[attr-defined]
sys.modules.setdefault("torch", types.ModuleType("torch"))
sys.modules["torch"].cuda = types.SimpleNamespace(is_available=lambda: False)  # type: ignore[attr-defined]
sys.modules.setdefault("torch.nn", types.ModuleType("nn"))

from mockup_generation.generator import MockupGenerator, GenerationError  # noqa: E402
from mockup_generation.settings import settings  # noqa: E402


class DummySession:
    """HTTP client that always raises ``RequestException``."""

    def post(self, *a: object, **k: object) -> None:
        from requests.exceptions import RequestException

        raise RequestException("boom")

    def get(self, *a: object, **k: object) -> None:
        from requests.exceptions import RequestException

        raise RequestException("boom")


@pytest.fixture(autouse=True)  # type: ignore[misc]
def restore_provider() -> Iterator[None]:
    """Restore provider settings after each test."""
    prev_provider = settings.fallback_provider
    yield
    settings.fallback_provider = prev_provider


def test_fallback_api_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fallback API should raise :class:`GenerationError` after retries."""
    monkeypatch.setattr("requests.Session", lambda: DummySession())
    monkeypatch.setattr("time.sleep", lambda *_: None)
    gen = MockupGenerator()
    with pytest.raises(GenerationError):
        gen._fallback_api("prompt")


def test_fallback_api_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    """Image is returned when OpenAI responds successfully."""
    from io import BytesIO
    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (1, 1)).save(buf, format="PNG")
    data = buf.getvalue()

    class Session:
        def post(self, url: str, **_: object) -> object:
            assert url == "https://api.openai.com/v1/images/generations"
            return types.SimpleNamespace(
                json=lambda: {"data": [{"url": "http://x"}]},
                raise_for_status=lambda: None,
            )

        def get(self, url: str, **_: object) -> object:
            assert url == "http://x"
            return types.SimpleNamespace(content=data, raise_for_status=lambda: None)

    settings.fallback_provider = "openai"
    settings.openai_api_key = "x"
    monkeypatch.setattr("requests.Session", lambda: Session())
    monkeypatch.setattr("time.sleep", lambda *_: None)
    gen = MockupGenerator()
    img = gen._fallback_api("prompt")
    assert img.size == (1, 1)


def test_fallback_api_stability(monkeypatch: pytest.MonkeyPatch) -> None:
    """Image is returned when Stability responds successfully."""
    import base64
    from io import BytesIO
    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (1, 1)).save(buf, format="PNG")
    data = buf.getvalue()

    class Session:
        def post(self, url: str, **_: object) -> object:
            assert url.startswith("https://api.stability.ai/v1/generation/")
            return types.SimpleNamespace(
                json=lambda: {
                    "artifacts": [{"base64": base64.b64encode(data).decode()}]
                },
                raise_for_status=lambda: None,
            )

        def get(self, *a: object, **k: object) -> None:
            raise AssertionError("should not fetch external URL")

    settings.fallback_provider = "stability"
    settings.stability_ai_api_key = "x"
    monkeypatch.setattr("requests.Session", lambda: Session())
    monkeypatch.setattr("time.sleep", lambda *_: None)
    gen = MockupGenerator()
    img = gen._fallback_api("prompt")
    assert img.size == (1, 1)
