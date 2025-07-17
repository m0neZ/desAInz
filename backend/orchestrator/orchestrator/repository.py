"""Dagster definitions for the orchestrator."""

from dagster import Definitions

from .jobs import backup_job, cleanup_job, idea_job
from .schedules import daily_backup_schedule, hourly_cleanup_schedule


defs = Definitions(
    jobs=[idea_job, backup_job, cleanup_job],
    schedules=[daily_backup_schedule, hourly_cleanup_schedule],
)
