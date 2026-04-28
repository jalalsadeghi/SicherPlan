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
        if domain != "customer_ranking":
            return []
        return [
            _LookupRow(id="rank-1", code="a", label="A", description="Top-Ranking"),
            _LookupRow(id="rank-2", code="b", label="B", description="Mittleres Ranking"),
        ]


def _context(*permissions: str) -> AssistantToolExecutionContext:
    auth = RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="assistant-req-1",
    )
    return AssistantToolExecutionContext(
        auth_context=auth,
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        role_keys=auth.role_keys,
        permission_keys=auth.permission_keys,
        scope_kind="tenant",
    )


def test_dynamic_lookup_values_are_not_returned_without_customer_read_permission() -> None:
    registry = build_default_tool_registry(customer_repository=_CustomerLookupRepository())

    result = registry.execute_tool(
        tool_name="assistant.explain_lookup_or_option",
        input_data={"query": "what is Ranking", "page_id": "C-01", "language_code": "en"},
        context=_context("assistant.chat.access"),
    )

    assert result.ok is True
    assert result.data["matches"][0]["lookup_key"] == "customer.ranking_lookup_id"
    assert result.data["matches"][0]["value_resolution"] == "permission_limited"
    assert result.data["matches"][0]["values"] == []
    assert result.data["missing_permissions"] == [
        {
            "permission": "customers.customer.read",
            "reason": "The current user is not allowed to read the tenant-specific lookup catalog for this field.",
        }
    ]
