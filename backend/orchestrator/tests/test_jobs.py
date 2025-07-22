"""Tests for the Dagster orchestrator."""  # noqa: E402

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ORCHESTRATOR_PATH = ROOT / "backend" / "orchestrator"
sys.path.append(str(ORCHESTRATOR_PATH))  # noqa: E402
MONITORING_SRC = ROOT / "backend" / "monitoring" / "src"
sys.path.append(str(MONITORING_SRC))  # noqa: E402

from orchestrator.jobs import (  # noqa: E402
    backup_job,
    cleanup_job,
    idea_job,
    rotate_secrets_job,
    daily_summary_job,
)
import pytest  # noqa: E402
from dagster import DagsterInstance, RunRequest, build_sensor_context  # noqa: E402

from orchestrator.schedules import (  # noqa: E402
    daily_backup_schedule,
    daily_query_plan_schedule,
    hourly_cleanup_schedule,
    daily_summary_schedule,
    monthly_secret_rotation_schedule,
)
from orchestrator.sensors import idea_sensor  # noqa: E402
from orchestrator import ops  # noqa: E402


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


def test_query_plan_schedule_definition() -> None:
    """Daily query plan schedule is correctly configured."""

    assert daily_query_plan_schedule.job.name == "analyze_query_plans_job"
    assert daily_query_plan_schedule.cron_schedule == "30 6 * * *"


def test_daily_summary_schedule_definition() -> None:
    """Daily summary schedule is correctly configured."""

    assert daily_summary_schedule.job == daily_summary_job
    assert daily_summary_schedule.cron_schedule == "5 0 * * *"


def test_rotate_secrets_job_structure() -> None:
    """Rotate job should wait for approval before rotating secrets."""
    ops = [op.name for op in rotate_secrets_job.graph.node_dict.values()]
    assert ops == ["await_approval", "rotate_k8s_secrets_op"]


def test_secret_rotation_schedule_definition() -> None:
    """Monthly secret rotation schedule is correctly configured."""
    assert monthly_secret_rotation_schedule.job == rotate_secrets_job
    assert monthly_secret_rotation_schedule.cron_schedule == "0 0 1 * *"


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

    class MockClient:
        async def __aenter__(self) -> "MockClient":
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: type[BaseException] | None,
        ) -> None:
            return None

        async def get(self, url: str, *args: object, **kwargs: object) -> object:
            calls.append(url)

            class Resp:
                def raise_for_status(self) -> None:  # noqa: D401 - for test only
                    return None

                def json(self) -> dict[str, object]:  # noqa: D401 - for test only
                    return {"approved": True}

            return Resp()

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setattr(ops.httpx, "AsyncClient", MockClient)
    monkeypatch.setenv("APPROVAL_SERVICE_URL", "http://approval")
    instance = DagsterInstance.ephemeral()
    result = idea_job.execute_in_process(instance=instance)
    assert result.success
    assert calls == [
        f"http://approval/approvals/{result.dagster_run.run_id}",
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


def test_rotate_secrets_job_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run ``rotate_secrets_job`` and verify approval and Slack calls."""
    called: list[str] = []

    def fake_post(url: str, *args: object, **kwargs: object) -> object:
        called.append(url)

        class Resp:
            def raise_for_status(self) -> None:  # noqa: D401 - for test only
                return None

        return Resp()

    class MockClient:
        async def __aenter__(self) -> "MockClient":
            return self

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: type[BaseException] | None,
        ) -> None:
            return None

        async def get(self, url: str, *args: object, **kwargs: object) -> object:
            called.append(url)

            class Resp:
                def raise_for_status(self) -> None:  # noqa: D401 - for test only
                    return None

                def json(self) -> dict[str, object]:  # noqa: D401 - for test only
                    return {"approved": True}

            return Resp()

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setattr(ops.httpx, "AsyncClient", MockClient)
    monkeypatch.setenv("APPROVAL_SERVICE_URL", "http://approval")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "http://slack")
    monkeypatch.setattr(
        "scripts.rotate_secrets.rotate", lambda: called.append("rotate")
    )

    instance = DagsterInstance.ephemeral()
    result = rotate_secrets_job.execute_in_process(instance=instance)
    assert result.success
    assert f"http://approval/approvals/{result.dagster_run.run_id}" in called
    assert "http://slack" in called
