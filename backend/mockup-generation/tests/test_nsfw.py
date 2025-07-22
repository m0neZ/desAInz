"""Test CLIP-based NSFW filtering."""

from __future__ import annotations

from PIL import Image

from mockup_generation.post_processor import ensure_not_nsfw


def test_ensure_not_nsfw() -> None:
    """Smoke test for NSFW detection function."""
    img = Image.new("RGB", (32, 32), color="white")
    ensure_not_nsfw(img)
