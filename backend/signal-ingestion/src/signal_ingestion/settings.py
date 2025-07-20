"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore[misc]
    """Store configuration derived from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", secrets_dir="/run/secrets"
    )

    app_name: str = "signal-ingestion"
    log_level: str = "INFO"
    signal_retention_days: int = 90
    dedup_error_rate: float = 0.01
    dedup_capacity: int = 100_000
    dedup_ttl: int = 86_400
    ingest_interval_minutes: int = 60
    ingest_cron_schedule: str | None = None
    http_proxies: HttpUrl | None = None
    adapter_rate_limit: int = 5
    enabled_adapters: list[str] | None = None
    instagram_token: str | None = None
    instagram_user_id: str | None = None
    instagram_fetch_limit: int = 1
    reddit_user_agent: str = "signal-bot"
    reddit_fetch_limit: int = 1
    youtube_api_key: str | None = None
    youtube_fetch_limit: int = 1
    tiktok_video_urls: str | None = None
    tiktok_fetch_limit: int = 1
    nostalgia_query: str = 'subject:"nostalgia"'
    nostalgia_fetch_limit: int = 1
    events_country_code: str = "US"
    events_fetch_limit: int = 1

    @field_validator("ingest_cron_schedule", mode="before")  # type: ignore[misc]
    @classmethod
    def _empty_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator(  # type: ignore[misc]
        "dedup_error_rate",
        "dedup_capacity",
        "dedup_ttl",
        "ingest_interval_minutes",
        "adapter_rate_limit",
        "instagram_fetch_limit",
        "reddit_fetch_limit",
        "youtube_fetch_limit",
        "tiktok_fetch_limit",
        "nostalgia_fetch_limit",
        "events_fetch_limit",
        "enabled_adapters",
    )
    @classmethod
    def _positive(
        cls, value: float | int | list[str] | None
    ) -> float | int | list[str] | None:
        if isinstance(value, float):
            if not 0 <= value <= 1:
                raise ValueError("dedup_error_rate must be in [0,1]")
            return value
        if isinstance(value, list) or value is None:
            return value
        if value <= 0:
            raise ValueError("must be positive")
        return value

    @field_validator("enabled_adapters", mode="before")  # type: ignore[misc]
    @classmethod
    def _split_adapters(
        cls, value: str | list[str] | None
    ) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        value = value.strip()
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]


Settings.model_rebuild()
settings: Settings = Settings()
