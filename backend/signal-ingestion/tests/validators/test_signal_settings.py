"""Validation for signal_ingestion settings."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

import pytest  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from signal_ingestion.settings import Settings  # noqa: E402


def test_invalid_instagram_token() -> None:
    """Validation fails for empty Instagram token."""
    with pytest.raises(ValidationError):
        Settings(instagram_token=" ")


def test_invalid_tiktok_url() -> None:
    """Validation fails for malformed TikTok URL list."""
    with pytest.raises(ValidationError):
        Settings(tiktok_video_urls="not_a_url")
