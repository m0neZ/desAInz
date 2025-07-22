"""Integration test ensuring each migration folder has a single head."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests.utils import assert_single_head

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))


@pytest.mark.parametrize(
    "config_path",
    [
        "backend/shared/db/alembic_scoring_engine.ini",
        "backend/shared/db/alembic_api_gateway.ini",
        "backend/shared/db/alembic_marketplace_publisher.ini",
        "backend/shared/db/alembic_signal_ingestion.ini",
    ],
)
def test_alembic_heads_single(config_path: str) -> None:
    """Run ``alembic heads`` and assert a single head exists."""
    assert_single_head(config_path)
