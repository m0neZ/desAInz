"""Tests for PagerDuty utilities and SLA cooldown logic."""

from __future__ import annotations
from pathlib import Path
import sys
import types

from typing import Any

import fakeredis

# Add monitoring src to path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from monitoring import pagerduty  # noqa: E402


def _import_main(monkeypatch: Any):
    """Import ``monitoring.main`` with database connections patched."""
    monkeypatch.setitem(
        sys.modules,
        "psycopg2",
        types.SimpleNamespace(connect=lambda *a, **k: types.SimpleNamespace()),
    )
    from monitoring import main as main_module  # noqa: E402

    return main_module


PAGERDUTY_URL = pagerduty.PAGERDUTY_URL


def test_trigger_sla_violation_sends_request(
    requests_mock: Any, monkeypatch: Any
) -> None:
    """trigger_sla_violation should POST alert when routing key present."""
    monkeypatch.setenv("PAGERDUTY_ROUTING_KEY", "key")
    requests_mock.post(PAGERDUTY_URL, status_code=202)
    pagerduty.trigger_sla_violation(2.5)
    assert requests_mock.called
    history = requests_mock.request_history[0]
    assert history.json()["routing_key"] == "key"
    assert "2.50" in history.json()["payload"]["summary"]


def test_notify_listing_issue_sends_request(
    requests_mock: Any, monkeypatch: Any
) -> None:
    """notify_listing_issue should POST listing alert when routing key present."""
    monkeypatch.setenv("PAGERDUTY_ROUTING_KEY", "key")
    requests_mock.post(PAGERDUTY_URL, status_code=202)
    pagerduty.notify_listing_issue(123, "removed")
    assert requests_mock.called
    history = requests_mock.request_history[0]
    assert history.json()["payload"]["summary"] == "Listing 123 is removed"


def test_pagerduty_disabled_skips_request(requests_mock: Any, monkeypatch: Any) -> None:
    """No request should be made when ENABLE_PAGERDUTY is false."""
    monkeypatch.setenv("PAGERDUTY_ROUTING_KEY", "key")
    main = _import_main(monkeypatch)
    cfg = main.Settings(ENABLE_PAGERDUTY=False)
    requests_mock.post(PAGERDUTY_URL, status_code=202)
    pagerduty.trigger_sla_violation(1.0, cfg=cfg)
    assert not requests_mock.called


def test_sla_alert_respects_cooldown(monkeypatch: Any) -> None:
    """Subsequent SLA alerts are suppressed during cooldown."""
    main = _import_main(monkeypatch)
    fake = fakeredis.FakeRedis()
    monkeypatch.setattr(main, "sync_get", lambda key: fake.get(key))
    monkeypatch.setattr(
        main,
        "sync_set",
        lambda key, value, ttl=None: (
            fake.set(key, value) if ttl is None else fake.setex(key, ttl, value)
        ),
    )
    cfg = main.Settings(SLA_THRESHOLD_HOURS=2, SLA_ALERT_COOLDOWN_MINUTES=10)
    monkeypatch.setattr(main, "_record_latencies", lambda: [7200.0, 10800.0])
    times = iter([1000.0, 1000.0, 1000.0 + 601])

    def fake_time() -> float:
        try:
            return next(times)
        except StopIteration:  # pragma: no cover - extra calls
            return 1000.0 + 601

    monkeypatch.setattr(main.time, "time", fake_time)
    triggered: list[float] = []

    def fake_trigger(hours: float) -> None:
        triggered.append(hours)

    monkeypatch.setattr(main, "trigger_sla_violation", fake_trigger)
    main._check_sla(cfg)
    main._check_sla(cfg)
    main._check_sla(cfg)
    assert len(triggered) == 2
