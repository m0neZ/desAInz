"""Tests for post-processing validation helpers."""

from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))  # noqa: E402
sys.path.append(str(ROOT / "backend" / "mockup-generation"))  # noqa: E402

from PIL import Image

from mockup_generation.post_processor import (
    post_process_image,
    validate_dimensions,
    validate_file_size,
)


def test_validate_dimensions(tmp_path: Path) -> None:
    """Image dimensions are validated against provided limits."""
    img = Image.new("RGB", (100, 100))
    assert validate_dimensions(img, max_width=150, max_height=150)
    assert not validate_dimensions(img, max_width=50, max_height=150)


def test_validate_file_size(tmp_path: Path) -> None:
    """File size validation respects the configured threshold."""
    path = tmp_path / "f"
    path.write_bytes(b"x" * 1024)
    assert validate_file_size(path, max_file_size_mb=1)
    assert not validate_file_size(path, max_file_size_mb=0)


def test_post_process_image(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Post-processing pipeline returns saved image."""
    img = Image.new("RGB", (10, 10))
    path = tmp_path / "img.png"
    img.save(path)
    monkeypatch.setattr(
        "mockup_generation.post_processor.remove_background", lambda i: i
    )
    monkeypatch.setattr("mockup_generation.post_processor.convert_to_cmyk", lambda i: i)
    monkeypatch.setattr(
        "mockup_generation.post_processor.ensure_not_nsfw", lambda i: None
    )
    monkeypatch.setattr(
        "mockup_generation.post_processor.validate_color_space", lambda i: True
    )
    assert post_process_image(path).exists()
