from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolRegistry,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)
from app.modules.assistant.tools.base import AssistantTool
from app.modules.assistant.tools.redaction import redact_tool_payload
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


class EchoInput(BaseModel):
    text: str = Field(min_length=1, max_length=40)


class EchoOutput(BaseModel):
    echoed: str
    token: str | None = None


class ContextInput(BaseModel):
    tenant_id: str | None = None
    user_id: str | None = None


class ContextOutput(BaseModel):
    tenant_id: str
    user_id: str


class _EchoReadTool(AssistantTool):
    definition = AssistantToolDefinition(
        name="assistant.test_echo_read",
        description="Echo read-only test tool",
        input_schema=EchoInput,
        output_schema=EchoOutput,
        required_permissions=[],
        scope_behavior=AssistantToolScopeBehavior.CURRENT_USER,
        classification=AssistantToolClassification.READ_ONLY,
        enabled=True,
    )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        del context
        payload = EchoOutput(echoed=input_data.text, token="sk-secret12345").model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)


class _DisabledTool(AssistantTool):
    definition = AssistantToolDefinition(
        name="assistant.test_disabled",
        description="Disabled test tool",
        input_schema=EchoInput,
        output_schema=EchoOutput,
        enabled=False,
    )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        raise AssertionError("disabled tool must not execute")


class _WriteBlockedTool(AssistantTool):
    definition = AssistantToolDefinition(
        name="assistant.test_write_blocked",
        description="Write tool must not run",
        input_schema=EchoInput,
        output_schema=EchoOutput,
        classification=AssistantToolClassification.WRITE,
    )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        raise AssertionError("write tool must not execute")


class _BrokenTool(AssistantTool):
    definition = AssistantToolDefinition(
        name="assistant.test_broken",
        description="Broken test tool",
        input_schema=EchoInput,
        output_schema=EchoOutput,
    )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        raise RuntimeError("traceback boom with secret sk-live-hidden")


class _ContextTool(AssistantTool):
    definition = AssistantToolDefinition(
        name="assistant.test_context_read",
        description="Uses backend execution context only",
        input_schema=ContextInput,
        output_schema=ContextOutput,
    )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        del input_data
        return AssistantToolResult(
            ok=True,
            tool_name=self.definition.name,
            data=ContextOutput(tenant_id=context.tenant_id or "", user_id=context.user_id).model_dump(mode="json"),
        )


@dataclass
class _AuditRepository:
    records: list[object] = field(default_factory=list)

    def create_tool_call_audit(self, *, record) -> object:  # noqa: ANN001, ANN201
        self.records.append(record)
        return record


def _auth_context(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-1",
    )


def _tool_context(*permissions: str) -> AssistantToolExecutionContext:
    auth_context = _auth_context(*permissions)
    return AssistantToolExecutionContext(
        auth_context=auth_context,
        tenant_id=auth_context.tenant_id,
        user_id=auth_context.user_id,
        role_keys=auth_context.role_keys,
        permission_keys=auth_context.permission_keys,
        scope_kind="tenant",
        conversation_id="conv-1",
        message_id="msg-1",
        request_id=auth_context.request_id,
    )


def test_known_read_only_tool_executes_when_permission_is_present() -> None:
    audit = _AuditRepository()
    registry = AssistantToolRegistry(audit_repository=audit)
    registry.register(_EchoReadTool())

    result = registry.execute_tool(
        tool_name="assistant.test_echo_read",
        input_data={"text": "hello"},
        context=_tool_context("assistant.chat.access"),
    )

    assert result.ok is True
    assert result.data == {"echoed": "hello", "token": "[REDACTED]"}
    assert audit.records[0].permission_decision == "allowed"


