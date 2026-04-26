"""Add assistant persistence baseline.

Revision ID: 0063_assistant_persistence_baseline
Revises: 0062_planning_service_categories_catalog
Create Date: 2026-04-26 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0063_assistant_persistence_baseline"
down_revision = "0062_planning_service_categories_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS assistant")

    op.create_table(
        "conversation",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("locale", sa.String(length=10), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("last_route_name", sa.String(length=255), nullable=True),
        sa.Column("last_route_path", sa.Text(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.CheckConstraint("status IN ('active', 'archived')", name="assistant_conversation_status_valid"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["iam.user_account.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_conversation"),
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_conversation_tenant_user_updated",
        "conversation",
        ["tenant_id", "user_id", "updated_at"],
        unique=False,
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_conversation_user_status",
        "conversation",
        ["user_id", "status"],
        unique=False,
        schema="assistant",
    )

    op.create_table(
        "knowledge_source",
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_path", sa.String(length=500), nullable=False),
        sa.Column("source_hash", sa.String(length=128), nullable=False),
        sa.Column("source_version", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("last_ingested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.CheckConstraint("status IN ('active', 'inactive', 'failed')", name="assistant_knowledge_source_status_valid"),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_source"),
        sa.UniqueConstraint("source_path", "source_hash", name="uq_assistant_knowledge_source_path_hash"),
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_knowledge_source_path_status",
        "knowledge_source",
        ["source_path", "status"],
        unique=False,
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_knowledge_source_type_status",
        "knowledge_source",
        ["source_type", "status"],
        unique=False,
        schema="assistant",
    )

    op.create_table(
        "page_route_catalog",
        sa.Column("page_id", sa.String(length=120), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("route_name", sa.String(length=255), nullable=True),
        sa.Column("path_template", sa.String(length=500), nullable=False),
        sa.Column("module_key", sa.String(length=120), nullable=False),
        sa.Column("api_families", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("required_permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("allowed_role_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("scope_kind", sa.String(length=64), nullable=True),
        sa.Column("supports_entity_deep_link", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("entity_param_map", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.PrimaryKeyConstraint("id", name="pk_page_route_catalog"),
        sa.UniqueConstraint("page_id", "path_template", name="uq_assistant_page_route_page_path"),
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_page_route_catalog_page_active",
        "page_route_catalog",
        ["page_id", "active"],
        unique=False,
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_page_route_catalog_module_active",
        "page_route_catalog",
        ["module_key", "active"],
        unique=False,
        schema="assistant",
    )

    op.create_table(
        "prompt_policy_version",
        sa.Column("policy_key", sa.String(length=120), nullable=False),
        sa.Column("version_label", sa.String(length=120), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["iam.user_account.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_prompt_policy_version"),
        sa.UniqueConstraint("policy_key", "version_label", name="uq_assistant_prompt_policy_key_version"),
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_prompt_policy_key_active",
        "prompt_policy_version",
        ["policy_key", "active"],
        unique=False,
        schema="assistant",
    )

    op.create_table(
        "message",
        sa.Column("conversation_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("detected_language", sa.String(length=16), nullable=True),
        sa.Column("response_language", sa.String(length=16), nullable=True),
        sa.Column("token_input", sa.Integer(), nullable=True),
        sa.Column("token_output", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.CheckConstraint("role IN ('user', 'assistant', 'tool', 'system_summary')", name="assistant_message_role_valid"),
        sa.ForeignKeyConstraint(["conversation_id"], ["assistant.conversation.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["iam.user_account.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name="pk_message"),
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_message_conversation_created",
        "message",
        ["conversation_id", "created_at"],
        unique=False,
        schema="assistant",
    )

    op.create_table(
        "knowledge_chunk",
        sa.Column("source_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("language_code", sa.String(length=16), nullable=True),
        sa.Column("module_key", sa.String(length=120), nullable=True),
        sa.Column("page_id", sa.String(length=120), nullable=True),
        sa.Column("role_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("permission_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.ForeignKeyConstraint(["source_id"], ["assistant.knowledge_source.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_chunk"),
        sa.UniqueConstraint("source_id", "chunk_index", name="uq_assistant_knowledge_chunk_source_index"),
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_knowledge_chunk_source_index",
        "knowledge_chunk",
        ["source_id", "chunk_index"],
        unique=False,
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_knowledge_chunk_module_page",
        "knowledge_chunk",
        ["module_key", "page_id"],
        unique=False,
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_knowledge_chunk_language",
        "knowledge_chunk",
        ["language_code"],
        unique=False,
        schema="assistant",
    )

    op.create_table(
        "tool_call",
        sa.Column("conversation_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tool_name", sa.String(length=160), nullable=False),
        sa.Column("input_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output_json_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("required_permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("permission_decision", sa.String(length=32), nullable=False),
        sa.Column("scope_kind", sa.String(length=64), nullable=True),
        sa.Column("entity_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.CheckConstraint(
            "permission_decision IN ('allowed', 'denied', 'failed')",
            name="assistant_tool_call_permission_decision_valid",
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["assistant.conversation.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["assistant.message.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["iam.user_account.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_tool_call"),
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_tool_call_conversation_created",
        "tool_call",
        ["conversation_id", "created_at"],
        unique=False,
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_tool_call_tenant_user_created",
        "tool_call",
        ["tenant_id", "user_id", "created_at"],
        unique=False,
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_tool_call_tool_name_created",
        "tool_call",
        ["tool_name", "created_at"],
        unique=False,
        schema="assistant",
    )

    op.create_table(
        "feedback",
        sa.Column("conversation_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("rating", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.CheckConstraint("rating IN ('helpful', 'not_helpful')", name="assistant_feedback_rating_valid"),
        sa.ForeignKeyConstraint(["conversation_id"], ["assistant.conversation.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["assistant.message.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["core.tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["iam.user_account.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_feedback"),
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_feedback_conversation_message",
        "feedback",
        ["conversation_id", "message_id"],
        unique=False,
        schema="assistant",
    )
    op.create_index(
        "ix_assistant_feedback_tenant_user_created",
        "feedback",
        ["tenant_id", "user_id", "created_at"],
        unique=False,
        schema="assistant",
    )


def downgrade() -> None:
    op.drop_index("ix_assistant_feedback_tenant_user_created", table_name="feedback", schema="assistant")
    op.drop_index("ix_assistant_feedback_conversation_message", table_name="feedback", schema="assistant")
    op.drop_table("feedback", schema="assistant")
    op.drop_index("ix_assistant_tool_call_tool_name_created", table_name="tool_call", schema="assistant")
    op.drop_index("ix_assistant_tool_call_tenant_user_created", table_name="tool_call", schema="assistant")
    op.drop_index("ix_assistant_tool_call_conversation_created", table_name="tool_call", schema="assistant")
    op.drop_table("tool_call", schema="assistant")
    op.drop_index("ix_assistant_knowledge_chunk_language", table_name="knowledge_chunk", schema="assistant")
    op.drop_index("ix_assistant_knowledge_chunk_module_page", table_name="knowledge_chunk", schema="assistant")
    op.drop_index("ix_assistant_knowledge_chunk_source_index", table_name="knowledge_chunk", schema="assistant")
    op.drop_table("knowledge_chunk", schema="assistant")
    op.drop_index("ix_assistant_message_conversation_created", table_name="message", schema="assistant")
    op.drop_table("message", schema="assistant")
    op.drop_index("ix_assistant_prompt_policy_key_active", table_name="prompt_policy_version", schema="assistant")
    op.drop_table("prompt_policy_version", schema="assistant")
    op.drop_index("ix_assistant_page_route_catalog_module_active", table_name="page_route_catalog", schema="assistant")
    op.drop_index("ix_assistant_page_route_catalog_page_active", table_name="page_route_catalog", schema="assistant")
    op.drop_table("page_route_catalog", schema="assistant")
    op.drop_index("ix_assistant_knowledge_source_type_status", table_name="knowledge_source", schema="assistant")
    op.drop_index("ix_assistant_knowledge_source_path_status", table_name="knowledge_source", schema="assistant")
    op.drop_table("knowledge_source", schema="assistant")
    op.drop_index("ix_assistant_conversation_user_status", table_name="conversation", schema="assistant")
    op.drop_index("ix_assistant_conversation_tenant_user_updated", table_name="conversation", schema="assistant")
    op.drop_table("conversation", schema="assistant")
