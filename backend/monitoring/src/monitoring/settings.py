"""Application settings for the monitoring service."""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    app_name: str = "monitoring"
    log_file: str = "app.log"
    sla_threshold_hours: float = 2.0
    SLA_THRESHOLD_HOURS: float = 2.0
    enable_pagerduty: bool = True
    ENABLE_PAGERDUTY: bool = True
    sla_alert_cooldown_minutes: int = 60
    SLA_ALERT_COOLDOWN_MINUTES: int = 60

    @field_validator("sla_threshold_hours")
    @classmethod
    def _positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("must be positive")
        return value

    @field_validator("sla_alert_cooldown_minutes")
    @classmethod
    def _cooldown_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be positive")
        return value


Settings.model_rebuild()
settings: Settings = Settings()
