from __future__ import annotations

from tests.modules.assistant.test_field_released_schedule_visibility import _context, _repository, _service


def test_customer_portal_user_is_denied_safely_by_default() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-visible"},
        actor=_context(role_keys=("customer_user",), permission_keys=("assistant.chat.access", "portal.customer.access")),
    )
    assert result.ok is False
    assert result.error_code == "assistant.tool.permission_denied"


def test_subcontractor_portal_user_is_denied_safely_by_default() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="field.inspect_released_schedule_visibility",
        input_data={"assignment_ref": "assignment-visible"},
        actor=_context(role_keys=("subcontractor_user",), permission_keys=("assistant.chat.access", "portal.subcontractor.access")),
    )
    assert result.ok is False
    assert result.error_code == "assistant.tool.permission_denied"
