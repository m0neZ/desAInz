"""Application settings loaded from environment variables."""

from __future__ import annotations

from pydantic import HttpUrl, ValidationError, field_validator, TypeAdapter
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore[misc]
    """Store configuration derived from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", secrets_dir="/run/secrets")

    app_name: str = "signal-ingestion"
    log_level: str = "INFO"
    signal_retention_days: int = 90
    dedup_ttl: int = 86_400
    ingest_interval_minutes: int = 60
    ingest_cron: str | None = None
    http_proxies: HttpUrl | None = None
    adapter_rate_limit: dict[str, int] = {}
    default_adapter_rate_limit: int = 5
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
    celery_broker_url: str = "redis://localhost:6379/0"
    nostalgia_query: str = 'subject:"nostalgia"'
    nostalgia_fetch_limit: int = 1
    events_country_code: str = "US"
    events_fetch_limit: int = 1

    @field_validator("adapter_rate_limit", mode="before")  # type: ignore[misc]
    @classmethod
    def _parse_limits(cls, value: str | dict[str, int] | None) -> dict[str, int]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        value = str(value).strip()
        if not value:
            return {}
        if value.isdigit():
            return {"default": int(value)}
        limits: dict[str, int] = {}
        for part in value.split(","):
            if ":" not in part:
                continue
            name, num = part.split(":", 1)
            limits[name.strip()] = int(num)
        return limits

    @field_validator(  # type: ignore[misc]
        "dedup_ttl",
        "ingest_interval_minutes",
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
            return value
        if isinstance(value, list) or value is None:
            return value
        if value <= 0:
            raise ValueError("must be positive")
        return value

    @field_validator("enabled_adapters", mode="before")  # type: ignore[misc]
    @classmethod
    def _split_adapters(cls, value: str | list[str] | None) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        value = value.strip()
        if not value:
            return []
        return [v.strip() for v in value.split(",") if v.strip()]

    @field_validator("ingest_cron", mode="before")  # type: ignore[misc]
    @classmethod
    def _empty_to_none(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value

    @field_validator(
        "instagram_token",
        "instagram_user_id",
        "youtube_api_key",
        mode="before",
    )
    @classmethod
    def _non_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("tiktok_video_urls")
    @classmethod
    def _valid_urls(cls, value: str | None) -> str | None:
        if value is None:
            return None
        urls = [v.strip() for v in value.split(",") if v.strip()]
        try:
            TypeAdapter(list[HttpUrl]).validate_python(urls)
        except ValidationError as exc:  # pragma: no cover - unreachable
            raise ValueError("invalid URL") from exc
        return ",".join(urls)

    def adapter_limit(self, name: str) -> int:
        """Return request limit for ``name`` or the default."""
        return self.adapter_rate_limit.get(
            name,
            self.adapter_rate_limit.get("default", self.default_adapter_rate_limit),
        )


Settings.model_rebuild()
settings: Settings = Settings()
