"""employee availability and absence foundation

Revision ID: 0023_employee_availability_absence_foundation
Revises: 0022_employee_qualification_foundation
Create Date: 2026-03-19 23:58:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0023_employee_availability_absence_foundation"
down_revision = "0022_employee_qualification_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employee_availability_rule",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("rule_kind", sa.String(length=40), nullable=False, server_default="availability"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recurrence_type", sa.String(length=20), nullable=False, server_default="none"),
        sa.Column("weekday_mask", sa.String(length=7), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint(
            "rule_kind IN ('availability', 'unavailable', 'free_wish')",
            name="employee_availability_rule_kind_valid",
        ),
        sa.CheckConstraint(
            "recurrence_type IN ('none', 'weekly')",
            name="employee_availability_rule_recurrence_valid",
        ),
        sa.CheckConstraint("ends_at > starts_at", name="employee_availability_rule_window_valid"),
        sa.CheckConstraint(
            "(recurrence_type = 'none' AND weekday_mask IS NULL) OR "
            "(recurrence_type = 'weekly' AND weekday_mask IS NOT NULL)",
            name="employee_availability_rule_recurrence_fields_valid",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["core.tenant.id"],
            name=op.f("fk_employee_availability_rule_tenant_id_tenant"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_availability_rule_tenant_employee",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_availability_rule")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_availability_rule_tenant_id_id"),
        schema="hr",
    )
    op.create_index(
        "ix_hr_employee_availability_rule_employee_start",
        "employee_availability_rule",
        ["tenant_id", "employee_id", "starts_at"],
        unique=False,
        schema="hr",
    )
    op.create_table(
        "employee_absence",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("absence_type", sa.String(length=40), nullable=False, server_default="vacation"),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("quantity_days", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint(
            "absence_type IN ('vacation', 'sickness', 'child_care', 'other')",
            name="employee_absence_type_valid",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name="employee_absence_status_valid",
        ),
        sa.CheckConstraint("ends_on >= starts_on", name="employee_absence_window_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_absence_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_absence_tenant_employee",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_absence")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_absence_tenant_id_id"),
        schema="hr",
    )
    op.create_index(
        "ix_hr_employee_absence_employee_dates",
        "employee_absence",
        ["tenant_id", "employee_id", "starts_on", "ends_on"],
        unique=False,
        schema="hr",
    )
    op.create_table(
        "employee_leave_balance",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("balance_year", sa.Integer(), nullable=False),
        sa.Column("entitlement_days", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("carry_over_days", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("manual_adjustment_days", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("consumed_days", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("pending_days", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("balance_year >= 2000", name="employee_leave_balance_year_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_employee_leave_balance_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_leave_balance_tenant_employee",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_leave_balance")),
        sa.UniqueConstraint("tenant_id", "employee_id", "balance_year", name="uq_hr_employee_leave_balance_employee_year"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_leave_balance_tenant_id_id"),
        schema="hr",
    )
    op.create_table(
        "employee_event_application",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("planning_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("decided_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'withdrawn')",
            name="employee_event_application_status_valid",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["core.tenant.id"],
            name=op.f("fk_employee_event_application_tenant_id_tenant"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_employee_event_application_tenant_employee",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_event_application")),
        sa.UniqueConstraint(
            "tenant_id",
            "employee_id",
            "planning_record_id",
            name="uq_hr_employee_event_application_employee_planning_record",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_hr_employee_event_application_tenant_id_id"),
        schema="hr",
    )


def downgrade() -> None:
    op.drop_table("employee_event_application", schema="hr")
    op.drop_table("employee_leave_balance", schema="hr")
    op.drop_index("ix_hr_employee_absence_employee_dates", table_name="employee_absence", schema="hr")
    op.drop_table("employee_absence", schema="hr")
    op.drop_index("ix_hr_employee_availability_rule_employee_start", table_name="employee_availability_rule", schema="hr")
    op.drop_table("employee_availability_rule", schema="hr")
