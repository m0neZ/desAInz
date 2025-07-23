#!/usr/bin/env python
"""
Benchmark mock-up generation latency.

This script measures how long it takes to generate ``runs`` mock-ups using the
:class:`mockup_generation.generator.MockupGenerator`.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import asyncio
from time import perf_counter

from mockup_generation.generator import MockupGenerator


async def main(prompt: str, output_dir: Path, steps: int, runs: int) -> float:
    """Return total duration in seconds for generating ``runs`` mock-ups."""
    generator = MockupGenerator()
    generator.load()
    output_dir.mkdir(parents=True, exist_ok=True)

    start = perf_counter()
    for i in range(runs):
        await generator.generate(
            prompt,
            str(output_dir / f"mockup_{i}.png"),
            num_inference_steps=steps,
        )
    duration = perf_counter() - start
    print(f"Generated {runs} mock-ups in {duration:.2f}s")
    return duration


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", default="test mockup", help="generation prompt")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("mockups"),
        help="directory to store generated images",
    )
    parser.add_argument("--steps", type=int, default=30, help="inference steps")
    parser.add_argument("--runs", type=int, default=1, help="number of mock-ups")
    args = parser.parse_args()
    asyncio.run(main(args.prompt, args.output_dir, args.steps, args.runs))
