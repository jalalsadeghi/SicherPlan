"""Append-only audit and login event models."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class LoginEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "login_event"
    __table_args__ = (
        Index("ix_audit_login_event_tenant_created_at", "tenant_id", "created_at"),
        Index("ix_audit_login_event_user_created_at", "user_account_id", "created_at"),
        {"schema": "audit"},
    )

    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("iam.user_session.id", ondelete="SET NULL"),
        nullable=True,
    )
    tenant_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(80), nullable=True)
    auth_method: Mapped[str] = mapped_column(String(40), nullable=False, default="password", server_default="password")
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text(), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_event"
    __table_args__ = (
        Index("ix_audit_audit_event_tenant_created_at", "tenant_id", "created_at"),
        Index("ix_audit_audit_event_entity_created_at", "entity_type", "entity_id", "created_at"),
        {"schema": "audit"},
    )

    tenant_id: Mapped[str | None] = mapped_column(
        ForeignKey("core.tenant.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("iam.user_session.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="api", server_default="api")
    before_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    after_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )
