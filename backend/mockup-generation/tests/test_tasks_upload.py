"""Tests for upload step in generate_mockup."""

# mypy: ignore-errors

from __future__ import annotations

import types
from pathlib import Path

import sys
import asyncio
import warnings
from contextlib import asynccontextmanager
from typing import AsyncIterator
import pytest

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))  # noqa: E402

mock_celery_app = types.ModuleType("mockup_generation.celery_app")


def _task_decorator(*_d_args: object, **_d_kwargs: object) -> callable:
    def wrapper(func: callable) -> types.SimpleNamespace:
        return types.SimpleNamespace(run=func)

    return wrapper


mock_celery_app.app = types.SimpleNamespace(task=_task_decorator)
mock_celery_app.queue_for_gpu = lambda *args, **kwargs: None
sys.modules.setdefault("mockup_generation.celery_app", mock_celery_app)
from mockup_generation import tasks  # noqa: E402

_orig_generate_mockup = tasks.generate_mockup.run


def _call_generate_mockup(
    keywords: list[list[str]], output_dir: str, **kw: object
) -> object:
    dummy = types.SimpleNamespace(request=types.SimpleNamespace(delivery_info={}))
    return _orig_generate_mockup(dummy, keywords, output_dir, **kw)


tasks.generate_mockup = _call_generate_mockup

uc_mod = sys.modules.setdefault("UnleashClient", types.ModuleType("UnleashClient"))
uc_mod.UnleashClient = object
ld_mod = sys.modules.setdefault("ldclient", types.ModuleType("ldclient"))
ld_mod.LDClient = object
prom_mod = types.ModuleType("prometheus_client")
sys.modules["prometheus_client"] = prom_mod
prom_mod.CONTENT_TYPE_LATEST = ""
prom_mod.Counter = lambda *a, **k: types.SimpleNamespace(
    labels=lambda *_, **__: types.SimpleNamespace(inc=lambda *_, **__: None)
)
prom_mod.Gauge = lambda *a, **k: types.SimpleNamespace(
    inc=lambda *_, **__: None,
    dec=lambda *_, **__: None,
)
prom_mod.Histogram = lambda *a, **k: types.SimpleNamespace(
    labels=lambda *_, **__: types.SimpleNamespace(observe=lambda *_, **__: None)
)
prom_mod.REGISTRY = types.SimpleNamespace(register=lambda *a, **k: None)
prom_mod.generate_latest = lambda *a, **k: b""
sys.modules.setdefault("pgvector.sqlalchemy", types.ModuleType("pgvector.sqlalchemy"))
sys.modules["pgvector.sqlalchemy"].Vector = object
warnings.filterwarnings("ignore", category=UserWarning)


class DummyClient:
    """Collect upload calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    async def put_object(self, Bucket: str, Key: str, Body: bytes | str) -> None:
        self.calls.append((Bucket, Key, ""))


class DummyGenerator:
    """Write a dummy file and return its path."""

    def __init__(self) -> None:
        self.cleaned = False

    def generate(
        self,
        prompt: str,
        output: str,
        num_inference_steps: int = 30,
        **_kw: object,
    ) -> object:
        Path(output).write_text("x")
        return types.SimpleNamespace(image_path=output)

    def cleanup(self) -> None:
        self.cleaned = True


class DummyListing:
    """Simple listing data container."""

    title = "t"
    description = "d"
    tags = ["a"]


class DummyListingGen:
    """Return :class:`DummyListing` objects."""

    def generate(self, keywords: list[str]) -> DummyListing:
        return DummyListing()


def test_generate_mockup_upload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Image is uploaded using the storage client."""
    gen = DummyGenerator()
    monkeypatch.setattr(tasks, "generator", gen)
    monkeypatch.setattr(tasks, "ListingGenerator", lambda: DummyListingGen())

    @asynccontextmanager
    async def _client() -> AsyncIterator[DummyClient]:
        yield DummyClient()

    monkeypatch.setattr(tasks, "_get_storage_client", _client)
    monkeypatch.setattr(
        tasks,
        "redis_client",
        types.SimpleNamespace(
            lock=lambda *a, **k: types.SimpleNamespace(
                acquire=lambda *a, **k: True,
                locked=lambda: False,
                release=lambda: None,
            )
        ),
    )

    class _Lock:
        async def acquire(self, *args: object, **kwargs: object) -> bool:
            return True

        def locked(self) -> bool:
            return False

        async def release(self) -> None:
            return None

    monkeypatch.setattr(
        tasks,
        "async_redis_client",
        types.SimpleNamespace(lock=lambda *a, **k: _Lock()),
    )
    monkeypatch.setattr(tasks, "remove_background", lambda img: img)
    monkeypatch.setattr(tasks, "convert_to_cmyk", lambda img: img)
    monkeypatch.setattr(tasks, "ensure_not_nsfw", lambda img: None)
    monkeypatch.setattr(tasks, "validate_dpi_image", lambda img: True)
    monkeypatch.setattr(tasks, "validate_color_space", lambda img: True)
    monkeypatch.setattr(
        tasks.model_repository, "save_generated_mockup", lambda *a, **k: 1
    )
    called: list[str] = []
    monkeypatch.setattr(
        tasks, "_invalidate_cdn_cache", lambda path: called.append(path)
    )
    tasks.settings.s3_bucket = "b"
    tasks.settings.s3_endpoint = "http://test"  # type: ignore
    tasks.settings.s3_base_url = "http://cdn.test"  # type: ignore

    tasks.generate_mockup([["kw"]], str(tmp_path), model="m", gpu_index=0)
    assert gen.cleaned
