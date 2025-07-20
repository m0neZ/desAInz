"""Root-level pytest configuration."""

from tests.conftest import *  # noqa: F401,F403
import warnings
import os
from types import SimpleNamespace
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy

os.makedirs("/run/secrets", exist_ok=True)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("DATABASE_URL", "sqlite:///shared.db")
redis.Redis.from_url = lambda *a, **k: SimpleNamespace()

# Patch SQLAlchemy to handle ``AnyUrl`` instances from ``pydantic``.
_real_create_engine = sqlalchemy.create_engine
sqlalchemy.create_engine = lambda url, *a, **k: _real_create_engine(str(url), *a, **k)

import backend.shared.db as shared_db

shared_db.engine = create_engine("sqlite:///shared.db", echo=False, future=True)
shared_db.SessionLocal = sessionmaker(
    bind=shared_db.engine, autoflush=False, autocommit=False, future=True
)

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message='directory "/run/secrets" does not exist',
)
