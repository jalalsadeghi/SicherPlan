from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import (
    AssistantProviderRateLimitError,
    AssistantProviderRequest,
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
class _AlwaysRateLimitedProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest):  # noqa: ANN201
        self.requests.append(request)
        raise AssistantProviderRateLimitError(
            "Rate limit reached.",
            retry_after_seconds=0.0,
        )


def test_rate_limit_with_grounded_visibility_facts_returns_degraded_answer() -> None:
    repository = _DiagnosticRepository()
    provider = _AlwaysRateLimitedProvider()
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
            rate_limit_max_retries=0,
            rate_limit_retry_seconds=0,
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

    assert response.provider_degraded is True
    assert response.out_of_scope is False
    assert response.answer.startswith("Die Anfrage konnte nicht vollständig mit dem KI-Modell abgeschlossen werden.")
    assert response.source_basis
    assert response.links
    assert any(item.finding.startswith("Die Antwort wurde aus bereits geprüften SicherPlan-Kontexten erstellt.") for item in response.diagnosis)
    assert provider.requests
