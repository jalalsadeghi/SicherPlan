"""Pydantic schemas for the communication backbone."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageTemplateUpsert(BaseModel):
    tenant_id: str
    channel: str
    template_key: str
    language_code: str = "de"
    subject_template: str | None = None
    body_template: str
    metadata_json: dict[str, object] = Field(default_factory=dict)


class MessageTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    channel: str
    template_key: str
    language_code: str
    subject_template: str | None
    body_template: str
    metadata_json: dict[str, object]
    status: str
    version_no: int
    created_at: datetime
    updated_at: datetime


class MessageRecipientCreate(BaseModel):
    recipient_kind: str = "to"
    destination: str
    display_name: str | None = None
    user_account_id: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class RenderedMessageCreate(BaseModel):
    tenant_id: str
    channel: str
    template_key: str
    language_code: str = "de"
    placeholders: dict[str, object] = Field(default_factory=dict)
    recipients: list[MessageRecipientCreate]
    attachment_document_ids: list[str] = Field(default_factory=list)
    related_entity_type: str | None = None
    related_entity_id: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class DeliveryAttemptCreate(BaseModel):
    provider_key: str
    provider_message_ref: str | None = None
    outcome: str
    response_code: str | None = None
    response_summary: str | None = None
    error_code: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class MessageRecipientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    outbound_message_id: str
    recipient_kind: str
    destination: str
    display_name: str | None
    user_account_id: str | None
    status: str
    status_reason: str | None
    metadata_json: dict[str, object]
    created_at: datetime
    updated_at: datetime


class DeliveryAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    outbound_message_id: str
    recipient_id: str
    provider_key: str
    provider_message_ref: str | None
    outcome: str
    attempt_no: int
    response_code: str | None
    response_summary: str | None
    error_code: str | None
    metadata_json: dict[str, object]
    attempted_at: datetime


class OutboundMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    template_id: str | None
    channel: str
    template_key: str | None
    language_code: str
    subject_rendered: str | None
    body_rendered: str
    related_entity_type: str | None
    related_entity_id: str | None
    send_started_at: datetime | None
    metadata_json: dict[str, object]
    status: str
    version_no: int
    created_at: datetime
    updated_at: datetime
    recipients: list[MessageRecipientRead] = Field(default_factory=list)
    delivery_attempts: list[DeliveryAttemptRead] = Field(default_factory=list)
