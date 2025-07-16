#!/usr/bin/env bash

# Invalidate CloudFront cache for updated mockups
# Usage: ./invalidate_cache.sh <distribution-id> <path>

set -euo pipefail

DISTRIBUTION_ID="$1"
INVALIDATION_PATH="$2"

aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "$INVALIDATION_PATH"
