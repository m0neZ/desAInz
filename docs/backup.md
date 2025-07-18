# Backup and Restore

This document describes how backups are created and how to restore the
system in the event of data loss.

## Scheduled Backups

Backups run nightly using a Kubernetes CronJob defined in the `backup-jobs`
Helm chart. The job executes `scripts/backup.py` inside a small container
with `pg_dump` and the AWS CLI installed.

The script dumps the PostgreSQL database to a temporary file and uploads it to
the S3 bucket specified by `BACKUP_BUCKET`.

## Restoring from Backup

1. Download the desired SQL dump from your backup bucket:
   ```bash
   aws s3 cp s3://<bucket>/postgres/postgres_<timestamp>.sql ./restore.sql
   ```
2. Restore the database:
   ```bash
   psql -h <db-host> -U <user> -d <db-name> -f restore.sql
   ```

## Verify Backup Integrity

After restoring, run a simple query to ensure expected data is present:

```bash
psql -h <db-host> -U <user> -d <db-name> -c "SELECT count(*) FROM information_schema.tables;"
```

If the command returns a non-zero count, the backup was successfully restored.
