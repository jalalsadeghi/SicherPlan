from __future__ import annotations

from app.modules.assistant.tools import build_default_tool_registry
from app.modules.assistant.tools.base import AssistantToolExecutionContext
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


def _context() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"assistant.chat.access"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )


def test_platform_term_tool_returns_demand_groups_definition() -> None:
    registry = build_default_tool_registry()

    result = registry.execute_tool(
        tool_name="assistant.search_platform_terms",
        input_data={"query": "was bedeutet Demand groups", "page_id": "P-04", "language_code": "de"},
        context=AssistantToolExecutionContext(
            auth_context=_context(),
            tenant_id="tenant-1",
            user_id="assistant-user-1",
            role_keys=frozenset({"tenant_admin"}),
            permission_keys=frozenset({"assistant.chat.access"}),
            scope_kind="tenant",
        ),
    )

    assert result.ok is True
    assert result.data["matches"][0]["term_key"] == "planning.staffing.demand_groups"
    assert result.data["matches"][0]["source_basis"]


def test_platform_term_tool_returns_ai_74_english_term_set() -> None:
    registry = build_default_tool_registry()
    context = AssistantToolExecutionContext(
        auth_context=_context(),
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"assistant.chat.access"}),
        scope_kind="tenant",
    )
    expected = {
        "what are Staffing actions": "planning.staffing.staffing_actions",
        "what are Release gates": "planning.staffing.release_gates",
        "what is Override evidence": "planning.staffing.override_evidence",
        "what are Partner releases": "planning.staffing.partner_releases",
        "what are Dispatch messages": "planning.staffing.dispatch_messages",
        "what does minimum staffing mean": "planning.staffing.minimum_staffing",
        "what are mandatory proofs": "planning.staffing.mandatory_proofs",
    }
    for query, term_key in expected.items():
        result = registry.execute_tool(
            tool_name="assistant.search_platform_terms",
            input_data={"query": query, "page_id": "P-04", "language_code": "en"},
            context=context,
        )
        assert result.ok is True, query
        assert result.data["matches"][0]["term_key"] == term_key, query
