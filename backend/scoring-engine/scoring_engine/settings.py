"""Configuration for the scoring engine service."""

from __future__ import annotations

from pydantic import RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Expose configuration derived from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", secrets_dir="/run/secrets"
    )

    service_name: str = "scoring-engine"
    embed_batch_size: int = 50
    kafka_skip: bool = False
    celery_broker_url: RedisDsn = RedisDsn("redis://localhost:6379/0")

    @field_validator("embed_batch_size")  # type: ignore[misc]
    @classmethod
    def _positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("embed_batch_size must be positive")
        return value


Settings.model_rebuild()
settings: Settings = Settings()
