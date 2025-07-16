#!/usr/bin/env bash
set -euo pipefail
sleep 5
SCHEMA_REGISTRY_URL="http://localhost:8081"
for schema_file in /schemas/*.json; do
  topic=$(basename "$schema_file" .json)
  curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
    --data @"$schema_file" \
    "$SCHEMA_REGISTRY_URL/subjects/${topic}-value/versions"
done
