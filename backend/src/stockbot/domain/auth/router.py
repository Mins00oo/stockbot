"""Auth routes: pairing-key verify + Toss account connect.

Both endpoints are guarded by the pairing-key dependency.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from stockbot.core.db import get_session
from stockbot.core.security import verify_pairing_key
from stockbot.domain.auth import service
from stockbot.domain.auth.schemas import (
    PairingVerifyResponse,
    TossConnectRequest,
    TossConnectResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/pairing/verify",
    response_model=PairingVerifyResponse,
    dependencies=[Depends(verify_pairing_key)],
)
async def verify_pairing() -> PairingVerifyResponse:
    """Onboarding step 1: confirm the pairing key (auth handled by dependency)."""
    return PairingVerifyResponse(valid=True)


@router.post(
    "/toss/connect",
    response_model=TossConnectResponse,
    dependencies=[Depends(verify_pairing_key)],
)
async def connect_toss(
    body: TossConnectRequest,
    session: AsyncSession = Depends(get_session),
) -> TossConnectResponse:
    """Onboarding step 2: connect the Toss account using app/secret keys."""
    return await service.connect_toss(session, body)
