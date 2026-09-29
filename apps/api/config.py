"""
RepoMedic — Application Configuration

All settings are loaded from environment variables.
Never hard-code credentials here.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class Settings(BaseSettings):
    """
    Central settings object. All values come from environment variables.
    See .env.example for the full list.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: SecretStr = Field(default="change-me")
    app_url: str = "http://localhost:8000"

    @property
    def is_development(self) -> bool:
        return self.app_env == AppEnvironment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnvironment.PRODUCTION

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://repomedic:repomedic@localhost:5432/repomedic"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # -------------------------------------------------------------------------
    # Redis / Celery
    # -------------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # -------------------------------------------------------------------------
    # GitHub App
    # -------------------------------------------------------------------------
    github_app_id: str = ""
    github_app_name: str = "repomedic"
    github_private_key: str = ""
    github_private_key_path: str = ""
    github_webhook_secret: SecretStr = Field(default="")
    github_client_id: str = ""
    github_client_secret: SecretStr = Field(default="")

    @property
    def github_private_key_resolved(self) -> str:
        """Return the private key, loading from file path if needed."""
        if self.github_private_key:
            # Support base64-encoded or raw PEM
            key = self.github_private_key
            if not key.startswith("-----"):
                import base64
                key = base64.b64decode(key).decode("utf-8")
            return key
        if self.github_private_key_path:
            return Path(self.github_private_key_path).read_text()
        return ""

    # -------------------------------------------------------------------------
    # Nebius Token Factory — LLM
    # -------------------------------------------------------------------------
    nebius_api_key: SecretStr = Field(default="")
    nebius_base_url: str = "https://api.studio.nebius.ai/v1"
    nebius_embedding_model: str = "BAAI/bge-en-icl"

    # Model slots — configurable, never hard-coded in agent nodes
    nemotron_planner_model: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    nemotron_coder_model: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    nemotron_fast_model: str = "nvidia/llama-3.1-nemotron-8b-instruct"

    # -------------------------------------------------------------------------
    # Nebius Token Factory — Sandbox
    # -------------------------------------------------------------------------
    nebius_sandbox_url: str = ""
    nebius_sandbox_api_key: SecretStr = Field(default="")
    nebius_sandbox_timeout: int = 300
    nebius_sandbox_max_log_bytes: int = 51200  # 50KB

    # -------------------------------------------------------------------------
    # Tavily
    # -------------------------------------------------------------------------
    tavily_api_key: SecretStr = Field(default="")

    # -------------------------------------------------------------------------
    # Agent
    # -------------------------------------------------------------------------
    max_fix_iterations: int = 3
    max_context_tokens: int = 32000
    sandbox_timeout_seconds: int = 300

    # -------------------------------------------------------------------------
    # Frontend
    # -------------------------------------------------------------------------
    next_public_api_url: str = "http://localhost:8000"
    next_public_app_url: str = "http://localhost:3000"

    # -------------------------------------------------------------------------
    # Observability
    # -------------------------------------------------------------------------
    log_level: str = "INFO"
    otel_service_name: str = "repomedic-api"
    otel_exporter_otlp_endpoint: str = ""

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return upper


# Singleton settings instance
settings = Settings()
