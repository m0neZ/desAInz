"""Currency conversion utilities."""

from __future__ import annotations

import json
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict

import requests
import redis
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

EXCHANGE_RATES_KEY = "exchange_rates"


def update_exchange_rates(redis_client: redis.Redis, base_currency: str = "USD") -> None:
    """Fetch latest exchange rates and store them in Redis."""
    url = f"https://open.er-api.com/v6/latest/{base_currency}"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()
    rates = data.get("rates", {})
    redis_client.set(EXCHANGE_RATES_KEY, json.dumps(rates))


def get_rate(redis_client: redis.Redis, currency: str) -> float:
    """Return the exchange rate for ``currency`` from Redis."""
    from typing import cast

    data_raw = redis_client.get(EXCHANGE_RATES_KEY)
    data = cast(str | bytes | None, data_raw)
    if isinstance(data, bytes):
        data = data.decode()
    if data is None:
        update_exchange_rates(redis_client)
        data_raw = redis_client.get(EXCHANGE_RATES_KEY)
        data = cast(str | bytes | None, data_raw)
        if isinstance(data, bytes):
            data = data.decode()
    rates: Dict[str, Any] = json.loads(data or "{}")
    try:
        return float(rates[currency])
    except KeyError as exc:
        raise KeyError(f"unknown currency {currency}") from exc


def convert_price(amount: float, currency: str, redis_client: redis.Redis) -> float:
    """Convert ``amount`` in USD to ``currency`` rounded to two decimals."""
    rate = get_rate(redis_client, currency)
    value = Decimal(str(amount)) * Decimal(str(rate))
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def schedule_rate_updates(redis_client: redis.Redis, interval_hours: int = 1) -> BackgroundScheduler:
    """Schedule periodic updates of exchange rates."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        update_exchange_rates,
        "interval",
        hours=interval_hours,
        args=[redis_client],
        next_run_time=None,
    )
    scheduler.start()
    return scheduler
