#!/usr/bin/env bash

# Create a CloudFront distribution pointing to the given S3 bucket
# Usage: ./configure_cdn.sh <bucket-name> <origin-domain>

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <bucket-name> <origin-domain>" >&2
  exit 1
fi

command -v aws >/dev/null 2>&1 || {
  echo "AWS CLI is required" >&2
  exit 1
}

BUCKET="$1"
ORIGIN_DOMAIN="$2"

DISTRIBUTION_CONFIG=$(cat <<JSON
{
  "CallerReference": "$(date +%s)",
  "Comment": "Design Idea Engine CDN",
  "Enabled": true,
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "${BUCKET}",
        "DomainName": "${ORIGIN_DOMAIN}",
        "S3OriginConfig": {"OriginAccessIdentity": ""}
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "${BUCKET}",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TrustedSigners": {"Enabled": false, "Quantity": 0},
    "ForwardedValues": {"QueryString": false, "Cookies": {"Forward": "none"}},
    "DefaultTTL": 3600,
    "MaxTTL": 86400,
    "MinTTL": 0
  }
}
JSON
)

aws cloudfront create-distribution --distribution-config "$DISTRIBUTION_CONFIG"
