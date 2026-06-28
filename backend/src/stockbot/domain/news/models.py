"""ORM models for the news domain (Phase 1: raw_item + item_ticker).

Only metadata is persisted — never the article body (copyright, design §7).
Later phases add simhash / embedding_ref / story clustering columns; kept out of
Phase 1 to stay minimal (migrations are cheap).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stockbot.core.db import Base


class RawItem(Base):
    """A normalized, deduped news item (headline + link + snippet metadata)."""

    __tablename__ = "raw_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False, default="news")
    title: Mapped[str] = mapped_column(Text, nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    # Exact-dedup keys: canonical_url is unique (rejects re-fetch); exact_hash is
    # indexed (catches the same wire story under a different URL).
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    exact_hash: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tickers: Mapped[list[ItemTicker]] = relationship(
        back_populates="item", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (Index("ix_raw_item_exact_hash", "exact_hash"),)


class ItemTicker(Base):
    """Link from a news item to a symbol, with how the match was made."""

    __tablename__ = "item_ticker"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("raw_item.id", ondelete="CASCADE"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(Text, nullable=False)
    market: Mapped[str] = mapped_column(Text, nullable=False)
    matched_by: Mapped[str] = mapped_column(Text, nullable=False)  # source_tag | query
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)

    item: Mapped[RawItem] = relationship(back_populates="tickers")

    __table_args__ = (Index("ix_item_ticker_symbol", "symbol"),)
