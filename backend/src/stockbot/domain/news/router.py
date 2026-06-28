"""News routes: list stored items + manual ingest trigger. Pairing-key guarded."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from stockbot.core.db import get_session
from stockbot.core.security import verify_pairing_key
from stockbot.domain.news import service
from stockbot.domain.news.schemas import IngestRunResponse, NewsListResponse

router = APIRouter(
    prefix="/news",
    tags=["news"],
    dependencies=[Depends(verify_pairing_key)],
)


@router.get("", response_model=NewsListResponse)
async def list_news(
    symbol: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> NewsListResponse:
    """Recent stored news (newest first), optionally filtered to a symbol."""
    return await service.list_news(session, symbol=symbol, limit=limit, offset=offset)


@router.post("/ingest/run", response_model=IngestRunResponse)
async def run_ingest(
    session: AsyncSession = Depends(get_session),
) -> IngestRunResponse:
    """Trigger one ingest run now (independent of the scheduler) — for testing
    and on-demand refresh. Returns a {fetched, stored, deduped} summary."""
    return await service.run_ingest(session)
