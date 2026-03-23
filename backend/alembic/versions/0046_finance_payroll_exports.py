"""finance payroll exports

Revision ID: 0046_finance_payroll_exports
Revises: 0045_finance_employee_pay_profiles
Create Date: 2026-03-20 00:00:07.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0046_finance_payroll_exports"
down_revision = "0045_finance_employee_pay_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_integration_import_export_job_tenant_id_id'
                  AND connamespace = 'integration'::regnamespace
            ) THEN
                ALTER TABLE integration.import_export_job
                ADD CONSTRAINT uq_integration_import_export_job_tenant_id_id
                UNIQUE (tenant_id, id);
            END IF;
        END $$;
        """
    )
    op.create_table(
        "payroll_export_batch",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("batch_no", sa.String(length=80), nullable=False),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("batch_status_code", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("source_hash", sa.String(length=128), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("period_end >= period_start", name="payroll_export_batch_period_valid"),
        sa.CheckConstraint("batch_status_code IN ('draft','generated','queued','dispatched','failed','archived')", name="payroll_export_batch_status_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_payroll_export_batch_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "endpoint_id"], ["integration.endpoint.tenant_id", "integration.endpoint.id"], name="fk_finance_payroll_export_batch_tenant_endpoint", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "job_id"], ["integration.import_export_job.tenant_id", "integration.import_export_job.id"], name="fk_finance_payroll_export_batch_tenant_job", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "batch_no", name="uq_finance_payroll_export_batch_tenant_batch_no"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_export_batch_tenant_id_id"),
        schema="finance",
    )
    op.create_table(
        "payroll_export_item",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("actual_record_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("pay_code", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_code", sa.String(length=20), nullable=False),
        sa.Column("amount_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source_ref_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.CheckConstraint("quantity >= 0", name="payroll_export_item_quantity_nonnegative"),
        sa.CheckConstraint("amount_total >= 0", name="payroll_export_item_amount_nonnegative"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_payroll_export_item_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "batch_id"], ["finance.payroll_export_batch.tenant_id", "finance.payroll_export_batch.id"], name="fk_finance_payroll_export_item_tenant_batch", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "actual_record_id"], ["finance.actual_record.tenant_id", "finance.actual_record.id"], name="fk_finance_payroll_export_item_tenant_actual", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["hr.employee.tenant_id", "hr.employee.id"], name="fk_finance_payroll_export_item_tenant_employee", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_payroll_export_item_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "batch_id", "actual_record_id", "pay_code", name="uq_finance_payroll_export_item_source_line"),
        schema="finance",
    )


def downgrade() -> None:
    op.drop_table("payroll_export_item", schema="finance")
    op.drop_table("payroll_export_batch", schema="finance")
