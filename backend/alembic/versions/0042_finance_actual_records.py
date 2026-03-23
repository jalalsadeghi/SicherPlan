"""finance actual bridge records

Revision ID: 0042_finance_actual_records
Revises: 0041_field_attendance_records
Create Date: 2026-03-20 00:00:03.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0042_finance_actual_records"
down_revision = "0041_field_attendance_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS finance")
    op.create_table(
        "actual_record",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("attendance_record_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("actor_type_code", sa.String(length=40), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("subcontractor_worker_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("planned_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_break_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actual_break_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payable_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("billable_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("customer_adjustment_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("discrepancy_state_code", sa.String(length=40), nullable=False, server_default="clean"),
        sa.Column("discrepancy_codes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("discrepancy_details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("derivation_status_code", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("derived_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_by_actual_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint(
            "actor_type_code IN ('employee','subcontractor_worker')",
            name=op.f("ck_actual_record_actual_record_actor_type_valid"),
        ),
        sa.CheckConstraint(
            "(employee_id IS NOT NULL AND subcontractor_worker_id IS NULL AND actor_type_code = 'employee') OR "
            "(employee_id IS NULL AND subcontractor_worker_id IS NOT NULL AND actor_type_code = 'subcontractor_worker')",
            name=op.f("ck_actual_record_actual_record_actor_reference_valid"),
        ),
        sa.CheckConstraint(
            "discrepancy_state_code IN ('clean','warning','needs_review')",
            name=op.f("ck_actual_record_actual_record_discrepancy_state_valid"),
        ),
        sa.CheckConstraint(
            "derivation_status_code IN ('draft','derived','needs_review','superseded')",
            name=op.f("ck_actual_record_actual_record_derivation_status_valid"),
        ),
        sa.CheckConstraint("planned_break_minutes >= 0", name=op.f("ck_actual_record_actual_record_planned_break_nonnegative")),
        sa.CheckConstraint("actual_break_minutes >= 0", name=op.f("ck_actual_record_actual_record_actual_break_nonnegative")),
        sa.CheckConstraint("payable_minutes >= 0", name=op.f("ck_actual_record_actual_record_payable_nonnegative")),
        sa.CheckConstraint("billable_minutes >= 0", name=op.f("ck_actual_record_actual_record_billable_nonnegative")),
        sa.CheckConstraint(
            "customer_adjustment_minutes >= 0",
            name=op.f("ck_actual_record_actual_record_customer_adjustment_nonnegative"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_actual_record_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["ops.assignment.tenant_id", "ops.assignment.id"],
            name="fk_finance_actual_record_tenant_assignment",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_finance_actual_record_tenant_shift",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "attendance_record_id"],
            ["field.attendance_record.tenant_id", "field.attendance_record.id"],
            name="fk_finance_actual_record_tenant_attendance",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_finance_actual_record_tenant_employee",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "subcontractor_worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_finance_actual_record_tenant_worker",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "superseded_by_actual_id"],
            ["finance.actual_record.tenant_id", "finance.actual_record.id"],
            name="fk_finance_actual_record_tenant_superseded_by",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actual_record")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_actual_record_tenant_id_id"),
        schema="finance",
    )
    op.create_index(
        "ix_finance_actual_record_shift_derived",
        "actual_record",
        ["tenant_id", "shift_id", "derived_at"],
        unique=False,
        schema="finance",
    )
    op.create_index(
        "ix_finance_actual_record_attendance",
        "actual_record",
        ["tenant_id", "attendance_record_id"],
        unique=False,
        schema="finance",
    )
    op.create_index(
        "uq_finance_actual_record_assignment_current",
        "actual_record",
        ["tenant_id", "assignment_id"],
        unique=True,
        schema="finance",
        postgresql_where=sa.text("is_current = true AND archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_finance_actual_record_assignment_current", table_name="actual_record", schema="finance")
    op.drop_index("ix_finance_actual_record_attendance", table_name="actual_record", schema="finance")
    op.drop_index("ix_finance_actual_record_shift_derived", table_name="actual_record", schema="finance")
    op.drop_table("actual_record", schema="finance")
