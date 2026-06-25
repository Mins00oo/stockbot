"""Portfolio routes: holdings (home screen)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from stockbot.core.db import get_session
from stockbot.core.security import verify_pairing_key
from stockbot.domain.portfolio import service
from stockbot.domain.portfolio.schemas import HoldingsResponse

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get(
    "/holdings",
    response_model=HoldingsResponse,
    dependencies=[Depends(verify_pairing_key)],
)
async def get_holdings(
    session: AsyncSession = Depends(get_session),
) -> HoldingsResponse:
    """Return the connected account's holdings, totals in KRW."""
    return await service.get_holdings(session)
