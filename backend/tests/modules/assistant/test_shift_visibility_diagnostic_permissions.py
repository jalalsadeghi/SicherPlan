from __future__ import annotations

from app.modules.assistant.schemas import AssistantMessageCreate
from tests.modules.assistant.test_shift_visibility_diagnostic import (
    _DiagnosticRepository,
    _context,
    _conversation,
    _service,
)


def test_missing_mobile_access_permission_is_reported_safely() -> None:
    repository = _DiagnosticRepository()
    result = _service(repository).execute_registered_tool(
        tool_name="assistant.diagnose_employee_shift_visibility",
        input_data={"assignment_ref": "assignment-visible", "employee_ref": "employee-1", "date": "2026-05-01", "question_language": "en"},
        actor=_context(
            role_keys=("dispatcher",),
            permission_keys=("assistant.chat.access", "assistant.diagnostics.read", "employees.employee.read", "planning.shift.read", "planning.staffing.read"),
        ),
    )

    permissions = {row["permission"] for row in result.data["missing_permissions"]}
    assert "employees.employee.write" in permissions


def test_missing_planning_permission_is_reported_safely() -> None:
    repository = _DiagnosticRepository()
    result = _service(repository).execute_registered_tool(
        tool_name="assistant.diagnose_employee_shift_visibility",
        input_data={"assignment_ref": "assignment-visible", "employee_ref": "employee-1", "date": "2026-05-01", "question_language": "en"},
        actor=_context(
            role_keys=("dispatcher",),
            permission_keys=("assistant.chat.access", "assistant.diagnostics.read", "employees.employee.read", "employees.employee.write"),
        ),
    )

    permissions = {row["permission"] for row in result.data["missing_permissions"]}
    assert "planning.staffing.read" in permissions or "planning.shift.read" in permissions


def test_employee_self_service_can_only_check_own_shift() -> None:
    repository = _DiagnosticRepository()
    service = _service(repository)
    own = service.execute_registered_tool(
        tool_name="assistant.diagnose_employee_shift_visibility",
        input_data={"assignment_ref": "assignment-visible", "question_language": "en"},
        actor=_context(role_keys=("employee_user",), permission_keys=("assistant.chat.access", "portal.employee.access"), user_id="user-1"),
    )
    foreign = service.execute_registered_tool(
        tool_name="assistant.diagnose_employee_shift_visibility",
        input_data={"assignment_ref": "assignment-ambiguous-1", "employee_ref": "employee-2", "question_language": "en"},
        actor=_context(role_keys=("employee_user",), permission_keys=("assistant.chat.access", "portal.employee.access"), user_id="user-1"),
    )

    assert own.ok is True
    assert foreign.data["status"] in {"not_found_or_not_permitted", "unknown"}


def test_customer_and_subcontractor_portal_users_are_denied_safely() -> None:
    repository = _DiagnosticRepository()
    customer = _service(repository).execute_registered_tool(
        tool_name="assistant.diagnose_employee_shift_visibility",
        input_data={"assignment_ref": "assignment-visible", "employee_ref": "employee-1", "question_language": "en"},
        actor=_context(role_keys=("customer_user",), permission_keys=("assistant.chat.access",)),
    )
    subcontractor = _service(repository).execute_registered_tool(
        tool_name="assistant.diagnose_employee_shift_visibility",
        input_data={"assignment_ref": "assignment-visible", "employee_ref": "employee-1", "question_language": "en"},
        actor=_context(role_keys=("subcontractor_user",), permission_keys=("assistant.chat.access",)),
    )

    assert customer.ok is False
    assert subcontractor.ok is False


def test_internal_user_without_diagnostics_permission_gets_safe_limitation() -> None:
    repository = _DiagnosticRepository()
    conversation = _conversation(repository)
    response = _service(repository).add_message(
        conversation.id,
        AssistantMessageCreate(message="I assigned Markus to a shift on May 1, 2026, but the shift is not visible in the app. What is wrong?"),
        _context(
            role_keys=("dispatcher",),
            permission_keys=("assistant.chat.access", "employees.employee.read", "employees.employee.write", "planning.shift.read", "planning.staffing.read"),
        ),
    )

    assert response.out_of_scope is False
    assert any(row.permission == "assistant.diagnostics.read" for row in response.missing_permissions)
