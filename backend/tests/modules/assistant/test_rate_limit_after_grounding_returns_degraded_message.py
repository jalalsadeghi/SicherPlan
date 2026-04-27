from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.assistant.provider import AssistantProviderRateLimitError, AssistantProviderRequest
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import build_default_tool_registry
from tests.modules.assistant.test_shift_visibility_diagnostic import (
    _DiagnosticRepository,
    _context,
    _full_internal_permissions,
)


@dataclass
class _RateLimitedProvider:
    requests: list[AssistantProviderRequest] = field(default_factory=list)

    def generate(self, request: AssistantProviderRequest):  # noqa: ANN201
        self.requests.append(request)
        raise AssistantProviderRateLimitError("Rate limit reached.", retry_after_seconds=0.0)


def test_rate_limit_after_grounding_returns_stored_degraded_message() -> None:
    repository = _DiagnosticRepository()
    provider = _RateLimitedProvider()
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

    stored_messages = repository.list_messages_for_conversation(conversation.id)
    assistant_messages = [item for item in stored_messages if item.role == "assistant"]

    assert response.provider_degraded is True
    assert response.links
    assert assistant_messages
    assert assistant_messages[-1].structured_payload["provider_degraded"] is True
