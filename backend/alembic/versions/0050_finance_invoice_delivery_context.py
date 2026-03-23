"""finance invoice delivery context

Revision ID: 0050_finance_invoice_delivery_context
Revises: 0049_finance_customer_invoices
Create Date: 2026-03-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0050_finance_invoice_delivery_context"
down_revision = "0049_finance_customer_invoices"
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
    op.add_column("customer_invoice", sa.Column("job_id", postgresql.UUID(as_uuid=False), nullable=True), schema="finance")
    op.add_column("customer_invoice", sa.Column("invoice_email", sa.String(length=255), nullable=True), schema="finance")
    op.add_column("customer_invoice", sa.Column("dispatch_method_code", sa.String(length=80), nullable=True), schema="finance")
    op.add_column("customer_invoice", sa.Column("e_invoice_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False), schema="finance")
    op.add_column("customer_invoice", sa.Column("leitweg_id", sa.String(length=120), nullable=True), schema="finance")
    op.add_column("customer_invoice", sa.Column("payment_terms_days", sa.Integer(), nullable=True), schema="finance")
    op.add_column("customer_invoice", sa.Column("billing_profile_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False), schema="finance")
    op.add_column("customer_invoice", sa.Column("invoice_party_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False), schema="finance")
    op.add_column("customer_invoice", sa.Column("delivery_context_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False), schema="finance")
    op.add_column("customer_invoice", sa.Column("delivery_status_code", sa.String(length=40), server_default="not_queued", nullable=False), schema="finance")
    op.add_column("customer_invoice", sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True), schema="finance")
    op.create_foreign_key(
        "fk_finance_customer_invoice_tenant_job",
        "customer_invoice",
        "import_export_job",
        ["tenant_id", "job_id"],
        ["tenant_id", "id"],
        source_schema="finance",
        referent_schema="integration",
        ondelete="SET NULL",
    )
    op.drop_constraint("customer_invoice_status_valid", "customer_invoice", schema="finance", type_="check")
    op.create_check_constraint(
        "customer_invoice_status_valid",
        "customer_invoice",
        "invoice_status_code IN ('draft','issued','released','queued','sent','failed','archived')",
        schema="finance",
    )


def downgrade() -> None:
    op.drop_constraint("customer_invoice_status_valid", "customer_invoice", schema="finance", type_="check")
    op.create_check_constraint(
        "customer_invoice_status_valid",
        "customer_invoice",
        "invoice_status_code IN ('draft','issued','released','archived')",
        schema="finance",
    )
    op.drop_constraint("fk_finance_customer_invoice_tenant_job", "customer_invoice", schema="finance", type_="foreignkey")
    op.drop_column("customer_invoice", "dispatched_at", schema="finance")
    op.drop_column("customer_invoice", "delivery_status_code", schema="finance")
    op.drop_column("customer_invoice", "delivery_context_json", schema="finance")
    op.drop_column("customer_invoice", "invoice_party_snapshot_json", schema="finance")
    op.drop_column("customer_invoice", "billing_profile_snapshot_json", schema="finance")
    op.drop_column("customer_invoice", "payment_terms_days", schema="finance")
    op.drop_column("customer_invoice", "leitweg_id", schema="finance")
    op.drop_column("customer_invoice", "e_invoice_enabled", schema="finance")
    op.drop_column("customer_invoice", "dispatch_method_code", schema="finance")
    op.drop_column("customer_invoice", "invoice_email", schema="finance")
    op.drop_column("customer_invoice", "job_id", schema="finance")
