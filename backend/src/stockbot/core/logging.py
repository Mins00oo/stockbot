"""loguru setup.

Keeps a single configured sink. File rotation is wired for later operational
use; during dev the stderr sink is the important one.
"""

from __future__ import annotations

import sys

from loguru import logger

_configured = False


def setup_logging(level: str = "INFO") -> None:
    """Configure loguru once. Safe to call multiple times."""
    global _configured
    if _configured:
        return

    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        backtrace=False,
        diagnose=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> "
            "| <level>{level: <8}</level> "
            "| <cyan>{name}</cyan>:<cyan>{function}</cyan> "
            "- <level>{message}</level>"
        ),
    )
    _configured = True
