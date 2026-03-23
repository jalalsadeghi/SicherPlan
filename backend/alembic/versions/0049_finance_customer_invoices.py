"""finance customer invoices

Revision ID: 0049_finance_customer_invoices
Revises: 0048_finance_timesheets
Create Date: 2026-03-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0049_finance_customer_invoices"
down_revision = "0048_finance_timesheets"
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
                WHERE conname = 'uq_crm_customer_billing_profile_tenant_id_id'
                  AND connamespace = 'crm'::regnamespace
            ) THEN
                ALTER TABLE crm.customer_billing_profile
                ADD CONSTRAINT uq_crm_customer_billing_profile_tenant_id_id
                UNIQUE (tenant_id, id);
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        "customer_invoice",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("timesheet_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("billing_profile_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("invoice_party_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("invoice_no", sa.String(length=120), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("currency_code", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("layout_code", sa.String(length=80), nullable=True),
        sa.Column("invoice_status_code", sa.String(length=40), server_default="draft", nullable=False),
        sa.Column("subtotal_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("tax_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("customer_visible_flag", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("source_hash", sa.String(length=128), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_customer_invoice_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "customer_id"], ["crm.customer.tenant_id", "crm.customer.id"], name="fk_finance_customer_invoice_tenant_customer", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "timesheet_id"], ["finance.timesheet.tenant_id", "finance.timesheet.id"], name="fk_finance_customer_invoice_tenant_timesheet", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "billing_profile_id"], ["crm.customer_billing_profile.tenant_id", "crm.customer_billing_profile.id"], name="fk_finance_customer_invoice_tenant_billing_profile", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "invoice_party_id"], ["crm.customer_invoice_party.tenant_id", "crm.customer_invoice_party.id"], name="fk_finance_customer_invoice_tenant_invoice_party", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_customer_invoice"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_customer_invoice_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "invoice_no", name="uq_finance_customer_invoice_number"),
        sa.CheckConstraint("period_end >= period_start", name="customer_invoice_period_valid"),
        sa.CheckConstraint("due_date >= issue_date", name="customer_invoice_due_date_valid"),
        sa.CheckConstraint("invoice_status_code IN ('draft','issued','released','archived')", name="customer_invoice_status_valid"),
        sa.CheckConstraint("subtotal_amount >= 0", name="customer_invoice_subtotal_nonnegative"),
        sa.CheckConstraint("tax_amount >= 0", name="customer_invoice_tax_nonnegative"),
        sa.CheckConstraint("total_amount >= 0", name="customer_invoice_total_nonnegative"),
        schema="finance",
    )
    op.create_index("ix_finance_customer_invoice_customer_issue_date", "customer_invoice", ["tenant_id", "customer_id", "issue_date"], unique=False, schema="finance")

    op.create_table(
        "customer_invoice_line",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("timesheet_line_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("source_actual_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("rate_card_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("rate_line_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("surcharge_rule_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="100", nullable=False),
        sa.Column("line_kind_code", sa.String(length=40), server_default="base", nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_code", sa.String(length=20), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(8, 2), server_default="0", nullable=False),
        sa.Column("net_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("gross_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("source_ref_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_finance_customer_invoice_line_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "invoice_id"], ["finance.customer_invoice.tenant_id", "finance.customer_invoice.id"], name="fk_finance_customer_invoice_line_tenant_invoice", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "timesheet_line_id"], ["finance.timesheet_line.tenant_id", "finance.timesheet_line.id"], name="fk_finance_customer_invoice_line_tenant_timesheet_line", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "source_actual_id"], ["finance.actual_record.tenant_id", "finance.actual_record.id"], name="fk_finance_customer_invoice_line_tenant_actual", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "rate_card_id"], ["crm.customer_rate_card.tenant_id", "crm.customer_rate_card.id"], name="fk_finance_customer_invoice_line_tenant_rate_card", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "rate_line_id"], ["crm.customer_rate_line.tenant_id", "crm.customer_rate_line.id"], name="fk_finance_customer_invoice_line_tenant_rate_line", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "surcharge_rule_id"], ["crm.customer_surcharge_rule.tenant_id", "crm.customer_surcharge_rule.id"], name="fk_finance_customer_invoice_line_tenant_surcharge_rule", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_customer_invoice_line"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_finance_customer_invoice_line_tenant_id_id"),
        sa.CheckConstraint("quantity >= 0", name="customer_invoice_line_quantity_nonnegative"),
        sa.CheckConstraint("unit_price >= 0", name="customer_invoice_line_unit_price_nonnegative"),
        sa.CheckConstraint("net_amount >= 0", name="customer_invoice_line_net_nonnegative"),
        sa.CheckConstraint("tax_amount >= 0", name="customer_invoice_line_tax_nonnegative"),
        sa.CheckConstraint("gross_amount >= 0", name="customer_invoice_line_gross_nonnegative"),
        schema="finance",
    )
    op.create_index("ix_finance_customer_invoice_line_invoice_sort", "customer_invoice_line", ["tenant_id", "invoice_id", "sort_order"], unique=False, schema="finance")


def downgrade() -> None:
    op.drop_index("ix_finance_customer_invoice_line_invoice_sort", table_name="customer_invoice_line", schema="finance")
    op.drop_table("customer_invoice_line", schema="finance")
    op.drop_index("ix_finance_customer_invoice_customer_issue_date", table_name="customer_invoice", schema="finance")
    op.drop_table("customer_invoice", schema="finance")
