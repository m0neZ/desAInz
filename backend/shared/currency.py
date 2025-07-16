"""Utility for currency conversion using Redis-backed exchange rates."""

from __future__ import annotations

import asyncio
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping

import httpx
from redis.asyncio import Redis


class CurrencyConverter:
    """Convert prices between currencies using cached exchange rates."""

    def __init__(
        self,
        redis: Redis,
        base_currency: str = "USD",
        key: str = "exchange_rates",
    ) -> None:
        """Initialize the converter.

        Args:
            redis: Redis client instance.
            base_currency: The base currency for the rates.
            key: Redis key used to store the rates.
        """
        self._redis = redis
        self.base_currency = base_currency
        self.key = key

    async def update_rates(self, api_url: str) -> None:
        """Fetch latest rates from ``api_url`` and store them in Redis."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(api_url)
            resp.raise_for_status()
            data: Mapping[str, Any] = resp.json()
        rates = data.get("rates")
        if not isinstance(rates, Mapping):
            raise ValueError("Invalid response from rate provider")
        await self._redis.hset(self.key, mapping=dict(rates))
        await self._redis.set(f"{self.key}:base", self.base_currency)

    async def convert(
        self, amount: float, from_currency: str, to_currency: str
    ) -> float:
        """Convert ``amount`` from ``from_currency`` to ``to_currency``."""
        raw_from = await self._redis.hget(self.key, from_currency)
        raw_to = await self._redis.hget(self.key, to_currency)
        if raw_from is None or raw_to is None:
            raise ValueError("Missing exchange rate")
        rate_from = Decimal(
            raw_from.decode() if isinstance(raw_from, bytes) else raw_from
        )
        rate_to = Decimal(raw_to.decode() if isinstance(raw_to, bytes) else raw_to)
        decimal_amount = Decimal(str(amount)) / rate_from * rate_to
        return float(decimal_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    async def schedule_updates(self, api_url: str, interval: int) -> None:
        """Continually refresh rates every ``interval`` seconds."""
        while True:  # pragma: no cover - infinite loop
            try:
                await self.update_rates(api_url)
            except Exception:  # pragma: no cover - network failures
                pass
            await asyncio.sleep(interval)
