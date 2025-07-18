"""Dagster sensors for conditional job triggers."""

from __future__ import annotations

import os
from typing import Iterator, Union

from dagster import RunRequest, SensorEvaluationContext, SkipReason, sensor

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
