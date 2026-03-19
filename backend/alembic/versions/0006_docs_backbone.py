"""Docs backbone tables and object-storage metadata.

Revision ID: 0006_docs_backbone
Revises: 0005_audit_foundation
Create Date: 2026-03-19 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_docs_backbone"
down_revision = "0005_audit_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS docs")

    op.create_table(
        "document_type",
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system_type", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.PrimaryKeyConstraint("id", name="pk_document_type"),
        sa.UniqueConstraint("key", name="uq_docs_document_type_key"),
        schema="docs",
    )

    op.create_table(
        "document",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("document_type_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_module", sa.String(length=120), nullable=True),
        sa.Column("source_label", sa.String(length=255), nullable=True),
        sa.Column("current_version_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["document_type_id"], ["docs.document_type.id"], name="fk_document_document_type_id_document_type", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_document_tenant_id_tenant", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_document"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_docs_document_tenant_id_id"),
        schema="docs",
    )
    op.create_index("ix_docs_document_tenant_status", "document", ["tenant_id", "status"], unique=False, schema="docs")

    op.create_table(
        "document_version",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("object_bucket", sa.String(length=120), nullable=False),
        sa.Column("object_key", sa.String(length=500), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("is_revision_safe_pdf", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_document_version_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["iam.user_account.id"], name="fk_document_version_uploaded_by_user_id_user_account", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "document_id"], ["docs.document.tenant_id", "docs.document.id"], name="fk_docs_document_version_tenant_document", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_document_version"),
        sa.UniqueConstraint("document_id", "version_no", name="uq_docs_document_version_document_version_no"),
        sa.UniqueConstraint("object_bucket", "object_key", name="uq_docs_document_version_object_ref"),
        schema="docs",
    )
    op.create_index(
        "ix_docs_document_version_tenant_document_version",
        "document_version",
        ["tenant_id", "document_id", "version_no"],
        unique=False,
        schema="docs",
    )

    op.create_table(
        "document_link",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("owner_type", sa.String(length=120), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("relation_type", sa.String(length=80), nullable=False, server_default="attachment"),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("linked_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["linked_by_user_id"], ["iam.user_account.id"], name="fk_document_link_linked_by_user_id_user_account", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_document_link_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "document_id"], ["docs.document.tenant_id", "docs.document.id"], name="fk_docs_document_link_tenant_document", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_document_link"),
        sa.UniqueConstraint("tenant_id", "document_id", "owner_type", "owner_id", "relation_type", name="uq_docs_document_link_owner_relation"),
        schema="docs",
    )
    op.create_index("ix_docs_document_link_owner_lookup", "document_link", ["tenant_id", "owner_type", "owner_id"], unique=False, schema="docs")


def downgrade() -> None:
    op.drop_index("ix_docs_document_link_owner_lookup", table_name="document_link", schema="docs")
    op.drop_table("document_link", schema="docs")
    op.drop_index("ix_docs_document_version_tenant_document_version", table_name="document_version", schema="docs")
    op.drop_table("document_version", schema="docs")
    op.drop_index("ix_docs_document_tenant_status", table_name="document", schema="docs")
    op.drop_table("document", schema="docs")
    op.drop_table("document_type", schema="docs")
