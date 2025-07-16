#!/usr/bin/env python
"""Export OpenAPI schemas for all FastAPI microservices."""

from __future__ import annotations

import importlib
import json
import sys
from types import SimpleNamespace
from pathlib import Path

SERVICES: dict[str, dict[str, str]] = {
    "api-gateway": {
        "path": "backend/api-gateway/src",
        "module": "api_gateway.main",
        "app": "app",
    },
    "monitoring": {
        "path": "backend/monitoring/src",
        "module": "monitoring.main",
        "app": "app",
    },
    "signal-ingestion": {
        "path": "backend/signal-ingestion/src",
        "module": "signal_ingestion.main",
        "app": "app",
    },
    "optimization": {
        "path": "backend",
        "module": "optimization.api",
        "app": "app",
    },
}

OUTPUT_DIR = Path("docs/openapi")


def main() -> None:
    """Generate OpenAPI JSON files for all services."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    root_path = Path(__file__).resolve().parents[1]
    try:
        import kafka  # type: ignore

        kafka.KafkaProducer = lambda *a, **k: SimpleNamespace(
            send=lambda *a, **k: None,
            flush=lambda: None,
        )
    except Exception:
        pass
    driver_stub = SimpleNamespace(
        get=lambda *a, **k: None,
        find_element=lambda *a, **k: SimpleNamespace(
            send_keys=lambda *a, **k: None,
            click=lambda *a, **k: None,
        ),
        quit=lambda: None,
    )
    sys.modules.setdefault(
        "selenium",
        SimpleNamespace(
            webdriver=SimpleNamespace(
                Firefox=lambda *a, **k: driver_stub,
            )
        ),
    )
    sys.modules.setdefault(
        "selenium.webdriver", SimpleNamespace(Firefox=lambda *a, **k: driver_stub)
    )
    sys.modules.setdefault(
        "selenium.webdriver.firefox.options",
        SimpleNamespace(
            Options=lambda: SimpleNamespace(add_argument=lambda *a, **k: None)
        ),
    )
    for name, cfg in SERVICES.items():
        service_path = (root_path / cfg["path"]).resolve()
        sys.path.insert(0, str(service_path))
        sys.path.insert(0, str(root_path))
        module = importlib.import_module(cfg["module"])
        app = getattr(module, cfg["app"])
        schema = app.openapi()
        out_file = OUTPUT_DIR / f"{name}.json"
        out_file.write_text(json.dumps(schema, indent=2))
        sys.path.pop(0)
        sys.path.pop(0)


if __name__ == "__main__":  # pragma: no cover
    main()
