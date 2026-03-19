"""IAM foundation tables.

Revision ID: 0003_iam_foundation
Revises: 0002_core_tenant_backbone
Create Date: 2026-03-19 00:00:02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_iam_foundation"
down_revision = "0002_core_tenant_backbone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS iam")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_core_mandate_tenant_id_id'
                  AND connamespace = 'core'::regnamespace
            ) THEN
                ALTER TABLE core.mandate
                ADD CONSTRAINT uq_core_mandate_tenant_id_id UNIQUE (tenant_id, id);
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        "role",
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_portal_role", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_system_role", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id", name="pk_role"),
        sa.UniqueConstraint("key", name="uq_iam_role_key"),
        schema="iam",
    )

    op.create_table(
        "permission",
        sa.Column("key", sa.String(length=160), nullable=False),
        sa.Column("module", sa.String(length=80), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.PrimaryKeyConstraint("id", name="pk_permission"),
        sa.UniqueConstraint("key", name="uq_iam_permission_key"),
        schema="iam",
    )

    op.create_table(
        "user_account",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("locale", sa.String(length=10), nullable=False, server_default="de"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Europe/Berlin"),
        sa.Column("is_platform_user", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_password_login_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_user_account_tenant_id_tenant", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_user_account"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_iam_user_account_tenant_email"),
        sa.UniqueConstraint("tenant_id", "username", name="uq_iam_user_account_tenant_username"),
        schema="iam",
    )

    op.create_table(
        "external_identity",
        sa.Column("user_account_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("provider_user_name", sa.String(length=255), nullable=True),
        sa.Column("provider_email", sa.String(length=255), nullable=True),
        sa.Column("claims_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_account_id"], ["iam.user_account.id"], name="fk_external_identity_user_account_id_user_account", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_external_identity"),
        sa.UniqueConstraint("provider", "provider_user_name", name="uq_iam_external_identity_provider_username"),
        sa.UniqueConstraint("provider", "subject", name="uq_iam_external_identity_provider_subject"),
        schema="iam",
    )

    op.create_table(
        "role_permission",
        sa.Column("role_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["permission_id"], ["iam.permission.id"], name="fk_role_permission_permission_id_permission", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["iam.role.id"], name="fk_role_permission_role_id_role", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name="pk_role_permission"),
        schema="iam",
    )

    op.create_table(
        "user_role_assignment",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_account_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("scope_type", sa.String(length=40), nullable=False, server_default="tenant"),
        sa.Column("branch_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("mandate_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("subcontractor_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("scope_type IN ('tenant', 'branch', 'mandate', 'customer', 'subcontractor')", name="ck_user_role_assignment_scope_type_valid"),
        sa.CheckConstraint(
            "(scope_type = 'tenant' AND branch_id IS NULL AND mandate_id IS NULL AND customer_id IS NULL AND subcontractor_id IS NULL) OR "
            "(scope_type = 'branch' AND branch_id IS NOT NULL AND mandate_id IS NULL AND customer_id IS NULL AND subcontractor_id IS NULL) OR "
            "(scope_type = 'mandate' AND branch_id IS NULL AND mandate_id IS NOT NULL AND customer_id IS NULL AND subcontractor_id IS NULL) OR "
            "(scope_type = 'customer' AND branch_id IS NULL AND mandate_id IS NULL AND customer_id IS NOT NULL AND subcontractor_id IS NULL) OR "
            "(scope_type = 'subcontractor' AND branch_id IS NULL AND mandate_id IS NULL AND customer_id IS NULL AND subcontractor_id IS NOT NULL)",
            name="ck_user_role_assignment_scope_target_matches_type",
        ),
        sa.ForeignKeyConstraint(["role_id"], ["iam.role.id"], name="fk_user_role_assignment_role_id_role", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_user_role_assignment_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_account_id"], ["iam.user_account.id"], name="fk_user_role_assignment_user_account_id_user_account", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "branch_id"],
            ["core.branch.tenant_id", "core.branch.id"],
            name="fk_iam_user_role_assignment_tenant_branch",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "mandate_id"],
            ["core.mandate.tenant_id", "core.mandate.id"],
            name="fk_iam_user_role_assignment_tenant_mandate",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_role_assignment"),
        sa.UniqueConstraint(
            "user_account_id",
            "role_id",
            "scope_type",
            "tenant_id",
            "branch_id",
            "mandate_id",
            "customer_id",
            "subcontractor_id",
            name="uq_iam_user_role_assignment_scope_tuple",
        ),
        schema="iam",
    )

    op.create_table(
        "user_session",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_account_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("session_token_hash", sa.String(length=128), nullable=False),
        sa.Column("refresh_token_family", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=120), nullable=True),
        sa.Column("device_label", sa.String(length=255), nullable=True),
        sa.Column("device_id", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_user_session_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_account_id"], ["iam.user_account.id"], name="fk_user_session_user_account_id_user_account", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_user_session"),
        sa.UniqueConstraint("session_token_hash", name="uq_iam_user_session_token_hash"),
        schema="iam",
    )
    op.create_index(
        "ix_iam_user_session_user_account_revoked_at",
        "user_session",
        ["user_account_id", "revoked_at"],
        unique=False,
        schema="iam",
    )


def downgrade() -> None:
    op.drop_index("ix_iam_user_session_user_account_revoked_at", table_name="user_session", schema="iam")
    op.drop_table("user_session", schema="iam")
    op.drop_table("user_role_assignment", schema="iam")
    op.drop_table("role_permission", schema="iam")
    op.drop_table("external_identity", schema="iam")
    op.drop_table("user_account", schema="iam")
    op.drop_table("permission", schema="iam")
    op.drop_table("role", schema="iam")
