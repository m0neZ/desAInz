"""Benchmark import time for generator and post_processor modules."""

from __future__ import annotations

import importlib
import sys
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))  # noqa: E402

# Stub heavy dependencies
mods = {
    "cv2": types.ModuleType("cv2"),
    "numpy": types.ModuleType("numpy"),
    "yaml": types.ModuleType("yaml"),
    "PIL": types.ModuleType("PIL"),
    "PIL.Image": types.ModuleType("PIL.Image"),
    "requests": types.ModuleType("requests"),
    "diffusers": types.ModuleType("diffusers"),
    "torch": types.ModuleType("torch"),
    "mockup_generation.model_repository": types.ModuleType(
        "mockup_generation.model_repository"
    ),
}
mods["diffusers"].StableDiffusionXLPipeline = object  # type: ignore[attr-defined]
mods["torch"].cuda = types.SimpleNamespace(  # type: ignore[attr-defined]
    is_available=lambda: False
)
mods["mockup_generation.model_repository"].get_default_model_id = (  # type: ignore[attr-defined]
    lambda: "id"
)
mods["yaml"].safe_load = lambda *_args, **_kwargs: {}  # type: ignore[attr-defined]
for name, module in mods.items():
    sys.modules.setdefault(name, module)


def test_import_time_below_threshold() -> None:
    """Import generator and post_processor within the time limit."""
    start = time.perf_counter()
    importlib.import_module("mockup_generation.generator")
    importlib.import_module("mockup_generation.post_processor")
    duration = time.perf_counter() - start
    assert duration < 0.1
