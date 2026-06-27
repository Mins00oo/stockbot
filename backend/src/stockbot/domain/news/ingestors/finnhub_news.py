"""Finnhub company-news ingestor (US). The source tags each item with the
queried symbol, so matching is solved for free (matched_by="source_tag")."""

from __future__ import annotations

from datetime import UTC, datetime

from stockbot.core.clients.finnhub import FinnhubClient
from stockbot.domain.news.ingestors.base import RawItem
from stockbot.domain.news.normalize import clean_text


class FinnhubNewsIngestor:
    source = "finnhub"

    def __init__(self, client: FinnhubClient | None = None, *, days: int = 2) -> None:
        self._client = client or FinnhubClient()
        self._days = days

    @property
    def configured(self) -> bool:
        return self._client.configured

    async def fetch(self, symbol: str, market: str, name: str) -> list[RawItem]:
        raw = await self._client.get_company_news(symbol, days=self._days)
        items: list[RawItem] = []
        for r in raw:
            if not isinstance(r, dict):
                continue
            url = str(r.get("url") or "").strip()
            title = clean_text(str(r.get("headline") or ""))
            if not url or not title:
                continue
            ts = r.get("datetime")
            published = (
                datetime.fromtimestamp(ts, tz=UTC)
                if isinstance(ts, (int, float)) and ts > 0
                else None
            )
            raw_id = r.get("id")
            items.append(
                RawItem(
                    source=self.source,
                    source_type="news",
                    title=title,
                    original_url=url,
                    snippet=clean_text(str(r.get("summary") or "")) or None,
                    published_at=published,
                    source_tickers=[symbol],
                    matched_by="source_tag",
                    match_evidence=str(r.get("related") or symbol),
                    raw_ref=str(raw_id) if raw_id is not None else None,
                )
            )
        return items
