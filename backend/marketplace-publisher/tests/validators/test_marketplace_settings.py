"""Validation for marketplace_publisher settings."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

import pytest  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from marketplace_publisher.settings import Settings  # noqa: E402


def test_blank_unleash_token() -> None:
    with pytest.raises(ValidationError):
        Settings(unleash_api_token=" ")
