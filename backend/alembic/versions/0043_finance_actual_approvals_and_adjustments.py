"""finance actual approvals and adjustments

Revision ID: 0043_finance_actual_approvals_and_adjustments
Revises: 0042_finance_actual_records
Create Date: 2026-03-20 00:00:04.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0043_finance_actual_approvals_and_adjustments"
down_revision = "0042_finance_actual_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "actual_record",
        sa.Column("approval_stage_code", sa.String(length=40), nullable=False, server_default="draft"),
        schema="finance",
    )
    op.create_check_constraint(
        op.f("ck_actual_record_actual_record_approval_stage_valid"),
        "actual_record",
        "approval_stage_code IN ('draft','preliminary_submitted','operational_confirmed','finance_signed_off')",
        schema="finance",
    )

    op.create_table(
        "actual_approval",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("actual_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("stage_code", sa.String(length=40), nullable=False),
        sa.Column("actor_scope_code", sa.String(length=40), nullable=False),
        sa.Column("note_text", sa.String(length=1000), nullable=True),
        sa.Column("source_ref_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "stage_code IN ('preliminary_submitted','operational_confirmed','finance_signed_off')",
            name=op.f("ck_actual_approval_actual_approval_stage_valid"),
        ),
        sa.CheckConstraint(
            "actor_scope_code IN ('employee_self','field_lead','operational_lead','finance')",
            name=op.f("ck_actual_approval_actual_approval_actor_scope_valid"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_actual_approval_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_approval_tenant_actual",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actual_approval")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_actual_approval_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "actual_record_id", "stage_code", name="uq_finance_actual_approval_stage"),
        schema="finance",
    )

    op.create_table(
        "actual_reconciliation",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("actual_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("reconciliation_kind_code", sa.String(length=40), nullable=False),
        sa.Column("reason_code", sa.String(length=60), nullable=False),
        sa.Column("note_text", sa.String(length=1000), nullable=True),
        sa.Column("payroll_minutes_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("billable_minutes_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("customer_adjustment_minutes_delta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replacement_actor_type_code", sa.String(length=40), nullable=True),
        sa.Column("replacement_employee_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("replacement_subcontractor_worker_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("source_ref_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "reconciliation_kind_code IN ('sickness','cancellation','replacement','customer_adjustment','flat_rate')",
            name=op.f("ck_actual_reconciliation_actual_reconciliation_kind_valid"),
        ),
        sa.CheckConstraint(
            "replacement_actor_type_code IS NULL OR replacement_actor_type_code IN ('employee','subcontractor_worker')",
            name=op.f("ck_actual_reconciliation_actual_reconciliation_replacement_actor_type_valid"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_actual_reconciliation_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_reconciliation_tenant_actual",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "replacement_employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_finance_actual_reconciliation_tenant_employee",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "replacement_subcontractor_worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_finance_actual_reconciliation_tenant_worker",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actual_reconciliation")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_actual_reconciliation_tenant_id_id"),
        schema="finance",
    )

    op.create_table(
        "actual_allowance",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("actual_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("line_type_code", sa.String(length=40), nullable=False),
        sa.Column("reason_code", sa.String(length=60), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False, server_default="1"),
        sa.Column("unit_code", sa.String(length=40), nullable=True),
        sa.Column("amount_total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("source_ref_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("note_text", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "line_type_code IN ('allowance','flat_rate','customer_flat_rate')",
            name=op.f("ck_actual_allowance_actual_allowance_line_type_valid"),
        ),
        sa.CheckConstraint("quantity >= 0", name=op.f("ck_actual_allowance_actual_allowance_quantity_nonnegative")),
        sa.CheckConstraint("amount_total >= 0", name=op.f("ck_actual_allowance_actual_allowance_amount_nonnegative")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_actual_allowance_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_allowance_tenant_actual",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actual_allowance")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_actual_allowance_tenant_id_id"),
        schema="finance",
    )

    op.create_table(
        "actual_expense",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("actual_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("expense_type_code", sa.String(length=40), nullable=False),
        sa.Column("reason_code", sa.String(length=60), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False, server_default="1"),
        sa.Column("unit_code", sa.String(length=40), nullable=True),
        sa.Column("amount_total", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("source_ref_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("note_text", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("quantity >= 0", name=op.f("ck_actual_expense_actual_expense_quantity_nonnegative")),
        sa.CheckConstraint("amount_total >= 0", name=op.f("ck_actual_expense_actual_expense_amount_nonnegative")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_actual_expense_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_expense_tenant_actual",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actual_expense")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_actual_expense_tenant_id_id"),
        schema="finance",
    )

    op.create_table(
        "actual_comment",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("actual_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("visibility_code", sa.String(length=40), nullable=False, server_default="finance_only"),
        sa.Column("note_text", sa.String(length=2000), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "visibility_code IN ('shared','finance_only')",
            name=op.f("ck_actual_comment_actual_comment_visibility_valid"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_actual_comment_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "actual_record_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_comment_tenant_actual",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actual_comment")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_actual_comment_tenant_id_id"),
        schema="finance",
    )


def downgrade() -> None:
    op.drop_table("actual_comment", schema="finance")
    op.drop_table("actual_expense", schema="finance")
    op.drop_table("actual_allowance", schema="finance")
    op.drop_table("actual_reconciliation", schema="finance")
    op.drop_table("actual_approval", schema="finance")
    op.drop_constraint(op.f("ck_actual_record_actual_record_approval_stage_valid"), "actual_record", schema="finance")
    op.drop_column("actual_record", "approval_stage_code", schema="finance")
