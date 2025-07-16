"""Dagster hooks for recording job metrics."""

from dagster import HookContext, failure_hook, success_hook

from .metrics import (
    BACKUP_JOB_FAILURE,
    BACKUP_JOB_SUCCESS,
    CLEANUP_JOB_FAILURE,
    CLEANUP_JOB_SUCCESS,
)


@success_hook
def record_success(context: HookContext) -> None:
    """Increment success counters based on job name."""
    if context.job_name == "backup_job":
        BACKUP_JOB_SUCCESS.inc()
    elif context.job_name == "cleanup_job":
        CLEANUP_JOB_SUCCESS.inc()


@failure_hook
def record_failure(context: HookContext) -> None:
    """Increment failure counters based on job name."""
    if context.job_name == "backup_job":
        BACKUP_JOB_FAILURE.inc()
    elif context.job_name == "cleanup_job":
        CLEANUP_JOB_FAILURE.inc()
