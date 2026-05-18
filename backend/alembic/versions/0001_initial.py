"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("daily_budget", sa.Numeric(), nullable=True),
        sa.Column("lifetime_budget", sa.Numeric(), nullable=True),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("stop_time", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ad_sets",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("campaign_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("daily_budget", sa.Numeric(), nullable=True),
        sa.Column("lifetime_budget", sa.Numeric(), nullable=True),
        sa.Column("targeting", JSON(), nullable=True),
        sa.Column("bid_strategy", sa.Text(), nullable=True),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ads",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("ad_set_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("creative", JSON(), nullable=True),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "insights",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("ad_id", sa.Text(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=True),
        sa.Column("clicks", sa.Integer(), nullable=True),
        sa.Column("spend", sa.Numeric(), nullable=True),
        sa.Column("reach", sa.Integer(), nullable=True),
        sa.Column("frequency", sa.Numeric(), nullable=True),
        sa.Column("ctr", sa.Numeric(), nullable=True),
        sa.Column("cpc", sa.Numeric(), nullable=True),
        sa.Column("cpm", sa.Numeric(), nullable=True),
        sa.Column("conversions", sa.Integer(), nullable=True),
        sa.Column("conversion_value", sa.Numeric(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ad_id", "date", name="uq_insights_ad_id_date"),
    )


def downgrade() -> None:
    op.drop_table("insights")
    op.drop_table("ads")
    op.drop_table("ad_sets")
    op.drop_table("campaigns")
