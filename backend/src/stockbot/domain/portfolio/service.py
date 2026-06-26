"""Portfolio service: assemble the holdings view (per API 정의서 ④).

Flow:
  1. Load the single credentials row; if absent -> NotConnected.
  2. Decrypt the Toss keys, build a TossClient.
  3. Fetch the holdings overview. Current price = overview lastPrice (no /prices).
  4. Map each Toss item to our Holding shape.
  5. Sort holdings by evalAmountKrw descending.

NOTE (국내 전용): 현재는 국내(KR) 종목만 다룬다. 토스 API가 해외 종목의 "원화
매입원금/손익"을 종목별로 주지 않아(달러만 제공) 정확한 원화 환산이 불가능하므로,
부정확한 환산값을 노출하느니 해외는 목록·총계에서 모두 제외한다. 총계도 토스의
국내(원화) 버킷만 합산한다. 토스 API가 해외 원화 데이터를 제공하면 되살린다.

All Toss money values arrive as STRINGS and are parsed with Decimal; results are
emitted as floats (the API contract uses JSON numbers).

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

    # 국내(KR) 종목만. 토스가 해외 종목의 원화 매입원금/손익을 종목별로 주지 않아
    # 정확한 원화 환산이 불가능하므로 해외는 제외한다(모듈 docstring 참고). 따라서
    # 환율(get_exchange_rate)도 호출하지 않는다 — 남는 건 전부 원화.
    holdings: list[Holding] = []

    for it in items:
        if it.get("marketCountry", "KR") != "KR":
            continue  # 해외(US) 제외

        symbol = str(it.get("symbol", ""))
        quantity = _dec(it.get("quantity"))
        avg_price = _dec(it.get("averagePurchasePrice"))
        # Current price = holdings snapshot lastPrice (no separate /prices call).
        current_price = _dec(it.get("lastPrice"))

        market_value = it.get("marketValue", {}) or {}
        profit_loss = it.get("profitLoss", {}) or {}

        eval_amount = _dec(market_value.get("amount"))
        pnl = _dec(profit_loss.get("amount"))
        # Toss rate is a fraction (0.1077 = 10.77%); contract wants percent.
        pnl_rate = _dec(profit_loss.get("rate")) * Decimal("100")

        # KR이므로 원화 그대로 (evalAmountKrw == evalAmount, pnlKrw == pnl).
        holdings.append(
            Holding(
                symbol=symbol,
                name=str(it.get("name", "")),
                market="KR",
                quantity=float(quantity),
                avgPrice=float(avg_price),
                currentPrice=float(current_price),
                evalAmount=float(eval_amount),
                evalAmountKrw=float(eval_amount),
                pnl=float(pnl),
                pnlKrw=float(pnl),
                pnlRate=float(round(pnl_rate, 2)),
                currency="KRW",
            )
        )

    # Sort by eval value descending (per API 정의서).
    holdings.sort(key=lambda h: h.evalAmountKrw, reverse=True)

    # 총계도 국내(원화) 버킷만 사용. 토스 overview는 통화별 버킷(amount.krw=국내,
    # amount.usd=해외 USD)을 주는데, 해외 USD를 현재환율로 환산하면 부정확해지므로
    # 국내(krw) 버킷만 합산한다. (`amount` = gross 평가금액)
    mv_amount = (overview.get("marketValue") or {}).get("amount") or {}
    pur_amount = overview.get("totalPurchaseAmount") or {}

    total_value_krw = _dec(mv_amount.get("krw"))
    total_purchase_krw = _dec(pur_amount.get("krw"))
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
