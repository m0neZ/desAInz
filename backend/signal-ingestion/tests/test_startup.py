"""Tests for service startup logic."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.asyncio()
async def test_dedup_initialized_on_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify deduplication cache is initialized on service startup."""
    sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

    sys.modules.setdefault(
        "pgvector.sqlalchemy", SimpleNamespace(Vector=lambda *a, **k: None)
    )
    sys.modules.setdefault(
        "signal_ingestion.database",
        SimpleNamespace(
            get_session=lambda: None, init_db=lambda: None, SessionLocal=lambda: None
        ),
    )
    sys.modules.setdefault(
        "signal_ingestion.models", SimpleNamespace(Base=object, Signal=object)
    )
    sys.modules.setdefault(
        "celery",
        SimpleNamespace(Celery=lambda *a, **k: SimpleNamespace(conf=SimpleNamespace())),
    )
    scheduler = SimpleNamespace(start=lambda: None, shutdown=lambda: None)
    sys.modules.setdefault(
        "signal_ingestion.scheduler",
        SimpleNamespace(create_scheduler=lambda: scheduler),
    )
    sys.modules.setdefault(
        "signal_ingestion.ingestion", SimpleNamespace(ingest=lambda *a, **k: None)
    )
    sys.modules.setdefault("signal_ingestion.tasks", SimpleNamespace())
    sys.modules.setdefault(
        "signal_ingestion.publisher", SimpleNamespace(publish=lambda *a, **k: None)
    )

    called = False

    def fake_init(*_args: object) -> None:
        nonlocal called
        called = True

    sys.modules["signal_ingestion.dedup"] = SimpleNamespace(
        add_key=lambda *a, **k: None,
        is_duplicate=lambda *a, **k: False,
        initialize=fake_init,
    )

    sys.modules.setdefault(
        "backend.shared.kafka.schema_registry",
        SimpleNamespace(SchemaRegistryClient=lambda *a, **k: None),
    )
    sys.modules.setdefault(
        "kafka",
        SimpleNamespace(
            KafkaProducer=lambda *a, **k: SimpleNamespace(
                send=lambda *a, **k: None, flush=lambda: None
            ),
            KafkaConsumer=object,
        ),
    )
    sys.modules.setdefault(
        "backend.shared.db",
        SimpleNamespace(run_migrations_if_needed=lambda *_a, **_k: None),
    )

    from signal_ingestion import main as main_module

    await main_module.startup()

    assert called
