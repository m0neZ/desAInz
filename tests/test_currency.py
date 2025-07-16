"""Tests for currency conversion utilities."""

from __future__ import annotations

import pytest
import fakeredis.aioredis

from backend.shared.currency import CurrencyConverter


@pytest.mark.asyncio()  # type: ignore[misc]
async def test_rounding_rules() -> None:
    """Converted amounts should round half up to two decimals."""
    redis = fakeredis.aioredis.FakeRedis()
    converter = CurrencyConverter(redis)
    await redis.hset("exchange_rates", mapping={"USD": 1, "EUR": 0.9})
    result = await converter.convert(1.005, "USD", "USD")
    assert result == 1.01
    result = await converter.convert(10.0, "USD", "EUR")
    assert result == 9.0
    await redis.aclose()
