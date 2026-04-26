from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.modules.assistant.models import AssistantPageRouteCatalog
from app.modules.assistant.page_catalog_seed import ASSISTANT_PAGE_ROUTE_SEEDS
from app.modules.assistant.provider import MockAssistantProvider
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


@dataclass
class _AuditRepository:
    records: list[object] = field(default_factory=list)
    page_routes: list[AssistantPageRouteCatalog] = field(default_factory=list)

    def create_tool_call_audit(self, *, record) -> object:  # noqa: ANN001, ANN201
        self.records.append(record)
        return record

    def list_active_page_routes(self) -> list[AssistantPageRouteCatalog]:
        return [row for row in self.page_routes if row.active]

    def get_page_route_by_page_id(self, *, page_id: str) -> AssistantPageRouteCatalog | None:
        for row in self.page_routes:
            if row.page_id == page_id:
                return row
        return None


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


def _service(audit: _AuditRepository) -> AssistantService:
    class _NoopRepository:
        def create_conversation(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
        def get_conversation_for_user(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
        def list_messages_for_conversation(self, conversation_id: str): raise AssertionError("unused")
        def update_conversation_route_context(self, conversation, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
        def create_messages(self, conversation, messages): raise AssertionError("unused")  # noqa: ANN001,ANN201
        def update_message_payload(self, message, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704

    return AssistantService(
        runtime_config=AssistantRuntimeConfig(enabled=True, provider_mode="mock"),
        repository=_NoopRepository(),
        provider=MockAssistantProvider(),
        tool_registry=build_default_tool_registry(audit_repository=audit, page_catalog_repository=audit),
    )


def _audit_repository() -> _AuditRepository:
    repository = _AuditRepository()
    repository.page_routes = [
        AssistantPageRouteCatalog(
            id=str(uuid4()),
            page_id=seed.page_id,
            label=seed.label,
            route_name=seed.route_name,
            path_template=seed.path_template,
            module_key=seed.module_key,
            api_families=list(seed.api_families) or None,
            required_permissions=list(seed.required_permissions) or None,
            allowed_role_keys=list(seed.allowed_role_keys) or None,
            scope_kind=seed.scope_kind,
            supports_entity_deep_link=seed.supports_entity_deep_link,
            entity_param_map=seed.entity_param_map,
            active=seed.active,
        )
        for seed in ASSISTANT_PAGE_ROUTE_SEEDS
    ]
    return repository


def test_page_context_is_marked_non_authoritative() -> None:
    audit = _audit_repository()
    result = _service(audit).execute_registered_tool(
        tool_name="assistant.get_current_page_context",
        input_data={"path": "/planning/staffing", "page_id": "P-04", "route_name": "SicherPlanPlanningStaffing"},
        actor=_context("assistant.chat.access"),
    )

    assert result.ok is True
    assert result.data["is_authoritative"] is False
    assert result.data["is_known_page"] is True
    assert "hint only" in result.data["notes"][0]
    assert audit.records[0].tool_name == "assistant.get_current_page_context"


def test_sensitive_query_parameters_are_redacted_from_page_context() -> None:
    result = _service(_audit_repository()).execute_registered_tool(
        tool_name="assistant.get_current_page_context",
        input_data={
            "path": "/planning/staffing",
            "query": {
                "token": "abc",
                "auth": "bearer",
                "employee_id": "emp-1",
                "tab": "coverage",
            },
        },
        actor=_context("assistant.chat.access"),
    )

    assert result.ok is True
    assert result.data["safe_query"] == {"employee_id": "emp-1", "tab": "coverage"}


def test_long_and_suspicious_route_payloads_are_bounded_safely() -> None:
    long_path = "/" + ("planning/" * 120)
    result = _service(_audit_repository()).execute_registered_tool(
        tool_name="assistant.get_current_page_context",
        input_data={
            "path": long_path,
            "query": {"items": list(range(20)), "jwt": "hidden"},
            "ui_locale": "de-DE",
            "timezone": "Europe/Berlin",
        },
        actor=_context("assistant.chat.access"),
    )

    assert result.ok is True
    assert len(result.data["path"]) <= 500
    assert "jwt" not in result.data["safe_query"]
    assert len(result.data["safe_query"]["items"]) <= 10


def test_accessible_page_search_returns_only_allowed_pages() -> None:
    service = _service(_audit_repository())
    without_permission = service.execute_registered_tool(
        tool_name="assistant.search_accessible_pages",
        input_data={"query": "staffing"},
        actor=_context("assistant.chat.access"),
    )
    with_permission = service.execute_registered_tool(
        tool_name="assistant.search_accessible_pages",
        input_data={"query": "staffing"},
        actor=_context("assistant.chat.access", "planning.staffing.read"),
    )

    assert without_permission.ok is True
    assert without_permission.data["pages"] == []
    assert with_permission.ok is True
    assert with_permission.data["pages"][0]["page_id"] == "P-04"


def test_accessible_page_search_can_return_conservative_empty_results() -> None:
    result = _service(_audit_repository()).execute_registered_tool(
        tool_name="assistant.search_accessible_pages",
        input_data={"query": "nonexistent", "limit": 5},
        actor=_context("assistant.chat.access"),
    )

    assert result.ok is True
    assert result.data == {"pages": [], "truncated": False}
