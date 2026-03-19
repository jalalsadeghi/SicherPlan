"""Information portal backbone models for notices, audiences, evidence, and curated links."""

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

from app.db.base import AuditLifecycleMixin, Base, TimestampedMixin, UUIDPrimaryKeyMixin


class Notice(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "notice"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_info_notice_tenant_id_id"),
        Index("ix_info_notice_tenant_status_publish_from", "tenant_id", "status", "publish_from"),
        {"schema": "info"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    language_code: Mapped[str] = mapped_column(String(8), nullable=False, default="de", server_default="de")
    mandatory_acknowledgement: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    publish_from: Mapped[datetime | None] = mapped_column(nullable=True)
    publish_until: Mapped[datetime | None] = mapped_column(nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    unpublished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    related_entity_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    related_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    audiences: Mapped[list["NoticeAudience"]] = relationship(
        back_populates="notice",
        order_by="NoticeAudience.created_at",
    )
    reads: Mapped[list["NoticeRead"]] = relationship(
        back_populates="notice",
        order_by="NoticeRead.first_opened_at",
    )
    links: Mapped[list["NoticeLink"]] = relationship(
        back_populates="notice",
        order_by="NoticeLink.sort_order",
    )


class NoticeAudience(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "notice_audience"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "notice_id"],
            ["info.notice.tenant_id", "info.notice.id"],
            name="fk_info_notice_audience_tenant_notice",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "notice_id",
            "audience_kind",
            "target_value",
            name="uq_info_notice_audience_scope",
        ),
        Index("ix_info_notice_audience_notice_kind", "notice_id", "audience_kind"),
        {"schema": "info"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    notice_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    audience_kind: Mapped[str] = mapped_column(String(80), nullable=False)
    target_value: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    notice: Mapped[Notice] = relationship(back_populates="audiences")


class NoticeRead(UUIDPrimaryKeyMixin, TimestampedMixin, Base):
    __tablename__ = "notice_read"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "notice_id"],
            ["info.notice.tenant_id", "info.notice.id"],
            name="fk_info_notice_read_tenant_notice",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("notice_id", "user_account_id", name="uq_info_notice_read_notice_user"),
        Index("ix_info_notice_read_user_ack", "user_account_id", "acknowledged_at"),
        {"schema": "info"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    notice_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    user_account_id: Mapped[str] = mapped_column(ForeignKey("iam.user_account.id", ondelete="RESTRICT"), nullable=False)
    first_opened_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    last_opened_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(nullable=True)
    acknowledgement_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    notice: Mapped[Notice] = relationship(back_populates="reads")


class NoticeLink(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "notice_link"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "notice_id"],
            ["info.notice.tenant_id", "info.notice.id"],
            name="fk_info_notice_link_tenant_notice",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "notice_id", "url", name="uq_info_notice_link_notice_url"),
        {"schema": "info"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    notice_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    link_type: Mapped[str] = mapped_column(String(40), nullable=False, default="external", server_default="external")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
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

    notice: Mapped[Notice] = relationship(back_populates="links")
