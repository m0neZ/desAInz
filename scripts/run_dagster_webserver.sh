#!/usr/bin/env bash
# Start Dagster webserver for the orchestrator.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"
export DAGSTER_HOME="${DAGSTER_HOME:-$ROOT_DIR/backend/orchestrator}"
exec dagster-webserver -w backend/orchestrator/workspace.yaml -h 0.0.0.0 -p 3000
