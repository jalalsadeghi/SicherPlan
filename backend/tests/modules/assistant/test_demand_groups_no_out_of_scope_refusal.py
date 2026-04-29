from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from tests.modules.assistant.test_how_to_employee_create_exact_ui import _context, _repository


@dataclass
class _LanguageCapturingProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        answer = "Demand Groups sind Bedarfsgruppen in Staffing Coverage."
        return AssistantProviderResult(
            final_response={
                "answer": answer,
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
                "source_basis": [],
            },
            raw_text=answer,
            provider_name="fake-openai",
            provider_mode="openai",
            model_name="gpt-test",
        )


def test_demand_groups_question_does_not_return_out_of_scope_refusal() -> None:
    repository = _repository()
    provider = _LanguageCapturingProvider()
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
    assert response.response_language == "de"
    assert "P-04" not in response.answer
