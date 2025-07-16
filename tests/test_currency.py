"""Tests for currency conversion utilities."""

from __future__ import annotations

import fakeredis
from unittest.mock import patch

from backend.shared.currency import (
    convert_price,
    update_exchange_rates,
    EXCHANGE_RATES_KEY,
)


def test_update_and_convert_rounding() -> None:
    """Rates are stored in Redis and conversions are rounded half up."""
    redis_client = fakeredis.FakeRedis()
    fake_resp = {"rates": {"EUR": 0.8915}}
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = fake_resp
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status.return_value = None
        update_exchange_rates(redis_client)
    assert redis_client.exists(EXCHANGE_RATES_KEY)
    value = convert_price(10.0, "EUR", redis_client)
    assert value == 8.92
