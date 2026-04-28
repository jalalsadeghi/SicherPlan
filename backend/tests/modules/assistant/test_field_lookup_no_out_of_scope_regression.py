from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.field_dictionary import search_field_dictionary
from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from tests.modules.assistant.golden_qa_support import _GoldenLookupRepository
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _context, _repository


@dataclass
class _CapturingProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": "Rechtlicher Name ist der offizielle rechtliche Name des Kunden für Verträge, Rechnungen und formale Identität.",
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
                "source_basis": [
                    {
                        "source_type": "field_dictionary",
                        "source_name": "customer.legal_name",
                        "page_id": "C-01",
                        "module_key": "customers",
                        "title": "Rechtlicher Name",
                        "evidence": "customer.legal_name",
                    }
                ],
            },
            raw_text="Rechtlicher Name ist der offizielle rechtliche Name des Kunden für Verträge, Rechnungen und formale Identität.",
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
        )


def test_rechtlicher_name_no_longer_returns_out_of_scope() -> None:
    top_match = search_field_dictionary(
        query="was bedeutet Rechtlicher Name",
        language_code="de",
        page_id="C-01",
        route_name="SicherPlanCustomers",
    )
    assert top_match
    assert top_match[0].field_key == "customer.legal_name"

    repository = _repository()
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
            customer_repository=_GoldenLookupRepository(),
        ),
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="was bedeutet Rechtlicher Name",
            route_context={"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
        ),
        _context("assistant.chat.access", "assistant.knowledge.read", "customers.customer.read"),
    )

    assert response.out_of_scope is False
    assert provider.requests
    request = provider.requests[-1]
    assert request.grounding_context is not None
    assert request.grounding_context["retrieval_plan"]["intent_category"] == "field_meaning_question"
    field_sources = [item for item in request.grounding_context["sources"] if item["source_type"] == "field_dictionary"]
    assert field_sources
    assert any(item["source_name"] == "customer.legal_name" for item in field_sources)


def test_ambiguous_status_stays_in_scope_with_route_context() -> None:
    repository = _repository()
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
            customer_repository=_GoldenLookupRepository(),
        ),
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="was bedeutet Status",
            route_context={"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
        ),
        _context("assistant.chat.access", "assistant.knowledge.read", "customers.customer.read"),
    )

    assert response.out_of_scope is False
    request = provider.requests[-1]
    assert request.grounding_context is not None
    assert request.grounding_context["retrieval_plan"]["intent_category"] == "status_meaning_question"
