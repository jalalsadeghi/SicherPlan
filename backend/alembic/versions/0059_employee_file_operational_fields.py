"""Add missing operational employee-file fields.

This extends ``hr.employee`` with employment metadata and target-hour values
used by the Employees workspace while keeping all fields nullable for backward
compatibility with existing rows.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0059_employee_file_operational_fields"
down_revision = "0058_customer_rate_line_hr_catalog_refs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "employee",
        sa.Column("employment_type_code", sa.String(length=80), nullable=True),
        schema="hr",
    )
    op.add_column(
        "employee",
        sa.Column("target_weekly_hours", sa.Numeric(8, 2), nullable=True),
        schema="hr",
    )
    op.add_column(
        "employee",
        sa.Column("target_monthly_hours", sa.Numeric(8, 2), nullable=True),
        schema="hr",
    )
    op.create_check_constraint(
        "employee_target_weekly_hours_non_negative",
        "employee",
        "target_weekly_hours IS NULL OR target_weekly_hours >= 0",
        schema="hr",
    )
    op.create_check_constraint(
        "employee_target_monthly_hours_non_negative",
        "employee",
        "target_monthly_hours IS NULL OR target_monthly_hours >= 0",
        schema="hr",
    )


def downgrade() -> None:
    op.drop_constraint(
        "employee_target_monthly_hours_non_negative",
        "employee",
        schema="hr",
        type_="check",
    )
    op.drop_constraint(
        "employee_target_weekly_hours_non_negative",
        "employee",
        schema="hr",
        type_="check",
    )
    op.drop_column("employee", "target_monthly_hours", schema="hr")
    op.drop_column("employee", "target_weekly_hours", schema="hr")
    op.drop_column("employee", "employment_type_code", schema="hr")
