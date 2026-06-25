"""Application settings, loaded from environment / .env via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Values come from environment variables (or a local .env during dev).
    Field names map to UPPER_CASE env vars case-insensitively.
    """

    pairing_key: str
    database_url: str
    toss_key_enc_key: str
    toss_base_url: str = "https://openapi.tossinvest.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (single source of truth)."""
    return Settings()
