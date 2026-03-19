"""Notice backbone tables.

Revision ID: 0008_notice_backbone
Revises: 0007_comm_backbone
Create Date: 2026-03-19 01:25:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_notice_backbone"
down_revision = "0007_comm_backbone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS info")

    op.create_table(
        "notice",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.String(length=500), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("language_code", sa.String(length=8), nullable=False, server_default="de"),
        sa.Column("mandatory_acknowledgement", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("publish_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("publish_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unpublished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("related_entity_type", sa.String(length=120), nullable=True),
        sa.Column("related_entity_id", sa.String(length=36), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_notice_tenant_id_tenant", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_notice"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_info_notice_tenant_id_id"),
        schema="info",
    )
    op.create_index("ix_info_notice_tenant_status_publish_from", "notice", ["tenant_id", "status", "publish_from"], unique=False, schema="info")

    op.create_table(
        "notice_audience",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("notice_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("audience_kind", sa.String(length=80), nullable=False),
        sa.Column("target_value", sa.String(length=120), nullable=True),
        sa.Column("target_label", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_notice_audience_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "notice_id"], ["info.notice.tenant_id", "info.notice.id"], name="fk_info_notice_audience_tenant_notice", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_notice_audience"),
        sa.UniqueConstraint("tenant_id", "notice_id", "audience_kind", "target_value", name="uq_info_notice_audience_scope"),
        schema="info",
    )
    op.create_index("ix_info_notice_audience_notice_kind", "notice_audience", ["notice_id", "audience_kind"], unique=False, schema="info")

    op.create_table(
        "notice_read",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("notice_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("user_account_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("first_opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledgement_text", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_notice_read_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_account_id"], ["iam.user_account.id"], name="fk_notice_read_user_account_id_user_account", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "notice_id"], ["info.notice.tenant_id", "info.notice.id"], name="fk_info_notice_read_tenant_notice", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_notice_read"),
        sa.UniqueConstraint("notice_id", "user_account_id", name="uq_info_notice_read_notice_user"),
        schema="info",
    )
    op.create_index("ix_info_notice_read_user_ack", "notice_read", ["user_account_id", "acknowledged_at"], unique=False, schema="info")

    op.create_table(
        "notice_link",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("notice_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("link_type", sa.String(length=40), nullable=False, server_default="external"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_notice_link_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "notice_id"], ["info.notice.tenant_id", "info.notice.id"], name="fk_info_notice_link_tenant_notice", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_notice_link"),
        sa.UniqueConstraint("tenant_id", "notice_id", "url", name="uq_info_notice_link_notice_url"),
        schema="info",
    )


def downgrade() -> None:
    op.drop_table("notice_link", schema="info")
    op.drop_index("ix_info_notice_read_user_ack", table_name="notice_read", schema="info")
    op.drop_table("notice_read", schema="info")
    op.drop_index("ix_info_notice_audience_notice_kind", table_name="notice_audience", schema="info")
    op.drop_table("notice_audience", schema="info")
    op.drop_index("ix_info_notice_tenant_status_publish_from", table_name="notice", schema="info")
    op.drop_table("notice", schema="info")
