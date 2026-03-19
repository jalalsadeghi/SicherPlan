"""Shared document and storage metadata models."""

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


class DocumentType(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "document_type"
    __table_args__ = (
        UniqueConstraint("key", name="uq_docs_document_type_key"),
        {"schema": "docs"},
    )

    key: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_system_type: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))

    documents: Mapped[list["Document"]] = relationship(back_populates="document_type")


class Document(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "document"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_docs_document_tenant_id_id"),
        Index("ix_docs_document_tenant_status", "tenant_id", "status"),
        {"schema": "docs"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    document_type_id: Mapped[str | None] = mapped_column(
        ForeignKey("docs.document_type.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_module: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_version_no: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    document_type: Mapped[DocumentType | None] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document",
        order_by="DocumentVersion.version_no",
    )
    links: Mapped[list["DocumentLink"]] = relationship(back_populates="document")


class DocumentVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_version"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["docs.document.tenant_id", "docs.document.id"],
            name="fk_docs_document_version_tenant_document",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("document_id", "version_no", name="uq_docs_document_version_document_version_no"),
        UniqueConstraint("object_bucket", "object_key", name="uq_docs_document_version_object_ref"),
        Index("ix_docs_document_version_tenant_document_version", "tenant_id", "document_id", "version_no"),
        {"schema": "docs"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    object_bucket: Mapped[str] = mapped_column(String(120), nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    is_revision_safe_pdf: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    document: Mapped[Document] = relationship(back_populates="versions")


class DocumentLink(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_link"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "document_id"],
            ["docs.document.tenant_id", "docs.document.id"],
            name="fk_docs_document_link_tenant_document",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "document_id",
            "owner_type",
            "owner_id",
            "relation_type",
            name="uq_docs_document_link_owner_relation",
        ),
        Index("ix_docs_document_link_owner_lookup", "tenant_id", "owner_type", "owner_id"),
        {"schema": "docs"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    document_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    owner_type: Mapped[str] = mapped_column(String(120), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(80), nullable=False, default="attachment", server_default="attachment")
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linked_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("iam.user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    linked_at: Mapped[datetime] = mapped_column(
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

    document: Mapped[Document] = relationship(back_populates="links")
