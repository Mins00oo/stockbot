"""Naver Search API client — KR company news ingest (free tier).

Endpoint:
  - GET /v1/search/news.json?query=&display=&sort=date

Auth via headers X-Naver-Client-Id / X-Naver-Client-Secret. Free tier: 25,000
calls/day, ~10/s. There is no per-ticker feed for KR — we query by company name,
so the caller tags results with the symbol it queried for (pseudo per-ticker).

Network/HTTP errors return [] so the news run degrades gracefully (skips this
source) instead of failing the whole run. Each result item (Naver shape):
{title, originallink, link, description, pubDate}. ``title``/``description`` may
contain <b> tags and HTML entities — normalization happens in the ingestor.
"""

from __future__ import annotations

import httpx
from loguru import logger

from stockbot.core.config import get_settings

_TIMEOUT = httpx.Timeout(8.0, connect=4.0)


class NaverClient:
    """Stateless async client for the Naver news search endpoint."""

    def __init__(
        self, client_id: str | None = None, client_secret: str | None = None
    ) -> None:
        settings = get_settings()
        self._client_id = client_id if client_id is not None else settings.naver_client_id
        self._client_secret = (
            client_secret if client_secret is not None else settings.naver_client_secret
        )
        self._base_url = settings.naver_base_url.rstrip("/")

    @property
    def configured(self) -> bool:
        """Whether both Naver credentials are present (else calls no-op to [])."""
        return bool(self._client_id and self._client_secret)

    async def search_news(
        self, query: str, *, display: int = 20, sort: str = "date"
    ) -> list[dict]:
        """Search news for ``query`` (a company name). ``sort=date`` = newest
        first. ``display`` clamped to Naver max (1..100). Returns [] when
        unconfigured or on any error."""
        if not self.configured or not query.strip():
            return []
        url = f"{self._base_url}/v1/search/news.json"
        params = {
            "query": query,
            "display": str(max(1, min(display, 100))),
            "sort": sort,
        }
        headers = {
            "X-Naver-Client-Id": self._client_id,
            "X-Naver-Client-Secret": self._client_secret,
        }
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(url, params=params, headers=headers)
        except httpx.HTTPError as exc:
            logger.warning("Naver news search {!r} network error: {}", query, exc)
            return []
        if resp.status_code != 200:
            logger.info("Naver news search {!r} status {}", query, resp.status_code)
            return []
        body = resp.json()
        items = body.get("items") if isinstance(body, dict) else None
        return items if isinstance(items, list) else []
