"""Tests for run failure sensor notifications."""  # noqa: E402

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))

from dagster import DagsterInstance, build_run_status_sensor_context

from orchestrator.jobs import idea_job  # noqa: E402
from orchestrator.sensors import run_failure_notifier  # noqa: E402


@pytest.mark.asyncio()
async def test_run_failure_notifier(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sensor should trigger PagerDuty alert on failure."""
    calls: list[tuple[int, str]] = []

    def fake_notify(listing_id: int, state: str) -> None:  # noqa: D401
        calls.append((listing_id, state))

    monkeypatch.setattr("orchestrator.sensors.notify_listing_issue", fake_notify)

    class Resp:
        def raise_for_status(self) -> None:  # noqa: D401
            return None

        def json(self) -> dict[str, object]:  # noqa: D401
            return {"approved": False}

    monkeypatch.setattr("requests.get", lambda *a, **k: Resp())
    monkeypatch.delenv("APPROVAL_SERVICE_URL", raising=False)

    instance = DagsterInstance.ephemeral()
    result = idea_job.execute_in_process(instance=instance, raise_on_error=False)
    assert not result.success

    event = result.get_run_failure_event()
    context = build_run_status_sensor_context(
        sensor_name="run_failure_notifier",
        dagster_event=event,
        dagster_instance=instance,
        dagster_run=result.dagster_run,
    )
    run_failure_notifier(context)
    assert calls and calls[0][1] == "failed"
