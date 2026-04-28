from __future__ import annotations

from dataclasses import dataclass

from app.modules.assistant.tools import build_default_tool_registry
from app.modules.assistant.tools.base import AssistantToolExecutionContext
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


@dataclass
class _LookupRow:
    id: str
    code: str
    label: str
    description: str | None = None


class _CustomerLookupRepository:
    def list_lookup_values(self, tenant_id: str | None, domain: str):  # noqa: ANN001
        assert tenant_id == "tenant-1"
        if domain != "customer_category":
            return []
        return [
            _LookupRow(
                id="lookup-1",
                code="vip",
                label="VIP",
                description="Priorisierte Kundenklassifizierung fuer besonders wichtige Auftraggeber.",
            ),
            _LookupRow(
                id="lookup-2",
                code="standard",
                label="Standard",
                description="Normale Kundenklassifizierung ohne Sonderbehandlung.",
            ),
        ]


def _context(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )


def test_lookup_explanation_tool_resolves_dynamic_customer_catalog_values() -> None:
    registry = build_default_tool_registry(customer_repository=_CustomerLookupRepository())
    tool_context = AssistantToolExecutionContext(
        auth_context=_context("assistant.chat.access", "customers.customer.read"),
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"assistant.chat.access", "customers.customer.read"}),
        scope_kind="tenant",
    )

    result = registry.execute_tool(
        tool_name="assistant.explain_lookup_or_option",
        input_data={"query": "was bedeutet Klassifizierung", "page_id": "C-01", "language_code": "de"},
        context=tool_context,
    )

    assert tool_context.tenant_id == "tenant-1"
    assert result.ok is True
    assert result.data["missing_permissions"] == []
    assert result.data["matches"][0]["lookup_key"] == "customer.classification_lookup_id"
    assert result.data["matches"][0]["value_resolution"] == "dynamic"
    assert [row["value"] for row in result.data["matches"][0]["values"]] == ["vip", "standard"]


def test_lookup_explanation_tool_matches_static_option_value_meaning() -> None:
    registry = build_default_tool_registry()

    result = registry.execute_tool(
        tool_name="assistant.explain_lookup_or_option",
        input_data={"query": "what does workforce scope mixed mean", "page_id": "P-03", "language_code": "en"},
        context=AssistantToolExecutionContext(
            auth_context=_context("assistant.chat.access"),
            tenant_id="tenant-1",
            user_id="assistant-user-1",
            role_keys=frozenset({"tenant_admin"}),
            permission_keys=frozenset({"assistant.chat.access"}),
            scope_kind="tenant",
        ),
    )

    assert result.ok is True
    assert result.data["matches"][0]["lookup_key"] == "planning.workforce_scope_code"
    assert result.data["matches"][0]["matched_values"][0]["value"] == "mixed"
