"""Finnhub client — US stock fundamentals + company news (free tier).

Endpoints we use:
  - GET /stock/metric?symbol=&metric=all  (Basic Financials: PER/PBR/EPS/yield/52w/mktcap)
  - GET /stock/profile2?symbol=           (name/exchange/industry/logo/marketCap)
  - GET /company-news?symbol=&from=&to=   (per-symbol news, source-tagged by symbol)

Free tier: ~60 req/min, personal/non-commercial use. Auth via the ?token= query
param. Network/HTTP errors return None/[] so callers degrade gracefully (the
detail screen still renders; the news run skips this source) instead of failing.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
from loguru import logger

from stockbot.core.config import get_settings

_TIMEOUT = httpx.Timeout(8.0, connect=4.0)


class FinnhubClient:
    """Stateless async client for Finnhub free-tier endpoints."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.finnhub_api_key
        self._base_url = settings.finnhub_base_url.rstrip("/")

    @property
    def configured(self) -> bool:
        """Whether an API key is present (else calls no-op to None)."""
        return bool(self._api_key)

    async def _get(self, path: str, params: dict[str, str]) -> dict | None:
        if not self._api_key:
            return None
        url = f"{self._base_url}{path}"
        query = {**params, "token": self._api_key}
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(url, params=query)
        except httpx.HTTPError as exc:
            logger.warning("Finnhub GET {} network error: {}", path, exc)
            return None
        if resp.status_code != 200:
            logger.info("Finnhub GET {} status {}", path, resp.status_code)
            return None
        body = resp.json()
        return body if isinstance(body, dict) else None

    async def get_basic_financials(self, symbol: str) -> dict | None:
        """Return the 'metric' object (peTTM, pbAnnual, epsTTM, dividend yield,
        52-week high/low, marketCapitalization, ...) or None."""
        body = await self._get("/stock/metric", {"symbol": symbol, "metric": "all"})
        if not body:
            return None
        metric = body.get("metric")
        return metric if isinstance(metric, dict) else None

    async def get_profile(self, symbol: str) -> dict | None:
        """Return company profile (name, exchange, finnhubIndustry, logo,
        marketCapitalization, shareOutstanding) or None."""
        return await self._get("/stock/profile2", {"symbol": symbol})

    async def get_company_news(self, symbol: str, *, days: int = 2) -> list[dict]:
        """Return recent company news for ``symbol`` over the last ``days``.

        Each item (Finnhub shape): {category, datetime(unix s), headline, id,
        image, related(symbol), source, summary, url}. The list is already tagged
        to ``symbol`` by the query. Returns [] when unconfigured or on any error.
        """
        if not self._api_key:
            return []
        today = datetime.now(UTC).date()
        params = {
            "symbol": symbol,
            "from": str(today - timedelta(days=max(1, days))),
            "to": str(today),
        }
        url = f"{self._base_url}/company-news"
        query = {**params, "token": self._api_key}
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(url, params=query)
        except httpx.HTTPError as exc:
            logger.warning("Finnhub company-news {} network error: {}", symbol, exc)
            return []
        if resp.status_code != 200:
            logger.info("Finnhub company-news {} status {}", symbol, resp.status_code)
            return []
        body = resp.json()
        return body if isinstance(body, list) else []
