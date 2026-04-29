from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _context, _repository


@dataclass
class _CapturingProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": "Demand Groups sind Staffing-Slots in Staffing Coverage.",
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
                "source_basis": [],
            },
            raw_text="Demand Groups sind Staffing-Slots in Staffing Coverage.",
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
        )


def test_platform_term_prompt_grounding_contains_term_definition_related_fields_and_link() -> None:
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
        ),
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="was bedeutet Demand groups",
            route_context={"page_id": "P-04", "route_name": "SicherPlanPlanningStaffing", "path": "/admin/planning-staffing"},
        ),
        _context("assistant.chat.access", "assistant.knowledge.read", "planning.staffing.read"),
    )

    assert response.out_of_scope is False
    request = provider.requests[-1]
    assert request.grounding_context is not None
    assert request.grounding_context["response_language"] == "de"
    assert request.grounding_context["retrieval_plan"]["intent_category"] == "platform_term_meaning_question"

    sources = request.grounding_context["sources"]
    term_sources = [item for item in sources if item["source_type"] == "platform_term_dictionary"]
    assert term_sources
    assert any(item["source_name"] == "planning.staffing.demand_groups" for item in term_sources)
    assert any(item["source_type"] == "field_dictionary" for item in sources)
    assert any(item["source_type"] == "workflow" for item in sources)
    assert any(
        item["source_type"] == "allowed_navigation_link"
        and item.get("page_id") == "P-04"
        and item.get("title") == "Staffing Coverage"
        for item in sources
    )
