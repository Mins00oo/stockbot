"""Stock-detail routes: detail / quote / chart / orderbook / trades.

All guarded by the pairing key. Data comes from Toss (+ Finnhub for US
fundamentals). `market` (KR/US) is optional — inferred from the symbol if absent.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from stockbot.core.db import get_session
from stockbot.core.security import verify_pairing_key
from stockbot.domain.stocks import service
from stockbot.domain.stocks.schemas import (
    ChartResponse,
    Orderbook,
    Quote,
    StockDetail,
    TradesResponse,
)

router = APIRouter(
    prefix="/stocks",
    tags=["stocks"],
    dependencies=[Depends(verify_pairing_key)],
)


@router.get("/{symbol}", response_model=StockDetail)
async def stock_detail(
    symbol: str,
    market: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> StockDetail:
    """Open-time detail: identity·fundamentals·52w·price-limits·KR warnings."""
    return await service.get_detail(session, symbol, market)


@router.get("/{symbol}/quote", response_model=Quote)
async def stock_quote(
    symbol: str,
    market: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> Quote:
    """Live quote (poll ~2s): price·change·volume (+US KRW)."""
    return await service.get_quote(session, symbol, market)


@router.get("/{symbol}/chart", response_model=ChartResponse)
async def stock_chart(
    symbol: str,
    range_: str = Query("3M", alias="range"),
    session: AsyncSession = Depends(get_session),
) -> ChartResponse:
    """Chart candles for a period: range = 1D|1W|1M|3M|1Y (default 3M)."""
    return await service.get_chart(session, symbol, range_)


@router.get("/{symbol}/orderbook", response_model=Orderbook)
async def stock_orderbook(
    symbol: str,
    session: AsyncSession = Depends(get_session),
) -> Orderbook:
    """10-level orderbook snapshot."""
    return await service.get_orderbook(session, symbol)


@router.get("/{symbol}/trades", response_model=TradesResponse)
async def stock_trades(
    symbol: str,
    session: AsyncSession = Depends(get_session),
) -> TradesResponse:
    """Recent executed trades snapshot."""
    return await service.get_trades(session, symbol)
