from __future__ import annotations

import sys
from pathlib import Path
from random import Random

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from mockup_generation.prompt_builder import PromptContext, build_prompt  # noqa: E402


def test_build_prompt_deterministic() -> None:
    ctx = PromptContext(keywords=["red", "cat", "hat"], extra={"note": "test"})
    rng = Random(0)
    prompt1 = build_prompt(ctx, rng=rng)
    rng.seed(0)
    prompt2 = build_prompt(ctx, rng=rng)
    assert prompt1 == prompt2
    assert "vector art" in prompt1
    assert "test" in prompt1
