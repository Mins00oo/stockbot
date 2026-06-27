"""Common ingestor contract: the RawItem shape + the Ingestor protocol.

Every source adapter turns its provider-specific response into a list of
``RawItem`` (design §2). Only metadata is captured — never article bodies
(copyright constraint, design §7).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel

SourceType = Literal["news", "filing", "macro"]
MatchedBy = Literal["source_tag", "query"]


class RawItem(BaseModel):
    """A normalized news/filing/macro item, before dedup and storage."""

    source: str  # naver | finnhub | rss:hankyung | dart | edgar | gdelt | av
    source_type: SourceType = "news"
    title: str
    original_url: str  # publisher's original link (not a Naver mirror)
    snippet: str | None = None  # provider-supplied short summary (NOT the body)
    published_at: datetime | None = None
    # Symbols the source tags this item with (Finnhub) or we queried for (Naver).
    source_tickers: list[str] = []
    matched_by: MatchedBy = "source_tag"
    # Human-auditable evidence for the match (e.g. the company name we queried).
    match_evidence: str | None = None
    raw_ref: str | None = None  # provider id (Finnhub id, Naver link, ...)


@runtime_checkable
class Ingestor(Protocol):
    """Fetch + normalize news for one symbol into RawItems."""

    source: str

    async def fetch(self, symbol: str, market: str, name: str) -> list[RawItem]: ...
