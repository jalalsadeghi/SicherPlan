"""Assistant persistence models."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampedMixin, UUIDPrimaryKeyMixin


class AssistantConversation(UUIDPrimaryKeyMixin, TimestampedMixin, Base):
    __tablename__ = "conversation"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'archived')", name="assistant_conversation_status_valid"),
        Index("ix_assistant_conversation_tenant_user_updated", "tenant_id", "user_id", "updated_at"),
        Index("ix_assistant_conversation_user_status", "user_id", "status"),
        {"schema": "assistant"},
    )

    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", server_default="active")
    last_route_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_route_path: Mapped[str | None] = mapped_column(Text(), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(nullable=True)

    messages: Mapped[list["AssistantMessage"]] = relationship(
        back_populates="conversation",
        order_by="AssistantMessage.created_at",
    )
    tool_calls: Mapped[list["AssistantToolCall"]] = relationship(
        back_populates="conversation",
        order_by="AssistantToolCall.created_at",
    )
    feedback_items: Mapped[list["AssistantFeedback"]] = relationship(
        back_populates="conversation",
        order_by="AssistantFeedback.created_at",
    )


class AssistantMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "message"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'tool', 'system_summary')",
            name="assistant_message_role_valid",
        ),
        Index("ix_assistant_message_conversation_created", "conversation_id", "created_at"),
        {"schema": "assistant"},
    )

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("assistant.conversation.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=True,
    )
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    structured_payload: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    detected_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    response_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    token_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    conversation: Mapped[AssistantConversation] = relationship(back_populates="messages")
    tool_calls: Mapped[list["AssistantToolCall"]] = relationship(
        back_populates="message",
        order_by="AssistantToolCall.created_at",
    )
    feedback_items: Mapped[list["AssistantFeedback"]] = relationship(
        back_populates="message",
        order_by="AssistantFeedback.created_at",
    )


class AssistantToolCall(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "tool_call"
    __table_args__ = (
        CheckConstraint(
            "permission_decision IN ('allowed', 'denied', 'failed')",
            name="assistant_tool_call_permission_decision_valid",
        ),
        Index("ix_assistant_tool_call_conversation_created", "conversation_id", "created_at"),
        Index("ix_assistant_tool_call_tenant_user_created", "tenant_id", "user_id", "created_at"),
        Index("ix_assistant_tool_call_tool_name_created", "tool_name", "created_at"),
        {"schema": "assistant"},
    )

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("assistant.conversation.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_id: Mapped[str | None] = mapped_column(
        ForeignKey("assistant.message.id", ondelete="SET NULL"),
        nullable=True,
    )
    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="RESTRICT"),
        nullable=False,
    )
    tool_name: Mapped[str] = mapped_column(String(160), nullable=False)
    input_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    output_json_summary: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    required_permissions: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    permission_decision: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_refs: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    conversation: Mapped[AssistantConversation] = relationship(back_populates="tool_calls")
    message: Mapped[AssistantMessage | None] = relationship(back_populates="tool_calls")


class AssistantFeedback(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint(
            "rating IN ('helpful', 'not_helpful')",
            name="assistant_feedback_rating_valid",
        ),
        Index("ix_assistant_feedback_conversation_message", "conversation_id", "message_id"),
        Index("ix_assistant_feedback_tenant_user_created", "tenant_id", "user_id", "created_at"),
        {"schema": "assistant"},
    )

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("assistant.conversation.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_id: Mapped[str] = mapped_column(
        ForeignKey("assistant.message.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="RESTRICT"),
        nullable=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rating: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    conversation: Mapped[AssistantConversation] = relationship(back_populates="feedback_items")
    message: Mapped[AssistantMessage] = relationship(back_populates="feedback_items")


class AssistantKnowledgeSource(UUIDPrimaryKeyMixin, TimestampedMixin, Base):
    __tablename__ = "knowledge_source"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'failed')", name="assistant_knowledge_source_status_valid"),
        UniqueConstraint("source_path", "source_hash", name="uq_assistant_knowledge_source_path_hash"),
        Index("ix_assistant_knowledge_source_path_status", "source_path", "status"),
        Index("ix_assistant_knowledge_source_type_status", "source_type", "status"),
        {"schema": "assistant"},
    )

    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_path: Mapped[str] = mapped_column(String(500), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    source_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
    last_ingested_at: Mapped[datetime | None] = mapped_column(nullable=True)

    chunks: Mapped[list["AssistantKnowledgeChunk"]] = relationship(
        back_populates="source",
        order_by="AssistantKnowledgeChunk.chunk_index",
    )


class AssistantKnowledgeChunk(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_chunk"
    __table_args__ = (
        UniqueConstraint("source_id", "chunk_index", name="uq_assistant_knowledge_chunk_source_index"),
        Index("ix_assistant_knowledge_chunk_source_index", "source_id", "chunk_index"),
        Index("ix_assistant_knowledge_chunk_module_page", "module_key", "page_id"),
        Index("ix_assistant_knowledge_chunk_language", "language_code"),
        {"schema": "assistant"},
    )

    source_id: Mapped[str] = mapped_column(
        ForeignKey("assistant.knowledge_source.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    language_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    module_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    page_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    content_preview: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workflow_keys: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    role_keys: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    permission_keys: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    api_families: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    domain_terms: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    language_aliases: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    embedding: Mapped[list[float] | dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    source: Mapped[AssistantKnowledgeSource] = relationship(back_populates="chunks")


class AssistantPageRouteCatalog(UUIDPrimaryKeyMixin, TimestampedMixin, Base):
    __tablename__ = "page_route_catalog"
    __table_args__ = (
        UniqueConstraint("page_id", "path_template", name="uq_assistant_page_route_page_path"),
        Index("ix_assistant_page_route_catalog_page_active", "page_id", "active"),
        Index("ix_assistant_page_route_catalog_module_active", "module_key", "active"),
        {"schema": "assistant"},
    )

    page_id: Mapped[str] = mapped_column(String(120), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    route_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    path_template: Mapped[str] = mapped_column(String(500), nullable=False)
    module_key: Mapped[str] = mapped_column(String(120), nullable=False)
    api_families: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    required_permissions: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    allowed_role_keys: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    scope_kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
    supports_entity_deep_link: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    entity_param_map: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )


class AssistantPageHelpManifest(UUIDPrimaryKeyMixin, TimestampedMixin, Base):
    __tablename__ = "page_help_manifest"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'draft', 'unverified')",
            name="assistant_page_help_manifest_status_valid",
        ),
        UniqueConstraint(
            "page_id",
            "language_code",
            "manifest_version",
            name="uq_assistant_page_help_manifest_page_lang_version",
        ),
        Index("ix_assistant_page_help_manifest_page_active", "page_id", "status"),
        Index("ix_assistant_page_help_manifest_module", "module_key"),
        {"schema": "assistant"},
    )

    page_id: Mapped[str] = mapped_column(String(120), nullable=False)
    route_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    path_template: Mapped[str | None] = mapped_column(String(500), nullable=True)
    module_key: Mapped[str] = mapped_column(String(120), nullable=False)
    language_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    manifest_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        server_default="active",
    )
    manifest_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    verified_from: Mapped[list[dict[str, object]] | dict[str, object] | None] = mapped_column(
        JSONB,
        nullable=True,
    )


class AssistantPromptPolicyVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "prompt_policy_version"
    __table_args__ = (
        UniqueConstraint("policy_key", "version_label", name="uq_assistant_prompt_policy_key_version"),
        Index("ix_assistant_prompt_policy_key_active", "policy_key", "active"),
        {"schema": "assistant"},
    )

    policy_key: Mapped[str] = mapped_column(String(120), nullable=False)
    version_label: Mapped[str] = mapped_column(String(120), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    created_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
