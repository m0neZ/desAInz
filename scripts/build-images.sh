#!/usr/bin/env bash
# Build Docker images for all microservices.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICES_DIR="$ROOT_DIR/services"

if [[ ! -d "$SERVICES_DIR" ]]; then
  echo "No services directory found at $SERVICES_DIR" >&2
  exit 1
fi

for svc in "$SERVICES_DIR"/*; do
  if [[ -d "$svc" && -f "$svc/Dockerfile" ]]; then
    name="$(basename "$svc")"
    image="$name:latest"
    echo "Building $image from $svc"
    docker build -t "$image" "$svc"
  fi
done
