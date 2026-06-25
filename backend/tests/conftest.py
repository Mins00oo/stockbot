"""Shared test fixtures.

Sets required env vars BEFORE the app's Settings are constructed, generates a
valid Fernet key, and provides an ASGI httpx client. The DB session and Toss
client are dependency-overridden / injected per test, so no real Postgres or
network is touched.
"""

from __future__ import annotations

import os

import pytest

# Must be set before stockbot.core.config.Settings is instantiated.
from cryptography.fernet import Fernet

PAIRING_KEY = "test-pairing-key"

os.environ.setdefault("PAIRING_KEY", PAIRING_KEY)
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://stockbot:stockbot@localhost:5432/stockbot"
)
os.environ.setdefault("TOSS_KEY_ENC_KEY", Fernet.generate_key().decode())
os.environ.setdefault("TOSS_BASE_URL", "https://openapi.tossinvest.com")


@pytest.fixture
def app():
    from stockbot.main import create_app

    return create_app()


@pytest.fixture
async def client(app):
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def auth_headers():
    return {"X-Pairing-Key": PAIRING_KEY}
