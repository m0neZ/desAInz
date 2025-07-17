#!/usr/bin/env python3
"""Generate OpenAPI specs for microservices."""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

SERVICES = {
    "analytics": {"module": "backend.analytics.api", "app": "app"},
    "optimization": {"module": "backend.optimization.api", "app": "app"},
    "signal-ingestion": {
        "module": "signal_ingestion.main",
        "app": "app",
        "path": PROJECT_ROOT / "backend" / "signal-ingestion" / "src",
    },
    "marketplace-publisher": {
        "module": "marketplace_publisher.main",
        "app": "app",
        "path": PROJECT_ROOT / "backend" / "marketplace-publisher" / "src",
    },
    "monitoring": {
        "module": "monitoring.main",
        "app": "app",
        "path": PROJECT_ROOT / "backend" / "monitoring" / "src",
    },
    "api-gateway": {
        "module": "api_gateway.main",
        "app": "app",
        "path": PROJECT_ROOT / "backend" / "api-gateway" / "src",
    },
}

OPENAPI_DIR = PROJECT_ROOT / "openapi"
OPENAPI_DIR.mkdir(exist_ok=True)

for name, spec in SERVICES.items():
    extra_path = spec.get("path")
    if extra_path:
        sys.path.insert(0, str(extra_path))
    module_name = spec["module"]
    if module_name == "main":
        module_path = extra_path / "main.py" if extra_path else Path("main.py")
        spec_obj = importlib.util.spec_from_file_location(
            "service_template_main", module_path
        )
        module = importlib.util.module_from_spec(spec_obj)
        assert spec_obj.loader is not None
        spec_obj.loader.exec_module(module)
    else:
        module = importlib.import_module(module_name)
    app = getattr(module, spec["app"])
    if hasattr(app, "openapi"):
        data = app.openapi()
    else:
        continue
    path = OPENAPI_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

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
    },
    "components": {
        "schemas": {
            "WeightsUpdate": WeightsUpdate.model_json_schema(),
            "ScoreRequest": ScoreRequest.model_json_schema(),
        }
    },
}
(OPENAPI_DIR / "scoring-engine.json").write_text(
    json.dumps(spec, indent=2), encoding="utf-8"
)
