"""Tests for the Dagster orchestrator."""

from orchestrator.jobs import (
    backup_job,
    cleanup_job,
    idea_job,
)
from orchestrator.schedules import daily_backup_schedule, hourly_cleanup_schedule


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
