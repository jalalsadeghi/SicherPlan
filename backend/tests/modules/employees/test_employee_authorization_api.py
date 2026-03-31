from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import Request

from app.errors import ApiException
from app.modules.employees.router import create_employee
from app.modules.employees.schemas import EmployeeOperationalCreate, EmployeeOperationalRead
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.auth_router import get_current_auth_context
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization


def _tenant_id() -> str:
    return str(uuid4())


def _request(tenant_id: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": f"/api/employees/tenants/{tenant_id}/employees",
            "path_params": {"tenant_id": tenant_id},
            "headers": [],
        }
    )


def _payload(tenant_id: str) -> EmployeeOperationalCreate:
    return EmployeeOperationalCreate(
        tenant_id=tenant_id,
        personnel_no="EMP-1001",
        first_name="Mina",
        last_name="Schmidt",
        preferred_name="Mina",
        work_email="mina.schmidt@example.invalid",
    )


def _context(
    *,
    tenant_id: str,
    permission_keys: frozenset[str] | None = None,
    scopes: tuple[AuthenticatedRoleScope, ...] | None = None,
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=permission_keys if permission_keys is not None else frozenset({"employees.employee.write"}),
        scopes=(
            scopes
            if scopes is not None
            else (
                AuthenticatedRoleScope(
                    role_key="tenant_admin",
                    scope_type="branch",
                    branch_id=str(uuid4()),
                ),
            )
        ),
        request_id="req-1",
    )


class RecordingEmployeeService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def create_employee(self, tenant_id, payload, context):  # noqa: ANN001
        self.calls.append((tenant_id, context.user_id))
        now = datetime.now(UTC)
        return EmployeeOperationalRead(
            id=str(uuid4()),
            tenant_id=tenant_id,
            personnel_no=payload.personnel_no,
            first_name=payload.first_name,
            last_name=payload.last_name,
            preferred_name=payload.preferred_name,
            work_email=payload.work_email,
            work_phone=payload.work_phone,
            mobile_phone=payload.mobile_phone,
            default_branch_id=payload.default_branch_id,
            default_mandate_id=payload.default_mandate_id,
            hire_date=payload.hire_date,
            termination_date=payload.termination_date,
            employment_type_code=payload.employment_type_code,
            target_weekly_hours=payload.target_weekly_hours,
            target_monthly_hours=payload.target_monthly_hours,
            user_id=payload.user_id,
            notes=payload.notes,
            status="active",
            created_at=now,
            updated_at=now,
            archived_at=None,
            version_no=1,
            group_memberships=[],
        )


def test_tenant_admin_can_create_employee_in_own_tenant() -> None:
    tenant_id = _tenant_id()
    dependency = require_authorization("employees.employee.write", scope="tenant")
    authorized_context = dependency(_request(tenant_id), _context(tenant_id=tenant_id))
    service = RecordingEmployeeService()

    result = create_employee(UUID(tenant_id), _payload(tenant_id), authorized_context, service)  # type: ignore[arg-type]

    assert result.tenant_id == tenant_id
    assert service.calls == [(tenant_id, "user-1")]


def test_tenant_admin_cannot_create_employee_in_another_tenant() -> None:
    caller_tenant_id = _tenant_id()
    target_tenant_id = _tenant_id()
    dependency = require_authorization("employees.employee.write", scope="tenant")

    with pytest.raises(ApiException) as raised:
        dependency(_request(target_tenant_id), _context(tenant_id=caller_tenant_id))

    assert raised.value.status_code == 403
    assert raised.value.code == "iam.authorization.scope_denied"


def test_caller_without_employee_write_permission_is_rejected() -> None:
    tenant_id = _tenant_id()
    dependency = require_authorization("employees.employee.write", scope="tenant")

    with pytest.raises(ApiException) as raised:
        dependency(_request(tenant_id), _context(tenant_id=tenant_id, permission_keys=frozenset()))

    assert raised.value.status_code == 403
    assert raised.value.code == "iam.authorization.permission_denied"


def test_unauthenticated_create_employee_request_is_rejected() -> None:
    with pytest.raises(ApiException) as raised:
        get_current_auth_context(
            _request(_tenant_id()),
            credentials=None,
            service=SimpleNamespace(),
        )

    assert raised.value.status_code == 401
    assert raised.value.code == "iam.auth.invalid_access_token"
