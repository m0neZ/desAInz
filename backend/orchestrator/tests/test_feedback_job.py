"""Tests for the feedback update job and schedule."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from dagster import DagsterInstance

ROOT = Path(__file__).resolve().parents[3]
ORCHESTRATOR_PATH = ROOT / "backend" / "orchestrator"
sys.path.append(str(ORCHESTRATOR_PATH))  # noqa: E402
MONITORING_SRC = ROOT / "backend" / "monitoring" / "src"
sys.path.append(str(MONITORING_SRC))  # noqa: E402
FEEDBACK_SRC = ROOT / "backend" / "feedback-loop"
sys.path.append(str(FEEDBACK_SRC))  # noqa: E402

from orchestrator.jobs import feedback_update_job  # noqa: E402
from orchestrator.schedules import (
    daily_feedback_update_schedule,
    hourly_idea_schedule,
)  # noqa: E402


def test_feedback_update_schedule() -> None:
    """Ensure feedback update schedule triggers the correct job."""
    assert daily_feedback_update_schedule.job == feedback_update_job
    assert daily_feedback_update_schedule.cron_schedule == "0 3 * * *"


def test_hourly_idea_schedule() -> None:
    """Verify the hourly idea job schedule."""
    from orchestrator.jobs import idea_job

    assert hourly_idea_schedule.job == idea_job
    assert hourly_idea_schedule.cron_schedule == "15 * * * *"


def test_feedback_update_job_exec(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the feedback update job with a mocked service."""
    calls: list[str] = []

    def fake_update(url: str) -> dict[str, float]:
        calls.append(url)
        return {"freshness": 1.0}

    monkeypatch.setattr("feedback_loop.update_weights_from_db", fake_update)
    instance = DagsterInstance.ephemeral()
    result = feedback_update_job.execute_in_process(instance=instance)
    assert result.success
    assert calls == ["http://scoring-engine:5002"]
