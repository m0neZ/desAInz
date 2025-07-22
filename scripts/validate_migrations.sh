#!/usr/bin/env bash
# Validate that the Alembic migration chain has a single head.

set -euo pipefail

python scripts/check_heads.py "$@"
