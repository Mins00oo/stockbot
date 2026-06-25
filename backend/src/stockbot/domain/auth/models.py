"""ORM models for the auth domain."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from stockbot.core.db import Base


class Credentials(Base):
    """Single-row table holding the encrypted Toss keys + account seq.

    Only one row ever exists (id == 1); see the repository's upsert.
    """

    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    toss_app_key_enc: Mapped[str] = mapped_column(Text, nullable=False)
    toss_secret_key_enc: Mapped[str] = mapped_column(Text, nullable=False)
    account_seq: Mapped[str] = mapped_column(Text, nullable=False)
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
