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

Token caching: ONE access token per app_key, shared process-wide (not per
instance) and issued under a lock, so concurrent requests reuse the same token
instead of each minting one. Toss invalidates the previous token on re-issue, so
holding exactly one avoids requests stomping each other's tokens. In-memory =>
single worker only; back this with DB/Redis if you ever run multiple workers.
"""

from __future__ import annotations

import asyncio
import time

import httpx
from loguru import logger

from stockbot.core.config import get_settings
from stockbot.core.errors import TossAuthFailed, TossUnavailable

# Re-issue a bit before the real expiry to avoid edge-of-expiry 401s.
_EXPIRY_SKEW_SECONDS = 60
_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

# Process-wide token cache keyed by app_key: app_key -> (token, expiry_monotonic).
# Shared across all TossClient instances/requests so we never hold >1 token per
# app_key. `_token_locks` serializes issuance per app_key (one issue at a time;
# others wait and reuse). In-memory => single worker only (see module docstring).
_token_cache: dict[str, tuple[str, float]] = {}
_token_locks: dict[str, asyncio.Lock] = {}


def _lock_for(app_key: str) -> asyncio.Lock:
    lock = _token_locks.get(app_key)
    if lock is None:
        lock = asyncio.Lock()
        _token_locks[app_key] = lock
    return lock


class TossClient:
    """Async client. The access token is shared per app_key (see module
    docstring), so instances are cheap and safe to create per request."""

    def __init__(self, app_key: str, secret_key: str) -> None:
        self._app_key = app_key
        self._secret_key = secret_key
        self._base_url = get_settings().toss_base_url.rstrip("/")

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

        expiry = time.monotonic() + float(expires_in) - _EXPIRY_SKEW_SECONDS
        _token_cache[self._app_key] = (token, expiry)
        return token

    async def ensure_token(self) -> str:
        """Return a valid token for this app_key, issuing once (under a lock)
        only if absent/expired. Concurrent callers reuse the same token rather
        than each issuing one (which would invalidate the others)."""
        cached = _token_cache.get(self._app_key)
        if cached is not None and time.monotonic() < cached[1]:
            return cached[0]
        async with _lock_for(self._app_key):
            cached = _token_cache.get(self._app_key)  # re-check after the lock
            if cached is not None and time.monotonic() < cached[1]:
                return cached[0]
            return await self.issue_token()

    async def _token(self) -> str:
        return await self.ensure_token()

    async def _reissue_after_401(self, stale_token: str) -> None:
        """A 401 means our token was invalidated (e.g. an external re-issue).
        Drop it and issue a fresh one — but only if nobody already refreshed it
        (compare-and-swap under the lock), so concurrent 401s don't stampede."""
        async with _lock_for(self._app_key):
            cached = _token_cache.get(self._app_key)
            if (
                cached is not None
                and cached[0] != stale_token
                and time.monotonic() < cached[1]
            ):
                return  # someone already refreshed; the retry will reuse it
            await self.issue_token()

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
        # Two attempts: if the first 401s (token invalidated out from under us),
        # re-issue once and retry. A second 401 is a real auth failure.
        for attempt in (1, 2):
            token = await self.ensure_token()
            req_headers = {"Authorization": f"Bearer {token}"}
            if headers:
                req_headers.update(headers)
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.get(url, params=params, headers=req_headers)
            except httpx.HTTPError as exc:
                logger.warning("Toss GET {} network error: {}", path, exc)
                raise TossUnavailable() from exc

            if resp.status_code == 401:
                logger.info(
                    "Toss GET {} unauthorized (attempt {}): {}", path, attempt, resp.text
                )
                if attempt == 1:
                    await self._reissue_after_401(token)
                    continue
                raise TossAuthFailed()
            if resp.status_code >= 500:
                logger.warning("Toss GET {} 5xx: {}", path, resp.status_code)
                raise TossUnavailable()
            if resp.status_code != 200:
                logger.warning(
                    "Toss GET {} status {}: {}", path, resp.status_code, resp.text
                )
                raise TossUnavailable()

            body = resp.json()
            # /api/v1/* responses are enveloped as {"result": ...}.
            if isinstance(body, dict) and "result" in body:
                return body["result"]
            return body

        # Unreachable: every path above returns or raises.
        raise TossAuthFailed()

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

    # ------------------------------------------------------------------ #
    # Market data for the stock-detail screen (no account header needed)
    # ------------------------------------------------------------------ #
    async def get_candles(
        self,
        symbol: str,
        interval: str,
        *,
        count: int = 200,
        before: str | None = None,
    ) -> list[dict]:
        """Return OHLCV candles. ``interval`` is "1m" (minute) or "1d" (daily).

        Each item: {timestamp, openPrice, highPrice, lowPrice, closePrice,
        volume, currency}. count clamped to Toss max (1..200).
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "count": str(max(1, min(count, 200))),
        }
        if before:
            params["before"] = before
        result = await self._get("/api/v1/candles", params=params)
        if isinstance(result, dict):
            candles = result.get("candles")
            return candles if isinstance(candles, list) else []
        return result if isinstance(result, list) else []

    async def get_daily_candles(self, symbol: str, *, total: int = 252) -> list[dict]:
        """Fetch up to ~``total`` most-recent DAILY candles, paginating via the
        ``nextBefore`` cursor (Toss caps each call at 200). Used for a true
        52-week (≈1 year) high/low and the 1Y chart. Candles may span pages —
        the caller should sort by timestamp."""
        out: list[dict] = []
        before: str | None = None
        for _ in range(4):  # 252d ~= 2 pages; iteration cap as a backstop
            remaining = total - len(out)
            if remaining <= 0:
                break
            params = {
                "symbol": symbol,
                "interval": "1d",
                "count": str(max(1, min(remaining, 200))),
            }
            if before:
                params["before"] = before
            result = await self._get("/api/v1/candles", params=params)
            if isinstance(result, dict):
                candles = result.get("candles") or []
                next_before = result.get("nextBefore")
            elif isinstance(result, list):
                candles = result
                next_before = None
            else:
                break
            if not candles:
                break
            out.extend(candles)
            if not next_before:
                break
            before = str(next_before)
        return out

    async def get_orderbook(self, symbol: str) -> dict:
        """Return the 10-level orderbook snapshot.

        Result: {timestamp, currency, asks: [{price, volume}], bids: [{price, volume}]}.
        """
        result = await self._get("/api/v1/orderbook", params={"symbol": symbol})
        return result if isinstance(result, dict) else {}

    async def get_trades(self, symbol: str, *, count: int = 50) -> list[dict]:
        """Return recent executed trades (Toss max 50). Each: {price, volume,
        timestamp, currency}. Toss does NOT expose a buy/sell side flag."""
        result = await self._get(
            "/api/v1/trades",
            params={"symbol": symbol, "count": str(max(1, min(count, 50)))},
        )
        if isinstance(result, dict):
            trades = result.get("trades")
            return trades if isinstance(trades, list) else []
        return result if isinstance(result, list) else []

    async def get_price_limits(self, symbol: str) -> dict:
        """Return daily price limits: {timestamp, upperLimitPrice, lowerLimitPrice,
        currency}. Limits may be null (e.g. US stocks have no daily limit)."""
        result = await self._get("/api/v1/price-limits", params={"symbol": symbol})
        return result if isinstance(result, dict) else {}

    async def get_stock_info(self, symbol: str) -> dict:
        """Return one stock's basic info via /stocks?symbols= (returns first match).

        Fields incl: symbol, name, englishName, market, currency,
        sharesOutstanding, securityType, status, listDate, koreanMarketDetail.
        """
        result = await self._get("/api/v1/stocks", params={"symbols": symbol})
        if isinstance(result, list):
            return result[0] if result else {}
        if isinstance(result, dict):
            items = result.get("stocks") or result.get("items")
            if isinstance(items, list):
                return items[0] if items else {}
            return result
        return {}

    async def get_stock_warnings(self, symbol: str) -> list[dict]:
        """Return KR market-warning flags. Each: {warningType, exchange, startDate,
        endDate}. warningType enum incl. LIQUIDATION_TRADING, OVERHEATED,
        INVESTMENT_WARNING, INVESTMENT_RISK, VI_STATIC, VI_DYNAMIC,
        VI_STATIC_AND_DYNAMIC, STOCK_WARRANTS."""
        result = await self._get(f"/api/v1/stocks/{symbol}/warnings")
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            items = result.get("warnings") or result.get("items")
            return items if isinstance(items, list) else []
        return []
