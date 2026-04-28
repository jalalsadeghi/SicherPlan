from __future__ import annotations

from app.modules.assistant.field_dictionary import search_field_dictionary
from app.modules.assistant.tools.field_dictionary_tools import SearchFieldDictionaryTool
from app.modules.assistant.tools.base import AssistantToolExecutionContext
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


def _tool_context() -> AssistantToolExecutionContext:
    auth_context = RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"assistant.chat.access"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )
    return AssistantToolExecutionContext(
        auth_context=auth_context,
        tenant_id=auth_context.tenant_id,
        user_id=auth_context.user_id,
        role_keys=auth_context.role_keys,
        permission_keys=auth_context.permission_keys,
        scope_kind="tenant",
    )


def test_rechtlicher_name_maps_to_customer_legal_name() -> None:
    matches = search_field_dictionary(
        query="Rechtlicher Name",
        language_code="de",
        page_id="C-01",
        route_name="SicherPlanCustomers",
        limit=5,
    )

    assert matches
    assert matches[0].field_key == "customer.legal_name"
    assert matches[0].page_id == "C-01"
    assert matches[0].module_key == "customers"


def test_legal_name_maps_to_same_customer_field() -> None:
    matches = search_field_dictionary(
        query="Legal name",
        language_code="en",
        page_id="C-01",
        route_name="SicherPlanCustomers",
        limit=5,
    )

    assert matches
    assert matches[0].field_key == "customer.legal_name"


def test_search_field_dictionary_tool_returns_source_basis() -> None:
    tool = SearchFieldDictionaryTool()
    result = tool.execute(
        input_data=tool.definition.input_schema(query="Rechtlicher Name", language_code="de", page_id="C-01"),
        context=_tool_context(),
    )

    assert result.ok is True
    assert result.data["matches"][0]["field_key"] == "customer.legal_name"
    assert any(item["source_type"] == "frontend_locale" for item in result.data["matches"][0]["source_basis"])
