"""Tests for the Dagster orchestrator."""  # noqa: E402

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT))  # noqa: E402

from orchestrator.jobs import (  # noqa: E402
    backup_job,
    cleanup_job,
    idea_job,
)
import pytest  # noqa: E402
from dagster import DagsterInstance, RunRequest, build_sensor_context  # noqa: E402

from orchestrator.schedules import (  # noqa: E402
    daily_backup_schedule,  # noqa: E402
    hourly_cleanup_schedule,  # noqa: E402
)
from orchestrator.sensors import idea_sensor  # noqa: E402


def test_job_structure() -> None:
    """Verify job includes all steps in order."""
    ops = [op.name for op in idea_job.graph.node_dict.values()]
    assert ops == [
        "ingest_signals",
        "score_signals",
        "generate_content",
        "await_approval",
        "publish_content",
    ]


def test_backup_schedule_definition() -> None:
    """Daily backup schedule is correctly configured."""
    assert daily_backup_schedule.job == backup_job
    assert daily_backup_schedule.cron_schedule == "0 0 * * *"


def test_cleanup_schedule_definition() -> None:
    """Hourly cleanup schedule is correctly configured."""
    assert hourly_cleanup_schedule.job == cleanup_job
    assert hourly_cleanup_schedule.cron_schedule == "0 * * * *"


def test_idea_job_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run ``idea_job`` with a Dagster instance and verify op order."""
    calls: list[str] = []

    def fake_post(url: str, *args: object, **kwargs: object) -> object:
        calls.append(url)

        class Resp:
            def raise_for_status(self) -> None:  # noqa: D401 - for test only
                """Pretend the request succeeded."""

            def json(self) -> dict[str, object]:  # noqa: D401 - for test only
                """Return a minimal payload."""
                if url.endswith("/ingest"):
                    return {"signals": ["s1"]}
                if url.endswith("/score"):
                    return {"score": 1}
                if url.endswith("/generate"):
                    return {"items": ["i1"]}
                return {"task_id": 1}

        return Resp()

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setenv("APPROVE_PUBLISHING", "true")
    instance = DagsterInstance.ephemeral()
    result = idea_job.execute_in_process(instance=instance)
    assert result.success
    assert calls == [
        "http://signal-ingestion:8004/ingest",
        "http://scoring-engine:5002/score",
        "http://mockup-generation:8000/generate",
        "http://marketplace-publisher:8001/publish",
    ]


def test_idea_sensor_triggers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure ``idea_sensor`` requests a run when enabled."""
    monkeypatch.setenv("AUTO_RUN_IDEA", "true")
    context = build_sensor_context()
    requests = list(idea_sensor(context))
    assert requests and isinstance(requests[0], RunRequest)
