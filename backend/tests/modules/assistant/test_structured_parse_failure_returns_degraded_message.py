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
class _InvalidStructuredProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest) -> AssistantProviderResult:
        self.requests.append(request)
        return AssistantProviderResult(
            final_response={
                "answer": "Bitte prüfen Sie Mitarbeiterprofil, aktive Zuweisung und Freigabe.",
            },
            raw_text='{"answer":"Bitte prüfen Sie Mitarbeiterprofil, aktive Zuweisung und Freigabe."',
            requested_tool_calls=[],
            response_id="resp-parse-1",
            output_items=[],
            usage=None,
            provider_name="openai",
            provider_mode="openai",
            model_name="gpt-4o",
            latency_ms=0,
            finish_reason="stop",
        )


def test_initial_structured_parse_failure_with_grounding_returns_degraded_message() -> None:
    repository = _DiagnosticRepository()
    provider = _InvalidStructuredProvider()
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
            message="Ich habe Markus einer Schicht zugewiesen, aber sie ist in der mobilen App nicht sichtbar. Woran liegt das?"
        ),
        _context(role_keys=("dispatcher",), permission_keys=_full_internal_permissions()),
    )

    assert len(provider.requests) == 2
    assert response.provider_degraded is True
    assert response.out_of_scope is False
    assert response.answer.startswith("Die Anfrage konnte nicht vollständig mit dem KI-Modell abgeschlossen werden.")
    assert "Bitte prüfen Sie Mitarbeiterprofil" in response.answer
    assert any(item.finding == "provider_degraded" for item in response.diagnosis)
    assert response.source_basis
