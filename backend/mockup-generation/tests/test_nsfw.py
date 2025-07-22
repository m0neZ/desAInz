"""Test CLIP-based NSFW filtering."""

from __future__ import annotations

from mockup_generation.post_processor import ensure_not_nsfw
from PIL import Image


def test_ensure_not_nsfw() -> None:
    """Smoke test for NSFW detection function."""
    img = Image.new("RGB", (32, 32), color="white")
    ensure_not_nsfw(img)
