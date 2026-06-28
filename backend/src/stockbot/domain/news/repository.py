"""Persistence for news items: dedup-aware insert + recent listing."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stockbot.domain.news.ingestors.base import RawItem as RawItemDTO
from stockbot.domain.news.models import ItemTicker, RawItem


async def exists(session: AsyncSession, canonical_url: str, exact_hash: str) -> bool:
    """True if an item with this canonical_url OR exact_hash is already stored
    (either key matching means it's a duplicate, design §3)."""
    result = await session.execute(
        select(RawItem.id)
        .where(
            (RawItem.canonical_url == canonical_url)
            | (RawItem.exact_hash == exact_hash)
        )
        .limit(1)
    )
    return result.first() is not None


async def insert_item(
    session: AsyncSession,
    item: RawItemDTO,
    *,
    canonical_url: str,
    exact_hash: str,
    market: str,
) -> RawItem:
    """Insert a RawItem + its symbol links. Caller dedups first via ``exists``.

    The get_session dependency / scheduler job commits; here we only flush so the
    row gets an id for the FK links.
    """
    row = RawItem(
        source=item.source,
        source_type=item.source_type,
        title=item.title,
        original_url=item.original_url,
        canonical_url=canonical_url,
        exact_hash=exact_hash,
        snippet=item.snippet,
        published_at=item.published_at,
        raw_ref=item.raw_ref,
    )
    row.tickers = [
        ItemTicker(
            symbol=symbol,
            market=market,
            matched_by=item.matched_by,
            evidence=item.match_evidence,
        )
        for symbol in item.source_tickers
    ]
    session.add(row)
    await session.flush()
    return row


async def list_recent(
    session: AsyncSession,
    *,
    symbol: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[RawItem]:
    """Recent items, newest first (by fetched_at). Optionally filtered to a symbol."""
    stmt = select(RawItem)
    if symbol:
        stmt = stmt.join(RawItem.tickers).where(ItemTicker.symbol == symbol)
    stmt = (
        stmt.order_by(RawItem.fetched_at.desc(), RawItem.id.desc())
        .limit(max(1, min(limit, 200)))
        .offset(max(0, offset))
    )
    result = await session.execute(stmt)
    return list(result.scalars().unique().all())
