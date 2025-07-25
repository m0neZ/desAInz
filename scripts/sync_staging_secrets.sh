#!/usr/bin/env bash
# Sync production secrets to the staging namespace.
#
# Usage: ./scripts/sync_staging_secrets.sh <prod-namespace> <staging-namespace>

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <prod-namespace> <staging-namespace>" >&2
  exit 1
fi

command -v kubectl >/dev/null 2>&1 || {
  echo "kubectl is required" >&2
  exit 1
}

PROD_NS="$1"
STAGING_NS="$2"

if ! kubectl get namespace "$PROD_NS" >/dev/null 2>&1; then
  echo "Namespace $PROD_NS does not exist" >&2
  exit 1
fi

if ! kubectl get namespace "$STAGING_NS" >/dev/null 2>&1; then
  echo "Namespace $STAGING_NS does not exist" >&2
  exit 1
fi

kubectl get secrets -n "$PROD_NS" --no-headers -o custom-columns=:metadata.name |
  while read -r secret; do
    kubectl get secret "$secret" -n "$PROD_NS" -o yaml \
      | sed "s/namespace: $PROD_NS/namespace: $STAGING_NS/" \
      | kubectl apply -n "$STAGING_NS" -f -
  done

echo "Secrets from namespace $PROD_NS have been mirrored to $STAGING_NS."
