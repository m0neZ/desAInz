#!/usr/bin/env bash
# Build Docker images for all microservices using Docker Buildx.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if ! docker buildx inspect >/dev/null 2>&1; then
  docker buildx create --use
fi

docker buildx bake -f docker-compose.yml \
  --set '*.platform=linux/amd64,linux/arm64' --progress plain "$@"
