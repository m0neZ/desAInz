"""Tests for currency conversion utilities."""

from __future__ import annotations

import fakeredis
import pytest

from backend.shared.currency import CurrencyConverter


@pytest.fixture()
def redis_client() -> fakeredis.FakeRedis:
    """Return a fake Redis instance."""
    return fakeredis.FakeRedis(decode_responses=True)


def test_rounding(redis_client: fakeredis.FakeRedis) -> None:
    """Converted values should be rounded to two decimals."""
    converter = CurrencyConverter()
    converter._redis = redis_client  # inject fake client
    converter.store_rate("USD", "EUR", 0.9)
    assert converter.convert(10, "USD", "EUR") == 9.0
    assert converter.convert(10.555, "USD", "EUR") == 9.5


def test_same_currency(redis_client: fakeredis.FakeRedis) -> None:
    """Amounts in the same currency are rounded only."""
    converter = CurrencyConverter()
    converter._redis = redis_client
    assert converter.convert(10.555, "USD", "USD") == 10.56
