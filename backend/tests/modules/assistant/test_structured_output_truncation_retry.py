from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import (
    AssistantProviderRequest,
    AssistantProviderResult,
    AssistantProviderStructuredOutputTruncatedError,
)
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from tests.modules.assistant.test_shift_visibility_diagnostic import (
    _DiagnosticRepository,
    _context,
    _full_internal_permissions,
)


@dataclass
class _TruncationThenSuccessProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        if len(self.requests) == 1:
            raise AssistantProviderStructuredOutputTruncatedError(
                'Invalid JSON: EOF while parsing a string at line 1 column 201.',
                provider_error_type="StructuredOutputTruncated",
                safe_message='Invalid JSON: EOF while parsing a string at line 1 column 201.',
            )
        return AssistantProviderResult(
            final_response={
                "answer": "Ich habe die Freigabe geprüft. Kontrollieren Sie bitte die Freigabe, die Sichtbarkeit und den Mitarbeiterzugang in den freigegebenen Bereichen.",
                "confidence": "medium",
                "out_of_scope": False,
                "diagnosis": [
                    {
                        "finding": "Die Freigabe- und Sichtbarkeitskette sollte geprüft werden.",
                        "severity": "info",
                        "evidence": "Die Retry-Antwort wurde als kompaktes gueltiges JSON erzeugt.",
                    }
                ],
                "links": [],
                "missing_permissions": [],
                "next_steps": ["Pruefen Sie die Freigabe- und Sichtbarkeitsflags."],
                "tool_trace_id": None,
                "source_basis": [],
            },
            raw_text='{"answer":"ok"}',
            provider_name="openai",
            provider_mode="openai",
            model_name="gpt-4o",
        )


def test_truncated_structured_output_retries_with_higher_output_cap_and_smaller_context() -> None:
    repository = _DiagnosticRepository()
    provider = _TruncationThenSuccessProvider()
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
            min_structured_output_tokens=800,
            max_output_tokens=1200,
            continuation_max_output_tokens=900,
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
            message="Ich habe einem Mitarbeiter eine Schicht zugewiesen, aber sie wird in der mobilen App nicht angezeigt. Woran könnte das liegen?"
        ),
        _context(role_keys=("dispatcher",), permission_keys=_full_internal_permissions()),
    )

    assert response.response_language == "de"
    assert response.out_of_scope is False
    assert response.provider_degraded is False
    assert len(provider.requests) == 2
    assert provider.requests[0].max_output_tokens >= 800
    assert provider.requests[0].max_output_tokens != 200
    assert provider.requests[1].max_output_tokens > provider.requests[0].max_output_tokens
    assert provider.requests[1].metadata["structured_output_retry_attempted"] is True
    assert provider.requests[1].metadata["structured_output_compact_mode"] is True
    assert provider.requests[1].metadata["estimated_input_tokens"] <= provider.requests[0].metadata["estimated_input_tokens"]

