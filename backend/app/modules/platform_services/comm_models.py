"""Communication backbone models for templates, outbound messages, recipients, and attempts."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditLifecycleMixin, Base, UUIDPrimaryKeyMixin


class MessageTemplate(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "message_template"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "channel",
            "template_key",
            "language_code",
            name="uq_comm_message_template_tenant_channel_key_language",
        ),
        {"schema": "comm"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    template_key: Mapped[str] = mapped_column(String(120), nullable=False)
    language_code: Mapped[str] = mapped_column(String(8), nullable=False, default="de", server_default="de")
    subject_template: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_template: Mapped[str] = mapped_column(Text(), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )


class OutboundMessage(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "outbound_message"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_comm_outbound_message_tenant_id_id"),
        Index("ix_comm_outbound_message_tenant_status", "tenant_id", "status"),
        {"schema": "comm"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("comm.message_template.id", ondelete="SET NULL"),
        nullable=True,
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    template_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    language_code: Mapped[str] = mapped_column(String(8), nullable=False, default="de", server_default="de")
    subject_rendered: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_rendered: Mapped[str] = mapped_column(Text(), nullable=False)
    related_entity_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    related_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    send_started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    template: Mapped[MessageTemplate | None] = relationship()
    recipients: Mapped[list["MessageRecipient"]] = relationship(
        back_populates="outbound_message",
        order_by="MessageRecipient.created_at",
    )
    delivery_attempts: Mapped[list["DeliveryAttempt"]] = relationship(
        back_populates="outbound_message",
        order_by="DeliveryAttempt.attempted_at",
        overlaps="recipient,delivery_attempts",
    )


class MessageRecipient(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "message_recipient"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "outbound_message_id"],
            ["comm.outbound_message.tenant_id", "comm.outbound_message.id"],
            name="fk_comm_message_recipient_tenant_message",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_comm_message_recipient_tenant_id_id"),
        Index("ix_comm_message_recipient_tenant_message", "tenant_id", "outbound_message_id"),
        {"schema": "comm"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    outbound_message_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    recipient_kind: Mapped[str] = mapped_column(String(10), nullable=False, default="to", server_default="to")
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    status_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    outbound_message: Mapped[OutboundMessage] = relationship(back_populates="recipients")
    delivery_attempts: Mapped[list["DeliveryAttempt"]] = relationship(
        back_populates="recipient",
        order_by="DeliveryAttempt.attempted_at",
        overlaps="outbound_message,delivery_attempts",
    )


class DeliveryAttempt(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "delivery_attempt"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "outbound_message_id"],
            ["comm.outbound_message.tenant_id", "comm.outbound_message.id"],
            name="fk_comm_delivery_attempt_tenant_message",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "recipient_id"],
            ["comm.message_recipient.tenant_id", "comm.message_recipient.id"],
            name="fk_comm_delivery_attempt_tenant_recipient",
            ondelete="RESTRICT",
        ),
        Index("ix_comm_delivery_attempt_recipient_attempted_at", "recipient_id", "attempted_at"),
        {"schema": "comm"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    outbound_message_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    recipient_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    provider_key: Mapped[str] = mapped_column(String(80), nullable=False)
    provider_message_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    response_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    response_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    attempted_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    outbound_message: Mapped[OutboundMessage] = relationship(
        back_populates="delivery_attempts",
        overlaps="recipient,delivery_attempts",
    )
    recipient: Mapped[MessageRecipient] = relationship(
        back_populates="delivery_attempts",
        overlaps="outbound_message,delivery_attempts",
    )
