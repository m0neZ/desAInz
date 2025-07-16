"""Tests for currency conversion utilities."""

from __future__ import annotations

import fakeredis
import pytest

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "currency", Path(__file__).resolve().parents[1] / "currency.py"
)
currency = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(currency)


def setup_module(module: object) -> None:
    """Use fakeredis for tests."""
    currency.redis_client = fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture(autouse=True)
def _mock_rates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock rate fetching to provide deterministic values."""
    rates = {"EUR": 0.8456}

    def _fake_fetch(base: str = currency.BASE_CURRENCY) -> dict[str, float]:
        return rates

    monkeypatch.setattr(currency, "_fetch_rates", _fake_fetch)
    currency.redis_client.flushall()
    currency.update_rates()


def test_convert_price_rounding() -> None:
    """Converted amounts are rounded using ``ROUND_HALF_UP``."""
    result = currency.convert_price(1.0, "EUR")
    assert result == 0.85
