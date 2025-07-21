# Maintenance Scripts

This project includes automated routines for cleaning up old artifacts.
The `scripts/maintenance.py` module defines scheduled tasks that perform
the following actions:

- **Archive and delete mockups**: mockup images older than twelve months are
  moved to the path defined by `COLD_STORAGE_PATH` before their database records
  are removed.
- **Purge stale signals and logs**: any signal entries older than thirty days
  are deleted along with log files under the directory specified by `LOG_DIR`.
- **Delete old S3 objects**: objects older than the configured retention period
  are removed from the bucket defined by `S3_BUCKET`.
- **Remove audit log entries**: records older than eighteen months are purged to
  keep the audit table compact.

A scheduler is configured to run these tasks daily using `apscheduler`.
The Dagster orchestrator exposes the same routines via the `cleanup_job`, which
is scheduled hourly. Administrators can trigger the job manually from the Admin
Dashboard.

Run the script directly to start the scheduler:

```bash
python scripts/maintenance.py
```

Environment variables can override the storage paths:

- `COLD_STORAGE_PATH` – directory for archived mockups (defaults to `cold_storage`)
- `LOG_DIR` – directory containing log files (defaults to `logs`)
- `S3_BUCKET` – target bucket for object cleanup
- `S3_RETENTION_DAYS` – optional retention period in days (defaults to 90)

## Log Rotation

The `scripts/rotate_logs.sh` helper rotates application logs. It moves `*.log`
files in `LOG_DIR` into an `archive` directory with a timestamp suffix and
removes archives older than seven days.

Run the script via cron:

```bash
0 1 * * * /app/scripts/rotate_logs.sh
```

## Dependency Updates

Dependencies for Python, JavaScript, and GitHub Actions are kept current via Dependabot.
Weekly update PRs run on all `requirements*.txt`, `package.json` files, and workflow definitions. These PRs must pass the full test suite before merge.

## Query Plan Analysis

Slow database statements can be inspected using `scripts/analyze_query_plans.py`.
The script reads from `pg_stat_statements` and prints `EXPLAIN` plans for the worst offenders.
Use the optional `SLOW_QUERY_LIMIT` environment variable to adjust how many statements are inspected.

```bash
python scripts/analyze_query_plans.py
```

The `daily_query_plan_schedule` Dagster schedule runs the analysis once a day.

## Nightly Backups

In production Docker Compose deployments a `backup` service runs `scripts/backup.py`
using cron. The container uploads a PostgreSQL dump to the bucket defined by
`BACKUP_BUCKET` every night at midnight UTC.

## Monthly Secret Rotation

Secrets used by internal services are rotated automatically. The
`monthly_secret_rotation_schedule` triggers `rotate_secrets_job` on the first day
of every month. The job waits for manual approval via the `/approvals` API
before executing `scripts/rotate_secrets.rotate()`.
Once the rotation completes a Slack message is sent if `SLACK_WEBHOOK_URL` is
configured.
