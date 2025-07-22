#!/usr/bin/env python
"""Capture runtime profiling data for a Python module."""

from __future__ import annotations

import argparse
import cProfile
import pstats
import runpy
from pathlib import Path


def profile_module(module: str, output: Path) -> None:
    """Run ``module`` under ``cProfile`` and write stats to ``output``."""
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        runpy.run_module(module, run_name="__main__")
    finally:
        profiler.disable()
        output.parent.mkdir(parents=True, exist_ok=True)
        profiler.dump_stats(str(output))
        stats = pstats.Stats(profiler)
        stats.sort_stats(pstats.SortKey.CUMULATIVE)
        stats.print_stats(20)


def main() -> None:
    """Parse arguments and profile the requested module."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", help="Python module to run, e.g. 'app.main'")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("profile.prof"),
        help="Path to write cProfile data",
    )
    args = parser.parse_args()
    profile_module(args.module, args.output)


if __name__ == "__main__":
    main()
