from __future__ import annotations

from tests.modules.assistant.test_employee_tools import _context, _repository, _service


def test_employee_self_service_user_cannot_inspect_another_employee() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.get_employee_operational_profile",
        input_data={"employee_ref": "employee-1"},
        actor=_context(
            role_keys=("employee_user",),
            permission_keys=("assistant.chat.access", "portal.employee.access"),
            user_id="user-2",
        ),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.permission_denied"


def test_customer_portal_user_cannot_use_employee_admin_tools() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.search_employee_by_name",
        input_data={"name": "Markus"},
        actor=_context(role_keys=("customer_user",), permission_keys=("assistant.chat.access", "portal.customer.access")),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.permission_denied"


def test_mobile_access_status_requires_existing_employee_access_permission_mapping() -> None:
    repository = _repository()
    result = _service(repository).execute_registered_tool(
        tool_name="employees.get_employee_mobile_access_status",
        input_data={"employee_ref": "employee-1"},
        actor=_context(role_keys=("tenant_admin",), permission_keys=("assistant.chat.access", "employees.employee.read")),
    )

    assert result.ok is False
    assert result.error_code == "assistant.tool.permission_denied"
    assert result.missing_permissions == [
        {
            "permission": "assistant.chat.access",
            "reason": "The current user does not have the required permission for this assistant tool.",
        },
        {
            "permission": "employees.employee.write",
            "reason": "The current user does not have the required permission for this assistant tool.",
        }
    ]
