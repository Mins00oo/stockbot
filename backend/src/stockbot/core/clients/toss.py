"""Async Toss Open API client.

Wraps the endpoints we need for today's slice:
  - POST /oauth2/token        (client_credentials grant, x-www-form-urlencoded)
  - GET  /api/v1/accounts
  - GET  /api/v1/holdings     (requires X-Tossinvest-Account header)
  - GET  /api/v1/prices       (batch, up to 200 symbols, comma-separated)
  - GET  /api/v1/exchange-rate

Conventions (verified against toss_openapi.json v1.1.1):
  - Success bodies for /api/v1/* are wrapped in an envelope: {"result": ...}.
  - The token endpoint follows OAuth2 standard shape (no envelope):
    {"access_token", "token_type", "expires_in"}.
  - Money/decimal values arrive as STRINGS — callers parse with Decimal.
  - Auth uses Authorization: Bearer <token> on every /api/v1/* call.

Error mapping:
  - Token 401 (invalid_client) or any-call 401 -> TossAuthFailed.
  - Network errors / timeouts / 5xx -> TossUnavailable.

Token caching: one access token kept in-memory with its expiry. Re-issued on
expiry (Toss invalidates the previous token on re-issue, which is fine since we
only ever hold one).
"""

from __future__ import annotations

import time

import httpx
from loguru import logger

from stockbot.core.config import get_settings
from stockbot.core.errors import TossAuthFailed, TossUnavailable

# Re-issue a bit before the real expiry to avoid edge-of-expiry 401s.
_EXPIRY_SKEW_SECONDS = 60
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class TossClient:
    """Stateful async client. Holds one cached access token in memory."""

    def __init__(self, app_key: str, secret_key: str) -> None:
        self._app_key = app_key
        self._secret_key = secret_key
        self._base_url = get_settings().toss_base_url.rstrip("/")
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------ #
    # Token handling
    # ------------------------------------------------------------------ #
    async def issue_token(self) -> str:
        """Issue (or re-issue) an access token via client_credentials grant.

        Caches the token + expiry in memory. Returns the access token.
        """
        url = f"{self._base_url}/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self._app_key,
            "client_secret": self._secret_key,
        }
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(url, data=data)
        except httpx.HTTPError as exc:
            logger.warning("Toss token request network error: {}", exc)
            raise TossUnavailable() from exc

        if resp.status_code in (400, 401):
            # invalid_client / invalid_request -> the keys are bad.
            logger.info("Toss token rejected ({}): {}", resp.status_code, resp.text)
            raise TossAuthFailed()
        if resp.status_code >= 500:
            logger.warning("Toss token 5xx: {}", resp.status_code)
            raise TossUnavailable()
        if resp.status_code != 200:
            logger.warning("Toss token unexpected status: {}", resp.status_code)
            raise TossUnavailable()

        body = resp.json()
        token = body.get("access_token")
        expires_in = body.get("expires_in", 0)
        if not token:
            logger.warning("Toss token response missing access_token: {}", body)
            raise TossUnavailable()

        self._access_token = token
        self._token_expires_at = time.monotonic() + float(expires_in) - _EXPIRY_SKEW_SECONDS
        return token

    async def _token(self) -> str:
        """Return a valid cached token, re-issuing if absent or expired."""
        if self._access_token is None or time.monotonic() >= self._token_expires_at:
            return await self.issue_token()
        return self._access_token

    async def _auth_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {await self._token()}"}
        if extra:
            headers.update(extra)
        return headers

    # ------------------------------------------------------------------ #
    # Generic GET with central error mapping + envelope unwrap
    # ------------------------------------------------------------------ #
    async def _get(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> object:
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.get(
                    url,
                    params=params,
                    headers=await self._auth_headers(headers),
                )
        except httpx.HTTPError as exc:
            logger.warning("Toss GET {} network error: {}", path, exc)
            raise TossUnavailable() from exc

        if resp.status_code == 401:
            logger.info("Toss GET {} unauthorized: {}", path, resp.text)
            raise TossAuthFailed()
        if resp.status_code >= 500:
            logger.warning("Toss GET {} 5xx: {}", path, resp.status_code)
            raise TossUnavailable()
        if resp.status_code != 200:
            logger.warning("Toss GET {} status {}: {}", path, resp.status_code, resp.text)
            raise TossUnavailable()

        body = resp.json()
        # /api/v1/* responses are enveloped as {"result": ...}.
        if isinstance(body, dict) and "result" in body:
            return body["result"]
        return body

    # ------------------------------------------------------------------ #
    # Endpoints
    # ------------------------------------------------------------------ #
    async def get_accounts(self) -> list[dict]:
        """Return account list. Each item: {accountNo, accountSeq, accountType}."""
        result = await self._get("/api/v1/accounts")
        return result if isinstance(result, list) else []

    async def get_holdings(self, account_seq: str) -> dict:
        """Return the holdings overview for an account.

        ``account_seq`` is passed via the X-Tossinvest-Account header (integer
        value, sent as string per HTTP). Result is a HoldingsOverview dict with
        keys: totalPurchaseAmount, marketValue, profitLoss, dailyProfitLoss, items.
        """
        result = await self._get(
            "/api/v1/holdings",
            headers={"X-Tossinvest-Account": str(account_seq)},
        )
        return result if isinstance(result, dict) else {}

    async def get_prices(self, symbols: list[str]) -> list[dict]:
        """Return current prices for up to 200 symbols (comma-separated query).

        Each item: {symbol, timestamp|null, lastPrice(str), currency}.
        Empty input -> empty list (no call made).
        """
        if not symbols:
            return []
        result = await self._get(
            "/api/v1/prices",
            params={"symbols": ",".join(symbols)},
        )
        return result if isinstance(result, list) else []

    async def get_exchange_rate(
        self, base_currency: str = "USD", quote_currency: str = "KRW"
    ) -> dict:
        """Return the current exchange rate (default USD->KRW).

        Result: {baseCurrency, quoteCurrency, rate(str), midRate, basisPoint,
                 rateChangeType, validFrom, validUntil}.
        """
        result = await self._get(
            "/api/v1/exchange-rate",
            params={"baseCurrency": base_currency, "quoteCurrency": quote_currency},
        )
        return result if isinstance(result, dict) else {}
