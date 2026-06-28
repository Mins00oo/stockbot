"""FastAPI application factory and ASGI entrypoint.

Wires routers (health / auth / portfolio) and registers the global exception
handlers so services only ever raise typed errors.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from stockbot.core import scheduler
from stockbot.core.error_handlers import register_exception_handlers
from stockbot.core.logging import setup_logging
from stockbot.domain.auth.router import router as auth_router
from stockbot.domain.health.router import router as health_router
from stockbot.domain.news.router import router as news_router
from stockbot.domain.portfolio.router import router as portfolio_router
from stockbot.domain.stocks.router import router as stocks_router

# Windows only: psycopg's async mode can't run on the default ProactorEventLoop,
# so force the SelectorEventLoop before uvicorn creates the loop. (Set at import
# time, before serving.) Guarded by platform → no-op on Linux (the prod VM).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start the in-process scheduler on boot, stop it on shutdown.

    Note: httpx's ASGITransport (used in tests) does NOT run lifespan, so the
    scheduler stays off in tests; SCHEDULER_ENABLED=false is an explicit switch.
    """
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(title="Stock Bot API", version="0.1.0", lifespan=lifespan)

    # Global error handling (single place — Spring @RestControllerAdvice analogue).
    register_exception_handlers(app)

    # Routers.
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(portfolio_router)
    app.include_router(stocks_router)
    app.include_router(news_router)

    return app


app = create_app()
