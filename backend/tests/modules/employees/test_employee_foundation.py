from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.db import Base
from app.errors import ApiException
from app.modules.core.models import Address, Branch, Mandate
from app.modules.core.schemas import LookupValueRead
from app.modules.employees.models import (
    Employee,
    EmployeeAddressHistory,
    EmployeeGroup,
    EmployeeGroupMember,
    EmployeeNote,
    EmployeePrivateProfile,
)
from app.modules.employees.schemas import (
    EmployeeAddressHistoryCreate,
    EmployeeFilter,
    EmployeeLifecycleTransitionRequest,
    EmployeeNoteCreate,
    EmployeeNoteUpdate,
    EmployeeOperationalCreate,
    EmployeeOperationalUpdate,
    EmployeePrivateProfileCreate,
    EmployeePrivateProfileUpdate,
)
from app.modules.employees.service import EmployeeService
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.iam.models import Role, UserAccount, UserRoleAssignment
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository


def _context(*permissions: str, tenant_id: str = "tenant-1") -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-1",
    )


@dataclass
class FakeEmployeeRepository:
    tenant_id: str = "tenant-1"
    branch_id: str = "22222222-2222-2222-2222-222222222222"
    mandate_id: str = "33333333-3333-3333-3333-333333333333"
    user_id: str = "11111111-1111-1111-1111-111111111111"
    address_id: str = "address-1"
    address_seq: int = 1
    employees: dict[str, Employee] = field(default_factory=dict)
    addresses: dict[str, Address] = field(default_factory=dict)
    private_profiles: dict[str, EmployeePrivateProfile] = field(default_factory=dict)
    address_history: dict[str, list[EmployeeAddressHistory]] = field(default_factory=dict)
    groups: dict[str, EmployeeGroup] = field(default_factory=dict)
    group_members: dict[str, EmployeeGroupMember] = field(default_factory=dict)
    notes: dict[str, list[EmployeeNote]] = field(default_factory=dict)
    role_assignments: dict[str, UserRoleAssignment] = field(default_factory=dict)
    branches: dict[str, Branch] = field(default_factory=dict)
    mandates: dict[str, Mandate] = field(default_factory=dict)
    lookup_values: list[LookupValueRead] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.branch = Branch(
            id=self.branch_id,
            tenant_id=self.tenant_id,
            code="BER",
            name="Berlin",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.mandate = Mandate(
            id=self.mandate_id,
            tenant_id=self.tenant_id,
            branch_id=self.branch_id,
            code="M-001",
            name="Mandate",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.user = UserAccount(
            id=self.user_id,
            tenant_id=self.tenant_id,
            username="sysadmin",
            email="sysadmin@example.com",
            full_name="System Admin",
            password_hash="hashed",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.employee_role = Role(
            id="role-employee-user",
            key="employee_user",
            name="Employee User",
            description="",
            is_portal_role=True,
            is_system_role=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.address = Address(
            id=self.address_id,
            street_line_1="Musterstrasse 1",
            postal_code="10115",
            city="Berlin",
            country_code="DE",
        )
        self.branches[self.branch_id] = self.branch
        self.mandates[self.mandate_id] = self.mandate
        self.addresses = {self.address_id: self.address}
        self.lookup_values = [
            LookupValueRead(
                id="lookup-marital-single",
                tenant_id=None,
                domain="marital_status",
                code="single",
                label="Ledig",
                description="Keine bestehende Ehe oder eingetragene Partnerschaft",
                sort_order=10,
                status="active",
                version_no=1,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                created_by_user_id=None,
                updated_by_user_id=None,
                archived_at=None,
            ),
            LookupValueRead(
                id="lookup-marital-married",
                tenant_id=None,
                domain="marital_status",
                code="married",
                label="Verheiratet",
                description="Verheiratet oder in bestehender Ehe",
                sort_order=20,
                status="active",
                version_no=1,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                created_by_user_id=None,
                updated_by_user_id=None,
                archived_at=None,
            ),
        ]

    def list_employees(self, tenant_id: str, filters=None) -> list[Employee]:  # noqa: ANN001
        rows = [row for row in self.employees.values() if row.tenant_id == tenant_id]
        if filters is not None:
            if not getattr(filters, "include_archived", False):
                rows = [row for row in rows if row.archived_at is None]
            if getattr(filters, "status", None):
                rows = [row for row in rows if row.status == filters.status]
        rows.sort(key=lambda row: row.personnel_no)
        return rows

    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None:
        row = self.employees.get(employee_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def update_employee(self, row: Employee) -> Employee:
        self.employees[row.id] = row
        return row

    def get_employee_private_profile(self, tenant_id: str, employee_id: str) -> EmployeePrivateProfile | None:
        row = self.private_profiles.get(employee_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def list_employee_address_history(self, tenant_id: str, employee_id: str) -> list[EmployeeAddressHistory]:
        rows = [row for row in self.address_history.get(employee_id, []) if row.tenant_id == tenant_id]
        rows.sort(key=lambda row: row.valid_from)
        return rows

    def get_employee_address_history(
        self,
        tenant_id: str,
        employee_id: str,
        history_id: str,
    ) -> EmployeeAddressHistory | None:
        for row in self.address_history.get(employee_id, []):
            if row.tenant_id == tenant_id and row.id == history_id:
                return row
        return None

    def list_groups(self, tenant_id: str) -> list[EmployeeGroup]:
        return [row for row in self.groups.values() if row.tenant_id == tenant_id]

    def get_group(self, tenant_id: str, group_id: str) -> EmployeeGroup | None:
        row = self.groups.get(group_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def get_group_member(self, tenant_id: str, member_id: str) -> EmployeeGroupMember | None:
        row = self.group_members.get(member_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def list_notes(self, tenant_id: str, employee_id: str) -> list[EmployeeNote]:
        return [row for row in self.notes.get(employee_id, []) if row.tenant_id == tenant_id]

    def get_note(self, tenant_id: str, employee_id: str, note_id: str) -> EmployeeNote | None:
        for row in self.notes.get(employee_id, []):
            if row.tenant_id == tenant_id and row.id == note_id:
                return row
        return None

    @staticmethod
    def _stamp_lifecycle(row) -> None:  # noqa: ANN001
        now = datetime.now(UTC)
        if getattr(row, "status", None) is None:
            row.status = "active"
        if getattr(row, "created_at", None) is None:
            row.created_at = now
        if getattr(row, "updated_at", None) is None:
            row.updated_at = now
        if getattr(row, "version_no", None) is None:
            row.version_no = 1

    def create_employee(self, row: Employee) -> Employee:
        row.id = row.id or str(uuid4())
        self._stamp_lifecycle(row)
        self.employees[row.id] = row
        return row

    def create_private_profile(self, row: EmployeePrivateProfile) -> EmployeePrivateProfile:
        row.id = row.id or str(uuid4())
        self._stamp_lifecycle(row)
        self.private_profiles[row.employee_id] = row
        return row

    def update_private_profile(self, row: EmployeePrivateProfile) -> EmployeePrivateProfile:
        self._stamp_lifecycle(row)
        self.private_profiles[row.employee_id] = row
        return row

    def create_address_history(self, row: EmployeeAddressHistory) -> EmployeeAddressHistory:
        row.id = row.id or str(uuid4())
        self._stamp_lifecycle(row)
        row.address = self.get_address(row.address_id)
        self.address_history.setdefault(row.employee_id, []).append(row)
        return row

    def update_address_history(self, row: EmployeeAddressHistory) -> EmployeeAddressHistory:
        self._stamp_lifecycle(row)
        rows = self.address_history.setdefault(row.employee_id, [])
        for index, existing in enumerate(rows):
            if existing.id == row.id:
                rows[index] = row
                break
        return row

    def create_group(self, row: EmployeeGroup) -> EmployeeGroup:
        row.id = row.id or str(uuid4())
        self._stamp_lifecycle(row)
        self.groups[row.id] = row
        return row

    def update_group(self, row: EmployeeGroup) -> EmployeeGroup:
        self._stamp_lifecycle(row)
        self.groups[row.id] = row
        return row

    def create_group_member(self, row: EmployeeGroupMember) -> EmployeeGroupMember:
        row.id = row.id or str(uuid4())
        self._stamp_lifecycle(row)
        self.group_members[row.id] = row
        return row

    def update_group_member(self, row: EmployeeGroupMember) -> EmployeeGroupMember:
        self._stamp_lifecycle(row)
        self.group_members[row.id] = row
        return row

    def create_note(self, row: EmployeeNote) -> EmployeeNote:
        row.id = row.id or str(uuid4())
        self._stamp_lifecycle(row)
        self.notes.setdefault(row.employee_id, []).append(row)
        return row

    def update_note(self, row: EmployeeNote) -> EmployeeNote:
        self._stamp_lifecycle(row)
        rows = self.notes.setdefault(row.employee_id, [])
        for index, existing in enumerate(rows):
            if existing.id == row.id:
                rows[index] = row
                break
        return row

    def find_employee_by_personnel_no(
        self,
        tenant_id: str,
        personnel_no: str,
        *,
        exclude_id: str | None = None,
    ) -> Employee | None:
        for row in self.employees.values():
            if row.tenant_id != tenant_id or row.personnel_no != personnel_no:
                continue
            if exclude_id is not None and row.id == exclude_id:
                continue
            return row
        return None

    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None) -> Employee | None:
        for row in self.employees.values():
            if row.tenant_id != tenant_id or row.user_id != user_id or row.archived_at is not None:
                continue
            if exclude_id is not None and row.id == exclude_id:
                continue
            return row
        return None

    def find_group_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> EmployeeGroup | None:
        for row in self.groups.values():
            if row.tenant_id != tenant_id or row.code != code:
                continue
            if exclude_id is not None and row.id == exclude_id:
                continue
            return row
        return None

    def get_user_account(self, tenant_id: str, user_id: str) -> UserAccount | None:
        if tenant_id == self.tenant_id and user_id == self.user_id:
            return self.user
        return None

    def find_role_assignment(self, tenant_id: str, user_id: str, role_key: str) -> UserRoleAssignment | None:
        assignment = self.role_assignments.get(f"{tenant_id}:{user_id}:{role_key}")
        return assignment

    def update_role_assignment(self, row: UserRoleAssignment) -> UserRoleAssignment:
        self.role_assignments[f"{row.tenant_id}:{row.user_account_id}:employee_user"] = row
        return row

    def get_branch(self, tenant_id: str, branch_id: str) -> Branch | None:
        branch = self.branches.get(branch_id)
        if branch is None or tenant_id != self.tenant_id:
            return None
        return branch

    def get_mandate(self, tenant_id: str, mandate_id: str) -> Mandate | None:
        mandate = self.mandates.get(mandate_id)
        if mandate is None or tenant_id != self.tenant_id:
            return None
        return mandate

    def get_address(self, address_id: str) -> Address | None:
        return self.addresses.get(address_id)

    def create_address(self, row: Address) -> Address:
        self.address_seq += 1
        row.id = row.id or f"address-{self.address_seq}"
        self.addresses[row.id] = row
        return row

    def list_lookup_values(self, tenant_id: str, domain: str) -> list[LookupValueRead]:
        return [row for row in self.lookup_values if row.domain == domain and row.archived_at is None]


class TestEmployeeFoundationMetadata(unittest.TestCase):
    def test_expected_employee_tables_are_registered(self) -> None:
        self.assertIn("hr.employee", Base.metadata.tables)
        self.assertIn("hr.employee_private_profile", Base.metadata.tables)
        self.assertIn("hr.employee_address_history", Base.metadata.tables)
        self.assertIn("hr.employee_group", Base.metadata.tables)
        self.assertIn("hr.employee_group_member", Base.metadata.tables)
        self.assertIn("hr.employee_note", Base.metadata.tables)

    def test_employee_constraints_cover_personnel_and_user_link_uniqueness(self) -> None:
        constraint_names = {
            constraint.name for constraint in Employee.__table__.constraints if isinstance(constraint, UniqueConstraint)
        }
        check_names = {
            constraint.name for constraint in Employee.__table__.constraints if isinstance(constraint, CheckConstraint)
        }
        index_names = {index.name for index in Employee.__table__.indexes if isinstance(index, Index)}
        self.assertIn("uq_hr_employee_tenant_personnel_no", constraint_names)
        self.assertIn("uq_hr_employee_tenant_id_id", constraint_names)
        self.assertIn("uq_hr_employee_tenant_user_id", index_names)
        self.assertIn("ck_employee_employee_target_weekly_hours_non_negative", check_names)
        self.assertIn("ck_employee_employee_target_monthly_hours_non_negative", check_names)

    def test_private_profile_is_strict_one_to_one(self) -> None:
        constraint_names = {
            constraint.name
            for constraint in EmployeePrivateProfile.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn("uq_hr_employee_private_profile_employee", constraint_names)

    def test_docs_service_supports_employee_owner_links(self) -> None:
        self.assertIn("hr.employee", SqlAlchemyDocumentRepository.SUPPORTED_OWNER_TYPES)


class TestEmployeeService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeEmployeeRepository()
        self.audit_events: list[object] = []

        class RecordingAuditRepository:
            def __init__(self, sink: list[object]) -> None:
                self.sink = sink

            def create_login_event(self, payload):  # noqa: ANN001
                return payload

            def create_audit_event(self, payload):  # noqa: ANN001
                self.sink.append(payload)
                return payload

        self.service = EmployeeService(self.repository, audit_service=AuditService(RecordingAuditRepository(self.audit_events)))

    def test_operational_create_and_private_profile_stay_separate(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1001",
                first_name="Anna",
                last_name="Schmidt",
                default_branch_id=self.repository.branch_id,
                default_mandate_id=self.repository.mandate_id,
                employment_type_code="full_time",
                target_weekly_hours=40,
                target_monthly_hours=173.2,
                user_id=self.repository.user_id,
            ),
            _context("employees.employee.write"),
        )

        private_profile = self.service.upsert_private_profile(
            "tenant-1",
            employee.id,
            EmployeePrivateProfileCreate(
                tenant_id="tenant-1",
                employee_id=employee.id,
                private_email="anna.private@example.de",
                tax_id="DE123",
            ),
            _context("employees.private.write"),
        )

        operational = self.service.get_operational_employee(
            "tenant-1",
            employee.id,
            _context("employees.employee.read"),
        )

        self.assertEqual(operational.personnel_no, "EMP-1001")
        self.assertEqual(operational.employment_type_code, "full_time")
        self.assertEqual(operational.target_weekly_hours, 40)
        self.assertEqual(operational.target_monthly_hours, 173.2)
        self.assertFalse(hasattr(operational, "tax_id"))
        self.assertEqual(private_profile.tax_id, "DE123")

    def test_private_profile_uses_marital_status_code_and_accepts_legacy_alias(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1001C",
                first_name="Lea",
                last_name="Sommer",
            ),
            _context("employees.employee.write"),
        )

        created = self.service.upsert_private_profile(
            "tenant-1",
            employee.id,
            EmployeePrivateProfileCreate(
                tenant_id="tenant-1",
                employee_id=employee.id,
                marital_status_code="married",
            ),
            _context("employees.private.write"),
        )

        updated = self.service.update_private_profile(
            "tenant-1",
            employee.id,
            EmployeePrivateProfileUpdate.model_validate(
                {
                    "marital_status": "single",
                    "version_no": created.version_no,
                }
            ),
            _context("employees.private.write"),
        )

        self.assertEqual(created.marital_status_code, "married")
        self.assertEqual(updated.marital_status_code, "single")

    def test_private_profile_marital_status_options_require_private_read_permission(self) -> None:
        rows = self.service.list_private_profile_marital_status_options(
            "tenant-1",
            _context("employees.private.read"),
        )

        self.assertEqual([row.code for row in rows], ["single", "married"])

        with self.assertRaises(ApiException):
            self.service.list_private_profile_marital_status_options(
                "tenant-1",
                _context("employees.employee.read"),
            )

    def test_operational_update_persists_status_and_target_hours(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1001B",
                first_name="Mara",
                last_name="Klein",
            ),
            _context("employees.employee.write"),
        )

        updated = self.service.update_employee(
            "tenant-1",
            employee.id,
            EmployeeOperationalUpdate(
                status="inactive",
                employment_type_code="part_time",
                target_weekly_hours=30,
                target_monthly_hours=130,
                version_no=employee.version_no,
            ),
            _context("employees.employee.write"),
        )

        self.assertEqual(updated.status, "inactive")
        self.assertEqual(updated.employment_type_code, "part_time")
        self.assertEqual(updated.target_weekly_hours, 30)
        self.assertEqual(updated.target_monthly_hours, 130)

    def test_private_profile_requires_private_permission(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1002",
                first_name="Ben",
                last_name="Fischer",
            ),
            _context("employees.employee.write"),
        )
        self.service.upsert_private_profile(
            "tenant-1",
            employee.id,
            EmployeePrivateProfileCreate(
                tenant_id="tenant-1",
                employee_id=employee.id,
                private_email="ben.private@example.de",
            ),
            _context("employees.private.write"),
        )

        with self.assertRaises(ApiException) as ctx:
            self.service.get_private_profile(
                "tenant-1",
                employee.id,
                _context("employees.employee.read"),
            )

        self.assertEqual(ctx.exception.message_key, "errors.iam.authorization.permission_denied")

    def test_address_history_rejects_overlapping_windows(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1003",
                first_name="Clara",
                last_name="Neumann",
            ),
            _context("employees.employee.write"),
        )

        self.service.add_address_history(
            "tenant-1",
            employee.id,
            EmployeeAddressHistoryCreate(
                tenant_id="tenant-1",
                employee_id=employee.id,
                address_id="address-1",
                address_type="home",
                valid_from=date(2026, 1, 1),
                valid_to=date(2026, 6, 30),
            ),
            _context("employees.private.write"),
        )

        with self.assertRaises(ApiException) as ctx:
            self.service.add_address_history(
                "tenant-1",
                employee.id,
                EmployeeAddressHistoryCreate(
                    tenant_id="tenant-1",
                    employee_id=employee.id,
                    address_id="address-1",
                    address_type="home",
                    valid_from=date(2026, 6, 1),
                    valid_to=date(2026, 12, 31),
                ),
                _context("employees.private.write"),
            )

        self.assertEqual(ctx.exception.message_key, "errors.employees.address_history.overlap")

    def test_address_history_can_create_inline_address_on_admin_endpoint(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1003A",
                first_name="Clara",
                last_name="Neumann",
            ),
            _context("employees.employee.write"),
        )

        created = self.service.add_address_history(
            "tenant-1",
            employee.id,
            EmployeeAddressHistoryCreate(
                tenant_id="tenant-1",
                employee_id=employee.id,
                address={
                    "street_line_1": "Neue Strasse 5",
                    "street_line_2": "2. OG",
                    "postal_code": "40210",
                    "city": "Duesseldorf",
                    "state_region": "NRW",
                    "country_code": "de",
                },
                address_type="home",
                valid_from=date(2026, 1, 1),
                valid_to=None,
            ),
            _context("employees.private.write"),
        )

        self.assertEqual(created.address.street_line_1, "Neue Strasse 5")
        self.assertEqual(created.address.country_code, "DE")
        self.assertEqual(created.address_id, created.address.id)

    def test_duplicate_user_link_is_blocked(self) -> None:
        self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1004",
                first_name="Dora",
                last_name="Becker",
                user_id=self.repository.user_id,
            ),
            _context("employees.employee.write"),
        )

        with self.assertRaises(ApiException) as ctx:
            self.service.create_employee(
                "tenant-1",
                EmployeeOperationalCreate(
                    tenant_id="tenant-1",
                    personnel_no="EMP-1005",
                    first_name="Eva",
                    last_name="Lorenz",
                    user_id=self.repository.user_id,
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(ctx.exception.message_key, "errors.employees.employee.duplicate_user_link")

    def test_create_employee_allows_empty_user_id(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1005A",
                first_name="Jana",
                last_name="Klein",
                user_id="   ",
            ),
            _context("employees.employee.write"),
        )

        self.assertIsNone(employee.user_id)

    def test_create_employee_rejects_non_uuid_user_id(self) -> None:
        with self.assertRaises(ApiException) as ctx:
            self.service.create_employee(
                "tenant-1",
                EmployeeOperationalCreate(
                    tenant_id="tenant-1",
                    personnel_no="EMP-1005B",
                    first_name="Lars",
                    last_name="Winter",
                    user_id="usr-emp-0042",
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.message_key, "errors.employees.user.invalid_id_format")

    def test_create_employee_rejects_missing_valid_uuid_user_account(self) -> None:
        missing_user_id = str(uuid4())

        with self.assertRaises(ApiException) as ctx:
            self.service.create_employee(
                "tenant-1",
                EmployeeOperationalCreate(
                    tenant_id="tenant-1",
                    personnel_no="EMP-1005C",
                    first_name="Mila",
                    last_name="Brandt",
                    user_id=missing_user_id,
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.message_key, "errors.employees.user.not_found")

    def test_create_employee_accepts_existing_valid_uuid_user_id(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1005D",
                first_name="Nina",
                last_name="Voss",
                user_id=self.repository.user_id,
            ),
            _context("employees.employee.write"),
        )

        self.assertEqual(employee.user_id, self.repository.user_id)

    def test_create_employee_rejects_non_uuid_default_branch_id(self) -> None:
        with self.assertRaises(ApiException) as ctx:
            self.service.create_employee(
                "tenant-1",
                EmployeeOperationalCreate(
                    tenant_id="tenant-1",
                    personnel_no="EMP-1005E",
                    first_name="Nora",
                    last_name="Weiss",
                    default_branch_id="Cologne HQ",
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.message_key, "errors.employees.employee.invalid_branch_id_format")

    def test_create_employee_rejects_non_uuid_default_mandate_id(self) -> None:
        with self.assertRaises(ApiException) as ctx:
            self.service.create_employee(
                "tenant-1",
                EmployeeOperationalCreate(
                    tenant_id="tenant-1",
                    personnel_no="EMP-1005F",
                    first_name="Omar",
                    last_name="Jung",
                    default_mandate_id="Night Shift",
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.message_key, "errors.employees.employee.invalid_mandate_id_format")

    def test_create_employee_accepts_existing_branch_and_mandate(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1005G",
                first_name="Paul",
                last_name="Kurz",
                default_branch_id=self.repository.branch_id,
                default_mandate_id=self.repository.mandate_id,
            ),
            _context("employees.employee.write"),
        )

        self.assertEqual(employee.default_branch_id, self.repository.branch_id)
        self.assertEqual(employee.default_mandate_id, self.repository.mandate_id)

    def test_create_employee_rejects_missing_branch_and_mandate_records(self) -> None:
        missing_branch_id = str(uuid4())
        missing_mandate_id = str(uuid4())

        with self.assertRaises(ApiException) as branch_ctx:
            self.service.create_employee(
                "tenant-1",
                EmployeeOperationalCreate(
                    tenant_id="tenant-1",
                    personnel_no="EMP-1005H",
                    first_name="Ria",
                    last_name="Koch",
                    default_branch_id=missing_branch_id,
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(branch_ctx.exception.status_code, 404)
        self.assertEqual(branch_ctx.exception.message_key, "errors.employees.employee.branch_not_found")

        with self.assertRaises(ApiException) as mandate_ctx:
            self.service.create_employee(
                "tenant-1",
                EmployeeOperationalCreate(
                    tenant_id="tenant-1",
                    personnel_no="EMP-1005I",
                    first_name="Sara",
                    last_name="Graf",
                    default_mandate_id=missing_mandate_id,
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(mandate_ctx.exception.status_code, 404)
        self.assertEqual(mandate_ctx.exception.message_key, "errors.employees.employee.mandate_not_found")

    def test_create_employee_rejects_branch_mandate_mismatch(self) -> None:
        other_branch = Branch(
            id="44444444-4444-4444-4444-444444444444",
            tenant_id=self.repository.tenant_id,
            code="CGN",
            name="Cologne",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        other_mandate = Mandate(
            id="55555555-5555-5555-5555-555555555555",
            tenant_id=self.repository.tenant_id,
            branch_id=other_branch.id,
            code="M-002",
            name="Cologne Mandate",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.repository.branches[other_branch.id] = other_branch
        self.repository.mandates[other_mandate.id] = other_mandate

        with self.assertRaises(ApiException) as ctx:
            self.service.create_employee(
                "tenant-1",
                EmployeeOperationalCreate(
                    tenant_id="tenant-1",
                    personnel_no="EMP-1005J",
                    first_name="Timo",
                    last_name="Kern",
                    default_branch_id=self.repository.branch_id,
                    default_mandate_id=other_mandate.id,
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.message_key, "errors.employees.employee.mandate_branch_mismatch")

    def test_archive_reactivate_is_non_destructive_and_hidden_by_default(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-2001",
                first_name="Eva",
                last_name="Kurz",
                user_id=self.repository.user_id,
            ),
            _context("employees.employee.write"),
        )
        assignment = UserRoleAssignment(
            id="assignment-1",
            tenant_id="tenant-1",
            user_account_id=self.repository.user_id,
            role_id=self.repository.employee_role.id,
            scope_type="tenant",
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
        )
        assignment_key = f"tenant-1:{self.repository.user_id}:employee_user"
        self.repository.role_assignments[assignment_key] = assignment

        archived = self.service.archive_employee(
            "tenant-1",
            employee.id,
            EmployeeLifecycleTransitionRequest(version_no=employee.version_no),
            _context("employees.employee.write"),
        )
        self.assertEqual(self.repository.role_assignments[assignment_key].status, "inactive")
        visible_default = self.service.list_operational_employees("tenant-1", _context("employees.employee.read"))
        visible_all = self.service.list_operational_employees(
            "tenant-1",
            _context("employees.employee.read"),
            EmployeeFilter(include_archived=True),
        )
        reactivated = self.service.reactivate_employee(
            "tenant-1",
            employee.id,
            EmployeeLifecycleTransitionRequest(version_no=archived.version_no),
            _context("employees.employee.write"),
        )

        self.assertEqual(archived.status, "archived")
        self.assertIsNotNone(archived.archived_at)
        self.assertEqual(len([row for row in visible_default if row.id == employee.id]), 0)
        self.assertEqual(len([row for row in visible_all if row.id == employee.id]), 1)
        self.assertEqual(self.repository.role_assignments[assignment_key].status, "active")
        self.assertIsNone(reactivated.archived_at)
        self.assertEqual(reactivated.status, "active")

    def test_hr_sensitive_changes_emit_audit_events(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-3001",
                first_name="Nina",
                last_name="Hartmann",
            ),
            _context("employees.employee.write"),
        )
        profile = self.service.upsert_private_profile(
            "tenant-1",
            employee.id,
            EmployeePrivateProfileCreate(
                tenant_id="tenant-1",
                employee_id=employee.id,
                private_email="nina.private@example.com",
                tax_id="TAX-1",
            ),
            _context("employees.private.write"),
        )
        self.service.update_private_profile(
            "tenant-1",
            employee.id,
            EmployeePrivateProfileUpdate(
                private_email="nina.changed@example.com",
                tax_id="TAX-2",
                version_no=profile.version_no,
            ),
            _context("employees.private.write"),
        )

        event_types = [event.event_type for event in self.audit_events]
        self.assertIn("employees.employee.created", event_types)
        self.assertIn("employees.private_profile.created", event_types)
        self.assertIn("employees.private_profile.updated", event_types)

    def test_employee_notes_support_reminders_and_positive_activity(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1006",
                first_name="Finn",
                last_name="Haas",
            ),
            _context("employees.employee.write"),
        )

        reminder = self.service.create_note(
            "tenant-1",
            employee.id,
            EmployeeNoteCreate(
                tenant_id="tenant-1",
                employee_id=employee.id,
                note_type="reminder",
                title="Ausweis pruefen",
                body="Lichtbildausweis vor Einsatzbeginn pruefen",
                reminder_at=date(2026, 4, 1),
            ),
            _context("employees.employee.write"),
        )
        positive = self.service.create_note(
            "tenant-1",
            employee.id,
            EmployeeNoteCreate(
                tenant_id="tenant-1",
                employee_id=employee.id,
                note_type="positive_activity",
                title="Lob vom Kunden",
                body="Sehr gute Schichtuebergabe dokumentiert.",
            ),
            _context("employees.employee.write"),
        )
        updated = self.service.update_note(
            "tenant-1",
            employee.id,
            reminder.id,
            EmployeeNoteUpdate(version_no=reminder.version_no, completed_at=date(2026, 4, 2)),
            _context("employees.employee.write"),
        )

        notes = self.service.list_notes("tenant-1", employee.id, _context("employees.employee.read"))

        self.assertEqual(len(notes), 2)
        self.assertEqual(positive.note_type, "positive_activity")
        self.assertEqual(updated.completed_at, date(2026, 4, 2))

    def test_reminder_note_requires_reminder_date(self) -> None:
        employee = self.service.create_employee(
            "tenant-1",
            EmployeeOperationalCreate(
                tenant_id="tenant-1",
                personnel_no="EMP-1007",
                first_name="Greta",
                last_name="Wolf",
            ),
            _context("employees.employee.write"),
        )

        with self.assertRaises(ApiException) as ctx:
            self.service.create_note(
                "tenant-1",
                employee.id,
                EmployeeNoteCreate(
                    tenant_id="tenant-1",
                    employee_id=employee.id,
                    note_type="reminder",
                    title="Fehlt",
                ),
                _context("employees.employee.write"),
            )

        self.assertEqual(ctx.exception.message_key, "errors.employees.note.reminder_date_required")


if __name__ == "__main__":
    unittest.main()
