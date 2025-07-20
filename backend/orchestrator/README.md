# Orchestrator

This module contains all Dagster jobs and schedules for desAInz.

## Schedules

- **daily_backup_schedule**: Runs `backup_job` every day at 00:00 UTC. Ensures backups are created regularly.
- **hourly_cleanup_schedule**: Runs `cleanup_job` every hour. Removes temporary data to keep storage usage low.
- **daily_summary_schedule**: Runs `daily_summary_job` every day at 00:05 UTC. Generates a JSON report of recent activity.

Metrics for job success and failure are exported as Prometheus counters:
`backup_job_success_total`, `backup_job_failure_total`, `cleanup_job_success_total`, and `cleanup_job_failure_total`.


## Dagster UI

Start the Dagster webserver to inspect pipeline status and logs:

```bash
./scripts/run_dagster_webserver.sh
```

Then open http://localhost:3000 in your browser. The server loads
`backend/orchestrator/workspace.yaml` and `backend/orchestrator/dagster.yaml`
for configuration.

## Environment Variables

Copy `.env.example` to `.env` and adjust the values.
