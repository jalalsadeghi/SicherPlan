"""Integration endpoint, job, and transactional outbox models."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditLifecycleMixin, Base, TimestampedMixin, UUIDPrimaryKeyMixin


class IntegrationEndpoint(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "endpoint"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_integration_endpoint_tenant_id_id"),
        UniqueConstraint("tenant_id", "provider_key", "endpoint_type", name="uq_integration_endpoint_tenant_provider_type"),
        {"schema": "integration"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    provider_key: Mapped[str] = mapped_column(String(120), nullable=False)
    endpoint_type: Mapped[str] = mapped_column(String(80), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    auth_mode: Mapped[str] = mapped_column(String(40), nullable=False, default="token", server_default="token")
    config_public_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    secret_ciphertext: Mapped[str | None] = mapped_column(Text(), nullable=True)
    last_tested_at: Mapped[datetime | None] = mapped_column(nullable=True)


class ImportExportJob(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "import_export_job"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "endpoint_id"],
            ["integration.endpoint.tenant_id", "integration.endpoint.id"],
            name="fk_integration_job_tenant_endpoint",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_integration_import_export_job_tenant_id_id"),
        Index("ix_integration_job_tenant_status", "tenant_id", "status"),
        {"schema": "integration"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    endpoint_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    job_direction: Mapped[str] = mapped_column(String(20), nullable=False)
    job_type: Mapped[str] = mapped_column(String(120), nullable=False)
    request_payload_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    result_summary_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    error_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    requested_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("iam.user_account.id", ondelete="SET NULL"), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)


class OutboxEvent(UUIDPrimaryKeyMixin, TimestampedMixin, Base):
    __tablename__ = "outbox_event"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_integration_outbox_event_dedupe_key"),
        Index("ix_integration_outbox_event_status_next_attempt", "status", "next_attempt_at"),
        {"schema": "integration"},
    )

    tenant_id: Mapped[str | None] = mapped_column(ForeignKey("core.tenant.id", ondelete="SET NULL"), nullable=True)
    endpoint_id: Mapped[str | None] = mapped_column(ForeignKey("integration.endpoint.id", ondelete="SET NULL"), nullable=True)
    aggregate_type: Mapped[str] = mapped_column(String(120), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_type: Mapped[str] = mapped_column(String(160), nullable=False)
    topic: Mapped[str] = mapped_column(String(160), nullable=False)
    payload_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(nullable=True)
    attempt_count: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    last_error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_error_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    processed_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, default="pending", server_default="pending")

    endpoint: Mapped[IntegrationEndpoint | None] = relationship()
