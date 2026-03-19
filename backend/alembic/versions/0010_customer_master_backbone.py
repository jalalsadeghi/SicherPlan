"""Customer master backbone tables.

Revision ID: 0010_customer_master_backbone
Revises: 0009_integration_backbone
Create Date: 2026-03-19 03:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0010_customer_master_backbone"
down_revision = "0009_integration_backbone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS crm")

    op.create_table(
        "customer",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_number", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("external_ref", sa.String(length=120), nullable=True),
        sa.Column("legal_form_lookup_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("classification_lookup_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("ranking_lookup_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("customer_status_lookup_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("default_branch_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("default_mandate_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["classification_lookup_id"], ["core.lookup_value.id"], name="fk_customer_classification_lookup_id_lookup_value", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_status_lookup_id"], ["core.lookup_value.id"], name="fk_customer_customer_status_lookup_id_lookup_value", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["legal_form_lookup_id"], ["core.lookup_value.id"], name="fk_customer_legal_form_lookup_id_lookup_value", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ranking_lookup_id"], ["core.lookup_value.id"], name="fk_customer_ranking_lookup_id_lookup_value", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_customer_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "default_branch_id"], ["core.branch.tenant_id", "core.branch.id"], name="fk_crm_customer_tenant_branch", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "default_mandate_id"], ["core.mandate.tenant_id", "core.mandate.id"], name="fk_crm_customer_tenant_mandate", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_customer"),
        sa.UniqueConstraint("tenant_id", "customer_number", name="uq_crm_customer_tenant_customer_number"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_crm_customer_tenant_id_id"),
        schema="crm",
    )

    op.create_table(
        "customer_contact",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=True),
        sa.Column("function_label", sa.String(length=120), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("mobile", sa.String(length=64), nullable=True),
        sa.Column("is_primary_contact", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_billing_contact", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_customer_contact_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "customer_id"], ["crm.customer.tenant_id", "crm.customer.id"], name="fk_crm_customer_contact_tenant_customer", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["iam.user_account.id"], name="fk_customer_contact_user_id_user_account", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_customer_contact"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_crm_customer_contact_tenant_id_id"),
        schema="crm",
    )
    op.create_index("ix_crm_customer_contact_tenant_customer", "customer_contact", ["tenant_id", "customer_id"], unique=False, schema="crm")
    op.create_index(
        "uq_crm_customer_contact_primary_per_customer",
        "customer_contact",
        ["tenant_id", "customer_id"],
        unique=True,
        schema="crm",
        postgresql_where=sa.text("is_primary_contact = true AND archived_at IS NULL"),
    )
    op.create_index(
        "uq_crm_customer_contact_tenant_user_id",
        "customer_contact",
        ["tenant_id", "user_id"],
        unique=True,
        schema="crm",
        postgresql_where=sa.text("user_id IS NOT NULL AND archived_at IS NULL"),
    )

    op.create_table(
        "customer_address",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("address_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("address_type", sa.String(length=40), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.CheckConstraint("address_type IN ('registered', 'billing', 'mailing', 'service')", name="ck_customer_address_crm_customer_address_type_valid"),
        sa.ForeignKeyConstraint(["address_id"], ["common.address.id"], name="fk_customer_address_address_id_address", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_customer_address_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "customer_id"], ["crm.customer.tenant_id", "crm.customer.id"], name="fk_crm_customer_address_tenant_customer", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_customer_address"),
        sa.UniqueConstraint("tenant_id", "customer_id", "address_id", "address_type", name="uq_crm_customer_address_customer_address_type"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_crm_customer_address_tenant_id_id"),
        schema="crm",
    )
    op.create_index(
        "ix_crm_customer_address_tenant_customer_type",
        "customer_address",
        ["tenant_id", "customer_id", "address_type"],
        unique=False,
        schema="crm",
    )
    op.create_index(
        "uq_crm_customer_address_default_per_type",
        "customer_address",
        ["tenant_id", "customer_id", "address_type"],
        unique=True,
        schema="crm",
        postgresql_where=sa.text("is_default = true AND archived_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_crm_customer_address_default_per_type", table_name="customer_address", schema="crm")
    op.drop_index("ix_crm_customer_address_tenant_customer_type", table_name="customer_address", schema="crm")
    op.drop_table("customer_address", schema="crm")
    op.drop_index("uq_crm_customer_contact_tenant_user_id", table_name="customer_contact", schema="crm")
    op.drop_index("uq_crm_customer_contact_primary_per_customer", table_name="customer_contact", schema="crm")
    op.drop_index("ix_crm_customer_contact_tenant_customer", table_name="customer_contact", schema="crm")
    op.drop_table("customer_contact", schema="crm")
    op.drop_table("customer", schema="crm")
