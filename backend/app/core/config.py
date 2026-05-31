from __future__ import annotations

from decimal import Decimal
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven application settings."""

    app_env: str = Field(default="local")
    app_name: str = Field(default="AI Agent Control Plane")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")

    database_url: str = Field(
        default="postgresql+psycopg://agentops:agentops@localhost:5432/agentops"
    )

    redis_url: str = Field(default="redis://localhost:6379/0")
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/1")

    prometheus_metrics_enabled: bool = Field(default=False)
    otel_service_name: str = Field(default="ai-agent-control-plane-api")
    deployment_min_success_rate: Decimal = Field(default=Decimal("0.95"))

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings for process lifetime."""
    return Settings()
