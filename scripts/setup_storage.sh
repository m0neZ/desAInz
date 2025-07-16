#!/usr/bin/env bash

# Setup S3 or MinIO bucket structure based on the blueprint
# Usage: ./setup_storage.sh <bucket-name> [--minio]

set -euo pipefail

BUCKET="$1"
USE_MINIO="${2:-}"

create_path() {
  local path="$1"
  if [ "$USE_MINIO" = "--minio" ]; then
    mc cp /dev/null "${BUCKET}/${path}placeholder" >/dev/null
  else
    aws s3 cp /dev/null "s3://${BUCKET}/${path}placeholder" >/dev/null
  fi
}

for DIR in raw-signals generated-mockups published-assets backups; do
  create_path "${DIR}/"
done

create_path "raw-signals/year=2024/month=01/day=15/"
create_path "generated-mockups/example-idea/variants/"
create_path "backups/database/"
create_path "backups/configurations/"

echo "Bucket ${BUCKET} initialized."
