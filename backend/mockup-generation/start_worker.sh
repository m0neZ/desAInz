#!/usr/bin/env bash
# Start the Celery worker with task checkpointing enabled.
set -euo pipefail
STATE_DIR=/var/run/celery
mkdir -p "$STATE_DIR"
CONCURRENCY=${GPU_WORKER_CONCURRENCY:-1}
exec celery -A mockup_generation.celery_app worker \
  --loglevel=info \
  -Q gpu-${GPU_WORKER_INDEX} \
  --concurrency="${CONCURRENCY}" \
  --statedb="$STATE_DIR/worker.state" \
  --task-events \
  --without-gossip --without-mingle

