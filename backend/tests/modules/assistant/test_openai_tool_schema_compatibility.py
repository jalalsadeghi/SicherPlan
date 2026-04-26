from __future__ import annotations

from app.modules.assistant.openai_client import OpenAIResponsesProvider
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.assistant.tools.base import AssistantToolExecutionContext
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


def test_available_tool_schemas_normalize_for_responses_api() -> None:
    registry = build_default_tool_registry(
        page_catalog_repository=object(),
        page_help_repository=object(),
        employee_repository=object(),
        planning_repository=object(),
    )
    required_permissions = {"assistant.chat.access"}
    for tool in registry._tools.values():  # noqa: SLF001
        required_permissions.update(tool.definition.required_permissions)
    auth_context = RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(required_permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )
    tools = registry.list_available_tools(
        context=AssistantToolExecutionContext(
            auth_context=auth_context,
            tenant_id="tenant-1",
            user_id="assistant-user-1",
            role_keys=auth_context.role_keys,
            permission_keys=auth_context.permission_keys,
            scope_kind="tenant",
        )
    )
    normalized = OpenAIResponsesProvider._normalize_tools_for_responses_api(tools)  # noqa: SLF001

    assert normalized
    assert len(normalized) == len(tools)
    for item in normalized:
        assert item["type"] == "function"
        assert isinstance(item.get("name"), str) and item["name"]
        assert "function" not in item
        assert isinstance(item.get("parameters"), dict)
        assert item["parameters"].get("type") == "object"

