"""Global exception handlers.

Convert typed AppErrors and FastAPI request-validation failures into the
standard error envelope:  {"error": {"code", "message"}} + HTTP status.
Registered once in main.py (Spring's @RestControllerAdvice equivalent).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from stockbot.core.errors import AppError, Internal, ValidationError


def _envelope(code: str, message: str) -> dict[str, dict[str, str]]:
    return {"error": {"code": code, "message": message}}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    if exc.status >= 500:
        logger.error("AppError {} on {}: {}", exc.code, request.url.path, exc.message)
    else:
        logger.info("AppError {} on {}: {}", exc.code, request.url.path, exc.message)
    return JSONResponse(
        status_code=exc.status,
        content=_envelope(exc.code, exc.message),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Map FastAPI/Pydantic body validation to our VALIDATION_ERROR catalog entry.
    err = ValidationError()
    logger.info("Validation error on {}: {}", request.url.path, exc.errors())
    return JSONResponse(
        status_code=err.status,
        content=_envelope(err.code, err.message),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Anything not caught above is an internal error — never leak details.
    err = Internal()
    logger.exception("Unhandled error on {}: {}", request.url.path, exc)
    return JSONResponse(
        status_code=err.status,
        content=_envelope(err.code, err.message),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Wire all handlers onto the app (called from main.py)."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
