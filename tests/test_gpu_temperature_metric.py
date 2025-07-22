"""Tests for GPU temperature metric update logic."""

import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "backend/mockup-generation")
)
client_mod = ModuleType("aiobotocore.client")
setattr(client_mod, "AioBaseClient", object)
sys.modules.setdefault("aiobotocore.client", client_mod)
session_mod = ModuleType("aiobotocore.session")
setattr(session_mod, "get_session", lambda: None)
sys.modules.setdefault("aiobotocore.session", session_mod)
botocore_exceptions = ModuleType("botocore.exceptions")
setattr(botocore_exceptions, "ClientError", Exception)
sys.modules.setdefault("botocore.exceptions", botocore_exceptions)
celery_mod = ModuleType("celery")
setattr(celery_mod, "Celery", object)
setattr(celery_mod, "Task", object)
setattr(celery_mod, "chord", lambda *args, **kwargs: None)
sys.modules["celery"] = celery_mod
signals_mod = ModuleType("celery.signals")
setattr(signals_mod, "worker_ready", object)
sys.modules["celery.signals"] = signals_mod


def test_gpu_temperature_metric(monkeypatch: Any) -> None:
    """GPU temperature gauge should use output from ``nvidia-smi``."""

    from mockup_generation.tasks import GPU_TEMPERATURE, _update_gpu_temperature

    class Result:
        stdout = "55\n"

    def fake_run(*args: Any, **kwargs: Any) -> Result:
        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)
    _update_gpu_temperature()
    assert GPU_TEMPERATURE._value.get() == 55.0
