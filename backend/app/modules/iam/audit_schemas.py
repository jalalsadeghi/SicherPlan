"""Schemas for audit and login event emission."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginEventWrite(BaseModel):
    tenant_id: str | None = None
    user_account_id: str | None = None
    session_id: str | None = None
    tenant_code: str | None = None
    identifier: str
    outcome: str
    failure_reason: str | None = None
    auth_method: str = "password"
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class LoginEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str | None
    user_account_id: str | None
    session_id: str | None
    tenant_code: str | None
    identifier: str
    outcome: str
    failure_reason: str | None
    auth_method: str
    ip_address: str | None
    user_agent: str | None
    request_id: str | None
    created_at: datetime
    metadata_json: dict[str, object]


class AuditEventWrite(BaseModel):
    tenant_id: str | None = None
    actor_user_id: str | None = None
    actor_session_id: str | None = None
    event_type: str
    entity_type: str
    entity_id: str
    request_id: str | None = None
    source: str = "api"
    before_json: dict[str, object] = Field(default_factory=dict)
    after_json: dict[str, object] = Field(default_factory=dict)
    metadata_json: dict[str, object] = Field(default_factory=dict)


class AuditEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str | None
    actor_user_id: str | None
    actor_session_id: str | None
    event_type: str
    entity_type: str
    entity_id: str
    request_id: str | None
    source: str
    before_json: dict[str, object]
    after_json: dict[str, object]
    metadata_json: dict[str, object]
    created_at: datetime
