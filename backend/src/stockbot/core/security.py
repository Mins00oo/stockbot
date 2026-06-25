"""Security helpers: pairing-key auth dependency + Toss key encryption.

- ``verify_pairing_key`` is a FastAPI dependency guarding protected endpoints.
- ``encrypt`` / ``decrypt`` use Fernet (symmetric, from `cryptography`) keyed by
  settings.toss_key_enc_key, used to store Toss app/secret keys at rest.
"""

from __future__ import annotations

import secrets
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Header

from stockbot.core.config import get_settings
from stockbot.core.errors import Internal, Unauthorized

PAIRING_KEY_HEADER = "X-Pairing-Key"


async def verify_pairing_key(
    x_pairing_key: str | None = Header(default=None, alias=PAIRING_KEY_HEADER),
) -> None:
    """Reject the request unless X-Pairing-Key matches the configured secret.

    Uses a constant-time comparison to avoid timing leaks.
    """
    expected = get_settings().pairing_key
    if not x_pairing_key or not secrets.compare_digest(x_pairing_key, expected):
        raise Unauthorized()


@lru_cache
def _fernet() -> Fernet:
    """Cached Fernet built from the configured encryption key."""
    key = get_settings().toss_key_enc_key
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as exc:  # malformed / missing key
        raise Internal("암호화 키 설정이 올바르지 않아요") from exc


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string, returning the Fernet token as text."""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a Fernet token back to plaintext."""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise Internal("저장된 키를 복호화할 수 없어요") from exc
