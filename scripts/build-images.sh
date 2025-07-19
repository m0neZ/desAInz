#!/usr/bin/env bash
# Build Docker images for all microservices.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICES=(
  backend/api-gateway
  backend/feedback-loop
  backend/marketplace-publisher
  backend/mockup-generation
  backend/monitoring
  backend/orchestrator
  backend/scoring-engine
  backend/signal-ingestion
  frontend/admin-dashboard
  docker/postgres
  docker/pgbouncer
  docker/redis
  docker/kafka
  docker/minio
  docker/backup
)

for svc in "${SERVICES[@]}"; do
  path="$ROOT_DIR/$svc"
  if [[ -f "$path/Dockerfile" ]]; then
    name="$(basename "$svc")"
    context="$path"
    if [[ "$svc" == "backend/orchestrator" ]]; then
      context="$ROOT_DIR"
    fi
    echo "Building ${name}:latest from $path"
    docker build -t "${name}:latest" -f "$path/Dockerfile" "$context"
  fi
done
