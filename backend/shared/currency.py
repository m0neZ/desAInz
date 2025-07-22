"""Currency conversion utilities with Redis caching."""

from __future__ import annotations

import json
import logging
import os
from decimal import Decimal, ROUND_HALF_UP
from typing import cast

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests

from backend.shared.cache import SyncRedis, get_sync_client
from backend.shared.config import settings

logger = logging.getLogger(__name__)

REDIS_URL = settings.redis_url
EXCHANGE_API_URL = os.environ.get(
    "EXCHANGE_API_URL", "https://api.exchangerate.host/latest"
)
BASE_CURRENCY = os.environ.get("BASE_CURRENCY", "USD")
REDIS_KEY = "exchange_rates"
UPDATE_INTERVAL_MINUTES = int(os.environ.get("EXCHANGE_UPDATE_MINUTES", "60"))

redis_client: SyncRedis = get_sync_client()
scheduler = BackgroundScheduler()


def _fetch_rates(base: str = BASE_CURRENCY) -> dict[str, float]:
    """Fetch latest exchange rates from external API."""
    response = requests.get(EXCHANGE_API_URL, params={"base": base}, timeout=10)
    response.raise_for_status()
    data = response.json()
    rates: dict[str, float] = {
        currency: float(rate) for currency, rate in data.get("rates", {}).items()
    }
    return rates


def update_rates() -> None:
    """Fetch and store exchange rates in Redis."""
    rates = _fetch_rates()
    redis_client.set(REDIS_KEY, json.dumps(rates))
    logger.info("stored %d exchange rates", len(rates))


def start_rate_updater() -> None:
    """Start scheduler for periodic exchange rate updates."""
    if scheduler.running:
        return
    scheduler.add_job(
        update_rates,
        trigger=IntervalTrigger(minutes=UPDATE_INTERVAL_MINUTES),
        next_run_time=None,
    )
    update_rates()
    scheduler.start()


def get_rate(currency: str) -> float:
    """Return rate for ``currency`` relative to base currency."""
    data_raw = redis_client.get(REDIS_KEY)
    if data_raw is None:
        update_rates()
        data_raw = redis_client.get(REDIS_KEY) or "{}"
    if isinstance(data_raw, bytes):
        data_str = data_raw.decode()
    else:
        data_str = cast(str, data_raw)
    rates = json.loads(data_str)
    if currency not in rates:
        raise KeyError(currency)
    return float(rates[currency])


def convert_price(amount: float, currency: str) -> float:
    """Convert ``amount`` from base currency to ``currency`` rounded to cents."""
    rate = get_rate(currency)
    quantized = (Decimal(str(amount)) * Decimal(str(rate))).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return float(quantized)
