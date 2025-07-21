"""Validation for monitoring settings."""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

import pytest  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from monitoring.settings import Settings  # noqa: E402


def test_invalid_log_file() -> None:
    with pytest.raises(ValidationError):
        Settings(log_file="invalid.txt")
