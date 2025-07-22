#!/usr/bin/env bash
# Validate that the Alembic migration chain has a single head and no branches.

set -euo pipefail

HEADS=$(alembic -c backend/shared/db/alembic.ini heads | wc -l)
if [ "$HEADS" -ne 1 ]; then
  echo "Multiple migration heads detected:" >&2
  alembic -c backend/shared/db/alembic.ini heads >&2
  exit 1
fi

BRANCHES=$(alembic -c backend/shared/db/alembic.ini branches | wc -l)
if [ "$BRANCHES" -ne 0 ]; then
  echo "Divergent migration branches detected:" >&2
  alembic -c backend/shared/db/alembic.ini branches >&2
  exit 1
fi

alembic -c backend/shared/db/alembic.ini heads
