"""shift series exceptions

Revision ID: 0032_shift_series_exceptions
Revises: 0031_shift_planning_foundation
Create Date: 2026-03-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0032_shift_series_exceptions"
down_revision = "0031_shift_planning_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shift_series_exception",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shift_series_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("exception_date", sa.Date(), nullable=False),
        sa.Column("action_code", sa.String(length=40), nullable=False),
        sa.Column("override_local_start_time", sa.Time(), nullable=True),
        sa.Column("override_local_end_time", sa.Time(), nullable=True),
        sa.Column("override_break_minutes", sa.Integer(), nullable=True),
        sa.Column("override_shift_type_code", sa.String(length=80), nullable=True),
        sa.Column("override_meeting_point", sa.String(length=255), nullable=True),
        sa.Column("override_location_text", sa.String(length=255), nullable=True),
        sa.Column("customer_visible_flag", sa.Boolean(), nullable=True),
        sa.Column("subcontractor_visible_flag", sa.Boolean(), nullable=True),
        sa.Column("stealth_mode_flag", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_ops_shift_series_exception_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_series_id"], ["ops.shift_series.tenant_id", "ops.shift_series.id"], name="fk_ops_shift_series_exception_tenant_series", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shift_series_exception")),
        sa.UniqueConstraint("tenant_id", "shift_series_id", "exception_date", name="uq_ops_shift_series_exception_date"),
        sa.CheckConstraint("action_code IN ('skip', 'override')", name=op.f("ck_shift_series_exception_shift_series_exception_action_valid")),
        sa.CheckConstraint(
            "(override_local_start_time IS NULL AND override_local_end_time IS NULL) OR "
            "(override_local_start_time IS NOT NULL AND override_local_end_time IS NOT NULL)",
            name=op.f("ck_shift_series_exception_shift_series_exception_override_time_pair"),
        ),
        sa.CheckConstraint(
            "override_break_minutes IS NULL OR override_break_minutes >= 0",
            name=op.f("ck_shift_series_exception_shift_series_exception_break_nonnegative"),
        ),
        schema="ops",
    )


def downgrade() -> None:
    op.drop_table("shift_series_exception", schema="ops")
