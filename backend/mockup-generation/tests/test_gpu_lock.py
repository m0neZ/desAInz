"""Tests for GPU slot locking."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # noqa: E402

import types  # noqa: E402

diffusers_mod = types.ModuleType("diffusers")
diffusers_mod.StableDiffusionXLPipeline = object  # type: ignore[attr-defined]
sys.modules.setdefault("diffusers", diffusers_mod)
sys.modules.setdefault("torch", types.ModuleType("torch"))

import fakeredis  # noqa: E402
import pytest  # noqa: E402

from mockup_generation import tasks  # noqa: E402


def test_gpu_slot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lock is acquired and released using the context manager."""
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(tasks, "redis_client", fake)
    monkeypatch.setattr(tasks, "GPU_SLOTS", 1)

    with tasks.gpu_slot():
        assert fake.lock("gpu_slot:0").locked()
    assert not fake.lock("gpu_slot:0").locked()
