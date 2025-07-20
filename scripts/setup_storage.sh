#!/usr/bin/env bash

# Setup S3 or MinIO buckets and lifecycle policies based on the blueprint.
# Usage: ./setup_storage.sh <bucket-name> [--minio]

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <bucket-name> [--minio]" >&2
  echo "Requires the AWS CLI for S3 or the mc client for MinIO." >&2
  exit 1
fi

BUCKET="$1"
USE_MINIO="${2:-}"

# Detect available CLI tools when --minio is not explicitly provided.
if [[ -z "$USE_MINIO" ]]; then
  if command -v aws >/dev/null 2>&1; then
    USE_MINIO=""
  elif command -v mc >/dev/null 2>&1; then
    echo "AWS CLI not found. Falling back to 'mc' (MinIO)." >&2
    USE_MINIO="--minio"
  else
    echo "Neither AWS CLI nor 'mc' found. Install one of them or pass --minio." >&2
    exit 1
  fi
fi

# Validate that the chosen CLI exists.
if [[ "$USE_MINIO" == "--minio" ]]; then
  if ! command -v mc >/dev/null 2>&1; then
    echo "MinIO client 'mc' not found. Install it or remove --minio to use AWS S3." >&2
    exit 1
  fi
else
  if ! command -v aws >/dev/null 2>&1; then
    echo "AWS CLI not found. Install it from https://aws.amazon.com/cli/." >&2
    exit 1
  fi
fi

create_bucket() {
  if [ "$USE_MINIO" = "--minio" ]; then
    if ! mc ls "$BUCKET" >/dev/null 2>&1; then
      mc mb "$BUCKET"
    fi
    mc ilm add --transition-days 365 --transition-storage-class GLACIER "$BUCKET" >/dev/null
  else
    if ! aws s3api head-bucket --bucket "$BUCKET" >/dev/null 2>&1; then
      aws s3api create-bucket --bucket "$BUCKET"
    fi
    aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET" --lifecycle-configuration '{"Rules":[{"ID":"ArchiveAfter12Months","Prefix":"","Status":"Enabled","Transitions":[{"Days":365,"StorageClass":"GLACIER"}]}]}'
  fi
}

create_path() {
  local path="$1"
  if [ "$USE_MINIO" = "--minio" ]; then
    mc cp /dev/null "${BUCKET}/${path}placeholder" >/dev/null
  else
    aws s3 cp /dev/null "s3://${BUCKET}/${path}placeholder" >/dev/null
  fi
}

create_bucket

for DIR in raw-signals generated-mockups published-assets backups; do
  create_path "${DIR}/"
done

create_path "raw-signals/year=2024/month=01/day=15/"
create_path "generated-mockups/example-idea/variants/"
create_path "backups/database/"
create_path "backups/configurations/"

echo "Bucket ${BUCKET} initialized."
