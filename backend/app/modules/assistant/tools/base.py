"""Base types for assistant tool registry execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel

from app.modules.iam.authz import RequestAuthorizationContext


class AssistantToolClassification(str, Enum):
    READ_ONLY = "read_only"
    WRITE = "write"


class AssistantToolScopeBehavior(str, Enum):
    PLATFORM = "platform"
    TENANT = "tenant"
    BRANCH = "branch"
    MANDATE = "mandate"
    CUSTOMER = "customer"
    SUBCONTRACTOR = "subcontractor"
    EMPLOYEE_SELF_SERVICE = "employee_self_service"
    CURRENT_USER = "current_user"


@dataclass(frozen=True)
class AssistantToolDefinition:
    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    required_permissions: list[str] = field(default_factory=list)
    scope_behavior: AssistantToolScopeBehavior = AssistantToolScopeBehavior.TENANT
    redaction_policy: str = "default"
    classification: AssistantToolClassification = AssistantToolClassification.READ_ONLY
    enabled: bool = True
    max_rows: int = 50
    timeout_seconds: int = 15


@dataclass(frozen=True)
class AssistantToolExecutionContext:
    auth_context: RequestAuthorizationContext
    tenant_id: str | None
    user_id: str
    role_keys: frozenset[str]
    permission_keys: frozenset[str]
    scope_kind: str
    conversation_id: str | None = None
    message_id: str | None = None
    request_id: str | None = None


@dataclass(frozen=True)
class AssistantToolResult:
    ok: bool
    tool_name: str
    data: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    missing_permissions: list[dict[str, str]] = field(default_factory=list)
    redacted_output: dict[str, Any] | None = None
    entity_refs: dict[str, Any] | None = None
    duration_ms: int | None = None
    permission_decision: str = "allowed"


class AssistantTool(Protocol):
    definition: AssistantToolDefinition

    def execute(
        self,
        *,
        input_data: BaseModel,
        context: AssistantToolExecutionContext,
    ) -> AssistantToolResult: ...
