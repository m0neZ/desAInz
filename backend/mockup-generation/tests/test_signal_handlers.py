"""Tests for GPU lock cleanup on process termination."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))


@pytest.mark.skipif(sys.platform == "win32", reason="Signals not supported")
def test_gpu_lock_released_on_sigterm(tmp_path: Path) -> None:
    """Process releases the GPU lock when receiving SIGTERM."""
    lock_dir = tmp_path / "locks"
    lock_dir.mkdir()
    script = tmp_path / "worker.py"
    script.write_text(
        textwrap.dedent(
            f"""
            import os
            import signal
            import sys
            import time
            import asyncio
            from pathlib import Path
            import types

            sys.path.append(str(Path(__file__).resolve().parents[2]))

            celery_mod = types.ModuleType('mockup_generation.celery_app')
            celery_mod.app = object()
            sys.modules['mockup_generation.celery_app'] = celery_mod

            botocore_mod = types.ModuleType('botocore.client')
            botocore_mod.BaseClient = object
            sys.modules['botocore.client'] = botocore_mod
            minio_mod = types.ModuleType('minio')
            minio_mod.Minio = object
            sys.modules['minio'] = minio_mod

            from mockup_generation import tasks

            class _FileLock:
                def __init__(self, path: Path) -> None:
                    self.path = path
                    self._locked = False

                def acquire(self, blocking: bool = False) -> bool:
                    if self.path.exists():
                        return False
                    self.path.touch()
                    self._locked = True
                    return True

                def release(self) -> None:
                    if self._locked and self.path.exists():
                        self.path.unlink()
                    self._locked = False

                def locked(self) -> bool:
                    return self._locked and self.path.exists()

            class _DummyRedis:
                def __init__(self, root: Path) -> None:
                    self.root = root

                def lock(self, name: str, timeout: int | None = None, blocking_timeout: int = 0):
                    return _FileLock(self.root / name)

                def get(self, key: str):
                    return None

            tasks.async_redis_client = _DummyRedis(Path({repr(str(lock_dir))}))
            tasks.get_gpu_slots = lambda: 1
            async def run() -> None:
                async with tasks.gpu_slot():
                    print('acquired', flush=True)
                    while True:
                        await asyncio.sleep(0.1)

            asyncio.run(run())
            """
        )
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{ROOT}:{env.get('PYTHONPATH', '')}"
    proc = subprocess.Popen(
        [sys.executable, str(script)], stdout=subprocess.PIPE, env=env
    )
    assert proc.stdout.readline().decode().strip() == "acquired"
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=5)

    lock_file = lock_dir / "gpu_slot:0"
    assert not lock_file.exists()
