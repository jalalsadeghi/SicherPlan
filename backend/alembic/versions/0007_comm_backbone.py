"""Communication backbone tables.

Revision ID: 0007_comm_backbone
Revises: 0006_docs_backbone
Create Date: 2026-03-19 01:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007_comm_backbone"
down_revision = "0006_docs_backbone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS comm")

    op.create_table(
        "message_template",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("template_key", sa.String(length=120), nullable=False),
        sa.Column("language_code", sa.String(length=8), nullable=False, server_default="de"),
        sa.Column("subject_template", sa.String(length=255), nullable=True),
        sa.Column("body_template", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_message_template_tenant_id_tenant", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_message_template"),
        sa.UniqueConstraint("tenant_id", "channel", "template_key", "language_code", name="uq_comm_message_template_tenant_channel_key_language"),
        schema="comm",
    )

    op.create_table(
        "outbound_message",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("template_key", sa.String(length=120), nullable=True),
        sa.Column("language_code", sa.String(length=8), nullable=False, server_default="de"),
        sa.Column("subject_rendered", sa.String(length=255), nullable=True),
        sa.Column("body_rendered", sa.Text(), nullable=False),
        sa.Column("related_entity_type", sa.String(length=120), nullable=True),
        sa.Column("related_entity_id", sa.String(length=36), nullable=True),
        sa.Column("send_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["template_id"], ["comm.message_template.id"], name="fk_outbound_message_template_id_message_template", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_outbound_message_tenant_id_tenant", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_outbound_message"),
        schema="comm",
    )
    op.create_index("ix_comm_outbound_message_tenant_status", "outbound_message", ["tenant_id", "status"], unique=False, schema="comm")

    op.create_table(
        "message_recipient",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("outbound_message_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("recipient_kind", sa.String(length=10), nullable=False, server_default="to"),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("user_account_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("status_reason", sa.String(length=120), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_message_recipient_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_account_id"], ["iam.user_account.id"], name="fk_message_recipient_user_account_id_user_account", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id", "outbound_message_id"], ["comm.outbound_message.tenant_id", "comm.outbound_message.id"], name="fk_comm_message_recipient_tenant_message", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_message_recipient"),
        schema="comm",
    )
    op.create_index("ix_comm_message_recipient_tenant_message", "message_recipient", ["tenant_id", "outbound_message_id"], unique=False, schema="comm")

    op.create_table(
        "delivery_attempt",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("outbound_message_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("provider_key", sa.String(length=80), nullable=False),
        sa.Column("provider_message_ref", sa.String(length=255), nullable=True),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("response_code", sa.String(length=80), nullable=True),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_delivery_attempt_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "outbound_message_id"], ["comm.outbound_message.tenant_id", "comm.outbound_message.id"], name="fk_comm_delivery_attempt_tenant_message", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "recipient_id"], ["comm.message_recipient.tenant_id", "comm.message_recipient.id"], name="fk_comm_delivery_attempt_tenant_recipient", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_delivery_attempt"),
        schema="comm",
    )
    op.create_index("ix_comm_delivery_attempt_recipient_attempted_at", "delivery_attempt", ["recipient_id", "attempted_at"], unique=False, schema="comm")


def downgrade() -> None:
    op.drop_index("ix_comm_delivery_attempt_recipient_attempted_at", table_name="delivery_attempt", schema="comm")
    op.drop_table("delivery_attempt", schema="comm")
    op.drop_index("ix_comm_message_recipient_tenant_message", table_name="message_recipient", schema="comm")
    op.drop_table("message_recipient", schema="comm")
    op.drop_index("ix_comm_outbound_message_tenant_status", table_name="outbound_message", schema="comm")
    op.drop_table("outbound_message", schema="comm")
    op.drop_table("message_template", schema="comm")
