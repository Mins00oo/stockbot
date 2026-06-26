"""Response models for the stock-detail screen (per docs/.../DETAIL_SCREEN.md).

Numbers are emitted as JSON numbers (floats); money is in the stock's native
currency (KRW for KR, USD for US) unless a field name says otherwise.
"""

from __future__ import annotations

from pydantic import BaseModel


class PriceLimits(BaseModel):
    """Daily upper/lower price limits. null where not applicable (US has none —
    we surface a ±10% reference band instead, see service)."""

    upper: float | None = None
    lower: float | None = None


class Fundamentals(BaseModel):
    """Valuation. KR: marketCap + 52w only. US: all fields (per/pbr/eps/yield)."""

    marketCap: float | None = None  # native currency (KRW for KR, USD for US)
    week52High: float | None = None
    week52Low: float | None = None
    per: float | None = None
    pbr: float | None = None
    eps: float | None = None
    dividendYield: float | None = None  # percent (e.g. 1.9 = 1.9%)


class TradingWarning(BaseModel):
    """KR market-warning flag."""

    type: str  # Toss warningType enum
    label: str  # human label (정리매매/단기과열/투자주의/투자위험/VI 등)


class StockDetail(BaseModel):
    """Open-time detail payload (semi-static — poll /quote for live price)."""

    symbol: str
    name: str
    market: str  # "KR" | "US"
    exchange: str | None = None  # KOSPI/KOSDAQ/NASDAQ/NYSE
    currency: str  # KRW | USD
    industry: str | None = None  # US only (Finnhub); null for KR
    prevClose: float | None = None
    priceLimits: PriceLimits = PriceLimits()
    fundamentals: Fundamentals = Fundamentals()
    warnings: list[TradingWarning] = []


class Quote(BaseModel):
    """Live quote (poll target, ~2s)."""

    symbol: str
    price: float
    prevClose: float | None = None
    change: float | None = None  # price - prevClose (native currency)
    changeRate: float | None = None  # percent
    volume: float | None = None  # today's traded volume (shares)
    currency: str
    krwPrice: float | None = None  # US only: price converted to KRW


class ChartPoint(BaseModel):
    t: str  # ISO timestamp
    close: float
    volume: float


class ChartResponse(BaseModel):
    range: str  # 1D | 1W | 1M | 3M | 1Y
    currency: str
    points: list[ChartPoint] = []
    periodReturn: float | None = None  # percent vs first point of the range


class OrderbookLevel(BaseModel):
    price: float
    volume: float


class Orderbook(BaseModel):
    asks: list[OrderbookLevel] = []  # sell side
    bids: list[OrderbookLevel] = []  # buy side
    currency: str | None = None


class Trade(BaseModel):
    time: str  # ISO timestamp
    price: float
    volume: float


class TradesResponse(BaseModel):
    trades: list[Trade] = []
    currency: str | None = None
