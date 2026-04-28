from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _repository as page_help_repository


@dataclass
class _CapturingProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": "Rechtlicher Name ist der offizielle Name des Kunden für Verträge und Rechnungen.",
                "confidence": "high",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
            },
            raw_text="Rechtlicher Name ist der offizielle Name des Kunden für Verträge und Rechnungen.",
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
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


def test_field_question_attaches_field_dictionary_grounding_to_provider() -> None:
    repository = page_help_repository()
    provider = _CapturingProvider()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            openai_configured=True,
            response_model="gpt-5.5-mini",
        ),
        repository=repository,
        provider=provider,
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            page_help_repository=repository,
        ),
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="was bedeutet Rechtlicher Name",
            route_context={"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
        ),
        _context("assistant.chat.access", "assistant.knowledge.read"),
    )

    assert response.out_of_scope is False
    assert provider.requests
    assert provider.requests[0].grounding_context is not None
    assert provider.requests[0].grounding_context["retrieval_plan"]["intent_category"] == "field_meaning_question"
    source_types = [item["source_type"] for item in provider.requests[0].grounding_context["sources"]]
    assert "field_dictionary" in source_types
    assert "page_help_manifest" in source_types
