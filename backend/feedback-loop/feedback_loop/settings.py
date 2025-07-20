"""Feedback loop configuration loaded from environment variables."""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Store configuration for scheduler intervals."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    publisher_metrics_interval_minutes: int = 60
    weight_update_interval_minutes: int = 1440

    @field_validator(
        "publisher_metrics_interval_minutes",
        "weight_update_interval_minutes",
    )
    @classmethod
    def _positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be positive")
        return value


Settings.model_rebuild()
settings: Settings = Settings()
