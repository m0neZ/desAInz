#!/usr/bin/env bash
# Tag and push Docker images with git SHA and semantic version.

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <registry> <version>" >&2
  exit 1
fi

REGISTRY="$1"
VERSION="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICES_DIR="$ROOT_DIR/services"

SHA="$(git -C "$ROOT_DIR" rev-parse --short HEAD)"

if [[ ! -d "$SERVICES_DIR" ]]; then
  echo "No services directory found at $SERVICES_DIR" >&2
  exit 1
fi

for svc in "$SERVICES_DIR"/*; do
  if [[ -d "$svc" && -f "$svc/Dockerfile" ]]; then
    name="$(basename "$svc")"
    local_image="$name:latest"
    sha_tag="$REGISTRY/$name:$SHA"
    version_tag="$REGISTRY/$name:$VERSION"
    echo "Tagging and pushing $name"
    docker tag "$local_image" "$sha_tag"
    docker tag "$local_image" "$version_tag"
    docker push "$sha_tag"
    docker push "$version_tag"
  fi
done
