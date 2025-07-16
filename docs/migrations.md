# Database Migrations

This project uses Alembic for schema migrations. Migrations for the different
services live under `backend/shared/db/migrations`.

## Creating a Migration

Run Alembic to generate a new migration after applying model changes. Example
for the scoring engine service:

```bash
alembic -c backend/shared/db/alembic.ini revision -m "add status" --autogenerate
```

See `backend/shared/db/migrations/scoring_engine/versions/0002_add_status_column.py`
for an example that adds a `status` column with the default value `pending`.

## Merge Migrations

When multiple branches introduce migrations independently, Alembic may create
separate heads. Before merging branches, generate a merge migration to keep the
history linear:

```bash
alembic -c backend/shared/db/alembic.ini merge -m "merge heads" HEADS
```

Commit the resulting merge file so that the migration chain has a single head.

