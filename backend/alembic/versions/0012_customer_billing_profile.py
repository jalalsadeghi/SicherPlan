"""Add CRM customer billing profile and invoice party tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0012_customer_billing_profile"
down_revision = "0011_customer_history_and_exports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_billing_profile",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("invoice_email", sa.String(length=255), nullable=True),
        sa.Column("payment_terms_days", sa.Integer(), nullable=True),
        sa.Column("payment_terms_note", sa.String(length=255), nullable=True),
        sa.Column("tax_number", sa.String(length=120), nullable=True),
        sa.Column("vat_id", sa.String(length=120), nullable=True),
        sa.Column("tax_exempt", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("tax_exemption_reason", sa.String(length=255), nullable=True),
        sa.Column("bank_account_holder", sa.String(length=255), nullable=True),
        sa.Column("bank_iban", sa.String(length=64), nullable=True),
        sa.Column("bank_bic", sa.String(length=64), nullable=True),
        sa.Column("bank_name", sa.String(length=255), nullable=True),
        sa.Column("contract_reference", sa.String(length=120), nullable=True),
        sa.Column("debtor_number", sa.String(length=120), nullable=True),
        sa.Column("billing_note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_crm_customer_billing_profile_tenant_customer",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_billing_profile")),
        sa.UniqueConstraint("tenant_id", "customer_id", name="uq_crm_customer_billing_profile_customer"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_crm_customer_billing_profile_tenant_id_id"),
        schema="crm",
    )

    op.create_table(
        "customer_invoice_party",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("address_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("invoice_email", sa.String(length=255), nullable=True),
        sa.Column("invoice_layout_lookup_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("external_ref", sa.String(length=120), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_crm_customer_invoice_party_tenant_customer",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["address_id"], ["common.address.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["invoice_layout_lookup_id"], ["core.lookup_value.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_invoice_party")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_crm_customer_invoice_party_tenant_id_id"),
        schema="crm",
    )
    op.create_index(
        "ix_crm_customer_invoice_party_customer",
        "customer_invoice_party",
        ["tenant_id", "customer_id"],
        unique=False,
        schema="crm",
    )
    op.create_index(
        "uq_crm_customer_invoice_party_default_per_customer",
        "customer_invoice_party",
        ["tenant_id", "customer_id"],
        unique=True,
        schema="crm",
        postgresql_where=sa.text("is_default = true AND archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_crm_customer_invoice_party_default_per_customer", table_name="customer_invoice_party", schema="crm")
    op.drop_index("ix_crm_customer_invoice_party_customer", table_name="customer_invoice_party", schema="crm")
    op.drop_table("customer_invoice_party", schema="crm")
    op.drop_table("customer_billing_profile", schema="crm")
