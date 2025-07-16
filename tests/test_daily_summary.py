# flake8: noqa
"""Tests for daily summary script."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(
    str(
        Path(__file__).resolve().parents[1]
        / "backend"
        / "marketplace-publisher"
        / "src"
    )
)

import pytest
from scripts.daily_summary import generate_daily_summary


@pytest.mark.asyncio
async def test_generate_daily_summary() -> None:
    """Summary returns all expected keys."""
    from unittest.mock import AsyncMock, patch

    with patch(
        "scripts.daily_summary._marketplace_stats", new=AsyncMock(return_value={})
    ):
        result = await generate_daily_summary()
    assert "ideas_generated" in result
    assert "mockup_success_rate" in result
    assert "marketplace_stats" in result
