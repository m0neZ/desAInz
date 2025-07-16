#!/usr/bin/env bash
# Simple script to block execution until required services respond on their ports

set -euo pipefail

services=("postgres:5432" "redis:6379" "kafka:9092" "minio:9000")

for svc in "${services[@]}"; do
    host="${svc%%:*}"
    port="${svc##*:}"
    echo "Waiting for $host:$port ..."
    while ! nc -z "$host" "$port" >/dev/null 2>&1; do
        sleep 1
    done
    echo "$host:$port is up"
done
