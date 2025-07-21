# Backup and Restore

This document describes how backups are created and how to restore the
system in the event of data loss.

## Scheduled Backups

Backups run nightly using a Kubernetes CronJob defined in the `backup-jobs`
Helm chart. The job executes `scripts/backup.py` inside a small container
with `pg_dump` and the AWS CLI installed.

The script dumps the PostgreSQL database to a temporary file and uploads it to
the S3 bucket specified by `BACKUP_BUCKET`.

Use `scripts/apply_s3_lifecycle.py` to configure the bucket with a lifecycle
policy that transitions objects to Glacier after 365 days. Run the script once
after bucket creation:

```bash
python scripts/apply_s3_lifecycle.py <bucket>
```

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

## Full System Restore After Outage

The following steps outline how to rebuild a production environment after a
major outage. The commands assume a Docker Compose deployment but can be
adapted to Kubernetes.

1. **Provision infrastructure**. Ensure the target machines are running and
   Docker is installed. Copy over the compose files from the repository or
   clone the project.
2. **Restore environment variables**. Retrieve the secret files from your
   vault or backups and place them under `secrets/` and the appropriate
   `.env` locations.
3. **Download the latest backup** from your S3 bucket:
   ```bash
   aws s3 cp s3://<bucket>/postgres/postgres_<timestamp>.sql ./restore.sql
   ```
4. **Start the database service** and load the SQL dump:
   ```bash
   docker compose up -d db
   psql -h localhost -U <user> -d <db-name> -f restore.sql
   ```
5. **Run migrations** to bring the schema up to date:
   ```bash
   docker compose exec api alembic upgrade head
   ```
6. **Start remaining services**:
   ```bash
   docker compose up -d
   ```
7. **Verify the deployment**. Check the health endpoints and run a smoke test:
   ```bash
   curl -f http://localhost:8000/health
   ```
   If the command succeeds, the application is operational.

This process restores the latest database dump and reinstates all services with
their secrets intact.
