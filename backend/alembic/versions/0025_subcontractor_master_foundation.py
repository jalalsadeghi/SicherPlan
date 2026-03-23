"""subcontractor master foundation

Revision ID: 0025_subcontractor_master_foundation
Revises: 0024_employee_compensation_and_credentials
Create Date: 2026-03-20 02:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0025_subcontractor_master_foundation"
down_revision = "0024_employee_compensation_and_credentials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS partner"))

    op.create_table(
        "subcontractor",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("subcontractor_number", sa.String(length=50), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("legal_form_lookup_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("subcontractor_status_lookup_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("managing_director_name", sa.String(length=255), nullable=True),
        sa.Column("address_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
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
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)",
            name="partner_subcontractor_coordinates_valid",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_subcontractor_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["legal_form_lookup_id"], ["core.lookup_value.id"], name=op.f("fk_subcontractor_legal_form_lookup_id_lookup_value"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subcontractor_status_lookup_id"], ["core.lookup_value.id"], name=op.f("fk_subcontractor_subcontractor_status_lookup_id_lookup_value"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["address_id"], ["common.address.id"], name=op.f("fk_subcontractor_address_id_address"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subcontractor")),
        sa.UniqueConstraint("tenant_id", "subcontractor_number", name="uq_partner_subcontractor_tenant_number"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_tenant_id_id"),
        schema="partner",
    )

    op.create_table(
        "subcontractor_contact",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("subcontractor_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("function_label", sa.String(length=120), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("mobile", sa.String(length=64), nullable=True),
        sa.Column("is_primary_contact", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("portal_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_subcontractor_contact_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "subcontractor_id"], ["partner.subcontractor.tenant_id", "partner.subcontractor.id"], name="fk_partner_subcontractor_contact_tenant_subcontractor", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["iam.user_account.id"], name=op.f("fk_subcontractor_contact_user_id_user_account"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subcontractor_contact")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_contact_tenant_id_id"),
        schema="partner",
    )
    op.create_index("ix_partner_subcontractor_contact_tenant_subcontractor", "subcontractor_contact", ["tenant_id", "subcontractor_id"], unique=False, schema="partner")
    op.create_index(
        "uq_partner_subcontractor_contact_primary_per_company",
        "subcontractor_contact",
        ["tenant_id", "subcontractor_id"],
        unique=True,
        schema="partner",
        postgresql_where=sa.text("is_primary_contact = true AND archived_at IS NULL"),
    )
    op.create_index(
        "uq_partner_subcontractor_contact_tenant_user_id",
        "subcontractor_contact",
        ["tenant_id", "user_id"],
        unique=True,
        schema="partner",
        postgresql_where=sa.text("user_id IS NOT NULL AND archived_at IS NULL"),
    )

    op.create_table(
        "subcontractor_scope",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("subcontractor_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("mandate_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="partner_subcontractor_scope_window_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_subcontractor_scope_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "subcontractor_id"], ["partner.subcontractor.tenant_id", "partner.subcontractor.id"], name="fk_partner_subcontractor_scope_tenant_subcontractor", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "branch_id"], ["core.branch.tenant_id", "core.branch.id"], name="fk_partner_subcontractor_scope_tenant_branch", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "mandate_id"], ["core.mandate.tenant_id", "core.mandate.id"], name="fk_partner_subcontractor_scope_tenant_mandate", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subcontractor_scope")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_partner_subcontractor_scope_tenant_id_id"),
        schema="partner",
    )

    op.create_table(
        "subcontractor_finance_profile",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("subcontractor_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("invoice_email", sa.String(length=255), nullable=True),
        sa.Column("payment_terms_days", sa.Integer(), nullable=True),
        sa.Column("payment_terms_note", sa.String(length=255), nullable=True),
        sa.Column("tax_number", sa.String(length=120), nullable=True),
        sa.Column("vat_id", sa.String(length=120), nullable=True),
        sa.Column("bank_account_holder", sa.String(length=255), nullable=True),
        sa.Column("bank_iban", sa.String(length=64), nullable=True),
        sa.Column("bank_bic", sa.String(length=64), nullable=True),
        sa.Column("bank_name", sa.String(length=255), nullable=True),
        sa.Column("invoice_delivery_method_lookup_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("invoice_status_mode_lookup_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("billing_note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name=op.f("fk_subcontractor_finance_profile_tenant_id_tenant"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "subcontractor_id"], ["partner.subcontractor.tenant_id", "partner.subcontractor.id"], name="fk_partner_subcontractor_finance_profile_tenant_subcontractor", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["invoice_delivery_method_lookup_id"], ["core.lookup_value.id"], name=op.f("fk_subcontractor_finance_profile_invoice_delivery_method_lookup_id_lookup_value"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invoice_status_mode_lookup_id"], ["core.lookup_value.id"], name=op.f("fk_subcontractor_finance_profile_invoice_status_mode_lookup_id_lookup_value"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subcontractor_finance_profile")),
        sa.UniqueConstraint("tenant_id", "subcontractor_id", name="uq_partner_subcontractor_finance_profile_company"),
        schema="partner",
    )


def downgrade() -> None:
    op.drop_table("subcontractor_finance_profile", schema="partner")
    op.drop_table("subcontractor_scope", schema="partner")
    op.drop_index("uq_partner_subcontractor_contact_tenant_user_id", table_name="subcontractor_contact", schema="partner")
    op.drop_index("uq_partner_subcontractor_contact_primary_per_company", table_name="subcontractor_contact", schema="partner")
    op.drop_index("ix_partner_subcontractor_contact_tenant_subcontractor", table_name="subcontractor_contact", schema="partner")
    op.drop_table("subcontractor_contact", schema="partner")
    op.drop_table("subcontractor", schema="partner")
