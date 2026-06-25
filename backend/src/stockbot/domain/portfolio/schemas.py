"""Response models for the portfolio domain (per API 정의서 ④)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Market = Literal["KR", "US"]
CurrencyCode = Literal["KRW", "USD"]


class Holding(BaseModel):
    symbol: str
    name: str
    market: Market
    quantity: float
    avgPrice: float
    currentPrice: float
    evalAmount: float
    evalAmountKrw: float
    pnl: float
    pnlRate: float
    currency: CurrencyCode


class HoldingsResponse(BaseModel):
    totalValueKrw: float
    totalPnlKrw: float
    totalPnlRate: float
    totalPurchaseKrw: float
    holdings: list[Holding]
