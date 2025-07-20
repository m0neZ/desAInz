"""Tests for post-processing validation helpers."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))  # noqa: E402
sys.path.append(str(ROOT / "backend" / "mockup-generation"))  # noqa: E402

from PIL import Image

from mockup_generation.post_processor import validate_dimensions, validate_file_size


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
