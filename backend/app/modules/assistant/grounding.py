"""Typed grounding context for provider-bound assistant requests."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.modules.assistant.schemas import AssistantMissingPermission


class AssistantGroundingSource(BaseModel):
    source_id: str | None = None
    source_type: str
    source_name: str | None = None
    page_id: str | None = None
    module_key: str | None = None
    title: str | None = None
    content: str | None = None
    facts: dict[str, Any] = Field(default_factory=dict)
    score: float | None = None
    why_selected: list[str] = Field(default_factory=list)
    content_bearing: bool = False
    verified: bool = False
    permission_checked: bool = False


class AssistantGroundingContext(BaseModel):
    detected_language: str
    response_language: str
    route_context: dict[str, Any] | None = None
    auth_summary: dict[str, Any]
    retrieval_plan: dict[str, Any]
    query_expansion: dict[str, Any] = Field(default_factory=dict)
    sources: list[AssistantGroundingSource] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)
    missing_permissions: list[AssistantMissingPermission] = Field(default_factory=list)
    grounding_trimmed: bool = False
    trim_reason: str | None = None
