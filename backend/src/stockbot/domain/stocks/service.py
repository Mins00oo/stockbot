"""Stock-detail service: assemble the detail screen's data from Toss + Finnhub.

  - detail : identity + fundamentals + 52w + price-limits + KR warnings (open-time)
  - quote  : live price/change/volume (+ US KRW conversion) — ~2s poll target
  - chart  : candles for a period (1D=minute, others=daily) + period return
  - orderbook / trades : 10-level depth / recent ticks (passthrough)

KR values are KRW, US values stay native (USD). Market cap = current price x
sharesOutstanding (both from Toss) — uniform for KR/US. 52-week high/low: US from
Finnhub, KR computed from ~252 daily candles (≈1 year, paginated). Previous close
is derived from daily candles (Toss doesn't return it directly).

Raises NotConnected if Toss isn't connected. Finnhub failures degrade to null
fields and never fail the request.
"""

from __future__ import annotations

import asyncio
import re
from decimal import Decimal, InvalidOperation

from sqlalchemy.ext.asyncio import AsyncSession

from stockbot.core.clients.finnhub import FinnhubClient
from stockbot.core.clients.toss import TossClient
from stockbot.core.errors import NotConnected
from stockbot.core.security import decrypt
from stockbot.domain.auth import repository
from stockbot.domain.stocks.schemas import (
    ChartPoint,
    ChartResponse,
    Fundamentals,
    Orderbook,
    OrderbookLevel,
    PriceLimits,
    Quote,
    StockDetail,
    Trade,
    TradesResponse,
    TradingWarning,
)

# UI period -> (Toss candle interval, count). 1D = intraday minute; others daily.
# 1Y (252 trading days ≈ 1 year) exceeds Toss's 200/call, so it paginates via
# get_daily_candles (used by get_chart and the 52-week high/low).
_RANGE_MAP: dict[str, tuple[str, int]] = {
    "1D": ("1m", 200),
    "1W": ("1d", 5),
    "1M": ("1d", 22),
    "3M": ("1d", 66),
    "1Y": ("1d", 252),
}
_DEFAULT_RANGE = "3M"

# US stocks have no daily price limit — show a +/- reference band instead.
_US_LIMIT_BAND = Decimal("0.10")

_WARNING_LABELS: dict[str, str] = {
    "LIQUIDATION_TRADING": "정리매매",
    "OVERHEATED": "단기과열",
    "INVESTMENT_WARNING": "투자경고",
    "INVESTMENT_RISK": "투자위험",
    "VI_STATIC": "정적 VI",
    "VI_DYNAMIC": "동적 VI",
    "VI_STATIC_AND_DYNAMIC": "정적·동적 VI",
    "STOCK_WARRANTS": "신주인수권증권",
}


