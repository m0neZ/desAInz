"""Dagster sensors for conditional job triggers."""

from __future__ import annotations

import os
from typing import Iterator, Union

from dagster import (
    DagsterRunStatus,
    RunFailureSensorContext,
    RunRequest,
    RunsFilter,
    SensorEvaluationContext,
    SkipReason,
    run_failure_sensor,
    sensor,
)

from monitoring.pagerduty import notify_listing_issue

from .jobs import idea_job

MAX_RESCHEDULE_ATTEMPTS = 3


@sensor(job=idea_job, minimum_interval_seconds=3600)  # type: ignore[misc]
def idea_sensor(
    context: SensorEvaluationContext,
) -> Iterator[Union[RunRequest, SkipReason]]:
    """Trigger ``idea_job`` when ``AUTO_RUN_IDEA`` is enabled."""
    if os.environ.get("AUTO_RUN_IDEA") == "true":
        yield RunRequest(
            run_key=context.cursor,
            tags={"trigger": "sensor"},
        )
    else:
        yield SkipReason("AUTO_RUN_IDEA not enabled")


@run_failure_sensor(monitor_all_code_locations=True)  # type: ignore[misc]
def run_failure_notifier(context: RunFailureSensorContext) -> None:
    """Notify Slack when a run fails."""
    try:
        cleaned = context.dagster_run.run_id.replace("-", "")
        notify_listing_issue(int(cleaned, 16), "failed")
    except Exception as exc:  # pragma: no cover - best effort
        context.log.warning("notification failed: %s", exc)


@sensor(minimum_interval_seconds=60)  # type: ignore[misc]
def reschedule_failed_runs(
    context: SensorEvaluationContext,
) -> Iterator[RunRequest]:
    """Reschedule failed runs until ``MAX_RESCHEDULE_ATTEMPTS`` is reached."""
    filters = RunsFilter(statuses=[DagsterRunStatus.FAILURE])
    for run in context.instance.get_runs(filters=filters):
        attempts = int(run.tags.get("retry_attempt", "0"))
        if attempts >= MAX_RESCHEDULE_ATTEMPTS:
            continue
        yield RunRequest(
            run_key=f"{run.run_id}:{attempts + 1}",
            job_name=run.job_name,
            run_config=run.run_config,
            tags={**run.tags, "retry_attempt": str(attempts + 1)},
        )
