"""Performance tests for mockup generation."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
import threading
from pathlib import Path

import pytest
import torch

from mockup_generation.generator import MockupGenerator


def test_generation_speed(tmp_path: Path) -> None:
    """Ensure generation completes within a reasonable timeframe."""
    generator = MockupGenerator()
    start = time.perf_counter()
    generator.generate("test", str(tmp_path / "img.png"), num_inference_steps=1)
    duration = time.perf_counter() - start
    assert duration < 30


def test_cleanup_reduces_memory() -> None:
    """Pipeline resources are released after cleanup."""
    import psutil
    import gc

    generator = MockupGenerator()
    generator.pipeline = bytearray(50 * 1024 * 1024)
    proc = psutil.Process()
    before = proc.memory_info().rss
    generator.cleanup()
    gc.collect()
    after = proc.memory_info().rss
    assert generator.pipeline is None
    assert after <= before


def test_concurrent_generation_gpu_utilization(tmp_path: Path) -> None:
    """Generate multiple mockups concurrently and verify GPU utilization."""

    if not torch.cuda.is_available():
        pytest.skip("CUDA is required for GPU utilization test")

    try:
        import pynvml
    except Exception:  # pragma: no cover - optional dependency
        pytest.skip("pynvml is required to measure GPU utilization")

    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    util_samples: list[int] = []
    done = threading.Event()

    def monitor() -> None:
        while not done.is_set():
            rates = pynvml.nvmlDeviceGetUtilizationRates(handle)
            util_samples.append(rates.gpu)
            time.sleep(0.1)

    generator = MockupGenerator()
    prompts = [f"test {i}" for i in range(3)]
    paths = [tmp_path / f"img_{i}.png" for i in range(3)]

    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.start()

    with ThreadPoolExecutor(max_workers=3) as executor:
        for prompt, path in zip(prompts, paths):
            executor.submit(
                generator.generate,
                prompt,
                str(path),
                num_inference_steps=1,
            )

    done.set()
    monitor_thread.join()
    pynvml.nvmlShutdown()

    assert all(p.exists() for p in paths)
    assert max(util_samples, default=0) > 0
