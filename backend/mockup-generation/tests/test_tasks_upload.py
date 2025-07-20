"""Tests for upload step in generate_mockup."""

from __future__ import annotations

import types
from pathlib import Path

import sys
import warnings
import pytest

root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))  # noqa: E402

from mockup_generation import tasks  # noqa: E402

uc_mod = sys.modules.setdefault("UnleashClient", types.ModuleType("UnleashClient"))
uc_mod.UnleashClient = object
ld_mod = sys.modules.setdefault("ldclient", types.ModuleType("ldclient"))
ld_mod.LDClient = object
prom_mod = sys.modules.setdefault(
    "prometheus_client", types.ModuleType("prometheus_client")
)
prom_mod.CONTENT_TYPE_LATEST = ""
prom_mod.Counter = lambda *a, **k: types.SimpleNamespace(
    labels=lambda *_, **__: types.SimpleNamespace(inc=lambda *_, **__: None)
)
prom_mod.Histogram = lambda *a, **k: types.SimpleNamespace(
    labels=lambda *_, **__: types.SimpleNamespace(observe=lambda *_, **__: None)
)
prom_mod.generate_latest = lambda *a, **k: b""
sys.modules.setdefault("pgvector.sqlalchemy", types.ModuleType("pgvector.sqlalchemy"))
sys.modules["pgvector.sqlalchemy"].Vector = object
warnings.filterwarnings("ignore", category=UserWarning)


class DummyClient:
    """Collect upload calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def upload_file(self, src: str, bucket: str, obj: str) -> None:
        self.calls.append((src, bucket, obj))


class DummyGenerator:
    """Write a dummy file and return its path."""

    def __init__(self) -> None:
        self.cleaned = False

    def generate(self, prompt: str, output: str, num_inference_steps: int = 30):
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
    monkeypatch.setattr(tasks, "_get_storage_client", lambda: DummyClient())
    monkeypatch.setattr(tasks, "remove_background", lambda img: img)
    monkeypatch.setattr(tasks, "convert_to_cmyk", lambda img: img)
    monkeypatch.setattr(tasks, "ensure_not_nsfw", lambda img: None)
    monkeypatch.setattr(tasks, "validate_dpi_image", lambda img: True)
    monkeypatch.setattr(tasks, "validate_color_space", lambda img: True)
    monkeypatch.setattr(
        tasks.model_repository, "save_generated_mockup", lambda *a, **k: 1
    )
    tasks.settings.s3_bucket = "b"
    tasks.settings.s3_endpoint = "http://test"  # type: ignore

    res = tasks.generate_mockup.run([["kw"]], str(tmp_path))
    assert res[0]["uri"].startswith("http://test/b/generated-mockups/mockup_0.png")
    assert gen.cleaned
