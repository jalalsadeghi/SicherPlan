from __future__ import annotations

from uuid import UUID

from fastapi import status

from app.modules.assistant.router import add_assistant_message, router
from app.modules.assistant.schemas import AssistantMessageCreate
from app.modules.assistant.service import AssistantRuntimeConfig, AssistantService
from app.modules.assistant.tools import AssistantToolRegistry
from tests.modules.assistant.test_operational_diagnostic_tool_loop import (
    _OperationalDiagnosticProvider,
    _ShiftVisibilityDiagnosticTool,
    _context,
)
from tests.modules.assistant.test_out_of_scope import InMemoryAssistantRepository


def test_exact_german_shift_visibility_question_keeps_messages_route_at_201_and_avoids_502() -> None:
    messages_route = next(
        route
        for route in router.routes
        if getattr(route, "path", "") == "/api/assistant/conversations/{conversation_id}/messages"
    )
    assert messages_route.status_code == status.HTTP_201_CREATED

    repository = InMemoryAssistantRepository()
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )
    provider = _OperationalDiagnosticProvider()
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

    payload = add_assistant_message(
        UUID(conversation.id),
        AssistantMessageCreate(
            message="Ich habe einem Mitarbeiter eine Arbeitsschicht zugewiesen, diese wird jedoch in der mobilen App nicht angezeigt. Woran könnte das liegen?"
        ),
        _context(),
        service,
    )

    assert payload.response_language == "de"
    assert payload.answer.startswith("Ich habe die Freigabe geprüft.")
    assert payload.out_of_scope is False
