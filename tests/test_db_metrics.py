"""Verify Prometheus gauges for database pool usage."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from backend.shared.db import DB_POOL_IN_USE, DB_POOL_SIZE, register_pool_metrics


def test_pool_metrics_change() -> None:
    """Connection metrics should reflect acquired sessions."""
    engine = create_engine("sqlite:///:memory:", poolclass=QueuePool)
    SessionLocal = sessionmaker(bind=engine, future=True)
    register_pool_metrics(engine)

    start_in_use = DB_POOL_IN_USE._value.get()
    size = (
        engine.pool.size()
        if callable(getattr(engine.pool, "size", None))
        else engine.pool.size
    )
    assert DB_POOL_SIZE._value.get() == size

    with SessionLocal() as session:
        session.execute(text("SELECT 1"))
        assert DB_POOL_IN_USE._value.get() == start_in_use + 1
