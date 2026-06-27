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
    # US fundamentals (PER/PBR/EPS/dividend yield) AND US company-news for the
    # news pipeline. Empty = skip US fundamentals + US news gracefully.
    finnhub_api_key: str = ""
    finnhub_base_url: str = "https://finnhub.io/api/v1"

    # Naver Search API (KR news ingest). Issue at developers.naver.com (검색 API).
    # Empty = skip KR news ingest gracefully.
    naver_client_id: str = ""
    naver_client_secret: str = ""
    naver_base_url: str = "https://openapi.naver.com"

    # News scheduler (Phase 1: collect → normalize → dedup → store).
    # The scheduler runs in-process with the API server (see core/scheduler.py).
    scheduler_enabled: bool = True
    news_poll_interval_minutes: int = 15
    # Lookback window for source queries (Finnhub from/to). Re-runs overlap; the
    # exact-dedup layer (canonical_url + exact_hash) absorbs duplicates.
    news_lookback_days: int = 2

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
