"""Auth domain service: connect a Toss account.

Flow (per API 정의서 ③ POST /auth/toss/connect):
  1. Issue a Toss token with the provided app/secret keys (validates the keys).
  2. Fetch accounts; pick the first BROKERAGE account's accountSeq.
  3. Encrypt the keys and upsert the single credentials row.
  4. Return the connected account info.

Raises only typed errors (TossAuthFailed / TossUnavailable). The global handler
formats the response body.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from stockbot.core.clients.toss import TossClient
from stockbot.core.errors import TossAuthFailed
from stockbot.core.security import encrypt
from stockbot.domain.auth import repository
from stockbot.domain.auth.schemas import (
    AccountInfo,
    AuthStatusResponse,
    TossConnectRequest,
    TossConnectResponse,
)

# The API 정의서 example uses a fixed display name for the brokerage account.
_ACCOUNT_DISPLAY_NAME = "토스증권 계좌"


async def connect_toss(
    session: AsyncSession,
    req: TossConnectRequest,
    *,
    client: TossClient | None = None,
) -> TossConnectResponse:
    """Validate Toss keys, resolve the account, and persist encrypted creds."""
    toss = client or TossClient(req.app_key, req.secret_key)

    # 1. Issue token — bad keys surface here as TossAuthFailed.
    await toss.issue_token()

    # 2. Resolve the account to use.
    accounts = await toss.get_accounts()
    if not accounts:
        # Keys are valid but no usable (brokerage) account exists.
        raise TossAuthFailed("연결할 수 있는 토스 계좌가 없어요")

    account_seq = str(accounts[0].get("accountSeq"))

    # 3. Encrypt + upsert (single row).
    await repository.upsert_credentials(
        session,
        toss_app_key_enc=encrypt(req.app_key),
        toss_secret_key_enc=encrypt(req.secret_key),
        account_seq=account_seq,
    )

    # 4. Respond.
    return TossConnectResponse(
        connected=True,
        account=AccountInfo(seq=account_seq, name=_ACCOUNT_DISPLAY_NAME),
    )


async def get_status(session: AsyncSession) -> AuthStatusResponse:
    """Connection status = whether the encrypted credentials row exists.

    The backend is the source of truth for "connected" (the app's launch gate
    asks this instead of trusting a local flag that resets on relaunch).
    """
    creds = await repository.get_credentials(session)
    return AuthStatusResponse(connected=creds is not None)
