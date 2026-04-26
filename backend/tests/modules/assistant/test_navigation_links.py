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
class _AssistantRepository:
    audits: list[object] = field(default_factory=list)
    page_routes: list[AssistantPageRouteCatalog] = field(default_factory=list)

    def create_conversation(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def get_conversation_for_user(self, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def list_messages_for_conversation(self, conversation_id: str): raise AssertionError("unused")
    def update_conversation_route_context(self, conversation, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704
    def create_messages(self, conversation, messages): raise AssertionError("unused")  # noqa: ANN001,ANN201
    def update_message_payload(self, message, **kwargs): raise AssertionError("unused")  # noqa: ANN003,E704

    def create_tool_call_audit(self, *, record) -> object:  # noqa: ANN001, ANN201
        self.audits.append(record)
        return record

    def list_active_page_routes(self) -> list[AssistantPageRouteCatalog]:
        return [row for row in self.page_routes if row.active]

    def get_page_route_by_page_id(self, *, page_id: str) -> AssistantPageRouteCatalog | None:
        for row in self.page_routes:
            if row.page_id == page_id:
                return row
        return None


def _repository() -> _AssistantRepository:
    repository = _AssistantRepository()
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


def _service(repository: _AssistantRepository) -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(enabled=True, provider_mode="mock"),
        repository=repository,
        provider=MockAssistantProvider(),
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
        ),
    )


def _context(
    *,
    role_keys: tuple[str, ...],
    permission_keys: tuple[str, ...],
    tenant_id: str = "tenant-1",
) -> RequestAuthorizationContext:
    role_key = role_keys[0]
    scope_type = "tenant"
    if role_key == "customer_user":
        scope_type = "customer"
    elif role_key == "subcontractor_user":
        scope_type = "subcontractor"
    return RequestAuthorizationContext(
        session_id="assistant-session-1",
        user_id="assistant-user-1",
        tenant_id=tenant_id,
        role_keys=frozenset(role_keys),
        permission_keys=frozenset(permission_keys),
        scopes=(AuthenticatedRoleScope(role_key=role_key, scope_type=scope_type),),
        request_id="assistant-req-1",
    )


def test_dispatcher_can_search_accessible_planning_pages() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="assistant.search_accessible_pages",
        input_data={"module_key": "planning", "limit": 10},
        actor=_context(
            role_keys=("dispatcher",),
            permission_keys=("assistant.chat.access", "planning.ops.read", "planning.order.read", "planning.record.read", "planning.shift.read", "planning.staffing.read"),
        ),
    )

    assert result.ok is True
    page_ids = {row["page_id"] for row in result.data["pages"]}
    assert {"P-01", "P-02", "P-03", "P-04", "P-05"}.issubset(page_ids)


def test_employee_self_service_user_does_not_receive_internal_admin_links() -> None:
    repository = _repository()
    service = _service(repository)

    search_result = service.execute_registered_tool(
        tool_name="assistant.search_accessible_pages",
        input_data={"query": "planning"},
        actor=_context(role_keys=("employee_user",), permission_keys=("assistant.chat.access", "portal.employee.access")),
    )
    link_result = service.execute_registered_tool(
        tool_name="navigation.build_allowed_link",
        input_data={"page_id": "P-04"},
        actor=_context(role_keys=("employee_user",), permission_keys=("assistant.chat.access", "portal.employee.access")),
    )

    assert search_result.ok is True
    assert search_result.data["pages"] == []
    assert link_result.ok is True
    assert link_result.data["allowed"] is False
    assert link_result.data["link"] is None


def test_customer_portal_user_receives_only_customer_portal_links() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="assistant.search_accessible_pages",
        input_data={"query": "portal"},
        actor=_context(role_keys=("customer_user",), permission_keys=("assistant.chat.access", "portal.customer.access")),
    )

    assert result.ok is True
    assert [row["page_id"] for row in result.data["pages"]] == ["CP-01"]


def test_subcontractor_portal_user_receives_only_subcontractor_portal_links() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="assistant.search_accessible_pages",
        input_data={"query": "portal"},
        actor=_context(
            role_keys=("subcontractor_user",),
            permission_keys=("assistant.chat.access", "portal.subcontractor.access"),
        ),
    )

    assert result.ok is True
    assert [row["page_id"] for row in result.data["pages"]] == ["SP-01"]


def test_unauthorized_page_link_request_returns_missing_permissions() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="navigation.build_allowed_link",
        input_data={"page_id": "P-04", "reason": "Inspect staffing coverage"},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access",)),
    )

    assert result.ok is True
    assert result.data["allowed"] is False
    assert result.data["link"] is None
    assert result.data["missing_permissions"] == [
        {
            "permission": "planning.staffing.read",
            "reason": "Current user cannot access this workspace under the backend permission policy.",
        }
    ]


def test_unknown_page_id_is_rejected_safely() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="navigation.build_allowed_link",
        input_data={"page_id": "UNKNOWN-1"},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access",)),
    )

    assert result.ok is True
    assert result.data == {"allowed": False, "link": None, "missing_permissions": []}


def test_link_builder_whitelists_entity_query_parameters_and_ignores_tenant_injection() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="navigation.build_allowed_link",
        input_data={
            "page_id": "P-04",
            "entity_context": {
                "date": "2026-05-01",
                "assignment_id": "asg-1",
                "tenant_id": "forged-tenant",
                "unexpected": "ignore-me",
            },
            "reason": "Assignment validation",
        },
        actor=_context(
            role_keys=("dispatcher",),
            permission_keys=("assistant.chat.access", "planning.staffing.read"),
        ),
    )

    assert result.ok is True
    assert result.data["allowed"] is True
    assert result.data["link"]["route_name"] == "SicherPlanPlanningStaffing"
    assert result.data["link"]["path"] == "/admin/planning-staffing?assignment_id=asg-1&date=2026-05-01"
    assert "tenant_id" not in result.data["link"]["path"]


def test_navigation_tool_calls_are_audited_without_openai() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="navigation.build_allowed_link",
        input_data={"page_id": "CP-01"},
        actor=_context(role_keys=("customer_user",), permission_keys=("assistant.chat.access", "portal.customer.access")),
    )

    assert result.ok is True
    assert repository.audits
    assert repository.audits[0].tool_name == "navigation.build_allowed_link"
