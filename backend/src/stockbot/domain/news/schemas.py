"""Response models for the news domain."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from stockbot.domain.news.models import RawItem


class NewsTicker(BaseModel):
    symbol: str
    market: str
    matchedBy: str


class NewsItem(BaseModel):
    id: int
    source: str
    headline: str
    url: str
    snippet: str | None = None
    publishedAt: datetime | None = None
    fetchedAt: datetime
    tickers: list[NewsTicker] = []

    @classmethod
    def from_row(cls, row: RawItem) -> NewsItem:
        return cls(
            id=row.id,
            source=row.source,
            headline=row.title,
            url=row.original_url,
            snippet=row.snippet,
            publishedAt=row.published_at,
            fetchedAt=row.fetched_at,
            tickers=[
                NewsTicker(symbol=t.symbol, market=t.market, matchedBy=t.matched_by)
                for t in row.tickers
            ],
        )


class NewsListResponse(BaseModel):
    items: list[NewsItem]


class IngestRunResponse(BaseModel):
    """Summary of one ingest run (returned by the manual trigger)."""

    fetched: int  # RawItems produced by sources
    stored: int  # newly inserted (after dedup)
    deduped: int  # dropped as duplicates
    symbols: int  # target symbols processed
    skipped: str | None = None  # reason if the run was a no-op (e.g. not connected)