def _dec(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _f(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def infer_market(symbol: str, market: str | None) -> str:
    """KR/US. Trusts an app-provided market; else infers (6 digits = KR)."""
    if market in ("KR", "US"):
        return market
    return "KR" if re.fullmatch(r"\d{6}", symbol or "") else "US"


async def _toss(session: AsyncSession, client: TossClient | None) -> TossClient:
    if client is not None:
        return client
    creds = await repository.get_credentials(session)
    if creds is None:
        raise NotConnected()
    return TossClient(
        app_key=decrypt(creds.toss_app_key_enc),
        secret_key=decrypt(creds.toss_secret_key_enc),
    )


def _first_price(prices: list[dict]) -> Decimal | None:
    if prices and isinstance(prices[0], dict):
        return _dec(prices[0].get("lastPrice"))
    return None


def _first_currency(prices: list[dict], fallback: str) -> str:
    if prices and isinstance(prices[0], dict) and prices[0].get("currency"):
        return str(prices[0]["currency"])
    return fallback


def _sorted(candles: list[dict]) -> list[dict]:
    return sorted(candles, key=lambda c: str(c.get("timestamp", "")))


def _prev_close(candles: list[dict]) -> Decimal | None:
    """Previous session close = second-to-last daily candle close."""
    rows = _sorted(candles)
    if len(rows) >= 2:
        return _dec(rows[-2].get("closePrice"))
    if rows:
        return _dec(rows[-1].get("closePrice"))
    return None


def _today_volume(candles: list[dict]) -> Decimal | None:
    rows = _sorted(candles)
    return _dec(rows[-1].get("volume")) if rows else None


def _candle_52w(candles: list[dict]) -> tuple[Decimal | None, Decimal | None]:
    highs = [h for h in (_dec(c.get("highPrice")) for c in candles) if h is not None]
    lows = [low for low in (_dec(c.get("lowPrice")) for c in candles) if low is not None]
    return (max(highs) if highs else None, min(lows) if lows else None)


async def get_quote(
    session: AsyncSession,
    symbol: str,
    market: str | None = None,
    *,
    client: TossClient | None = None,
) -> Quote:
    """Live quote: current price, change vs prev close, today's volume."""
    toss = await _toss(session, client)
    mkt = infer_market(symbol, market)
    prices, candles = await asyncio.gather(
        toss.get_prices([symbol]),
        toss.get_candles(symbol, "1d", count=2),
    )
    price = _first_price(prices)
    prev = _prev_close(candles)
    change = (price - prev) if (price is not None and prev is not None) else None
    change_rate = (change / prev * 100) if (change is not None and prev) else None

    krw: float | None = None
    if mkt == "US" and price is not None:
        rate = await toss.get_exchange_rate("USD", "KRW")
        fx = _dec((rate or {}).get("rate"))
        if fx is not None:
            krw = _f(price * fx)

    return Quote(
        symbol=symbol,
        price=_f(price) or 0.0,
        prevClose=_f(prev),
        change=_f(change),
        changeRate=float(round(change_rate, 2)) if change_rate is not None else None,
        volume=_f(_today_volume(candles)),
        currency=_first_currency(prices, "USD" if mkt == "US" else "KRW"),
        krwPrice=krw,
    )


async def get_detail(
    session: AsyncSession,
    symbol: str,
    market: str | None = None,
    *,
    client: TossClient | None = None,
    finnhub: FinnhubClient | None = None,
) -> StockDetail:
    """Open-time detail: identity, fundamentals, 52w, price-limits, KR warnings."""
    toss = await _toss(session, client)
    mkt = infer_market(symbol, market)
    info, prices, candles, limits = await asyncio.gather(
        toss.get_stock_info(symbol),
        toss.get_prices([symbol]),
        toss.get_daily_candles(symbol, total=252),  # ≈1y for prevClose + 52-week
        toss.get_price_limits(symbol),
    )
    warnings_raw = await toss.get_stock_warnings(symbol) if mkt == "KR" else []

    price = _first_price(prices)
    prev = _prev_close(candles)

    fund = Fundamentals()
    shares = _dec(info.get("sharesOutstanding"))
    if price is not None and shares is not None:
        fund.marketCap = _f(price * shares)

    industry: str | None = None
    if mkt == "US":
        fh = finnhub or FinnhubClient()
        metric, profile = await asyncio.gather(
            fh.get_basic_financials(symbol), fh.get_profile(symbol)
        )
        if metric:
            fund.per = _f(_dec(metric.get("peTTM") or metric.get("peExclExtraTTM") or metric.get("peAnnual")))
            fund.pbr = _f(_dec(metric.get("pbAnnual") or metric.get("pbQuarterly")))
            fund.eps = _f(_dec(metric.get("epsTTM") or metric.get("epsAnnual")))
            fund.dividendYield = _f(_dec(metric.get("dividendYieldIndicatedAnnual") or metric.get("currentDividendYieldTTM")))
            fund.week52High = _f(_dec(metric.get("52WeekHigh")))
            fund.week52Low = _f(_dec(metric.get("52WeekLow")))
        if profile:
            industry = profile.get("finnhubIndustry") or None

    # 52-week: fall back to candle-derived high/low (KR always; US if Finnhub missing).
    if fund.week52High is None or fund.week52Low is None:
        hi, low = _candle_52w(candles)
        if fund.week52High is None:
            fund.week52High = _f(hi)
        if fund.week52Low is None:
            fund.week52Low = _f(low)

    # Price limits: KR from Toss; US (null) -> +/-10% reference band off prev close.
    limits = limits or {}
    pl = PriceLimits(
        upper=_f(_dec(limits.get("upperLimitPrice"))),
        lower=_f(_dec(limits.get("lowerLimitPrice"))),
    )
    if prev is not None:
        if pl.upper is None:
            pl.upper = _f(prev * (1 + _US_LIMIT_BAND))
        if pl.lower is None:
            pl.lower = _f(prev * (1 - _US_LIMIT_BAND))

    warnings = [
        TradingWarning(
            type=str(w["warningType"]),
            label=_WARNING_LABELS.get(str(w["warningType"]), str(w["warningType"])),
        )
        for w in (warnings_raw or [])
        if isinstance(w, dict) and w.get("warningType")
    ]

    return StockDetail(
        symbol=symbol,
        name=info.get("name") or symbol,
        market=mkt,
        exchange=info.get("market"),
        currency=info.get("currency") or ("USD" if mkt == "US" else "KRW"),
        industry=industry,
        prevClose=_f(prev),
        priceLimits=pl,
        fundamentals=fund,
        warnings=warnings,
    )


async def get_chart(
    session: AsyncSession,
    symbol: str,
    range_: str = _DEFAULT_RANGE,
    *,
    client: TossClient | None = None,
) -> ChartResponse:
    """Candles for a UI period. 1D = minute candles, others = daily."""
    toss = await _toss(session, client)
    rng = range_ if range_ in _RANGE_MAP else _DEFAULT_RANGE
    interval, count = _RANGE_MAP[rng]
    # 1Y (252d) exceeds Toss's 200/call -> paginate; shorter ranges fit one call.
    if rng == "1Y":
        candles = _sorted(await toss.get_daily_candles(symbol, total=count))
    else:
        candles = _sorted(await toss.get_candles(symbol, interval, count=count))

    points: list[ChartPoint] = []
    for c in candles:
        close = _dec(c.get("closePrice"))
        if close is None:
            continue
        points.append(
            ChartPoint(
                t=str(c.get("timestamp", "")),
                close=float(close),
                volume=_f(_dec(c.get("volume"))) or 0.0,
            )
        )

    period_return = None
    if len(points) >= 2 and points[0].close:
        period_return = round((points[-1].close - points[0].close) / points[0].close * 100, 2)

    currency = (candles[0].get("currency") if candles else None) or "KRW"
    return ChartResponse(range=rng, currency=str(currency), points=points, periodReturn=period_return)


async def get_orderbook(
    session: AsyncSession, symbol: str, *, client: TossClient | None = None
) -> Orderbook:
    """10-level orderbook snapshot (passthrough)."""
    toss = await _toss(session, client)
    ob = await toss.get_orderbook(symbol)

    def levels(key: str) -> list[OrderbookLevel]:
        return [
            OrderbookLevel(
                price=_f(_dec(x.get("price"))) or 0.0,
                volume=_f(_dec(x.get("volume"))) or 0.0,
            )
            for x in (ob.get(key) or [])
            if isinstance(x, dict)
        ]

    return Orderbook(asks=levels("asks"), bids=levels("bids"), currency=ob.get("currency"))


async def get_trades(
    session: AsyncSession, symbol: str, *, client: TossClient | None = None
) -> TradesResponse:
    """Recent executed trades snapshot (passthrough; no buy/sell side from Toss)."""
    toss = await _toss(session, client)
    raw = await toss.get_trades(symbol, count=50)
    trades = [
        Trade(
            time=str(t.get("timestamp", "")),
            price=_f(_dec(t.get("price"))) or 0.0,
            volume=_f(_dec(t.get("volume"))) or 0.0,
        )
        for t in raw
        if isinstance(t, dict)
    ]
    currency = raw[0].get("currency") if raw and isinstance(raw[0], dict) else None
    return TradesResponse(trades=trades, currency=currency)
