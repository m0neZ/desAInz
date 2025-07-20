"""Dagster schedules for periodic jobs."""

from dagster import ScheduleEvaluationContext, schedule

from .jobs import (
    backup_job,
    cleanup_job,
    analyze_query_plans_job,
    daily_summary_job,
)


@schedule(cron_schedule="0 0 * * *", job=backup_job, execution_timezone="UTC")
def daily_backup_schedule(_context: ScheduleEvaluationContext) -> dict[str, object]:
    """Trigger ``backup_job`` every day."""
    return {}


@schedule(cron_schedule="0 * * * *", job=cleanup_job, execution_timezone="UTC")
def hourly_cleanup_schedule(_context: ScheduleEvaluationContext) -> dict[str, object]:
    """Trigger ``cleanup_job`` every hour."""
    return {}


@schedule(
    cron_schedule="30 6 * * *", job=analyze_query_plans_job, execution_timezone="UTC"
)
def daily_query_plan_schedule(_context: ScheduleEvaluationContext) -> dict[str, object]:
    """Trigger ``analyze_query_plans_job`` every morning."""
    return {}


@schedule(cron_schedule="5 0 * * *", job=daily_summary_job, execution_timezone="UTC")
def daily_summary_schedule(_context: ScheduleEvaluationContext) -> dict[str, object]:
    """Trigger ``daily_summary_job`` every day."""
    return {}
