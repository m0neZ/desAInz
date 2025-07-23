"""Tests for CDN cache invalidation after publishing."""

import subprocess
from pathlib import Path
import sys
from types import ModuleType

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

pytestmark = pytest.mark.filterwarnings(
    r"ignore:datetime\.datetime\.utcnow\(\) is deprecated"
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend" / "marketplace-publisher" / "src"))  # noqa: E402
sys.path.append(str(ROOT))  # noqa: E402
sys.path.append(str(ROOT / "backend" / "mockup-generation"))  # noqa: E402

selenium = ModuleType("selenium")
webdriver_mod = ModuleType("selenium.webdriver")
firefox_mod = ModuleType("selenium.webdriver.firefox")
options_mod = ModuleType("selenium.webdriver.firefox.options")


class DummyOptions:
    """Stub Firefox options."""

    def add_argument(self, *_args: object) -> None:
        """Accept and ignore command line arguments."""
        pass


webdriver_mod.Firefox = lambda *a, **k: None
options_mod.Options = DummyOptions
selenium.webdriver = webdriver_mod
sys.modules.setdefault("selenium", selenium)
sys.modules.setdefault("selenium.webdriver", webdriver_mod)
sys.modules.setdefault("selenium.webdriver.firefox", firefox_mod)
sys.modules.setdefault("selenium.webdriver.firefox.options", options_mod)

from backend.shared.config import settings as shared_settings


class DummyClient:
    """Minimal client returning a fake listing ID."""

    def publish_design(self, design_path: Path, metadata: dict[str, object]) -> str:
        return "1"


@pytest.mark.asyncio()
async def test_cache_invalidation_called(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Invalidate caches when CDN is configured."""

    from marketplace_publisher import db

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    await db.init_db()
    monkeypatch.setattr(db, "get_oauth_token_sync", lambda *_a, **_k: None)
    monkeypatch.setattr(db, "upsert_oauth_token_sync", lambda *_a, **_k: None)
    from marketplace_publisher import publisher

    monkeypatch.setattr(publisher.rules, "validate_mockup", lambda *a, **k: None)

    publisher.CLIENTS[db.Marketplace.redbubble] = DummyClient()  # type: ignore[assignment]
    monkeypatch.setattr(publisher, "is_trademarked", lambda *_a, **_k: False)
    monkeypatch.setattr(publisher, "ensure_not_nsfw", lambda _i: None)

    called: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool = True) -> None:
        called.append(cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(shared_settings, "cdn_distribution_id", "DIST")

    design = tmp_path / "img.png"
    from PIL import Image

    Image.new("RGB", (1, 1)).save(design)

    async with session_factory() as session:
        task = await db.create_task(
            session,
            marketplace=db.Marketplace.redbubble,
            design_path=str(design),
        )
        result = await publisher.publish_with_retry(
            session,
            task.id,
            db.Marketplace.redbubble,
            design,
            {},
            max_attempts=1,
        )

    assert result == "1"
    assert called
    assert "invalidate_cache.sh" in called[0][0]


@pytest.mark.asyncio()
async def test_no_cache_invalidation_without_distribution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Do not invalidate caches when CDN is not configured."""

    from marketplace_publisher import db

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_factory)
    await db.init_db()
    monkeypatch.setattr(db, "get_oauth_token_sync", lambda *_a, **_k: None)
    monkeypatch.setattr(db, "upsert_oauth_token_sync", lambda *_a, **_k: None)
    from marketplace_publisher import publisher

    monkeypatch.setattr(publisher.rules, "validate_mockup", lambda *a, **k: None)

    publisher.CLIENTS[db.Marketplace.redbubble] = DummyClient()  # type: ignore[assignment]
    monkeypatch.setattr(publisher, "is_trademarked", lambda *_a, **_k: False)
    monkeypatch.setattr(publisher, "ensure_not_nsfw", lambda _i: None)

    called: list[list[str]] = []

    def fake_run(cmd: list[str], check: bool = True) -> None:
        called.append(cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(shared_settings, "cdn_distribution_id", None)

    design = tmp_path / "img.png"
    from PIL import Image

    Image.new("RGB", (1, 1)).save(design)

    async with session_factory() as session:
        task = await db.create_task(
            session,
            marketplace=db.Marketplace.redbubble,
            design_path=str(design),
        )
        result = await publisher.publish_with_retry(
            session,
            task.id,
            db.Marketplace.redbubble,
            design,
            {},
            max_attempts=1,
        )

    assert result == "1"
    assert called == []
