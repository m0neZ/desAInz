#!/usr/bin/env python
"""Verify Alembic environments have a single head."""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.shared.db import ensure_single_head


def main() -> None:
    """Validate all provided Alembic config files."""
    parser = argparse.ArgumentParser(description="Validate Alembic heads")
    parser.add_argument(
        "configs",
        nargs="*",
        help="Alembic config files",
    )
    args = parser.parse_args()

    if args.configs:
        configs = args.configs
    else:
        configs = [str(p) for p in Path("backend/shared/db").glob("alembic_*.ini")]

    for cfg in configs:
        ensure_single_head(cfg)


if __name__ == "__main__":  # pragma: no cover
    main()
