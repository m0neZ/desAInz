"""Celery tasks for updating exchange rates."""

from __future__ import annotations

import os
from celery import Celery

from .currency import CurrencyConverter, fetch_latest_rates

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
app = Celery("currency", broker=BROKER_URL)
app.conf.result_backend = BROKER_URL


@app.task  # type: ignore[misc]
def update_exchange_rates(base_currency: str = "USD") -> None:
    """Fetch and store latest exchange rates."""
    rates = fetch_latest_rates(base_currency)
    converter = CurrencyConverter()
    for code, rate in rates.items():
        converter.store_rate(base_currency, code, rate)
