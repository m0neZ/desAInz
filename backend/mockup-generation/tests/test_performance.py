"""Performance tests for mockup generation."""

from __future__ import annotations

import time

from mockup_generation.generator import MockupGenerator


def test_generation_speed(tmp_path) -> None:
    """Ensure generation completes within a reasonable timeframe."""
    generator = MockupGenerator()
    start = time.perf_counter()
    generator.generate("test", str(tmp_path / "img.png"), num_inference_steps=1)
    duration = time.perf_counter() - start
    assert duration < 30
