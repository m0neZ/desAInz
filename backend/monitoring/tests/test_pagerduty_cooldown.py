"""Tests for PagerDuty SLA cooldown logic."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any
from datetime import datetime, timedelta

# Add monitoring src to path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from monitoring import main, pagerduty  # noqa: E402


def _use_fake_redis(fake_redis: Any, monkeypatch: Any) -> None:
    monkeypatch.setattr(main, "sync_get", lambda k: fake_redis.get(k))
    monkeypatch.setattr(main, "sync_set", lambda k, v, ttl=None: fake_redis.set(k, v))
    monkeypatch.setattr(
        pagerduty, "sync_set", lambda k, v, ttl=None: fake_redis.set(k, v)
    )


def test_sla_cooldown_skips_alert(monkeypatch: Any, fake_redis: Any) -> None:
    """Alert should not fire again during the cooldown period."""
    _use_fake_redis(fake_redis, monkeypatch)
    monkeypatch.setattr(main, "_record_latencies", lambda: [10800.0])
    monkeypatch.setattr(main.settings, "SLA_THRESHOLD_HOURS", 1.0)
    monkeypatch.setattr(main.settings, "SLA_ALERT_COOLDOWN_HOURS", 1.0)
    monkeypatch.setenv("PAGERDUTY_ROUTING_KEY", "key")

    called: list[float] = []

    def fake_trigger(hours: float) -> None:
        called.append(hours)

    monkeypatch.setattr(main, "trigger_sla_violation", fake_trigger)

    # First call should trigger and store timestamp
    main._check_sla()
    assert called == [3.0]

    # Set last alert timestamp to 30 minutes ago
    fake_redis.set(
        pagerduty.SLA_LAST_ALERT_KEY,
        str((datetime.utcnow() - timedelta(minutes=30)).timestamp()),
    )

    called.clear()
    main._check_sla()
    assert called == []
