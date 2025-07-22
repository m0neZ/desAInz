"""Configuration for the mockup generation service."""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import RedisDsn, field_validator


class Settings(BaseSettings):  # type: ignore[misc]
    """Expose API keys and provider selection."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", secrets_dir="/run/secrets"
    )

    stability_ai_api_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-4"
    claude_api_key: str | None = None
    service_name: str = "mockup-generation"
    fallback_provider: Literal["stability", "openai"] = "stability"
    use_comfyui: bool = False
    comfyui_url: str = "http://localhost:8188"

    # Runtime and Celery configuration
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")
    gpu_slots: int = 1
    gpu_lock_timeout: int = 600
    gpu_queue_prefix: str = "gpu"
    gpu_worker_index: int = -1
    gpu_autoscale_factor: int = 2
    celery_broker: Literal["redis", "rabbitmq", "kafka"] = "redis"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    redis_host: str = "localhost"
    redis_port: str = "6379"
    redis_db: str = "0"
    rabbitmq_host: str = "localhost"
    rabbitmq_port: str = "5672"
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    kafka_bootstrap_servers: str = "localhost:9092"

    @field_validator("fallback_provider")  # type: ignore[misc]
    @classmethod
    def _valid_provider(cls, value: str) -> str:
        if value not in {"stability", "openai"}:
            raise ValueError("invalid provider")
        return value


Settings.model_rebuild()
settings: Settings = Settings()
