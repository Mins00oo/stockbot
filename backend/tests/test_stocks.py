"""Stock-detail service tests — Toss + Finnhub mocked (no network/DB)."""

from __future__ import annotations

import pytest

from stockbot.domain.stocks import service as svc


class _MockToss:
    def __init__(
        self,
        *,
        info=None,
        prices=None,
        candles_1d=None,
        candles_2=None,
        limits=None,
        warnings=None,
        rate=None,
    ):
        self._info = info or {}
        self._prices = prices or []
        self._candles_1d = candles_1d or []
        self._candles_2 = candles_2 if candles_2 is not None else (candles_1d or [])
        self._limits = limits or {}
        self._warnings = warnings or []
        self._rate = rate or {}

    async def issue_token(self):
        return "token"

    async def get_stock_info(self, symbol):
        return self._info

    async def get_prices(self, symbols):
        return self._prices

    async def get_candles(self, symbol, interval, *, count=200, before=None):
        return self._candles_2 if count <= 2 else self._candles_1d

    async def get_daily_candles(self, symbol, *, total=252):
        return self._candles_1d

    async def get_price_limits(self, symbol):
        return self._limits

    async def get_stock_warnings(self, symbol):
        return self._warnings

    async def get_exchange_rate(self, base_currency="USD", quote_currency="KRW"):
        return self._rate


class _MockFinnhub:
    def __init__(self, metric=None, profile=None):
        self._metric = metric
        self._profile = profile

    async def get_basic_financials(self, symbol):
        return self._metric

    async def get_profile(self, symbol):
        return self._profile


def _candle(ts, o, h, low, c, v, cur="KRW"):
    return {
        "timestamp": ts,
        "openPrice": o,
        "highPrice": h,
        "lowPrice": low,
        "closePrice": c,
        "volume": v,
        "currency": cur,
    }


@pytest.mark.asyncio
async def test_detail_kr_marketcap_from_shares_no_fundamentals():
    toss = _MockToss(
        info={"name": "삼성전자", "market": "KOSPI", "currency": "KRW", "sharesOutstanding": "100"},
        prices=[{"lastPrice": "71000", "currency": "KRW"}],
        candles_1d=[
            _candle("2026-06-24", "70000", "72000", "69000", "70000", "10"),
            _candle("2026-06-25", "70000", "73000", "68000", "71000", "20"),
        ],
        limits={"upperLimitPrice": "92300", "lowerLimitPrice": "49700"},
        warnings=[{"warningType": "OVERHEATED"}],
    )
    d = await svc.get_detail(session=object(), symbol="005930", market="KR", client=toss)

    assert d.market == "KR"
    assert d.fundamentals.marketCap == pytest.approx(71000 * 100)
    assert d.fundamentals.per is None and d.fundamentals.pbr is None
    assert d.fundamentals.week52High == pytest.approx(73000)
    assert d.fundamentals.week52Low == pytest.approx(68000)
    assert d.priceLimits.upper == pytest.approx(92300)
    assert d.prevClose == pytest.approx(70000)
    assert d.warnings and d.warnings[0].label == "단기과열"
    assert d.industry is None


@pytest.mark.asyncio
async def test_detail_us_fundamentals_and_reference_band():
    toss = _MockToss(
        info={"name": "Apple", "market": "NASDAQ", "currency": "USD", "sharesOutstanding": "1000"},
        prices=[{"lastPrice": "195", "currency": "USD"}],
        candles_1d=[
            _candle("2026-06-24", "190", "196", "189", "190", "5", "USD"),
            _candle("2026-06-25", "190", "197", "188", "195", "6", "USD"),
        ],
        limits={"upperLimitPrice": None, "lowerLimitPrice": None},  # US -> band
    )
    fh = _MockFinnhub(
        metric={
            "peTTM": "33.1",
            "pbAnnual": "51.2",
            "epsTTM": "6.47",
            "dividendYieldIndicatedAnnual": "0.4",
            "52WeekHigh": "237.2",
            "52WeekLow": "164.1",
        },
        profile={"finnhubIndustry": "Technology"},
    )
    d = await svc.get_detail(session=object(), symbol="AAPL", market="US", client=toss, finnhub=fh)

    assert d.market == "US"
    assert d.fundamentals.per == pytest.approx(33.1)
    assert d.fundamentals.pbr == pytest.approx(51.2)
    assert d.fundamentals.eps == pytest.approx(6.47)
    assert d.fundamentals.dividendYield == pytest.approx(0.4)
    assert d.fundamentals.week52High == pytest.approx(237.2)
    assert d.fundamentals.marketCap == pytest.approx(195 * 1000)
    # US has no daily limit -> +/-10% reference band off prevClose(190)
    assert d.priceLimits.upper == pytest.approx(190 * 1.10)
    assert d.priceLimits.lower == pytest.approx(190 * 0.90)
    assert d.industry == "Technology"
    assert d.warnings == []


@pytest.mark.asyncio
async def test_quote_change_rate_and_volume():
    toss = _MockToss(
        prices=[{"lastPrice": "71000", "currency": "KRW"}],
        candles_2=[
            _candle("2026-06-24", "x", "x", "x", "70000", "100"),
            _candle("2026-06-25", "x", "x", "x", "71000", "250"),
        ],
    )
    q = await svc.get_quote(session=object(), symbol="005930", market="KR", client=toss)

    assert q.price == pytest.approx(71000)
    assert q.prevClose == pytest.approx(70000)
    assert q.change == pytest.approx(1000)
    assert q.changeRate == pytest.approx(1.43)  # 1000/70000*100 -> 1.43
    assert q.volume == pytest.approx(250)
    assert q.krwPrice is None


@pytest.mark.asyncio
async def test_chart_period_return():
    toss = _MockToss(
        candles_1d=[
            _candle("2026-04-01", "x", "x", "x", "100", "10"),
            _candle("2026-06-25", "x", "x", "x", "112.83", "20"),
        ]
    )
    c = await svc.get_chart(session=object(), symbol="005930", range_="3M", client=toss)

    assert c.range == "3M"
    assert len(c.points) == 2
    assert c.periodReturn == pytest.approx(12.83)
