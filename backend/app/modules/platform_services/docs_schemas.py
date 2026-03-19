"""Pydantic schemas for the shared docs backbone."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: str
    name: str
    description: str | None
    is_system_type: bool


class DocumentCreate(BaseModel):
    tenant_id: str
    title: str
    document_type_key: str | None = None
    source_module: str | None = None
    source_label: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class DocumentVersionCreate(BaseModel):
    file_name: str
    content_type: str
    content_base64: str
    is_revision_safe_pdf: bool = False
    metadata_json: dict[str, object] = Field(default_factory=dict)


class DocumentLinkCreate(BaseModel):
    owner_type: str
    owner_id: str
    relation_type: str = "attachment"
    label: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class DocumentLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    document_id: str
    owner_type: str
    owner_id: str
    relation_type: str
    label: str | None
    linked_by_user_id: str | None
    linked_at: datetime
    metadata_json: dict[str, object]


class DocumentVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    document_id: str
    version_no: int
    file_name: str
    content_type: str
    object_bucket: str
    object_key: str
    checksum_sha256: str
    file_size_bytes: int
    uploaded_by_user_id: str | None
    uploaded_at: datetime
    is_revision_safe_pdf: bool
    metadata_json: dict[str, object]


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    title: str
    document_type_id: str | None
    source_module: str | None
    source_label: str | None
    status: str
    current_version_no: int
    metadata_json: dict[str, object]
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None
    version_no: int
    document_type: DocumentTypeRead | None = None
    versions: list[DocumentVersionRead] = Field(default_factory=list)
    links: list[DocumentLinkRead] = Field(default_factory=list)
