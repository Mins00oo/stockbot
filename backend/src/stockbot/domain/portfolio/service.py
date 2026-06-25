"""Portfolio service: assemble the holdings view (per API 정의서 ④).

Flow:
  1. Load the single credentials row; if absent -> NotConnected.
  2. Decrypt the Toss keys, build a TossClient.
  3. Fetch holdings (+ prices for current-price freshness, + USD->KRW rate).
  4. Map each Toss HoldingsItem to our Holding shape, converting USD evals to KRW.
  5. Compute totals in KRW; sort holdings by evalAmountKrw descending.

All Toss money values arrive as STRINGS and are parsed with Decimal; results are
emitted as floats (the API contract uses JSON numbers). Only KRW/USD are handled.

Raises only typed errors (NotConnected / TossAuthFailed / TossUnavailable).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from stockbot.core.clients.toss import TossClient
from stockbot.core.errors import NotConnected
from stockbot.core.security import decrypt
from stockbot.domain.auth import repository
from stockbot.domain.portfolio.schemas import Holding, HoldingsResponse


def _dec(value: object, default: str = "0") -> Decimal:
    """Parse a Toss string/number into Decimal, tolerating None/garbage."""
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        logger.warning("Could not parse decimal from {!r}; using {}", value, default)
        return Decimal(default)


async def get_holdings(
    session: AsyncSession,
    *,
    client: TossClient | None = None,
) -> HoldingsResponse:
    """Build the holdings response for the connected account."""
    creds = await repository.get_credentials(session)
    if creds is None:
        raise NotConnected()

    toss = client or TossClient(
        app_key=decrypt(creds.toss_app_key_enc),
        secret_key=decrypt(creds.toss_secret_key_enc),
    )

    overview = await toss.get_holdings(creds.account_seq)
    items: list[dict] = overview.get("items", []) or []

    # USD -> KRW rate (only if a US holding exists), used to convert each US
    # holding's eval amount to KRW for sorting/display.
    has_usd = any((it.get("currency") == "USD") for it in items)
    usd_to_krw = Decimal("0")
    if has_usd:
        rate = await toss.get_exchange_rate(base_currency="USD", quote_currency="KRW")
        usd_to_krw = _dec(rate.get("rate"))

    holdings: list[Holding] = []

    for it in items:
        symbol = str(it.get("symbol", ""))
        currency = it.get("currency", "KRW")
        market = it.get("marketCountry", "KR")

        quantity = _dec(it.get("quantity"))
        avg_price = _dec(it.get("averagePurchasePrice"))
        # Current price = holdings snapshot lastPrice. Live freshness comes from
        # the frontend re-fetching /holdings every 3s (no separate /prices call).
        current_price = _dec(it.get("lastPrice"))

        market_value = it.get("marketValue", {}) or {}
        profit_loss = it.get("profitLoss", {}) or {}

        eval_amount = _dec(market_value.get("amount"))
        pnl = _dec(profit_loss.get("amount"))
        # Toss rate is a fraction (0.1077 = 10.77%); contract wants percent.
        pnl_rate = _dec(profit_loss.get("rate")) * Decimal("100")

        # KRW conversion for sorting/display: KRW 1:1, USD uses the rate.
        eval_amount_krw = eval_amount * usd_to_krw if currency == "USD" else eval_amount

        holdings.append(
            Holding(
                symbol=symbol,
                name=str(it.get("name", "")),
                market=market,
                quantity=float(quantity),
                avgPrice=float(avg_price),
                currentPrice=float(current_price),
                evalAmount=float(eval_amount),
                evalAmountKrw=float(eval_amount_krw),
                pnl=float(pnl),
                pnlRate=float(round(pnl_rate, 2)),
                currency=currency,
            )
        )

    # Sort by KRW eval value descending (per API 정의서).
    holdings.sort(key=lambda h: h.evalAmountKrw, reverse=True)

    # Account-level totals come DIRECTLY from Toss's overview (raw, FX-/cost-adjusted
    # by Toss) — NOT summed/derived by us — so our numbers match the Toss app exactly.
    mv_krw = _dec(((overview.get("marketValue") or {}).get("amount") or {}).get("krw"))
    pl = overview.get("profitLoss") or {}
    pnl_krw_total = _dec((pl.get("amount") or {}).get("krw"))
    pnl_rate_total = _dec(pl.get("rate")) * Decimal("100")  # Toss gives a fraction
    purchase_krw = _dec((overview.get("totalPurchaseAmount") or {}).get("krw"))

    return HoldingsResponse(
        totalValueKrw=float(mv_krw),
        totalPnlKrw=float(pnl_krw_total),
        totalPnlRate=float(round(pnl_rate_total, 2)),
        totalPurchaseKrw=float(purchase_krw),
        holdings=holdings,
    )
