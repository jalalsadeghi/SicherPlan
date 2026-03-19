"""Core tenant backbone tables.

Revision ID: 0002_core_tenant_backbone
Revises: 0001_ci_baseline
Create Date: 2026-03-19 00:00:01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_core_tenant_backbone"
down_revision = "0001_ci_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute("CREATE SCHEMA IF NOT EXISTS common")
    op.execute("CREATE SCHEMA IF NOT EXISTS core")

    op.create_table(
        "address",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("street_line_1", sa.String(length=255), nullable=False),
        sa.Column("street_line_2", sa.String(length=255), nullable=True),
        sa.Column("postal_code", sa.String(length=32), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=128), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_address"),
        schema="common",
    )

    op.create_table(
        "tenant",
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("default_locale", sa.String(length=10), nullable=False, server_default="de"),
        sa.Column("default_currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Berlin"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id", name="pk_tenant"),
        sa.UniqueConstraint("code", name="uq_core_tenant_code"),
        schema="core",
    )

    op.create_table(
        "branch",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=64), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["address_id"], ["common.address.id"], name="fk_branch_address_id_address", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_branch_tenant_id_tenant", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_branch"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_core_branch_tenant_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_core_branch_tenant_id_id"),
        schema="core",
    )

    op.create_table(
        "mandate",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("external_ref", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_mandate_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "branch_id"],
            ["core.branch.tenant_id", "core.branch.id"],
            name="fk_core_mandate_tenant_branch",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_mandate"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_core_mandate_tenant_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_core_mandate_tenant_id_id"),
        schema="core",
    )

    op.create_table(
        "tenant_setting",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_tenant_setting_tenant_id_tenant", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_tenant_setting"),
        sa.UniqueConstraint("tenant_id", "key", name="uq_core_tenant_setting_tenant_key"),
        schema="core",
    )

    op.create_table(
        "lookup_value",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("domain", sa.String(length=80), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_lookup_value_tenant_id_tenant", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_lookup_value"),
        schema="core",
    )

    op.create_index(
        "uq_core_lookup_value_system_domain_code",
        "lookup_value",
        ["domain", "code"],
        unique=True,
        schema="core",
        postgresql_where=sa.text("tenant_id IS NULL"),
    )
    op.create_index(
        "uq_core_lookup_value_tenant_domain_code",
        "lookup_value",
        ["tenant_id", "domain", "code"],
        unique=True,
        schema="core",
        postgresql_where=sa.text("tenant_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_core_lookup_value_tenant_domain_code", table_name="lookup_value", schema="core")
    op.drop_index("uq_core_lookup_value_system_domain_code", table_name="lookup_value", schema="core")
    op.drop_table("lookup_value", schema="core")
    op.drop_table("tenant_setting", schema="core")
    op.drop_table("mandate", schema="core")
    op.drop_table("branch", schema="core")
    op.drop_table("tenant", schema="core")
    op.drop_table("address", schema="common")
