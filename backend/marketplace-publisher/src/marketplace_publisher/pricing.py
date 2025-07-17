"""Pricing utilities for marketplace listings."""

from __future__ import annotations

from typing import Mapping, Any

from .db import Marketplace

BASE_PRICE = 20.0
SCORE_FACTOR = 0.1
FEE_PERCENT: Mapping[Marketplace, float] = {
    Marketplace.redbubble: 0.2,
    Marketplace.amazon_merch: 0.3,
    Marketplace.etsy: 0.15,
    Marketplace.society6: 0.25,
}


def adjust_price(
    score: float, marketplace: Marketplace, base_price: float = BASE_PRICE
) -> float:
    """Return final price including score adjustment and fees."""
    adjusted = base_price * (1 + score * SCORE_FACTOR)
    fee = FEE_PERCENT.get(marketplace, 0.0)
    return round(adjusted * (1 + fee), 2)


def create_listing_metadata(
    score: float,
    marketplace: Marketplace,
    metadata: Mapping[str, Any] | None = None,
    base_price: float = BASE_PRICE,
) -> dict[str, Any]:
    """Return listing metadata with computed price."""
    data = dict(metadata or {})
    data["price"] = adjust_price(score, marketplace, base_price)
    return data
