"""Dagster definitions for the orchestrator."""

from dagster import Definitions

from .jobs import (
    analyze_query_plans_job,
    backup_job,
    cleanup_job,
    idea_job,
    rotate_secrets_job,
    daily_summary_job,
    sync_listings_job,
    privacy_purge_job,
)
from .schedules import (
    daily_backup_schedule,
    hourly_cleanup_schedule,
    daily_query_plan_schedule,
    daily_summary_schedule,
    monthly_secret_rotation_schedule,
    daily_listing_sync_schedule,
    weekly_privacy_purge_schedule,
)
from .sensors import idea_sensor, run_failure_notifier


defs = Definitions(
    jobs=[
        idea_job,
        backup_job,
        cleanup_job,
        analyze_query_plans_job,
        daily_summary_job,
        rotate_secrets_job,
        sync_listings_job,
        privacy_purge_job,
    ],
    schedules=[
        daily_backup_schedule,
        hourly_cleanup_schedule,
        daily_query_plan_schedule,
        daily_summary_schedule,
        monthly_secret_rotation_schedule,
        daily_listing_sync_schedule,
        weekly_privacy_purge_schedule,
    ],
    sensors=[idea_sensor, run_failure_notifier],
)
