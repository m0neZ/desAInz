"""Root-level pytest configuration."""

from tests.conftest import *  # noqa: F401,F403
import warnings
import os
from types import ModuleType, SimpleNamespace
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy
import sys

sys.modules.setdefault(
    "selenium",
    SimpleNamespace(
        webdriver=SimpleNamespace(
            Firefox=lambda *a, **k: SimpleNamespace(get=lambda *a, **k: None)
        )
    ),
)

sys.modules.setdefault(
    "selenium.webdriver",
    SimpleNamespace(Firefox=lambda *a, **k: SimpleNamespace(get=lambda *a, **k: None)),
)

sys.modules.setdefault(
    "opentelemetry.exporter.otlp.proto.grpc.trace_exporter",
    SimpleNamespace(OTLPSpanExporter=object),
)
sys.modules.setdefault(
    "opentelemetry.exporter.otlp.proto.http.trace_exporter",
    SimpleNamespace(OTLPSpanExporter=object),
)
sys.modules.setdefault(
    "opentelemetry.instrumentation.fastapi",
    SimpleNamespace(
        FastAPIInstrumentor=SimpleNamespace(instrument_app=lambda *a, **k: None)
    ),
)
sys.modules.setdefault(
    "opentelemetry.instrumentation.flask",
    SimpleNamespace(
        FlaskInstrumentor=lambda: SimpleNamespace(instrument_app=lambda *a, **k: None)
    ),
)
sys.modules.setdefault(
    "opentelemetry.sdk.trace.export",
    SimpleNamespace(BatchSpanProcessor=object),
)
sys.modules.setdefault(
    "opentelemetry.sdk.trace",
    SimpleNamespace(TracerProvider=object),
)
sys.modules.setdefault(
    "opentelemetry.sdk.resources",
    SimpleNamespace(Resource=SimpleNamespace(create=lambda *a, **k: None)),
)
sys.modules.setdefault(
    "opentelemetry.trace",
    SimpleNamespace(set_tracer_provider=lambda *a, **k: None),
)

# Stub LaunchDarkly client to avoid heavy dependency.
ld_mod = sys.modules.setdefault("ldclient", ModuleType("ldclient"))
ld_mod.LDClient = object
config_mod = ModuleType("ldclient.config")
config_mod.Config = object
context_mod = ModuleType("ldclient.context")
context_mod.Context = object
sys.modules.setdefault("ldclient.config", config_mod)
sys.modules.setdefault("ldclient.context", context_mod)

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
