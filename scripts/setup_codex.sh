#!/usr/bin/env bash
# Setup script for preparing the desAInz environment on Codex.
# Installs Python and Node dependencies and builds documentation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt

if command -v npm >/dev/null 2>&1; then
  npm ci --legacy-peer-deps
fi

# Build Sphinx documentation
python -m pip install sphinx myst-parser sphinxcontrib-mermaid
SKIP_APIDOC=1 SKIP_OPENAPI=1 python -m sphinx -W -b html docs docs/_build/html

