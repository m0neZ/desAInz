"""Dagster sensors for conditional job triggers."""

from __future__ import annotations

import os
from typing import Iterator, Union

from dagster import (
    RunFailureSensorContext,
    RunRequest,
    SensorEvaluationContext,
    SkipReason,
    run_failure_sensor,
    sensor,
)

from monitoring.pagerduty import notify_listing_issue

from .jobs import idea_job


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
