from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel

from app.modules.assistant.tools import (
    AssistantToolClassification,
    AssistantToolDefinition,
    AssistantToolExecutionContext,
    AssistantToolRegistry,
    AssistantToolResult,
    AssistantToolScopeBehavior,
)
from app.modules.assistant.tools.base import AssistantTool
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


class PermissionInput(BaseModel):
    employee_id: str


class PermissionOutput(BaseModel):
    employee_id: str
    visible: bool


class _PermissionTool(AssistantTool):
    definition = AssistantToolDefinition(
        name="assistant.test_permission_required",
        description="Permission-gated diagnostic tool",
        input_schema=PermissionInput,
        output_schema=PermissionOutput,
        required_permissions=["assistant.diagnostics.read"],
        scope_behavior=AssistantToolScopeBehavior.TENANT,
        classification=AssistantToolClassification.READ_ONLY,
    )

    def execute(self, *, input_data: BaseModel, context: AssistantToolExecutionContext) -> AssistantToolResult:
        del context
        payload = PermissionOutput(employee_id=input_data.employee_id, visible=True).model_dump(mode="json")
        return AssistantToolResult(ok=True, tool_name=self.definition.name, data=payload)


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


def test_missing_permission_is_rejected() -> None:
    audit = _AuditRepository()
    registry = AssistantToolRegistry(audit_repository=audit)
    registry.register(_PermissionTool())

    result = registry.execute_tool(
        tool_name="assistant.test_permission_required",
        input_data={"employee_id": "emp-1"},
        context=_tool_context("assistant.chat.access"),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.permission_denied"
    assert result.missing_permissions == [
        {
            "permission": "assistant.diagnostics.read",
            "reason": "The current user does not have the required permission for this assistant tool.",
        }
    ]
    assert audit.records[0].permission_decision == "denied"


def test_tool_call_audit_row_is_created_for_denied_execution() -> None:
    audit = _AuditRepository()
    registry = AssistantToolRegistry(audit_repository=audit)
    registry.register(_PermissionTool())

    registry.execute_tool(
        tool_name="assistant.test_permission_required",
        input_data={"employee_id": "emp-1"},
        context=_tool_context("assistant.chat.access"),
    )

    record = audit.records[0]
    assert record.tool_name == "assistant.test_permission_required"
    assert record.permission_decision == "denied"
    assert record.error_code == "assistant.tool.permission_denied"


def test_permission_gated_tool_executes_when_required_permission_is_present() -> None:
    registry = AssistantToolRegistry(audit_repository=_AuditRepository())
    registry.register(_PermissionTool())

    result = registry.execute_tool(
        tool_name="assistant.test_permission_required",
        input_data={"employee_id": "emp-1"},
        context=_tool_context("assistant.chat.access", "assistant.diagnostics.read"),
    )

    assert result.ok is True
    assert result.data == {"employee_id": "emp-1", "visible": True}


def test_tool_list_contains_only_tools_allowed_for_current_permissions() -> None:
    registry = AssistantToolRegistry(audit_repository=_AuditRepository())
    registry.register(_PermissionTool())

    without_permission = registry.list_available_tools(context=_tool_context("assistant.chat.access"))
    with_permission = registry.list_available_tools(
        context=_tool_context("assistant.chat.access", "assistant.diagnostics.read")
    )

    assert without_permission == []
    assert [tool["function"]["name"] for tool in with_permission] == ["assistant.test_permission_required"]
