"""FastAPI application factory and ASGI entrypoint.

Wires routers (health / auth / portfolio) and registers the global exception
handlers so services only ever raise typed errors.
"""

from __future__ import annotations

from fastapi import FastAPI

from stockbot.core.error_handlers import register_exception_handlers
from stockbot.core.logging import setup_logging
from stockbot.domain.auth.router import router as auth_router
from stockbot.domain.health.router import router as health_router
from stockbot.domain.portfolio.router import router as portfolio_router


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(title="Stock Bot API", version="0.1.0")

    # Global error handling (single place — Spring @RestControllerAdvice analogue).
    register_exception_handlers(app)

    # Routers.
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(portfolio_router)

    return app


app = create_app()
