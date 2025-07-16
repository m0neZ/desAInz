"""Prometheus metrics for orchestrator jobs."""

from prometheus_client import Counter

BACKUP_JOB_SUCCESS = Counter(
    "backup_job_success_total", "Number of successful backup job runs"
)
BACKUP_JOB_FAILURE = Counter(
    "backup_job_failure_total", "Number of failed backup job runs"
)
CLEANUP_JOB_SUCCESS = Counter(
    "cleanup_job_success_total", "Number of successful cleanup job runs"
)
CLEANUP_JOB_FAILURE = Counter(
    "cleanup_job_failure_total", "Number of failed cleanup job runs"
)
