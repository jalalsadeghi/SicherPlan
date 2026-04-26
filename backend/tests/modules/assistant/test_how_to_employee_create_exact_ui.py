from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.modules.assistant.models import AssistantPageHelpManifest, AssistantPageRouteCatalog
from app.modules.assistant.page_catalog_seed import ASSISTANT_PAGE_ROUTE_SEEDS
from app.modules.assistant.page_help_seed import ASSISTANT_PAGE_HELP_SEEDS
from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult, mock_provider_answer
from app.modules.assistant.schemas import AssistantClientContextInput, AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


@dataclass
class _PageHelpRepository(InMemoryAssistantRepository):
    page_help_rows: list[AssistantPageHelpManifest] = field(default_factory=list)
    page_routes: list[AssistantPageRouteCatalog] = field(default_factory=list)
    audits: list[object] = field(default_factory=list)

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

    def get_page_help_manifest(self, *, page_id: str, language_code: str | None = None) -> AssistantPageHelpManifest | None:
        candidates: list[str | None] = []
        if language_code:
            candidates.append(language_code)
        for fallback in ("en", "de", None):
            if fallback not in candidates:
                candidates.append(fallback)
        for candidate in candidates:
            for row in self.page_help_rows:
                if row.page_id == page_id and row.language_code == candidate and row.status in {"active", "unverified"}:
                    return row
        return None


class _GroundedCapturingProvider:
    def __init__(self, answer: str = "Grounded answer") -> None:
        self.answer = answer
        self.requests: list[AssistantProviderRequest] = []
        self.call_count = 0

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        self.call_count += 1
        return AssistantProviderResult(
            final_response={
                "answer": self.answer,
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text=self.answer,
        )


def _repository() -> _PageHelpRepository:
    repository = _PageHelpRepository()
    repository.page_help_rows = [
        AssistantPageHelpManifest(
            id=str(uuid4()),
            page_id=seed.page_id,
            route_name=seed.route_name,
            path_template=seed.path_template,
            module_key=seed.module_key,
            language_code=seed.language_code,
            manifest_version=seed.manifest_version,
            status=seed.status,
            manifest_json=seed.manifest_json,
            verified_from=seed.verified_from,
        )
        for seed in ASSISTANT_PAGE_HELP_SEEDS
    ]
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


def _service(repository: _PageHelpRepository, provider, *, provider_mode: str = "mock") -> AssistantService:
    return AssistantService(
        runtime_config=AssistantRuntimeConfig(enabled=True, provider_mode=provider_mode, max_input_chars=500),
        repository=repository,
        provider=provider,
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            page_help_repository=repository,
        ),
    )


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


def test_persian_employee_create_goes_to_provider_with_verified_ui_facts() -> None:
    repository = _repository()
    provider = _GroundedCapturingProvider(answer="پاسخ نهایی از مدل")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="fa",
        last_route_name=None,
        last_route_path=None,
    )

    response = _service(repository, provider).add_message(
        conversation.id,
        AssistantMessageCreate(
            message="چطور میتونم یک کارمند جدید بسازم؟",
            client_context=AssistantClientContextInput(ui_locale="fa"),
        ),
        _context("assistant.chat.access", "employees.employee.read", "employees.employee.write"),
    )

    assert response.out_of_scope is False
    assert response.answer == "پاسخ نهایی از مدل"
    assert provider.call_count == 1
    assert provider.requests[0].grounding_context is not None
    assert provider.requests[0].grounding_context["retrieval_plan"]["intent_category"] == "ui_action_question"
    assert any(item["tool_name"] == "assistant.find_ui_action" for item in provider.requests[0].tool_results)
    page_help_summary = next(item for item in provider.requests[0].tool_results if item["tool_name"] == "assistant.find_ui_action")
    assert page_help_summary["summary"]["data"]["action"]["label"] == "Create employee file"
    assert any(
        source["source_type"] == "ui_action" and source["page_id"] == "E-01"
        for source in provider.requests[0].grounding_context["sources"]
    )


def test_provider_receives_page_help_facts_not_canned_answer() -> None:
    repository = _repository()
    provider = _GroundedCapturingProvider(answer="Grounded employee guidance")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )

    response = _service(repository, provider).add_message(
        conversation.id,
        AssistantMessageCreate(message="How do I create a new Employee?"),
        _context("assistant.chat.access", "employees.employee.read", "employees.employee.write"),
    )

    assert response.answer == "Grounded employee guidance"
    assert "Create Employee or New Employee" not in response.answer
    assert response.answer != mock_provider_answer(response.response_language)
    assert provider.call_count == 1
    assert provider.requests[0].tool_results
    assert provider.requests[0].grounding_context is not None


def test_english_order_create_does_not_return_mock_when_openai_configured() -> None:
    repository = _repository()
    provider = _GroundedCapturingProvider(answer="To create a new order, start in Orders & Planning Records.")
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )

    response = _service(repository, provider, provider_mode="openai").add_message(
        conversation.id,
        AssistantMessageCreate(message="I want to create a new order. how can I do?"),
        _context("assistant.chat.access", "planning.order.read", "planning.record.read"),
    )

    assert response.out_of_scope is False
    assert response.answer.startswith("To create a new order")
    assert response.answer != mock_provider_answer(response.response_language)
    assert provider.call_count == 1
    assert any(item["tool_name"] == "assistant.search_workflow_help" for item in provider.requests[0].tool_results)
    assert provider.requests[0].grounding_context is not None
    assert provider.requests[0].grounding_context["retrieval_plan"]["workflow_intent"] == "order_create"
    assert "P-02" in provider.requests[0].grounding_context["retrieval_plan"]["likely_page_ids"]


def test_in_scope_page_without_verified_ui_action_stays_grounded_and_unverified() -> None:
    repository = _repository()
    provider = _GroundedCapturingProvider(
        answer="The documented order workflow is available, but the exact current UI button label is not verified."
    )
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="en",
        last_route_name=None,
        last_route_path=None,
    )

    response = _service(repository, provider, provider_mode="openai").add_message(
        conversation.id,
        AssistantMessageCreate(message="I want to create a new order. Tell me the exact button."),
        _context("assistant.chat.access", "planning.order.read", "planning.record.read"),
    )

    assert response.out_of_scope is False
    assert "not verified" in response.answer
    assert provider.requests[0].grounding_context is not None
    assert any(
        source["source_type"] == "page_help_manifest"
        and source["page_id"] == "P-02"
        and source["verified"] is False
        for source in provider.requests[0].grounding_context["sources"]
    )
