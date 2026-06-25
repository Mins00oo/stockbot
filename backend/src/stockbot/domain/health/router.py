"""Health route (public — no pairing key required)."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}
