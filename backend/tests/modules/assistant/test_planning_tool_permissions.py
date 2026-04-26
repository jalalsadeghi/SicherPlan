from __future__ import annotations

from tests.modules.assistant.test_planning_tools import _context, _repository, _service


def test_missing_shift_permission_returns_safe_missing_permissions_output() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.find_shifts",
        input_data={"date": "2026-05-01"},
        actor=_context(role_keys=("dispatcher",), permission_keys=("assistant.chat.access",)),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.permission_denied"
    assert result.missing_permissions == [
        {
            "permission": "assistant.chat.access",
            "reason": "The current user does not have the required permission for this assistant tool.",
        },
        {
            "permission": "planning.shift.read",
            "reason": "The current user does not have the required permission for this assistant tool.",
        },
    ]


def test_customer_portal_user_cannot_inspect_internal_planning_tools() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.inspect_shift_release_state",
        input_data={"shift_ref": "shift-1"},
        actor=_context(role_keys=("customer_user",), permission_keys=("assistant.chat.access", "portal.customer.access")),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.permission_denied"


def test_employee_self_service_user_cannot_inspect_other_users_assignments() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="planning.inspect_assignment",
        input_data={"assignment_ref": "assignment-1"},
        actor=_context(role_keys=("employee_user",), permission_keys=("assistant.chat.access", "portal.employee.access"), user_id="user-2"),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.permission_denied"
