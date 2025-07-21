#!/usr/bin/env bash
# Run integration tests with strict settings.

set -euo pipefail

pytest -W error tests/integration tests/e2e "$@"
