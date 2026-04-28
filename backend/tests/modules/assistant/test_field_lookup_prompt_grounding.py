from __future__ import annotations

from dataclasses import dataclass, field

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
                "answer": "Klassifizierung ist ein mandantenspezifisches Lookup-Feld.",
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
                "source_basis": [],
            },
            raw_text="Klassifizierung ist ein mandantenspezifisches Lookup-Feld.",
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
        )


def test_field_lookup_prompt_grounding_contains_field_and_lookup_definitions() -> None:
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
            message="was bedeutet Klassifizierung",
            route_context={"page_id": "C-01", "route_name": "SicherPlanCustomers", "path": "/admin/customers"},
        ),
        _context("assistant.chat.access", "assistant.knowledge.read", "customers.customer.read"),
    )

    assert response.out_of_scope is False
    request = provider.requests[-1]
    assert "field-label, lookup, status" in request.system_instructions
    assert request.grounding_context is not None
    assert request.grounding_context["retrieval_plan"]["intent_category"] == "lookup_meaning_question"
    lookup_sources = [item for item in request.grounding_context["sources"] if item["source_type"] == "lookup_dictionary"]
    assert lookup_sources
    assert any(item["source_name"] == "customer.classification_lookup_id" for item in lookup_sources)
    assert any(
        isinstance(item.get("facts"), dict)
        and item["facts"].get("value_source_kind") == "tenant_lookup"
        for item in lookup_sources
    )
