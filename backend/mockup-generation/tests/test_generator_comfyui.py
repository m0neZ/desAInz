"""Tests for MockupGenerator with ComfyUI integration."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Iterator

import pytest
import asyncio

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))  # noqa: E402

from mockup_generation.generator import MockupGenerator  # noqa: E402
from mockup_generation.settings import settings  # noqa: E402


class DummyPipeline:
    """Return a single white pixel image for any call."""

    def __call__(self, prompt: str, num_inference_steps: int = 30) -> SimpleNamespace:
        from PIL import Image

        return SimpleNamespace(images=[Image.new("RGB", (1, 1))])


@pytest.fixture(autouse=True)  # type: ignore[misc]
def reset_comfyui() -> Iterator[None]:
    """Restore :data:`settings.use_comfyui` after each test."""

    prev = settings.use_comfyui
    yield
    settings.use_comfyui = prev


def test_generate_with_diffusers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Generation uses the diffusion pipeline when ComfyUI is disabled."""
    settings.use_comfyui = False
    monkeypatch.setattr(
        MockupGenerator, "load", lambda self, model_identifier=None: None
    )
    gen = MockupGenerator()
    gen.pipeline = DummyPipeline()
    result = asyncio.run(
        gen.generate("test", str(tmp_path / "img.png"), num_inference_steps=1)
    )
    assert Path(result.image_path).exists()


def test_generate_with_comfyui(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Generation delegates to ComfyUI when enabled."""
    settings.use_comfyui = True
    called: list[dict[str, str]] = []

    def fake_execute(
        self: object, workflow: dict[str, str], output: str
    ) -> SimpleNamespace:
        Path(output).write_text("x")
        called.append(workflow)
        return SimpleNamespace(image_path=output, duration=0.1)

    monkeypatch.setattr(
        "mockup_generation.comfy_workflow.ComfyUIWorkflow.execute",
        fake_execute,
    )
    monkeypatch.setattr(MockupGenerator, "load", lambda *a, **k: None)
    gen = MockupGenerator()
    result = asyncio.run(gen.generate("prompt", str(tmp_path / "img.png")))
    assert called
    assert Path(result.image_path).exists()
