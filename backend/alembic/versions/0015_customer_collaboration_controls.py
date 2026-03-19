"""Add customer employee-block seam for portal/admin collaboration.

Revision ID: 0015_customer_collaboration_controls
Revises: 0014_customer_invoice_configuration
Create Date: 2026-03-19 18:15:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0015_customer_collaboration_controls"
down_revision = "0014_customer_invoice_configuration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_employee_block",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_crm_customer_employee_block_tenant_customer",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="crm",
        comment=(
            "Customer-owned employee-block seam. The hr.employee FK is intentionally deferred "
            "until the employees module lands so no duplicate employee master table is introduced."
        ),
    )
    op.create_index(
        "ix_crm_customer_employee_block_customer_effective",
        "customer_employee_block",
        ["tenant_id", "customer_id", "effective_from"],
        unique=False,
        schema="crm",
    )
    op.create_index(
        "ix_crm_customer_employee_block_employee",
        "customer_employee_block",
        ["tenant_id", "employee_id"],
        unique=False,
        schema="crm",
    )


def downgrade() -> None:
    op.drop_index("ix_crm_customer_employee_block_employee", table_name="customer_employee_block", schema="crm")
    op.drop_index(
        "ix_crm_customer_employee_block_customer_effective",
        table_name="customer_employee_block",
        schema="crm",
    )
    op.drop_table("customer_employee_block", schema="crm")
