"""Async SQLAlchemy engine, session factory, declarative Base, and FastAPI dep."""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from stockbot.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


@lru_cache
def get_engine() -> AsyncEngine:
    """Return a cached async engine built from settings.database_url."""
    settings = get_settings()
    return create_async_engine(settings.database_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return a cached async session factory."""
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped async session.

    Commits on success, rolls back on error, always closes.
    """
    factory = get_sessionmaker()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
