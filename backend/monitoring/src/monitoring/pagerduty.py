"""PagerDuty integration utilities."""

from __future__ import annotations

import os
from typing import Any

import requests

PAGERDUTY_URL = "https://events.pagerduty.com/v2/enqueue"


def trigger_sla_violation(duration_hours: float) -> None:
    """Send a PagerDuty alert for SLA breach if routing key configured."""
    routing_key = os.environ.get("PAGERDUTY_ROUTING_KEY")
    if not routing_key:
        return
    payload: dict[str, Any] = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": f"Signal-to-publish time {duration_hours:.2f}h exceeded SLA",
            "severity": "error",
            "source": "desAInz monitoring",
        },
    }
    try:
        requests.post(PAGERDUTY_URL, json=payload, timeout=5)
    except requests.RequestException:
        pass
