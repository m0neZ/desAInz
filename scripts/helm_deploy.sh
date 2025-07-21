#!/usr/bin/env bash
# Deploy all microservices via Helm.

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <registry> <tag> <env>" >&2
  exit 1
fi

command -v helm >/dev/null 2>&1 || {
  echo "helm is required" >&2
  exit 1
}

REGISTRY="$1"
TAG="$2"
ENV="$3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CHART_DIR="$ROOT_DIR/infrastructure/helm/all-services"

helm dependency update "$CHART_DIR"
helm upgrade --install desainz "$CHART_DIR" \
  --set global.image.registry="$REGISTRY" \
  --set global.image.tag="$TAG" \
  -f "$CHART_DIR/values-$ENV.yaml"
