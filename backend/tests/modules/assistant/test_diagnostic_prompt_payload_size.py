from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import AssistantProviderRequest, AssistantProviderResult
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from tests.modules.assistant.test_shift_visibility_diagnostic import (
    _DiagnosticRepository,
    _context,
    _full_internal_permissions,
)


@dataclass
class _CapturingProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest):  # noqa: ANN201
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": "Ich habe die Freigabe geprüft.",
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [],
                "links": [],
                "missing_permissions": [],
                "next_steps": [],
                "tool_trace_id": None,
                "source_basis": [],
            },
            raw_text="Ich habe die Freigabe geprüft.",
            requested_tool_calls=[],
            response_id="resp-1",
            output_items=[],
            usage=None,
            provider_name="test",
            provider_mode="openai",
            model_name="gpt-4o",
            latency_ms=0,
            finish_reason="stop",
        )


def test_diagnostic_request_compacts_tool_results_below_budget() -> None:
    repository = _DiagnosticRepository()
    provider = _CapturingProvider()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="dispatcher-1",
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
            response_model="gpt-4o",
            max_tool_result_chars=1500,
            max_tool_result_items=5,
            max_total_tool_result_chars=3500,
            max_diagnostic_facts=12,
        ),
        repository=repository,
        provider=provider,
        tool_registry=build_default_tool_registry(
            audit_repository=repository,
            page_catalog_repository=repository,
            employee_repository=repository,
            planning_repository=repository,
        ),
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="Ich habe Markus einer Schicht zugewiesen, aber sie ist in der mobilen App nicht sichtbar. Woran liegt das?"
        ),
        _context(role_keys=("dispatcher",), permission_keys=_full_internal_permissions()),
    )

    assert response.out_of_scope is False
    assert provider.requests
    request = provider.requests[0]
    assert request.metadata["estimated_tool_result_tokens"] < 1500
    assert request.metadata["tool_result_chars"] <= 3500
    assert request.metadata["tool_result_count"] <= 5
    assert request.metadata["tool_result_trimmed"] in {True, False}
