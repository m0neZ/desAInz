#!/usr/bin/env bash
# Run a smoke test on core services defined in docker-compose.test.yml.

set -euo pipefail

TIMEOUT=60

COMPOSE_FILES=(
  -f docker-compose.dev.yml
  -f docker-compose.test.yml
)
SERVICES=(api-gateway scoring-engine marketplace-publisher signal-ingestion feedback-loop)

cleanup() {
  docker compose "${COMPOSE_FILES[@]}" down
}
trap cleanup EXIT

docker compose "${COMPOSE_FILES[@]}" up -d "${SERVICES[@]}"

declare -A PORTS=(
  [api-gateway]=8001
  [scoring-engine]=5002
  [marketplace-publisher]=8003
  [signal-ingestion]=8004
  [feedback-loop]=8005
)

for svc in "${SERVICES[@]}"; do
  port="${PORTS[$svc]}"
  cid=$(docker compose "${COMPOSE_FILES[@]}" ps -q "$svc")
  start=$(date +%s)
  echo "Waiting for $svc on port $port ..."
  while ! curl -fsS "http://localhost:${port}/ready" >/dev/null 2>&1; do
    sleep 2
    status=$(docker inspect -f '{{.State.Status}}' "$cid")
    health=$(docker inspect -f '{{.State.Health.Status}}' "$cid" 2>/dev/null || echo "none")
    if [[ "$status" != "running" ]]; then
      echo "$svc container exited with status $status"
      exit 1
    fi
    if [[ "$health" == "unhealthy" ]]; then
      echo "$svc health check failed"
      exit 1
    fi
    if [[ $(($(date +%s) - start)) -ge $TIMEOUT ]]; then
      echo "Timed out waiting for $svc"
      docker compose "${COMPOSE_FILES[@]}" logs "$svc"
      exit 1
    fi
  done
  echo "$svc is ready"
done

echo "All services are ready."

