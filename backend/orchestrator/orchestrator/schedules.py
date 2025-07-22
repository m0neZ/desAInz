"""Dagster schedules for periodic jobs."""

from dagster import ScheduleEvaluationContext, schedule

from .jobs import (
    backup_job,
    cleanup_job,
    analyze_query_plans_job,
    daily_summary_job,
    rotate_secrets_job,
    rotate_s3_keys_job,
    sync_listings_job,
    privacy_purge_job,
    idea_job,
    feedback_update_job,
    maintain_spot_nodes_job,
)


@schedule(cron_schedule="0 0 * * *", job=backup_job, execution_timezone="UTC")  # type: ignore[misc]
def daily_backup_schedule(_context: ScheduleEvaluationContext) -> dict[str, object]:
    """Trigger ``backup_job`` every day."""
    return {}


@schedule(cron_schedule="0 * * * *", job=cleanup_job, execution_timezone="UTC")  # type: ignore[misc]
def hourly_cleanup_schedule(_context: ScheduleEvaluationContext) -> dict[str, object]:
    """Trigger ``cleanup_job`` every hour."""
    return {}


@schedule(  # type: ignore[misc]
    cron_schedule="30 6 * * *", job=analyze_query_plans_job, execution_timezone="UTC"
)
def daily_query_plan_schedule(_context: ScheduleEvaluationContext) -> dict[str, object]:
    """Trigger ``analyze_query_plans_job`` every morning."""
    return {}


@schedule(cron_schedule="5 0 * * *", job=daily_summary_job, execution_timezone="UTC")  # type: ignore[misc]
def daily_summary_schedule(_context: ScheduleEvaluationContext) -> dict[str, object]:
    """Trigger ``daily_summary_job`` every day."""
    return {}


@schedule(cron_schedule="0 0 1 * *", job=rotate_secrets_job, execution_timezone="UTC")  # type: ignore[misc]
def monthly_secret_rotation_schedule(
    _context: ScheduleEvaluationContext,
) -> dict[str, object]:
    """Rotate secrets on the first day of each month."""
    return {}


@schedule(cron_schedule="0 1 1 * *", job=rotate_s3_keys_job, execution_timezone="UTC")  # type: ignore[misc]
def rotate_s3_keys_schedule(
    _context: ScheduleEvaluationContext,
) -> dict[str, object]:
    """Rotate S3 access keys monthly."""
    return {}


@schedule(cron_schedule="0 2 * * *", job=sync_listings_job, execution_timezone="UTC")  # type: ignore[misc]
def daily_listing_sync_schedule(
    _context: ScheduleEvaluationContext,
) -> dict[str, object]:
    """Trigger ``sync_listings_job`` every day."""
    return {}


@schedule(cron_schedule="0 0 * * 0", job=privacy_purge_job, execution_timezone="UTC")  # type: ignore[misc]
def weekly_privacy_purge_schedule(
    _context: ScheduleEvaluationContext,
) -> dict[str, object]:
    """Run ``privacy_purge_job`` once a week."""
    return {}


@schedule(cron_schedule="15 * * * *", job=idea_job, execution_timezone="UTC")  # type: ignore[misc]
def hourly_idea_schedule(_context: ScheduleEvaluationContext) -> dict[str, object]:
    """Run ``idea_job`` every hour."""
    return {}


@schedule(cron_schedule="0 3 * * *", job=feedback_update_job, execution_timezone="UTC")  # type: ignore[misc]
def daily_feedback_update_schedule(
    _context: ScheduleEvaluationContext,
) -> dict[str, object]:
    """Update feedback weights once per day."""
    return {}


@schedule(  # type: ignore[misc]
    cron_schedule="*/10 * * * *", job=maintain_spot_nodes_job, execution_timezone="UTC"
)
def maintain_spot_nodes_schedule(
    _context: ScheduleEvaluationContext,
) -> dict[str, object]:
    """Check spot nodes every ten minutes."""
    return {}
