"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings for the service."""

    model_config = SettingsConfigDict(env_prefix="LLM_EAAS_", env_file=".env", extra="ignore")

    app_name: str = "LLM Evaluation-as-a-Service"
    environment: str = "local"
    allowed_origins: list[str] = ["http://localhost:3000"]

    database_url: str = Field(..., description="Async SQLAlchemy database URL")

    # LLM Provider Settings
    llm_provider: str = Field(default="ollama", description="LLM provider: 'openai' or 'ollama'")
    llm_model: str = Field(default="llama3.2", description="Model name to use")
    llm_base_url: Optional[str] = Field(default=None, description="Base URL for LLM API (for Ollama: http://localhost:11434/v1)")
    llm_api_key: str = Field(default="not-needed", description="API key (not needed for Ollama)")
    llm_timeout_seconds: int = 60
    
    # Legacy OpenAI settings for backward compatibility
    openai_api_key: str = Field(default="not-needed", description="OpenAI API key (deprecated, use llm_api_key)")
    openai_model: str = Field(default="gpt-4-mini", description="OpenAI model (deprecated, use llm_model)")
    openai_timeout_seconds: int = 60

    baseline_experiment_id: Optional[str] = None
    regression_threshold: float = 0.05
    max_judge_retries: int = 2
    judge_temperature_default: float = 0.2


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
