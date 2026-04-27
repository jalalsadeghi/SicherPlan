from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import (
    AssistantProviderInvalidRequestError,
    AssistantProviderRequest,
    AssistantProviderResult,
)
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import AssistantToolRegistry
from tests.modules.assistant.test_operational_diagnostic_tool_loop import (
    _ShiftVisibilityDiagnosticTool,
    _context,
)
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


@dataclass
class _InvalidContinuationProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        if len(self.requests) == 1:
            return AssistantProviderResult(
                final_response={},
                raw_text=None,
                response_id="resp-diag-1",
                output_items=[
                    {
                        "type": "function_call",
                        "id": "fc-diag-1",
                        "call_id": "call-diag-1",
                        "name": "assistant_diagnose_employee_shift_visibility",
                        "arguments": '{"employee_name":"Markus"}',
                    }
                ],
                requested_tool_calls=[
                    {
                        "id": "fc-diag-1",
                        "name": "assistant_diagnose_employee_shift_visibility",
                        "provider_tool_name": "assistant_diagnose_employee_shift_visibility",
                        "arguments": '{"employee_name":"Markus"}',
                        "call_id": "call-diag-1",
                        "response_item": {
                            "type": "function_call",
                            "id": "fc-diag-1",
                            "call_id": "call-diag-1",
                            "name": "assistant_diagnose_employee_shift_visibility",
                            "arguments": '{"employee_name":"Markus"}',
                        },
                    }
                ],
                provider_name="openai",
                provider_mode="openai",
                model_name="gpt-4o",
            )
        raise AssistantProviderInvalidRequestError("No tool call found for function call output with call_id call-diag-1.")


def test_invalid_continuation_after_tool_facts_returns_degraded_answer() -> None:
    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    provider = _InvalidContinuationProvider()
    registry = AssistantToolRegistry()
    registry.register(_ShiftVisibilityDiagnosticTool())
    service = AssistantService(
        runtime_config=AssistantRuntimeConfig(
            enabled=True,
            provider_mode="openai",
            env="development",
            openai_configured=True,
            mock_provider_allowed=False,
            response_model="gpt-4o",
            store_responses=False,
            max_tool_calls=8,
        ),
        repository=repository,
        provider=provider,
        tool_registry=registry,
    )

    response = service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="Ich habe einem Mitarbeiter eine Arbeitsschicht zugewiesen, diese wird jedoch in der mobilen App nicht angezeigt. Woran könnte das liegen?"
        ),
        _context(),
    )

    assert response.provider_degraded is True
    assert response.answer.startswith("Die Anfrage konnte nicht vollständig mit dem KI-Modell abgeschlossen werden.")
    assert response.source_basis
    assert any(item.finding == "provider_degraded" and item.severity == "warning" for item in response.diagnosis)
    assert response.next_steps
    assert len(provider.requests) == 2
