"""Persistence for the single Credentials row (id == 1)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from stockbot.domain.auth.models import Credentials

# The credentials table holds exactly one logical row.
_SINGLETON_ID = 1


async def get_credentials(session: AsyncSession) -> Credentials | None:
    """Return the stored credentials row, or None if not connected yet."""
    result = await session.execute(
        select(Credentials).where(Credentials.id == _SINGLETON_ID)
    )
    return result.scalar_one_or_none()


async def upsert_credentials(
    session: AsyncSession,
    *,
    toss_app_key_enc: str,
    toss_secret_key_enc: str,
    account_seq: str,
) -> Credentials:
    """Insert or update the single credentials row.

    Caller is responsible for committing (the get_session dependency commits on
    success).
    """
    existing = await get_credentials(session)
    if existing is None:
        existing = Credentials(
            id=_SINGLETON_ID,
            toss_app_key_enc=toss_app_key_enc,
            toss_secret_key_enc=toss_secret_key_enc,
            account_seq=account_seq,
        )
        session.add(existing)
    else:
        existing.toss_app_key_enc = toss_app_key_enc
        existing.toss_secret_key_enc = toss_secret_key_enc
        existing.account_seq = account_seq

    await session.flush()
    return existing
