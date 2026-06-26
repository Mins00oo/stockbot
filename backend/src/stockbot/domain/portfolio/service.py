"""Portfolio service: assemble the holdings view (per API 정의서 ④).

Flow:
  1. Load the single credentials row; if absent -> NotConnected.
  2. Decrypt the Toss keys, build a TossClient.
  3. Fetch the holdings overview (+ USD->KRW rate, only when a US holding exists).
     Current price = the overview's lastPrice; we do NOT call /prices.
  4. Map each Toss item to our Holding shape, converting USD evals to KRW.
  5. Sort holdings by evalAmountKrw descending. Account-level totals: Toss's
     overview gives per-currency buckets (krw = domestic, usd = foreign in USD)
     with no combined total, so we add the USD bucket converted at the Toss FX
     rate to the KRW bucket.

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
        pnl_krw = pnl * usd_to_krw if currency == "USD" else pnl

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
                pnlKrw=float(pnl_krw),
                pnlRate=float(round(pnl_rate, 2)),
                currency=currency,
            )
        )

    # Sort by KRW eval value descending (per API 정의서).
    holdings.sort(key=lambda h: h.evalAmountKrw, reverse=True)

    # Account-level totals in KRW. Toss's overview gives per-CURRENCY buckets
    # (amount.krw = domestic, amount.usd = foreign in USD) with NO combined total,
    # so we convert the USD bucket at the same Toss FX rate and add it to the KRW
    # bucket. (`amount` = gross 평가금액, matching the Toss app; `amountAfterCost`
    # would be net of selling costs.)
    mv_amount = (overview.get("marketValue") or {}).get("amount") or {}
    pur_amount = overview.get("totalPurchaseAmount") or {}

    total_value_krw = _dec(mv_amount.get("krw")) + _dec(mv_amount.get("usd")) * usd_to_krw
    total_purchase_krw = (
        _dec(pur_amount.get("krw")) + _dec(pur_amount.get("usd")) * usd_to_krw
    )
    # PnL derived from the KRW totals so on-screen numbers reconcile (Toss's own
    # profitLoss.rate is cost-adjusted and would not match value - purchase here).
    total_pnl_krw = total_value_krw - total_purchase_krw
    total_pnl_rate = (
        total_pnl_krw / total_purchase_krw * Decimal("100")
        if total_purchase_krw
        else Decimal("0")
    )

    return HoldingsResponse(
        totalValueKrw=float(total_value_krw),
        totalPnlKrw=float(total_pnl_krw),
        totalPnlRate=float(round(total_pnl_rate, 2)),
        totalPurchaseKrw=float(total_purchase_krw),
        holdings=holdings,
    )
