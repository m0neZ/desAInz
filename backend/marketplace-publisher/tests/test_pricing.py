"""Tests for price adjustments."""

import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"  # noqa: E402

from marketplace_publisher.pricing import (
    adjust_price,
    create_listing_metadata,
    BASE_PRICE,
    SCORE_FACTOR,
    FEE_PERCENT,
)
from marketplace_publisher.db import Marketplace  # noqa: E402

import pytest


def test_adjust_price_includes_score_and_fee() -> None:
    """Price scales with score and fee percentages."""
    price_low = adjust_price(0.0, Marketplace.redbubble)
    price_high = adjust_price(2.0, Marketplace.redbubble)
    assert price_high > price_low


@pytest.mark.parametrize("score", [0.0, 1.0, 2.5])
@pytest.mark.parametrize("marketplace", list(Marketplace))
def test_adjust_price_matches_formula(score: float, marketplace: Marketplace) -> None:
    """Verify final price equals formula for each marketplace."""
    expected = round(
        BASE_PRICE * (1 + score * SCORE_FACTOR) * (1 + FEE_PERCENT[marketplace]),
        2,
    )
    assert adjust_price(score, marketplace) == expected


def test_price_rounding_to_two_decimals() -> None:
    """Price is rounded to exactly two decimal places."""
    price = adjust_price(1.234, Marketplace.amazon_merch)
    assert price == round(price, 2)
    assert len(str(price).split(".")[1]) <= 2


def test_create_listing_metadata_adds_price() -> None:
    """Computed price is added to metadata and matches ``adjust_price``."""
    metadata = create_listing_metadata(1.0, Marketplace.etsy, {"title": "t"})
    assert "price" in metadata
    expected = adjust_price(1.0, Marketplace.etsy)
    assert metadata["price"] == expected


def test_create_listing_metadata_merges_existing_fields() -> None:
    """Extra metadata keys are preserved in the result."""
    meta = create_listing_metadata(0.5, Marketplace.society6, {"foo": "bar"})
    assert meta["foo"] == "bar"
    assert meta["price"] == adjust_price(0.5, Marketplace.society6)
