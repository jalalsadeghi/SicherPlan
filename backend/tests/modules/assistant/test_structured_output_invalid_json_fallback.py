from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import (
    AssistantProviderRequest,
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
class _AlwaysTruncatedProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest):  # noqa: ANN201
        self.requests.append(request)
        raise AssistantProviderStructuredOutputTruncatedError(
            'Invalid JSON: EOF while parsing a string at line 1 column 201.',
            provider_error_type="StructuredOutputTruncated",
            safe_message='Invalid JSON: EOF while parsing a string at line 1 column 201.',
        )


def test_truncated_structured_output_uses_grounded_fallback_after_retry() -> None:
    repository = _DiagnosticRepository()
    provider = _AlwaysTruncatedProvider()
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

    assert len(provider.requests) == 2
    assert response.provider_degraded is True
    assert response.answer.startswith("Die Anfrage konnte nicht vollständig mit dem KI-Modell abgeschlossen werden.")
    assert response.source_basis
    assert response.links
    assert response.response_language == "de"
