"""finance employee pay profiles

Revision ID: 0045_finance_employee_pay_profiles
Revises: 0044_finance_payroll_tariffs
Create Date: 2026-03-20 00:00:06.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0045_finance_employee_pay_profiles"
down_revision = "0044_finance_payroll_tariffs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employee_pay_profile",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tariff_table_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("payroll_region_code", sa.String(length=32), nullable=False),
        sa.Column("employment_type_code", sa.String(length=40), nullable=False),
        sa.Column("pay_cycle_code", sa.String(length=40), nullable=False, server_default="monthly"),
        sa.Column("pay_unit_code", sa.String(length=20), nullable=False, server_default="hour"),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("export_employee_code", sa.String(length=80), nullable=True),
        sa.Column("cost_center_code", sa.String(length=80), nullable=True),
        sa.Column("base_rate_override", sa.Numeric(12, 2), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("effective_until IS NULL OR effective_until >= effective_from", name="employee_pay_profile_window_valid"),
        sa.CheckConstraint("base_rate_override IS NULL OR base_rate_override >= 0", name="employee_pay_profile_base_rate_nonnegative"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_employee_pay_profile_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_finance_employee_pay_profile_tenant_employee", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "tariff_table_id"], ["finance.payroll_tariff_table.tenant_id", "finance.payroll_tariff_table.id"], name="fk_finance_employee_pay_profile_tenant_tariff_table", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_employee_pay_profile_tenant_id_id"),
        schema="finance",
    )
    op.create_index("ix_finance_employee_pay_profile_employee_window", "employee_pay_profile", ["tenant_id", "employee_id", "effective_from"], unique=False, schema="finance")


def downgrade() -> None:
    op.drop_index("ix_finance_employee_pay_profile_employee_window", table_name="employee_pay_profile", schema="finance")
    op.drop_table("employee_pay_profile", schema="finance")
