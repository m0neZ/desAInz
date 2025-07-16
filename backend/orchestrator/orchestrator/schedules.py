"""Dagster schedules for periodic jobs."""

from dagster import ScheduleEvaluationContext, schedule

from .jobs import backup_job, cleanup_job


@schedule(cron_schedule="0 0 * * *", job=backup_job, execution_timezone="UTC")
def daily_backup_schedule(_context: ScheduleEvaluationContext) -> dict[str, object]:
    """Trigger ``backup_job`` every day."""
    return {}


@schedule(cron_schedule="0 * * * *", job=cleanup_job, execution_timezone="UTC")
def hourly_cleanup_schedule(_context: ScheduleEvaluationContext) -> dict[str, object]:
    """Trigger ``cleanup_job`` every hour."""
    return {}
