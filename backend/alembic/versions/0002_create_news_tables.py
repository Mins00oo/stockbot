"""create news tables (raw_item, item_ticker)

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-27

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "raw_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("exact_hash", sa.Text(), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_ref", sa.Text(), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("canonical_url", name="uq_raw_item_canonical_url"),
    )
    op.create_index("ix_raw_item_exact_hash", "raw_item", ["exact_hash"])

    op.create_table(
        "item_ticker",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "item_id",
            sa.Integer(),
            sa.ForeignKey("raw_item.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("market", sa.Text(), nullable=False),
        sa.Column("matched_by", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
    )
    op.create_index("ix_item_ticker_symbol", "item_ticker", ["symbol"])


def downgrade() -> None:
    op.drop_index("ix_item_ticker_symbol", table_name="item_ticker")
    op.drop_table("item_ticker")
    op.drop_index("ix_raw_item_exact_hash", table_name="raw_item")
    op.drop_table("raw_item")
