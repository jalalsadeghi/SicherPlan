"""Integration backbone tables.

Revision ID: 0009_integration_backbone
Revises: 0008_notice_backbone
Create Date: 2026-03-19 02:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0009_integration_backbone"
down_revision = "0008_notice_backbone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS integration")

    op.create_table(
        "endpoint",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("provider_key", sa.String(length=120), nullable=False),
        sa.Column("endpoint_type", sa.String(length=80), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("auth_mode", sa.String(length=40), nullable=False, server_default="token"),
        sa.Column("config_public_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("secret_ciphertext", sa.Text(), nullable=True),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_endpoint_tenant_id_tenant", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_endpoint"),
        sa.UniqueConstraint("tenant_id", "provider_key", "endpoint_type", name="uq_integration_endpoint_tenant_provider_type"),
        schema="integration",
    )

    op.create_table(
        "import_export_job",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("job_direction", sa.String(length=20), nullable=False),
        sa.Column("job_type", sa.String(length=120), nullable=False),
        sa.Column("request_payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["iam.user_account.id"], name="fk_import_export_job_requested_by_user_id_user_account", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_import_export_job_tenant_id_tenant", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "endpoint_id"], ["integration.endpoint.tenant_id", "integration.endpoint.id"], name="fk_integration_job_tenant_endpoint", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_import_export_job"),
        schema="integration",
    )
    op.create_index("ix_integration_job_tenant_status", "import_export_job", ["tenant_id", "status"], unique=False, schema="integration")

    op.create_table(
        "outbox_event",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("aggregate_type", sa.String(length=120), nullable=False),
        sa.Column("aggregate_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=160), nullable=False),
        sa.Column("topic", sa.String(length=160), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column("last_error_summary", sa.Text(), nullable=True),
        sa.Column("processed_by", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["endpoint_id"], ["integration.endpoint.id"], name="fk_outbox_event_endpoint_id_endpoint", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], name="fk_outbox_event_tenant_id_tenant", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_outbox_event"),
        sa.UniqueConstraint("dedupe_key", name="uq_integration_outbox_event_dedupe_key"),
        schema="integration",
    )
    op.create_index("ix_integration_outbox_event_status_next_attempt", "outbox_event", ["status", "next_attempt_at"], unique=False, schema="integration")


def downgrade() -> None:
    op.drop_index("ix_integration_outbox_event_status_next_attempt", table_name="outbox_event", schema="integration")
    op.drop_table("outbox_event", schema="integration")
    op.drop_index("ix_integration_job_tenant_status", table_name="import_export_job", schema="integration")
    op.drop_table("import_export_job", schema="integration")
    op.drop_table("endpoint", schema="integration")
