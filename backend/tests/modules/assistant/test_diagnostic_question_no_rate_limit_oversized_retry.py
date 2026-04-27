from __future__ import annotations

from tests.modules.assistant.test_mobile_app_visibility_single_provider_call import (
    _StubTool,
    _generic_prefetch_tools,
    _service_with_registry,
)
from tests.modules.assistant.test_operational_diagnostic_tool_loop import _context
from app.modules.assistant.schemas import AssistantMessageCreate


def test_mobile_app_visibility_question_stays_below_continuation_budget_and_avoids_second_call() -> None:
    service, repository, provider = _service_with_registry(
        *_generic_prefetch_tools(),
        _StubTool(
            "employees.search_employee_by_name",
            {"matches": [{"employee_ref": "emp-1", "display_name": "Markus"}], "match_count": 1, "truncated": False},
        ),
        _StubTool(
            "employees.get_employee_operational_profile",
            {"found": True, "employee": {"employee_ref": "emp-1", "display_name": "Markus", "status": "active", "is_active": True, "has_user_link": True}},
        ),
        _StubTool(
            "employees.get_employee_mobile_access_status",
            {"found": True, "mobile_access": {"has_linked_user_account": True, "self_service_enabled": True, "mobile_context_available": True, "can_receive_released_schedules": False}},
        ),
    )
    conversation = repository.create_conversation(
        tenant_id="tenant-1",
        user_id="assistant-user-1",
        title=None,
        locale="de",
        last_route_name=None,
        last_route_path=None,
    )

    service.add_message(
        conversation.id,
        AssistantMessageCreate(
            message="Markus sieht seine zugewiesene Schicht am 1. Mai 2026 nicht in der mobilen App. Woran könnte das liegen?"
        ),
        _context(),
    )

    assert len(provider.requests) == 1
    assert provider.requests[0].metadata["estimated_input_tokens"] < 14000
    assert provider.requests[0].available_tools == []
