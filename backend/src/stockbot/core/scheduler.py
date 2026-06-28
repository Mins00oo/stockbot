"""In-process scheduler (module 17) — runs alongside the API server.

Design: APScheduler in the SAME process as FastAPI (tech-stack option A), started
from the app lifespan. Kept as a standalone module so it can later be split into a
separate worker (Postgres-coordinated) without rewriting the core.

Phase 1 registers one job: periodic news ingest. The job opens its OWN DB session
(not request-scoped) from the shared sessionmaker, runs the ingest, and commits.
Job exceptions are caught so a bad run never tears down the scheduler.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from stockbot.core.config import get_settings
from stockbot.core.db import get_sessionmaker
from stockbot.domain.news import service as news_service

_scheduler: AsyncIOScheduler | None = None


async def _news_ingest_job() -> None:
    factory = get_sessionmaker()
    async with factory() as session:
        try:
            summary = await news_service.run_ingest(session)
            await session.commit()
            logger.info("Scheduled news ingest: {}", summary.model_dump())
        except Exception:  # never let a failed run kill the scheduler
            await session.rollback()
            logger.exception("Scheduled news ingest failed")


def start() -> None:
    """Start the scheduler if enabled. No-op if already running or disabled."""
    global _scheduler
    settings = get_settings()
    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled (SCHEDULER_ENABLED=false)")
        return
    if _scheduler is not None:
        return

    interval = max(1, settings.news_poll_interval_minutes)
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        _news_ingest_job,
        trigger="interval",
        minutes=interval,
        id="news_ingest",
        max_instances=1,  # never overlap runs
        coalesce=True,  # collapse missed runs into one
        # First run shortly after boot so data shows up without waiting a full cycle.
        next_run_time=datetime.now(UTC) + timedelta(seconds=15),
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("Scheduler started: news ingest every {} min", interval)


def shutdown() -> None:
    """Stop the scheduler if running."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
