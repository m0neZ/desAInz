# Orchestrator

This module contains all Dagster jobs and schedules for desAInz.

## Schedules

- **daily_backup_schedule**: Runs `backup_job` every day at 00:00 UTC. Ensures backups are created regularly.
- **hourly_cleanup_schedule**: Runs `cleanup_job` every hour. Archives old
  mockups and purges stale signals and logs.

Metrics for job success and failure are exported as Prometheus counters:
`backup_job_success_total`, `backup_job_failure_total`, `cleanup_job_success_total`, and `cleanup_job_failure_total`.
