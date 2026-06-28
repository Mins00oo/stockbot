"""News ingest orchestration (Phase 1): collect → normalize → dedup → store.

``run_ingest`` is called both by the scheduler job and the manual trigger
endpoint. It never raises for the expected "nothing to do" cases (not connected,
no source keys) — it returns a summary with a ``skipped`` reason instead. A single
source failing is logged and skipped; other sources/symbols continue.
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from stockbot.core.clients.finnhub import FinnhubClient
from stockbot.core.clients.naver import NaverClient
from stockbot.core.clients.toss import TossClient
from stockbot.core.config import get_settings
from stockbot.domain.news import repository
from stockbot.domain.news.dedup import canonical_url, exact_hash
from stockbot.domain.news.ingestors.finnhub_news import FinnhubNewsIngestor
from stockbot.domain.news.ingestors.naver_news import NaverNewsIngestor
from stockbot.domain.news.schemas import IngestRunResponse, NewsItem, NewsListResponse
from stockbot.domain.news.symbols import get_target_symbols


async def run_ingest(
    session: AsyncSession,
    *,
    toss_client: TossClient | None = None,
    finnhub_client: FinnhubClient | None = None,
    naver_client: NaverClient | None = None,
    days: int | None = None,
) -> IngestRunResponse:
    """Fetch news for every target symbol, dedup, and store new items."""
    lookback = days if days is not None else get_settings().news_lookback_days
    targets = await get_target_symbols(session, client=toss_client)
    if not targets:
        logger.info("News ingest skipped: no target symbols (Toss not connected?)")
        return IngestRunResponse(
            fetched=0, stored=0, deduped=0, symbols=0, skipped="not_connected"
        )

    finnhub_ing = FinnhubNewsIngestor(finnhub_client, days=lookback)
    naver_ing = NaverNewsIngestor(naver_client)

    fetched = stored = deduped = 0
    seen_canonical: set[str] = set()
    seen_hash: set[str] = set()

    for t in targets:
        if t.market == "US":
            ingestors = [finnhub_ing] if finnhub_ing.configured else []
        else:
            ingestors = [naver_ing] if naver_ing.configured else []

        for ing in ingestors:
            try:
                raw_items = await ing.fetch(t.symbol, t.market, t.name)
            except Exception as exc:  # one source must not kill the run
                logger.warning(
                    "News ingest {} via {} failed: {}", t.symbol, ing.source, exc
                )
                continue

            for item in raw_items:
                fetched += 1
                canonical = canonical_url(item.original_url)
                ehash = exact_hash(item.title, item.snippet)
                # In-run dedup (cheap) then cross-run dedup (DB).
                if canonical in seen_canonical or ehash in seen_hash:
                    deduped += 1
                    continue
                if await repository.exists(session, canonical, ehash):
                    seen_canonical.add(canonical)
                    seen_hash.add(ehash)
                    deduped += 1
                    continue
                await repository.insert_item(
                    session,
                    item,
                    canonical_url=canonical,
                    exact_hash=ehash,
                    market=t.market,
                )
                seen_canonical.add(canonical)
                seen_hash.add(ehash)
                stored += 1

    logger.info(
        "News ingest done: symbols={} fetched={} stored={} deduped={}",
        len(targets),
        fetched,
        stored,
        deduped,
    )
    return IngestRunResponse(
        fetched=fetched, stored=stored, deduped=deduped, symbols=len(targets)
    )


async def list_news(
    session: AsyncSession,
    *,
    symbol: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> NewsListResponse:
    """Return stored news items, newest first (optionally filtered to a symbol)."""
    rows = await repository.list_recent(
        session, symbol=symbol, limit=limit, offset=offset
    )
    return NewsListResponse(items=[NewsItem.from_row(r) for r in rows])
