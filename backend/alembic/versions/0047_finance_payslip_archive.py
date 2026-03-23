"""finance payslip archive

Revision ID: 0047_finance_payslip_archive
Revises: 0046_finance_payroll_exports
Create Date: 2026-03-20 00:00:08.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0047_finance_payslip_archive"
down_revision = "0046_finance_payroll_exports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payroll_payslip_archive",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("export_batch_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("archive_status_code", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("superseded_by_archive_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("period_end >= period_start", name="payroll_payslip_archive_period_valid"),
        sa.CheckConstraint("archive_status_code IN ('active','superseded','import_failed')", name="payroll_payslip_archive_status_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_payroll_payslip_archive_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_finance_payroll_payslip_archive_tenant_employee", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "export_batch_id"], ["finance.payroll_export_batch.tenant_id", "finance.payroll_export_batch.id"], name="fk_finance_payroll_payslip_archive_tenant_batch", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "superseded_by_archive_id"], ["finance.payroll_payslip_archive.tenant_id", "finance.payroll_payslip_archive.id"], name="fk_finance_payroll_payslip_archive_tenant_superseded_by", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_payslip_archive_tenant_id_id"),
        schema="finance",
    )


def downgrade() -> None:
    op.drop_table("payroll_payslip_archive", schema="finance")
