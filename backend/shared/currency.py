"""Currency conversion utilities with Redis caching."""

from __future__ import annotations

import json
import logging
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, cast

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.shared.cache import SyncRedis, get_sync_client
from backend.shared.config import settings

logger = logging.getLogger(__name__)

REDIS_URL = settings.redis_url
EXCHANGE_API_URL = settings.exchange_api_url
BASE_CURRENCY = settings.base_currency
REDIS_KEY = "exchange_rates"
UPDATE_INTERVAL_MINUTES = settings.exchange_update_minutes

redis_client: SyncRedis = get_sync_client()
scheduler = BackgroundScheduler()


def _fetch_rates(base: str = BASE_CURRENCY) -> Dict[str, float]:
    """Fetch latest exchange rates from external API."""
    response = requests.get(EXCHANGE_API_URL, params={"base": base}, timeout=10)
    response.raise_for_status()
    data = response.json()
    rates = cast(dict[str, float], data.get("rates", {}))
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
    data = redis_client.get(REDIS_KEY)
    if data is None:
        update_rates()
        data = redis_client.get(REDIS_KEY) or "{}"
    rates = json.loads(cast(str, data))
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
