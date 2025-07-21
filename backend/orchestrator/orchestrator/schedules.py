"""Dagster schedules for periodic jobs."""

from dagster import ScheduleEvaluationContext, schedule

from .jobs import (
    backup_job,
    cleanup_job,
    analyze_query_plans_job,
    daily_summary_job,
    rotate_secrets_job,
    sync_listings_job,
    privacy_purge_job,
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


@schedule(cron_schedule="0 0 1 * *", job=rotate_secrets_job, execution_timezone="UTC")
def monthly_secret_rotation_schedule(
    _context: ScheduleEvaluationContext,
) -> dict[str, object]:
    """Rotate secrets on the first day of each month."""
    return {}


@schedule(cron_schedule="0 2 * * *", job=sync_listings_job, execution_timezone="UTC")
def daily_listing_sync_schedule(
    _context: ScheduleEvaluationContext,
) -> dict[str, object]:
    """Trigger ``sync_listings_job`` every day."""
    return {}


@schedule(cron_schedule="0 0 * * 0", job=privacy_purge_job, execution_timezone="UTC")
def weekly_privacy_purge_schedule(
    _context: ScheduleEvaluationContext,
) -> dict[str, object]:
    """Run ``privacy_purge_job`` once a week."""
    return {}
