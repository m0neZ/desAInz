"""Validation for marketplace_publisher settings."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

import pytest  # noqa: E402
from marketplace_publisher.settings import Settings  # noqa: E402
from pydantic import ValidationError  # noqa: E402


def test_blank_unleash_token() -> None:
    """Validation fails when Unleash token is blank."""
    with pytest.raises(ValidationError):
        Settings(unleash_api_token=" ")
