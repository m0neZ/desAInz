# Data Privacy

This project stores user generated signals and analytics metrics. To comply with privacy requirements we remove personally identifiable information (PII) and delete old records.

## PII Purging

Incoming signal data is sanitized by `signal_ingestion.privacy.purge_row`, which strips email addresses and phone numbers before a signal is persisted.
Stored records can be cleaned retroactively via `signal_ingestion.privacy.purge_pii_rows`.
The Dagster `privacy_purge_job` runs this routine once per week.
Deletion requests can be sent to `DELETE /privacy/signals` on the API gateway.
This endpoint calls `signal_ingestion.privacy.purge_pii_rows` and records an
audit log entry for traceability.

## Data Retention

Signals older than the configured `signal_retention_days` setting (default: 90 days) are removed by `signal_ingestion.retention.purge_old_signals`. Analytics logs should be pruned on the same schedule.

## Deduplication

`signal_ingestion.dedup` uses a Redis set to avoid processing duplicates.
The set expires after the number of seconds configured by `dedup_ttl`
(default: `86400` seconds).

## Compliance Steps

1. Set the retention period in the environment if different from the default.
2. Schedule periodic execution of the retention routine.
3. Use the API gateway deletion endpoint when users request removal.
4. Ensure documentation is built and published on every commit to main.
