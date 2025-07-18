# Database Migrations

This project uses Alembic for schema migrations. Migrations for the different
services live under `backend/shared/db/migrations`.

## Creating a Migration

Run Alembic to generate a new migration after applying model changes. Each
service has its own configuration file under `backend/shared/db`:

```
backend/shared/db/alembic_api_gateway.ini
backend/shared/db/alembic_scoring_engine.ini
backend/shared/db/alembic_marketplace_publisher.ini
backend/shared/db/alembic_signal_ingestion.ini
```

Example for the scoring engine service:

```bash
alembic -c backend/shared/db/alembic_scoring_engine.ini \
  revision -m "add status" --autogenerate
```

See `backend/shared/db/migrations/scoring_engine/versions/0002_add_status_column.py`
for an example that adds a `status` column with the default value `pending`.

## Merge Migrations

When multiple branches introduce migrations independently, Alembic may create
separate heads. Before merging branches, generate a merge migration to keep the
history linear:

```bash
alembic -c backend/shared/db/<config>.ini merge -m "merge heads" HEADS
```

Commit the resulting merge file so that the migration chain has a single head.

## Verifying Migrations

Run the migration tests to ensure each service's migrations apply cleanly on an
empty database:

```bash
pytest tests/test_migrations.py
```

