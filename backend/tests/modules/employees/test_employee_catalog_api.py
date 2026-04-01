from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.modules.employees.catalog_seed import seed_baseline_employee_catalogs
from app.modules.employees.models import FunctionType, QualificationType
from app.modules.employees.router import list_function_types, list_qualification_types
from app.modules.employees.schemas import FunctionTypeRead, QualificationTypeRead
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


class _FakeScalarResult:
    def __init__(self, value) -> None:  # noqa: ANN001
        self.value = value

    def one_or_none(self):  # noqa: ANN201
        return self.value


class _FakeSeedSession:
    def __init__(self) -> None:
        self.function_types: list[FunctionType] = []
        self.qualification_types: list[QualificationType] = []
        self._function_index = 1
        self._qualification_index = 1

    def add(self, row) -> None:  # noqa: ANN001
        if isinstance(row, FunctionType):
            row.id = row.id or f"function-{self._function_index}"
            self._function_index += 1
            row.status = row.status or "active"
            row.version_no = row.version_no or 1
            row.created_at = row.created_at or datetime.now(UTC)
            row.updated_at = row.updated_at or datetime.now(UTC)
            self.function_types.append(row)
            return
        if isinstance(row, QualificationType):
            row.id = row.id or f"qualification-{self._qualification_index}"
            self._qualification_index += 1
            row.status = row.status or "active"
            row.version_no = row.version_no or 1
            row.created_at = row.created_at or datetime.now(UTC)
            row.updated_at = row.updated_at or datetime.now(UTC)
            self.qualification_types.append(row)
            return
        raise AssertionError(f"Unexpected row type: {type(row)!r}")

    def scalars(self, statement):  # noqa: ANN001
        compiled = statement.compile()
        values = list(compiled.params.values())
        tenant_value, code_value = values
        entity_name = statement.column_descriptions[0]["entity"].__name__
        rows = self.function_types if entity_name == "FunctionType" else self.qualification_types
        for row in rows:
            if row.tenant_id == tenant_value and row.code == code_value:
                return _FakeScalarResult(row)
        return _FakeScalarResult(None)


def _context(tenant_id: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"employees.employee.read"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-test-1",
    )


@dataclass
class SeedBackedQualificationService:
    session: _FakeSeedSession

    def list_function_types(self, tenant_id: str, context: RequestAuthorizationContext) -> list[FunctionTypeRead]:
        rows = sorted(
            [row for row in self.session.function_types if row.tenant_id == tenant_id],
            key=lambda row: row.code,
        )
        return [FunctionTypeRead.model_validate(row) for row in rows]

    def list_qualification_types(self, tenant_id: str, context: RequestAuthorizationContext) -> list[QualificationTypeRead]:
        rows = sorted(
            [row for row in self.session.qualification_types if row.tenant_id == tenant_id],
            key=lambda row: row.code,
        )
        return [QualificationTypeRead.model_validate(row) for row in rows]


def test_catalog_list_endpoints_return_non_empty_data_for_baseline_initialized_tenant() -> None:
    tenant_id = str(uuid4())
    session = _FakeSeedSession()
    seed_baseline_employee_catalogs(session, tenant_id=tenant_id, actor_user_id="user-1")
    service = SeedBackedQualificationService(session)
    tenant_uuid = UUID(tenant_id)
    context = _context(tenant_id)

    function_payload = list_function_types(tenant_uuid, context, service)
    qualification_payload = list_qualification_types(tenant_uuid, context, service)

    assert [row.code for row in function_payload] == ["DISPATCH", "FIRE_WATCH", "SEC_GUARD", "SHIFT_SUP"]
    assert [row.code for row in qualification_payload] == ["CROWD_CONTROL", "FIRE_SAFETY", "FIRST_AID", "G34A"]
