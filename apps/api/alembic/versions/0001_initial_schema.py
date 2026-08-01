"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-30 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("decision_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("preferred_zone", sa.String(length=80), nullable=False),
        sa.Column("plan_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "venues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("zone", sa.String(length=80), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("average_drink_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("opening_time", sa.Time(), nullable=False),
        sa.Column("closing_time", sa.Time(), nullable=False),
        sa.Column("minimum_age", sa.Integer(), nullable=False),
        sa.Column("music_tags", sa.JSON(), nullable=False),
        sa.Column("ambience_tags", sa.JSON(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("data_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("budget", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_entry_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("origin_zone", sa.String(length=80), nullable=False),
        sa.Column("transport_type", sa.String(length=40), nullable=False),
        sa.Column("consumption_level", sa.String(length=40), nullable=False),
        sa.Column("max_return_time", sa.Time(), nullable=True),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.Column("restrictions", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "venue_id",
            sa.Integer(),
            sa.ForeignKey("venues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("estimated_average_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("all_within_budget", sa.Boolean(), nullable=False),
        sa.Column("average_travel_minutes", sa.Integer(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("tradeoffs", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "participant_costs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "recommendation_id",
            sa.Integer(),
            sa.ForeignKey("recommendations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "participant_id",
            sa.Integer(),
            sa.ForeignKey("participants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entry_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("consumption_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("transport_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("remaining_budget", sa.Numeric(10, 2), nullable=False),
        sa.Column("within_budget", sa.Boolean(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("participant_costs")
    op.drop_table("recommendations")
    op.drop_table("participants")
    op.drop_table("venues")
    op.drop_table("plans")
