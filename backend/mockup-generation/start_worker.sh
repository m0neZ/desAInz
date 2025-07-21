#!/usr/bin/env bash
# Start the Celery worker with task checkpointing enabled.
set -euo pipefail
STATE_DIR=/var/run/celery
mkdir -p "$STATE_DIR"
exec celery -A mockup_generation.celery_app worker \
  --loglevel=info \
  -Q gpu-${GPU_WORKER_INDEX} \
  --concurrency=1 \
  --statedb="$STATE_DIR/worker.state" \
  --task-events

