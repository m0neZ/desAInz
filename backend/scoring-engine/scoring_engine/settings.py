"""Configuration for the scoring engine service."""

from __future__ import annotations

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Store configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    service_name: str = "scoring-engine"
    celery_broker_url: AnyUrl = AnyUrl("redis://localhost:6379/0")
    embed_batch_size: int = 50
    kafka_skip: bool = False


Settings.model_rebuild()
settings = Settings()
