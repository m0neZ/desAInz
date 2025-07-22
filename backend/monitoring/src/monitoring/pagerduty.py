"""PagerDuty integration utilities."""

from __future__ import annotations

import os
from typing import Any

import requests

from backend.shared.http import request_with_retry
from .settings import settings

PAGERDUTY_URL = "https://events.pagerduty.com/v2/enqueue"


def _send_event(summary: str, severity: str, source: str) -> None:
    """Send an event to PagerDuty if integration is enabled."""

    if not settings.enable_pagerduty:
        return
    routing_key = os.environ.get("PAGERDUTY_ROUTING_KEY")
    if not routing_key:
        return
    payload: dict[str, Any] = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": summary,
            "severity": severity,
            "source": source,
        },
    }
    try:
        request_with_retry("POST", PAGERDUTY_URL, json=payload, timeout=5)
    except requests.RequestException:
        pass


def trigger_sla_violation(duration_hours: float) -> None:
    """Send an alert when the SLA threshold is breached."""

    _send_event(
        summary=f"Signal-to-publish time {duration_hours:.2f}h exceeded SLA",
        severity="error",
        source="desAInz monitoring",
    )


def notify_listing_issue(listing_id: int, state: str) -> None:
    """Alert administrators that ``listing_id`` needs attention."""

    _send_event(
        summary=f"Listing {listing_id} is {state}",
        severity="warning",
        source="desAInz listing sync",
    )
