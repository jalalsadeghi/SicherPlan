"""Pydantic schemas for notices, audience targeting, and acknowledgement evidence."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoticeAudienceCreate(BaseModel):
    audience_kind: str
    target_value: str | None = None
    target_label: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class NoticeLinkCreate(BaseModel):
    label: str
    url: str
    link_type: str = "external"
    sort_order: int = 100
    metadata_json: dict[str, object] = Field(default_factory=dict)


class NoticeCreate(BaseModel):
    tenant_id: str
    title: str
    summary: str | None = None
    body: str
    language_code: str = "de"
    mandatory_acknowledgement: bool = False
    publish_from: datetime | None = None
    publish_until: datetime | None = None
    related_entity_type: str | None = None
    related_entity_id: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)
    audiences: list[NoticeAudienceCreate] = Field(default_factory=list)
    curated_links: list[NoticeLinkCreate] = Field(default_factory=list)
    attachment_document_ids: list[str] = Field(default_factory=list)


class NoticePublishRequest(BaseModel):
    publish_from: datetime | None = None
    publish_until: datetime | None = None


class NoticeAcknowledgeRequest(BaseModel):
    acknowledgement_text: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class NoticeAudienceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    notice_id: str
    audience_kind: str
    target_value: str | None
    target_label: str | None
    metadata_json: dict[str, object]
    status: str
    created_at: datetime


class NoticeLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    notice_id: str
    label: str
    url: str
    link_type: str
    sort_order: int
    metadata_json: dict[str, object]
    created_at: datetime


class NoticeReadEvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    notice_id: str
    user_account_id: str
    first_opened_at: datetime
    last_opened_at: datetime
    acknowledged_at: datetime | None
    acknowledgement_text: str | None
    metadata_json: dict[str, object]
    created_at: datetime
    updated_at: datetime


class NoticeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    title: str
    summary: str | None
    body: str
    language_code: str
    mandatory_acknowledgement: bool
    publish_from: datetime | None
    publish_until: datetime | None
    published_at: datetime | None
    unpublished_at: datetime | None
    related_entity_type: str | None
    related_entity_id: str | None
    metadata_json: dict[str, object]
    status: str
    version_no: int
    created_at: datetime
    updated_at: datetime
    audiences: list[NoticeAudienceRead] = Field(default_factory=list)
    reads: list[NoticeReadEvidenceRead] = Field(default_factory=list)
    links: list[NoticeLinkRead] = Field(default_factory=list)
    attachment_document_ids: list[str] = Field(default_factory=list)


class NoticeListItem(BaseModel):
    id: str
    title: str
    summary: str | None
    language_code: str
    mandatory_acknowledgement: bool
    publish_from: datetime | None
    publish_until: datetime | None
    published_at: datetime | None
    status: str
    acknowledged_at: datetime | None = None
    audiences: list[NoticeAudienceRead] = Field(default_factory=list)
    links: list[NoticeLinkRead] = Field(default_factory=list)
    attachment_document_ids: list[str] = Field(default_factory=list)
