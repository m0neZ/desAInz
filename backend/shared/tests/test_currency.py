"""Tests for currency conversion utilities."""

from __future__ import annotations

from pathlib import Path
import importlib.util
from typing import Any

import fakeredis
import pytest
from apscheduler.schedulers.background import BackgroundScheduler

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
def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset Redis and scheduler before each test."""
    currency.redis_client.flushall()
    if currency.scheduler.running:
        currency.scheduler.shutdown()
    monkeypatch.setattr(currency, "scheduler", BackgroundScheduler())


def test_update_rates(requests_mock: Any) -> None:
    """Fetched rates are stored in Redis."""
    requests_mock.get(currency.EXCHANGE_API_URL, json={"rates": {"EUR": 0.84}})
    currency.update_rates()
    assert currency.redis_client.get(currency.REDIS_KEY) == '{"EUR": 0.84}'


def test_convert_price_rounding(requests_mock: Any) -> None:
    """Converted amounts are rounded using ``ROUND_HALF_UP``."""
    requests_mock.get(currency.EXCHANGE_API_URL, json={"rates": {"EUR": 0.8456}})
    currency.update_rates()
    result = currency.convert_price(1.0, "EUR")
    assert result == 0.85


def test_start_rate_updater_adds_job(monkeypatch: pytest.MonkeyPatch) -> None:
    """Scheduler runs periodic update job."""
    monkeypatch.setattr(currency, "scheduler", BackgroundScheduler())
    monkeypatch.setattr(
        currency, "_fetch_rates", lambda base=currency.BASE_CURRENCY: {"EUR": 1.0}
    )
    currency.start_rate_updater()
    jobs = currency.scheduler.get_jobs()
    assert len(jobs) == 1
    currency.scheduler.shutdown()
