"""Centralized, typed configuration (12-factor style).

Settings are read from environment variables (prefixed ``GROWTHAI_``) and an
optional ``.env`` file. Using ``pydantic-settings`` gives us validation, type
coercion and a single source of truth instead of scattered ``os.getenv`` calls.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root = three parents up from this file (src/growthai/config.py).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_DIR = PROJECT_ROOT / "datasets"
REPORTS_DIR = PROJECT_ROOT / "reports" / "generated"
ML_ARTIFACTS_DIR = PROJECT_ROOT / "ml" / "artifacts"


class Settings(BaseSettings):
    """Application settings, immutable per process."""

    model_config = SettingsConfigDict(
        env_prefix="GROWTHAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "GrowthAI"
    env: str = "development"
    log_level: str = "INFO"

    # Security
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    # Database
    database_url: str = "sqlite:///./growthai.db"

    # Reference standard
    default_standard: str = "WHO"

    # Chatbot / LLM
    llm_provider: str = "offline"
    openai_api_key: str = ""
    gemini_api_key: str = ""

    # Paths (not overridable via env by default; derived from project root)
    datasets_dir: Path = Field(default=DATASETS_DIR)
    reports_dir: Path = Field(default=REPORTS_DIR)
    ml_artifacts_dir: Path = Field(default=ML_ARTIFACTS_DIR)

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (one per process)."""
    settings = Settings()
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.ml_artifacts_dir.mkdir(parents=True, exist_ok=True)
    return settings
