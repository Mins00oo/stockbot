"""Auth endpoint tests.

The Toss client and DB session are dependency-overridden so no network or
Postgres is touched.
"""

from __future__ import annotations

import pytest

from stockbot.core.clients.toss import TossClient
from stockbot.core.db import get_session
from stockbot.domain.auth import service as auth_service
from stockbot.domain.auth.schemas import (
    AccountInfo,
    TossConnectResponse,
)


# ---------------------------------------------------------------------------
# pairing/verify
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_pairing_verify_ok(client, auth_headers):
    resp = await client.post("/auth/pairing/verify", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"valid": True}


@pytest.mark.asyncio
async def test_pairing_verify_missing_key(client):
    resp = await client.post("/auth/pairing/verify")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_pairing_verify_wrong_key(client):
    resp = await client.post(
        "/auth/pairing/verify", headers={"X-Pairing-Key": "nope"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


# ---------------------------------------------------------------------------
# toss/connect
# ---------------------------------------------------------------------------
class _FakeSession:
    """No-op async session stand-in for the get_session dependency."""

    async def commit(self):  # pragma: no cover - trivial
        return None

    async def rollback(self):  # pragma: no cover - trivial
        return None


@pytest.mark.asyncio
async def test_toss_connect_ok(app, client, auth_headers, monkeypatch):
    async def fake_session():
        yield _FakeSession()

    app.dependency_overrides[get_session] = fake_session

    async def fake_connect(session, req, *, client=None):
        assert req.app_key == "tskey_live_x"
        assert req.secret_key == "sk_y"
        return TossConnectResponse(
            connected=True,
            account=AccountInfo(seq="1", name="토스증권 계좌"),
        )

    monkeypatch.setattr(auth_service, "connect_toss", fake_connect)
    # The router imports the module symbol, so patch where it's looked up too.
    from stockbot.domain.auth import router as auth_router

    monkeypatch.setattr(auth_router.service, "connect_toss", fake_connect)

    resp = await client.post(
        "/auth/toss/connect",
        headers=auth_headers,
        json={"appKey": "tskey_live_x", "secretKey": "sk_y"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["connected"] is True
    assert body["account"] == {"seq": "1", "name": "토스증권 계좌"}

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_toss_connect_validation_error(client, auth_headers):
    # Missing secretKey -> RequestValidationError -> VALIDATION_ERROR.
    resp = await client.post(
        "/auth/toss/connect",
        headers=auth_headers,
        json={"appKey": "tskey_live_x"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_toss_connect_requires_pairing_key(client):
    resp = await client.post(
        "/auth/toss/connect",
        json={"appKey": "a", "secretKey": "b"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


# ---------------------------------------------------------------------------
# service unit test with a mocked Toss client
# ---------------------------------------------------------------------------
class _MockTossConnect(TossClient):
    def __init__(self, accounts):
        # Bypass real __init__ (no settings needed).
        self._accounts = accounts

    async def issue_token(self):
        return "tok"

    async def get_accounts(self):
        return self._accounts


@pytest.mark.asyncio
async def test_connect_service_picks_first_account(monkeypatch):
    captured = {}

    async def fake_upsert(session, *, toss_app_key_enc, toss_secret_key_enc, account_seq):
        captured["account_seq"] = account_seq
        return None

    monkeypatch.setattr(auth_service.repository, "upsert_credentials", fake_upsert)

    from stockbot.domain.auth.schemas import TossConnectRequest

    req = TossConnectRequest(appKey="tskey_live_x", secretKey="sk_y")
    mock = _MockTossConnect(accounts=[{"accountSeq": 42, "accountType": "BROKERAGE"}])

    resp = await auth_service.connect_toss(session=object(), req=req, client=mock)

    assert resp.connected is True
    assert resp.account.seq == "42"
    assert captured["account_seq"] == "42"
