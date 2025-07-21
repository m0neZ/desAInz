#!/usr/bin/env python3
"""Generate OpenAPI specs for microservices."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import hashlib
import re
from pathlib import Path
from typing import Iterable

from openapi_schema_validator import OAS30Validator

import types

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("KAFKA_SKIP", "1")
os.environ.setdefault("SELENIUM_SKIP", "1")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///openapi.db")
os.environ.setdefault("ABTEST_DB_URL", "sqlite:///abtest.db")
os.environ.setdefault("METRICS_DB_URL", "sqlite:///metrics.db")
os.environ.setdefault("OTEL_SDK_DISABLED", "1")

DOCS_OPENAPI_DIR = PROJECT_ROOT / "docs" / "openapi"
DOCS_INDEX = PROJECT_ROOT / "docs" / "openapi_specs.rst"


def discover_main_files(base: Path) -> Iterable[Path]:
    """Yield all FastAPI ``main.py`` files."""
    return base.glob("backend/*/**/main.py")


def ensure_doc(service: str) -> None:
    """Create minimal RST page for ``service`` if missing."""
    DOCS_OPENAPI_DIR.mkdir(exist_ok=True)
    doc_path = DOCS_OPENAPI_DIR / f"{service}.rst"
    if not doc_path.exists():
        title = f"{service.replace('-', ' ').title()} API"
        doc_path.write_text(
            f"{title}\n{'=' * len(title)}\n\n.. openapi:: ../../openapi/{service}.json\n   :encoding: utf-8\n",
            encoding="utf-8",
        )

    if DOCS_INDEX.exists():
        lines = DOCS_INDEX.read_text(encoding="utf-8").splitlines()
    else:
        lines = [
            "OpenAPI Specifications",
            "======================",
            "",
            ".. toctree::",
            "   :maxdepth: 1",
            "",
        ]

    entry = f"   openapi/{service}"
    if entry not in lines:
        lines.append(entry)
        DOCS_INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")


OPENAPI_DIR = PROJECT_ROOT / "openapi"
OPENAPI_DIR.mkdir(exist_ok=True)


def _write_spec(service: str, data: dict) -> None:
    """Write ``data`` to ``service`` JSON file with version hash."""
    stripped = dict(data)
    stripped.pop("x-spec-version", None)
    serialized = json.dumps(stripped, sort_keys=True).encode("utf-8")
    spec_hash = hashlib.sha256(serialized).hexdigest()
    data["x-spec-version"] = spec_hash
    path = OPENAPI_DIR / f"{service}.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _patch_shared_dependencies() -> None:
    """Stub modules that require external services."""
    currency = types.ModuleType("backend.shared.currency")

    def _convert_price(amount: float, currency: str) -> float:
        return amount

    def _start_rate_updater() -> None:  # pragma: no cover - stub
        return None

    setattr(currency, "convert_price", _convert_price)
    setattr(currency, "start_rate_updater", _start_rate_updater)
    sys.modules.setdefault("backend.shared.currency", currency)


def generate_from_file(main_file: Path) -> None:
    """Load FastAPI ``app`` from ``main_file`` and write its spec."""
    service = main_file.parts[1]
    service_root = PROJECT_ROOT / "backend" / service
    src_dir = service_root / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
    else:
        sys.path.insert(0, str(service_root))

    package_dir = main_file.parent
    package = package_dir.name if (package_dir / "__init__.py").exists() else ""
    module_name = f"{package}.main" if package else "main"
    spec_obj = importlib.util.spec_from_file_location(module_name, main_file)
    assert spec_obj is not None
    module = importlib.util.module_from_spec(spec_obj)
    if package and package not in sys.modules:
        pkg_spec = importlib.machinery.ModuleSpec(package, loader=None)
        pkg = importlib.util.module_from_spec(pkg_spec)
        pkg.__path__ = [str(package_dir)]
        sys.modules[package] = pkg
    sys.modules[module_name] = module
    _patch_shared_dependencies()
    assert spec_obj.loader is not None
    spec_obj.loader.exec_module(module)
    app = getattr(module, "app", None)
    if not app or not hasattr(app, "openapi"):
        return
    data = app.openapi()
    OAS30Validator.check_schema(data)
    _write_spec(service, data)
    ensure_doc(service)


for main_file in discover_main_files(PROJECT_ROOT):
    generate_from_file(main_file)

# scoring-engine manual spec
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "scoring-engine"))
try:
    from scoring_engine.app import ScoreRequest, WeightsUpdate
except Exception as exc:  # pragma: no cover - runtime import guard
    raise SystemExit(f"Failed importing scoring_engine: {exc}")

spec = {
    "openapi": "3.0.2",
    "info": {"title": "Scoring Engine", "version": "1.0.0"},
    "paths": {
        "/weights": {
            "get": {"responses": {"200": {"description": "OK"}}},
            "put": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/WeightsUpdate"}
                        }
                    },
                    "required": True,
                },
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/weights/feedback": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/WeightsUpdate"}
                        }
                    },
                    "required": True,
                },
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/score": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ScoreRequest"}
                        }
                    },
                    "required": True,
                },
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/centroid/{source}": {
            "get": {
                "parameters": [
                    {
                        "name": "source",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/health": {"get": {"responses": {"200": {"description": "OK"}}}},
        "/ready": {"get": {"responses": {"200": {"description": "Ready"}}}},
        "/metrics": {"get": {"responses": {"200": {"description": "OK"}}}},
    },
    "components": {
        "schemas": {
            "WeightsUpdate": WeightsUpdate.model_json_schema(),
            "ScoreRequest": ScoreRequest.model_json_schema(),
        }
    },
}
_write_spec("scoring-engine", spec)
OAS30Validator.check_schema(spec)
ensure_doc("scoring-engine")


def _parse_ts_type(type_str: str) -> dict:
    """Return JSON schema for basic TypeScript ``type_str``."""
    type_str = type_str.strip()
    if type_str.endswith("[]"):
        return {"type": "array", "items": _parse_ts_type(type_str[:-2])}
    if type_str in {"string", "number", "boolean"}:
        return {"type": type_str}
    if type_str == "void":
        return {"type": "null"}
    if type_str.startswith("{") and type_str.endswith("}"):
        props: dict[str, dict] = {}
        required: list[str] = []
        body = type_str[1:-1].strip()
        for m in re.finditer(r"(\w+): ([^;]+);", body):
            name, t = m.groups()
            props[name] = _parse_ts_type(t)
            required.append(name)
        return {"type": "object", "properties": props, "required": required}
    return {"$ref": f"#/components/schemas/{type_str}"}


def parse_trpc(path: Path) -> dict[str, dict]:
    """Parse interfaces from the tRPC TypeScript definitions."""
    text = path.read_text(encoding="utf-8")
    schemas: dict[str, dict] = {}
    for name, body in re.findall(r"export interface (\w+) \{([^}]*)\}", text, re.DOTALL):
        if name == "AppRouter":
            continue
        props: dict[str, dict] = {}
        required: list[str] = []
        for prop, typ in re.findall(r"(\w+): ([^;]+);", body):
            props[prop] = _parse_ts_type(typ)
            required.append(prop)
        schemas[name] = {"type": "object", "properties": props, "required": required, "title": name}
    return schemas


trpc_file = PROJECT_ROOT / "frontend" / "admin-dashboard" / "src" / "trpc.ts"
if trpc_file.exists():
    trpc_schemas = parse_trpc(trpc_file)
    api_spec_path = OPENAPI_DIR / "api-gateway.json"
    api_spec = json.loads(api_spec_path.read_text(encoding="utf-8"))
    api_spec.setdefault("components", {}).setdefault("schemas", {}).update(trpc_schemas)
    _write_spec("api-gateway", api_spec)
