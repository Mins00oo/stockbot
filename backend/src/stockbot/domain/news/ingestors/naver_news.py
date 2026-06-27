"""Naver Search API ingestor (KR). No real per-ticker feed exists for KR, so we
query by company name and tag results with that symbol (matched_by="query").

We store the publisher's ``originallink`` (not the Naver mirror) for attribution
and later body fetch. Titles/descriptions arrive with <b> tags + HTML entities —
``clean_text`` strips them.
"""

from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime

from loguru import logger

from stockbot.core.clients.naver import NaverClient
from stockbot.domain.news.ingestors.base import RawItem
from stockbot.domain.news.normalize import clean_text


def _parse_pubdate(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        logger.debug("Naver pubDate unparseable: {!r}", value)
        return None


class NaverNewsIngestor:
    source = "naver"

    def __init__(self, client: NaverClient | None = None, *, display: int = 20) -> None:
        self._client = client or NaverClient()
        self._display = display

    @property
    def configured(self) -> bool:
        return self._client.configured

    async def fetch(self, symbol: str, market: str, name: str) -> list[RawItem]:
        query = (name or "").strip()
        if not query:
            return []
        raw = await self._client.search_news(query, display=self._display)
        items: list[RawItem] = []
        for r in raw:
            if not isinstance(r, dict):
                continue
            # Prefer the publisher's original link; fall back to the Naver mirror.
            url = str(r.get("originallink") or r.get("link") or "").strip()
            title = clean_text(str(r.get("title") or ""))
            if not url or not title:
                continue
            items.append(
                RawItem(
                    source=self.source,
                    source_type="news",
                    title=title,
                    original_url=url,
                    snippet=clean_text(str(r.get("description") or "")) or None,
                    published_at=_parse_pubdate(r.get("pubDate")),
                    source_tickers=[symbol],
                    matched_by="query",
                    match_evidence=query,
                    raw_ref=str(r.get("link") or "") or None,
                )
            )
        return items
