#!/usr/bin/env bash
# Load environment variables from a file for local runs.
# Usage: ./load-env.sh [env_file]
# Defaults to .env if no file is specified.

set -euo pipefail

ENV_FILE="${1:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Environment file $ENV_FILE not found" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
