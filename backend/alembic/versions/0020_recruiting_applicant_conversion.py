"""recruiting applicant conversion

Revision ID: 0020_recruiting_applicant_conversion
Revises: 0019_employee_master_foundation
Create Date: 2026-03-19 23:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0020_recruiting_applicant_conversion"
down_revision = "0019_employee_master_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "applicant",
        sa.Column("converted_employee_id", postgresql.UUID(as_uuid=False), nullable=True),
        schema="hr",
    )
    op.create_foreign_key(
        "fk_hr_applicant_tenant_converted_employee",
        "applicant",
        "employee",
        ["tenant_id", "converted_employee_id"],
        ["tenant_id", "id"],
        source_schema="hr",
        referent_schema="hr",
        ondelete="SET NULL",
    )
    op.create_index(
        "uq_hr_applicant_tenant_converted_employee_id",
        "applicant",
        ["tenant_id", "converted_employee_id"],
        unique=True,
        schema="hr",
        postgresql_where=sa.text("converted_employee_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_hr_applicant_tenant_converted_employee_id", table_name="applicant", schema="hr")
    op.drop_constraint("fk_hr_applicant_tenant_converted_employee", "applicant", schema="hr", type_="foreignkey")
    op.drop_column("applicant", "converted_employee_id", schema="hr")
