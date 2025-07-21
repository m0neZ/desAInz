#!/usr/bin/env bash
# Run a smoke test on core services defined in docker-compose.test.yml.

set -euo pipefail

COMPOSE_FILES="-f docker-compose.dev.yml -f docker-compose.test.yml"
SERVICES=(api-gateway scoring-engine marketplace-publisher signal-ingestion feedback-loop)

cleanup() {
  docker compose $COMPOSE_FILES down
}
trap cleanup EXIT

docker compose $COMPOSE_FILES up -d "${SERVICES[@]}"

declare -A PORTS=([
  api-gateway]=8001
  [scoring-engine]=5002
  [marketplace-publisher]=8003
  [signal-ingestion]=8004
  [feedback-loop]=8005
)

for svc in "${SERVICES[@]}"; do
  port="${PORTS[$svc]}"
  echo "Waiting for $svc on port $port ..."
  until curl -fsS "http://localhost:${port}/ready" >/dev/null; do
    sleep 1
  done
  echo "$svc is ready"
done

echo "All services are ready."

