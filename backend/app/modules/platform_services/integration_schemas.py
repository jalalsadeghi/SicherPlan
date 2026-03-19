"""Pydantic schemas for integration endpoints, jobs, and outbox events."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IntegrationEndpointCreate(BaseModel):
    tenant_id: str
    provider_key: str
    endpoint_type: str
    base_url: str
    auth_mode: str = "token"
    config_public_json: dict[str, object] = Field(default_factory=dict)
    secret_config_json: dict[str, object] = Field(default_factory=dict)


class IntegrationEndpointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    provider_key: str
    endpoint_type: str
    base_url: str
    auth_mode: str
    config_public_json: dict[str, object]
    last_tested_at: datetime | None
    status: str
    version_no: int


class ImportExportJobCreate(BaseModel):
    tenant_id: str
    endpoint_id: str | None = None
    job_direction: str
    job_type: str
    request_payload_json: dict[str, object] = Field(default_factory=dict)
    result_document_id: str | None = None


class ImportExportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    endpoint_id: str | None
    job_direction: str
    job_type: str
    request_payload_json: dict[str, object]
    result_summary_json: dict[str, object]
    error_summary: str | None
    requested_by_user_id: str | None
    started_at: datetime | None
    completed_at: datetime | None
    status: str
    version_no: int
    result_document_ids: list[str] = Field(default_factory=list)


class OutboxEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str | None
    endpoint_id: str | None
    aggregate_type: str
    aggregate_id: str
    event_type: str
    topic: str
    payload_json: dict[str, object]
    dedupe_key: str
    published_at: datetime | None
    next_attempt_at: datetime | None
    attempt_count: int
    last_error_code: str | None
    last_error_summary: str | None
    processed_by: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class OutboxProcessRequest(BaseModel):
    worker_name: str = "dev-worker"
    limit: int = 25
