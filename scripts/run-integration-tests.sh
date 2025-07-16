#!/usr/bin/env bash
set -euo pipefail

# Install dependencies
pip install -q -r requirements.txt

# Format check
black --check src tests >/dev/null
flake8 src tests
mypy src tests

# Build docs
sphinx-build -W -b html docs docs/_build

# Run tests treating warnings as errors
PYTHONPATH=$(pwd)/src python -m pytest -W error tests/integration
