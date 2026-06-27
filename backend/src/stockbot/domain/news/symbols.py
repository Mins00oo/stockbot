"""Target-symbol provider for the news pipeline (extension point).

Phase 1: the targets are the user's Toss holdings (KR + US — note the portfolio
*display* service is KR-only, but news covers both markets). When a watchlist
feature lands, union its symbols in here; nothing downstream changes.
"""

from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from stockbot.core.clients.toss import TossClient
from stockbot.core.security import decrypt
from stockbot.domain.auth import repository as auth_repository


class TargetSymbol(BaseModel):
    symbol: str
    market: str  # KR | US
    name: str


async def get_target_symbols(
    session: AsyncSession, *, client: TossClient | None = None
) -> list[TargetSymbol]:
    """Return the symbols to scrape news for. Empty list if Toss isn't connected
    (caller treats that as a graceful skip, not an error)."""
    creds = await auth_repository.get_credentials(session)
    if creds is None:
        return []

    toss = client or TossClient(
        app_key=decrypt(creds.toss_app_key_enc),
        secret_key=decrypt(creds.toss_secret_key_enc),
    )
    overview = await toss.get_holdings(creds.account_seq)
    items: list[dict] = overview.get("items", []) or []

    out: list[TargetSymbol] = []
    seen: set[str] = set()
    for it in items:
        symbol = str(it.get("symbol") or "").strip()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        market = "KR" if it.get("marketCountry", "KR") == "KR" else "US"
        out.append(
            TargetSymbol(symbol=symbol, market=market, name=str(it.get("name") or symbol))
        )
    return out
