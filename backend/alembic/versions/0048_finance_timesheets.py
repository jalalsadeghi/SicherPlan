"""finance timesheets

Revision ID: 0048_finance_timesheets
Revises: 0047_finance_payslip_archive
Create Date: 2026-03-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0048_finance_timesheets"
down_revision = "0047_finance_payslip_archive"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "timesheet",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("scope_key", sa.String(length=255), nullable=False),
        sa.Column("source_hash", sa.String(length=128), nullable=False),
        sa.Column("billing_granularity_code", sa.String(length=40), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("total_planned_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_actual_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_billable_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("release_state_code", sa.String(length=40), server_default="draft", nullable=False),
        sa.Column("customer_visible_flag", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_timesheet_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "customer_id"], ["crm.customer.tenant_id", "crm.customer.id"], name="fk_finance_timesheet_tenant_customer", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["ops.customer_order.tenant_id", "ops.customer_order.id"], name="fk_finance_timesheet_tenant_order", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "planning_record_id"], ["ops.planning_record.tenant_id", "ops.planning_record.id"], name="fk_finance_timesheet_tenant_record", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_timesheet"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_timesheet_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "scope_key", name="uq_finance_timesheet_scope_key"),
        sa.CheckConstraint("period_end >= period_start", name="timesheet_period_valid"),
        sa.CheckConstraint("billing_granularity_code IN ('shift','planning_record','order_day')", name="timesheet_billing_granularity_valid"),
        sa.CheckConstraint("release_state_code IN ('draft','released','archived')", name="timesheet_release_state_valid"),
        schema="finance",
    )
    op.create_index("ix_finance_timesheet_customer_period", "timesheet", ["tenant_id", "customer_id", "period_start", "period_end"], unique=False, schema="finance")

    op.create_table(
        "timesheet_line",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("timesheet_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("actual_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("planning_mode_code", sa.String(length=40), nullable=True),
        sa.Column("line_label", sa.String(length=255), nullable=False),
        sa.Column("line_description", sa.Text(), nullable=False),
        sa.Column("planned_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("actual_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("billable_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("unit_code", sa.String(length=20), server_default="hour", nullable=False),
        sa.Column("source_ref_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("customer_safe_flag", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("personal_names_released", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_timesheet_line_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "timesheet_id"], ["finance.timesheet.tenant_id", "finance.timesheet.id"], name="fk_finance_timesheet_line_tenant_timesheet", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "actual_record_id"], ["finance.actual_record.tenant_id", "finance.actual_record.id"], name="fk_finance_timesheet_line_tenant_actual", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "shift_id"], ["ops.shift.tenant_id", "ops.shift.id"], name="fk_finance_timesheet_line_tenant_shift", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["ops.customer_order.tenant_id", "ops.customer_order.id"], name="fk_finance_timesheet_line_tenant_order", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "planning_record_id"], ["ops.planning_record.tenant_id", "ops.planning_record.id"], name="fk_finance_timesheet_line_tenant_record", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_timesheet_line"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_timesheet_line_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "timesheet_id", "actual_record_id", name="uq_finance_timesheet_line_actual_once"),
        schema="finance",
    )
    op.create_index("ix_finance_timesheet_line_timesheet_sort", "timesheet_line", ["tenant_id", "timesheet_id", "sort_order"], unique=False, schema="finance")


def downgrade() -> None:
    op.drop_index("ix_finance_timesheet_line_timesheet_sort", table_name="timesheet_line", schema="finance")
    op.drop_table("timesheet_line", schema="finance")
    op.drop_index("ix_finance_timesheet_customer_period", table_name="timesheet", schema="finance")
    op.drop_table("timesheet", schema="finance")
