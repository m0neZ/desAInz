"""Register JSON schemas with the schema registry."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
from typing import Iterable

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "backend"
    / "shared"
    / "kafka"
    / "schema_registry.py"
)
spec = importlib.util.spec_from_file_location("schema_registry", MODULE_PATH)
assert spec is not None
schema_registry = importlib.util.module_from_spec(spec)
sys.modules["schema_registry"] = schema_registry
assert spec.loader
spec.loader.exec_module(schema_registry)
SchemaRegistryClient = schema_registry.SchemaRegistryClient


SCHEMAS_DIR = pathlib.Path(__file__).resolve().parent.parent / "schemas"


class Settings(BaseSettings):
    """Schema registry configuration."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    registry_url: HttpUrl = HttpUrl("http://schema-registry:8081")
    registry_token: SecretStr | None = None


settings = Settings()


_CLIENT = SchemaRegistryClient(
    str(settings.registry_url),
    token=(
        settings.registry_token.get_secret_value() if settings.registry_token else None
    ),
)


def _register(schema_path: pathlib.Path) -> None:
    subject = schema_path.stem
    schema = json.loads(schema_path.read_text())
    _CLIENT.register(subject, schema)


def register_all() -> None:
    """Register every schema in the schemas directory."""
    for path in SCHEMAS_DIR.glob("*.json"):
        _register(path)


if __name__ == "__main__":
    register_all()
