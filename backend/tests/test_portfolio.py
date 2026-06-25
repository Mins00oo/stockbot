"""Portfolio endpoint + service tests.

The Toss client is mocked and the repository is monkeypatched so neither the
network nor Postgres is touched.
"""

from __future__ import annotations

import pytest

from stockbot.core.clients.toss import TossClient
from stockbot.core.db import get_session
from stockbot.domain.portfolio import service as pf_service


class _FakeSession:
    async def commit(self):  # pragma: no cover - trivial
        return None

    async def rollback(self):  # pragma: no cover - trivial
        return None


class _MockTossPortfolio(TossClient):
    """Mocked Toss client returning canned holdings/prices/rate."""

    def __init__(self, overview, prices, rate):
        self._overview = overview
        self._prices = prices
        self._rate = rate

    async def get_holdings(self, account_seq):
        return self._overview

    async def get_prices(self, symbols):
        return self._prices

    async def get_exchange_rate(self, base_currency="USD", quote_currency="KRW"):
        return self._rate


_OVERVIEW = {
    # Account-level totals (raw from Toss) — intentionally NOT equal to the sum
    # of items, to prove the service uses these directly rather than summing.
    "totalPurchaseAmount": {"krw": "6500000"},
    "marketValue": {"amount": {"krw": "7200000"}},
    "profitLoss": {"amount": {"krw": "700000"}, "rate": "0.1077"},
    "items": [
        {
            "symbol": "005930",
            "name": "삼성전자",
            "marketCountry": "KR",
            "currency": "KRW",
            "quantity": "10",
            "lastPrice": "72000",
            "averagePurchasePrice": "70000",
            "marketValue": {"amount": "720000"},
            "profitLoss": {"amount": "20000", "rate": "0.0286"},
        },
        {
            "symbol": "AAPL",
            "name": "Apple",
            "marketCountry": "US",
            "currency": "USD",
            "quantity": "5",
            "lastPrice": "195.0",
            "averagePurchasePrice": "180.0",
            "marketValue": {"amount": "975.0"},
            "profitLoss": {"amount": "75.0", "rate": "0.0833"},
        },
    ]
}
_PRICES = [
    {"symbol": "005930", "lastPrice": "72000", "currency": "KRW"},
    {"symbol": "AAPL", "lastPrice": "195.0", "currency": "USD"},
]
_RATE = {"baseCurrency": "USD", "quoteCurrency": "KRW", "rate": "1380"}


@pytest.mark.asyncio
async def test_holdings_service_assembles_and_converts(monkeypatch):
    async def fake_get_credentials(session):
        class _Creds:
            toss_app_key_enc = "x"
            toss_secret_key_enc = "y"
            account_seq = "1"

        return _Creds()

    monkeypatch.setattr(pf_service.repository, "get_credentials", fake_get_credentials)

    mock = _MockTossPortfolio(_OVERVIEW, _PRICES, _RATE)
    resp = await pf_service.get_holdings(session=object(), client=mock)

    # USD eval 975 * 1380 = 1,345,500 KRW.
    by_symbol = {h.symbol: h for h in resp.holdings}
    assert by_symbol["005930"].evalAmountKrw == pytest.approx(720000)
    assert by_symbol["AAPL"].evalAmountKrw == pytest.approx(975.0 * 1380)
    assert by_symbol["AAPL"].currency == "USD"
    assert by_symbol["AAPL"].pnlRate == pytest.approx(8.33)

    # Totals come straight from the Toss overview (raw), not summed by us.
    assert resp.totalValueKrw == pytest.approx(7200000)
    assert resp.totalPnlKrw == pytest.approx(700000)
    assert resp.totalPnlRate == pytest.approx(10.77)
    assert resp.totalPurchaseKrw == pytest.approx(6500000)

    # Sorted by evalAmountKrw descending (AAPL ~1.35M > Samsung 720k).
    assert resp.holdings[0].symbol == "AAPL"


@pytest.mark.asyncio
async def test_holdings_not_connected(app, client, auth_headers, monkeypatch):
    async def fake_session():
        yield _FakeSession()

    app.dependency_overrides[get_session] = fake_session

    async def fake_get_credentials(session):
        return None

    monkeypatch.setattr(pf_service.repository, "get_credentials", fake_get_credentials)

    resp = await client.get("/portfolio/holdings", headers=auth_headers)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "NOT_CONNECTED"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_holdings_requires_pairing_key(client):
    resp = await client.get("/portfolio/holdings")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"
