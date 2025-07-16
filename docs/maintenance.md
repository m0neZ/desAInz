# Maintenance Scripts

This project includes automated routines for cleaning up old artifacts.
The `scripts/maintenance.py` module defines scheduled tasks that perform
the following actions:

- **Archive and delete mockups**: mockup images older than twelve months are
  moved to the path defined by `COLD_STORAGE_PATH` before their database records
  are removed.
- **Purge stale signals and logs**: any signal entries older than thirty days
  are deleted along with log files under the directory specified by `LOG_DIR`.
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

## Dependency Updates

Dependencies for Python, JavaScript, and GitHub Actions are kept current via Dependabot.
Weekly update PRs run on all `requirements*.txt`, `package.json` files, and workflow definitions. These PRs must pass the full test suite before merge.
