"""shift planning foundation

Revision ID: 0031_shift_planning_foundation
Revises: 0030_planning_records_foundation
Create Date: 2026-03-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0031_shift_planning_foundation"
down_revision = "0030_planning_records_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shift_plan",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("workforce_scope_code", sa.String(length=40), nullable=False, server_default="internal"),
        sa.Column("planning_from", sa.Date(), nullable=False),
        sa.Column("planning_to", sa.Date(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_ops_shift_plan_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_ops_shift_plan_tenant_record",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shift_plan")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_shift_plan_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "planning_record_id", "name", name="uq_ops_shift_plan_record_name"),
        sa.CheckConstraint("planning_to >= planning_from", name=op.f("ck_shift_plan_shift_plan_window_valid")),
        sa.CheckConstraint(
            "workforce_scope_code IN ('internal', 'subcontractor', 'mixed')",
            name=op.f("ck_shift_plan_shift_plan_workforce_scope_valid"),
        ),
        schema="ops",
    )
    op.create_index("ix_ops_shift_plan_tenant_record_window", "shift_plan", ["tenant_id", "planning_record_id", "planning_from", "planning_to"], unique=False, schema="ops")

    op.create_table(
        "shift_template",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("local_start_time", sa.Time(), nullable=False),
        sa.Column("local_end_time", sa.Time(), nullable=False),
        sa.Column("default_break_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shift_type_code", sa.String(length=80), nullable=False),
        sa.Column("meeting_point", sa.String(length=255), nullable=True),
        sa.Column("location_text", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_ops_shift_template_tenant_id_tenant", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shift_template")),
        sa.UniqueConstraint("tenant_id", "code", name="uq_ops_shift_template_tenant_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_shift_template_tenant_id_id"),
        sa.CheckConstraint("default_break_minutes >= 0", name=op.f("ck_shift_template_shift_template_break_nonnegative")),
        schema="ops",
    )
    op.create_index("ix_ops_shift_template_tenant_status", "shift_template", ["tenant_id", "status"], unique=False, schema="ops")

    op.create_table(
        "shift_series",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shift_plan_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shift_template_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("recurrence_code", sa.String(length=40), nullable=False, server_default="daily"),
        sa.Column("interval_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("weekday_mask", sa.String(length=7), nullable=True),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("date_from", sa.Date(), nullable=False),
        sa.Column("date_to", sa.Date(), nullable=False),
        sa.Column("default_break_minutes", sa.Integer(), nullable=True),
        sa.Column("shift_type_code", sa.String(length=80), nullable=True),
        sa.Column("meeting_point", sa.String(length=255), nullable=True),
        sa.Column("location_text", sa.String(length=255), nullable=True),
        sa.Column("customer_visible_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("subcontractor_visible_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("stealth_mode_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("release_state", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_ops_shift_series_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_plan_id"], ["ops.shift_plan.tenant_id", "ops.shift_plan.id"], name="fk_ops_shift_series_tenant_plan", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_template_id"], ["ops.shift_template.tenant_id", "ops.shift_template.id"], name="fk_ops_shift_series_tenant_template", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shift_series")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_shift_series_tenant_id_id"),
        sa.CheckConstraint("date_to >= date_from", name=op.f("ck_shift_series_shift_series_window_valid")),
        sa.CheckConstraint("interval_count >= 1", name=op.f("ck_shift_series_shift_series_interval_positive")),
        sa.CheckConstraint("recurrence_code IN ('daily', 'weekly')", name=op.f("ck_shift_series_shift_series_recurrence_code_valid")),
        sa.CheckConstraint("default_break_minutes IS NULL OR default_break_minutes >= 0", name=op.f("ck_shift_series_shift_series_break_nonnegative")),
        schema="ops",
    )
    op.create_index("ix_ops_shift_series_tenant_plan_window", "shift_series", ["tenant_id", "shift_plan_id", "date_from", "date_to"], unique=False, schema="ops")

    op.create_table(
        "shift",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shift_plan_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shift_series_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("occurrence_date", sa.Date(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("break_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shift_type_code", sa.String(length=80), nullable=False),
        sa.Column("location_text", sa.String(length=255), nullable=True),
        sa.Column("meeting_point", sa.String(length=255), nullable=True),
        sa.Column("release_state", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("customer_visible_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("subcontractor_visible_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("stealth_mode_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source_kind_code", sa.String(length=40), nullable=False, server_default="generated"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_ops_shift_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_plan_id"], ["ops.shift_plan.tenant_id", "ops.shift_plan.id"], name="fk_ops_shift_tenant_plan", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_series_id"], ["ops.shift_series.tenant_id", "ops.shift_series.id"], name="fk_ops_shift_tenant_series", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shift")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_ops_shift_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "shift_series_id", "occurrence_date", name="uq_ops_shift_series_occurrence"),
        sa.CheckConstraint("ends_at > starts_at", name=op.f("ck_shift_shift_window_valid")),
        sa.CheckConstraint("break_minutes >= 0", name=op.f("ck_shift_shift_break_nonnegative")),
        schema="ops",
    )
    op.create_index("ix_ops_shift_tenant_plan_starts_at", "shift", ["tenant_id", "shift_plan_id", "starts_at"], unique=False, schema="ops")
    op.create_index("ix_ops_shift_tenant_starts_at", "shift", ["tenant_id", "starts_at"], unique=False, schema="ops")
    op.create_index("ix_ops_shift_tenant_status_starts_at", "shift", ["tenant_id", "status", "starts_at"], unique=False, schema="ops")


def downgrade() -> None:
    op.drop_index("ix_ops_shift_tenant_status_starts_at", table_name="shift", schema="ops")
    op.drop_index("ix_ops_shift_tenant_starts_at", table_name="shift", schema="ops")
    op.drop_index("ix_ops_shift_tenant_plan_starts_at", table_name="shift", schema="ops")
    op.drop_table("shift", schema="ops")
    op.drop_index("ix_ops_shift_series_tenant_plan_window", table_name="shift_series", schema="ops")
    op.drop_table("shift_series", schema="ops")
    op.drop_index("ix_ops_shift_template_tenant_status", table_name="shift_template", schema="ops")
    op.drop_table("shift_template", schema="ops")
    op.drop_index("ix_ops_shift_plan_tenant_record_window", table_name="shift_plan", schema="ops")
    op.drop_table("shift_plan", schema="ops")
