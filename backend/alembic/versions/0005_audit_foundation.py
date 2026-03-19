"""Audit foundation tables.

Revision ID: 0005_audit_foundation
Revises: 0004_iam_auth_flows
Create Date: 2026-03-19 00:00:04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_audit_foundation"
down_revision = "0004_iam_auth_flows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    op.create_table(
        "login_event",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("user_account_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("tenant_code", sa.String(length=50), nullable=True),
        sa.Column("identifier", sa.String(length=255), nullable=False),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("failure_reason", sa.String(length=80), nullable=True),
        sa.Column("auth_method", sa.String(length=40), nullable=False, server_default="password"),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["session_id"], ["iam.user_session.id"], name="fk_login_event_session_id_user_session", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_login_event_tenant_id_tenant", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_account_id"], ["iam.user_account.id"], name="fk_login_event_user_account_id_user_account", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_login_event"),
        schema="audit",
    )
    op.create_index("ix_audit_login_event_tenant_created_at", "login_event", ["tenant_id", "created_at"], unique=False, schema="audit")
    op.create_index("ix_audit_login_event_user_created_at", "login_event", ["user_account_id", "created_at"], unique=False, schema="audit")

    op.create_table(
        "audit_event",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("actor_session_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False, server_default="api"),
        sa.Column("before_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("after_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["actor_session_id"], ["iam.user_session.id"], name="fk_audit_event_actor_session_id_user_session", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["iam.user_account.id"], name="fk_audit_event_actor_user_id_user_account", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_audit_event_tenant_id_tenant", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_audit_event"),
        schema="audit",
    )
    op.create_index("ix_audit_audit_event_tenant_created_at", "audit_event", ["tenant_id", "created_at"], unique=False, schema="audit")
    op.create_index("ix_audit_audit_event_entity_created_at", "audit_event", ["entity_type", "entity_id", "created_at"], unique=False, schema="audit")


def downgrade() -> None:
    op.drop_index("ix_audit_audit_event_entity_created_at", table_name="audit_event", schema="audit")
    op.drop_index("ix_audit_audit_event_tenant_created_at", table_name="audit_event", schema="audit")
    op.drop_table("audit_event", schema="audit")
    op.drop_index("ix_audit_login_event_user_created_at", table_name="login_event", schema="audit")
    op.drop_index("ix_audit_login_event_tenant_created_at", table_name="login_event", schema="audit")
    op.drop_table("login_event", schema="audit")
