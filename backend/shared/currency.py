"""Currency conversion utilities using Redis for exchange rates."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, getcontext

import redis
import requests

getcontext().prec = 8


class CurrencyConverter:
    """Convert amounts using exchange rates stored in Redis."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0") -> None:
        """Create converter using ``redis_url`` for the connection."""
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Return ``amount`` converted from ``from_currency`` to ``to_currency``."""
        if from_currency.upper() == to_currency.upper():
            return float(Decimal(amount).quantize(Decimal("0.01"), ROUND_HALF_UP))
        key = f"rates:{from_currency.upper()}_{to_currency.upper()}"
        rate = self._redis.get(key)
        if rate is None:
            raise KeyError(f"missing exchange rate for {from_currency}->{to_currency}")
        converted = Decimal(amount) * Decimal(rate)
        return float(converted.quantize(Decimal("0.01"), ROUND_HALF_UP))

    def store_rate(self, from_currency: str, to_currency: str, rate: float) -> None:
        """Store an exchange rate in Redis."""
        key = f"rates:{from_currency.upper()}_{to_currency.upper()}"
        self._redis.set(key, rate)


def fetch_latest_rates(
    base_currency: str = "USD", api_url: str | None = None
) -> dict[str, float]:
    """Fetch latest exchange rates from an external API."""
    url = api_url or "https://api.exchangerate.host/latest"
    response = requests.get(url, params={"base": base_currency}, timeout=10)
    response.raise_for_status()
    data: dict[str, float] = response.json().get("rates", {})
    return data
