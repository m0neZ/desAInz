#!/usr/bin/env bash
# Run Locust load tests with strict settings.

set -euo pipefail

locust -f load_tests/locustfile.py \
  --headless \
  -u "${USERS:-10}" \
  -r "${SPAWN_RATE:-5}" \
  --run-time "${RUN_TIME:-1m}"
