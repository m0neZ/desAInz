#!/usr/bin/env bash
# Rotate log files daily by moving them to an archive folder and pruning old archives.

set -euo pipefail

LOG_DIR="${LOG_DIR:-logs}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

mkdir -p "${LOG_DIR}/archive"
TIMESTAMP="$(date +'%Y%m%d%H%M%S')"

shopt -s nullglob
for log_file in "${LOG_DIR}"/*.log; do
    mv "$log_file" "${LOG_DIR}/archive/$(basename "$log_file").${TIMESTAMP}"
    : > "$log_file"
done
shopt -u nullglob

find "${LOG_DIR}/archive" -type f -mtime +"${RETENTION_DAYS}" -delete
