#!/usr/bin/env bash

# Invalidate CloudFront cache for updated mockups
# Usage: ./invalidate_cache.sh <distribution-id> <path>

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <distribution-id> <path>" >&2
  exit 1
fi

command -v aws >/dev/null 2>&1 || {
  echo "AWS CLI is required" >&2
  exit 1
}

DISTRIBUTION_ID="$1"
INVALIDATION_PATH="$2"

aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "$INVALIDATION_PATH"