def test_unknown_tool_is_rejected() -> None:
    registry = AssistantToolRegistry(audit_repository=_AuditRepository())

    result = registry.execute_tool(
        tool_name="assistant.test_missing",
        input_data={"text": "hello"},
        context=_tool_context("assistant.chat.access"),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.not_found"


def test_disabled_tool_is_rejected() -> None:
    registry = AssistantToolRegistry(audit_repository=_AuditRepository())
    registry.register(_DisabledTool())

    result = registry.execute_tool(
        tool_name="assistant.test_disabled",
        input_data={"text": "hello"},
        context=_tool_context("assistant.chat.access"),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.disabled"


def test_write_tool_is_rejected_even_if_registered() -> None:
    registry = AssistantToolRegistry(audit_repository=_AuditRepository())
    registry.register(_WriteBlockedTool())

    result = registry.execute_tool(
        tool_name="assistant.test_write_blocked",
        input_data={"text": "hello"},
        context=_tool_context("assistant.chat.access"),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.write_blocked"


def test_invalid_input_is_rejected() -> None:
    registry = AssistantToolRegistry(audit_repository=_AuditRepository())
    registry.register(_EchoReadTool())

    result = registry.execute_tool(
        tool_name="assistant.test_echo_read",
        input_data={"text": ""},
        context=_tool_context("assistant.chat.access"),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.input_invalid"


def test_sql_like_input_is_rejected() -> None:
    registry = AssistantToolRegistry(audit_repository=_AuditRepository())
    registry.register(_EchoReadTool())

    result = registry.execute_tool(
        tool_name="assistant.test_echo_read",
        input_data={"sql": "select * from iam.user_account"},
        context=_tool_context("assistant.chat.access"),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.input_invalid"


def test_redaction_masks_sensitive_fields_recursively() -> None:
    payload = {
        "token": "sk-secret12345",
        "nested": [
            {"password_hash": "hash"},
            {"refresh_token": "eyJabc.def.ghi"},
        ],
    }

    redacted = redact_tool_payload(payload)

    assert redacted["token"] == "[REDACTED]"
    assert redacted["nested"][0]["password_hash"] == "[REDACTED]"
    assert redacted["nested"][1]["refresh_token"] == "[REDACTED]"


def test_tool_call_audit_row_is_created_for_allowed_execution() -> None:
    audit = _AuditRepository()
    registry = AssistantToolRegistry(audit_repository=audit)
    registry.register(_EchoReadTool())

    registry.execute_tool(
        tool_name="assistant.test_echo_read",
        input_data={"text": "hello"},
        context=_tool_context("assistant.chat.access"),
    )

    record = audit.records[0]
    assert record.tool_name == "assistant.test_echo_read"
    assert record.permission_decision == "allowed"
    assert record.output_json_summary["token"] == "[REDACTED]"


def test_unexpected_tool_exception_is_converted_to_safe_failure() -> None:
    audit = _AuditRepository()
    registry = AssistantToolRegistry(audit_repository=audit)
    registry.register(_BrokenTool())

    result = registry.execute_tool(
        tool_name="assistant.test_broken",
        input_data={"text": "hello"},
        context=_tool_context("assistant.chat.access"),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.execution_failed"
    assert result.error_message == "Tool execution failed safely."
    assert "traceback" not in (result.error_message or "").lower()
    assert audit.records[0].permission_decision == "failed"


def test_tool_list_for_model_contains_only_available_allowed_tools() -> None:
    registry = AssistantToolRegistry(audit_repository=_AuditRepository())
    registry.register(_EchoReadTool())
    registry.register(_DisabledTool())
    registry.register(_WriteBlockedTool())

    tools = registry.list_available_tools(context=_tool_context("assistant.chat.access"))

    assert [tool["function"]["name"] for tool in tools] == ["assistant.test_echo_read"]


def test_tool_execution_uses_backend_auth_context_not_model_supplied_ids() -> None:
    registry = AssistantToolRegistry(audit_repository=_AuditRepository())
    registry.register(_ContextTool())

    result = registry.execute_tool(
        tool_name="assistant.test_context_read",
        input_data={"tenant_id": "tenant-from-model", "user_id": "user-from-model"},
        context=_tool_context("assistant.chat.access"),
    )

    assert result.ok is True
    assert result.data == {"tenant_id": "tenant-1", "user_id": "user-1"}
