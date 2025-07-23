#!/usr/bin/env bash
# Validate that the Alembic migration chain has a single head.

set -euo pipefail

HEADS=$(alembic -c backend/shared/db/alembic.ini heads | wc -l)
if [ "$HEADS" -ne 1 ]; then
  echo "Multiple migration heads detected:" >&2
  alembic -c backend/shared/db/alembic.ini heads >&2
  exit 1
fi

alembic -c backend/shared/db/alembic.ini heads
