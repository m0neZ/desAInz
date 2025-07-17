"""Tests for price adjustments."""

import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"  # noqa: E402

from marketplace_publisher.pricing import (  # noqa: E402
    adjust_price,
    create_listing_metadata,
)
from marketplace_publisher.db import Marketplace  # noqa: E402


def test_adjust_price_includes_score_and_fee() -> None:
    """Price scales with score and fee percentages."""
    price_low = adjust_price(0.0, Marketplace.redbubble)
    price_high = adjust_price(2.0, Marketplace.redbubble)
    assert price_high > price_low


def test_create_listing_metadata_adds_price() -> None:
    """Computed price is added to metadata."""
    metadata = create_listing_metadata(1.0, Marketplace.etsy, {"title": "t"})
    assert "price" in metadata
    assert metadata["price"] > 0
