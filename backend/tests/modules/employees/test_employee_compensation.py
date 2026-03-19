from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint, UniqueConstraint

from app.db import Base
from app.errors import ApiException
from app.modules.core.models import Branch, Mandate
from app.modules.employees.compensation_service import EmployeeCompensationService
from app.modules.employees.models import (
    Employee,
    EmployeeAdvance,
    EmployeeAllowance,
    EmployeeIdCredential,
    EmployeeTimeAccount,
    EmployeeTimeAccountTxn,
    FunctionType,
    QualificationType,
)
from app.modules.employees.schemas import (
    EmployeeAdvanceCreate,
    EmployeeAdvanceUpdate,
    EmployeeAllowanceCreate,
    EmployeeAllowanceFilter,
    EmployeeAllowanceUpdate,
    EmployeeCredentialBadgeIssue,
    EmployeeCredentialCreate,
    EmployeeCredentialFilter,
    EmployeeCredentialUpdate,
    EmployeeTimeAccountCreate,
    EmployeeTimeAccountFilter,
    EmployeeTimeAccountTxnCreate,
)
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_models import Document, DocumentLink, DocumentVersion
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentRead, DocumentVersionCreate, DocumentVersionRead


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


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.audit_events: list[object] = []

    def create_login_event(self, payload):  # noqa: ANN001
        return payload

    def create_audit_event(self, payload):  # noqa: ANN001
        self.audit_events.append(payload)
        return payload


@dataclass
class FakeDocumentRepo:
    documents: list[Document] = field(default_factory=list)

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]:
        return [
            document
            for document in self.documents
            if document.tenant_id == tenant_id
            and any(link.owner_type == owner_type and link.owner_id == owner_id for link in document.links)
        ]


class FakeDocumentService:
    def __init__(self, repository: FakeDocumentRepo) -> None:
        self.repository = repository

    def create_document(self, tenant_id: str, payload: DocumentCreate, actor) -> DocumentRead:  # noqa: ANN001
        now = datetime.now(UTC)
        document = Document(
            id=f"document-{len(self.repository.documents) + 1}",
            tenant_id=tenant_id,
            title=payload.title,
            source_module=payload.source_module,
            source_label=payload.source_label,
            metadata_json=payload.metadata_json,
            current_version_no=0,
            status="active",
            created_at=now,
            updated_at=now,
            created_by_user_id=actor.user_id,
            updated_by_user_id=actor.user_id,
            version_no=1,
            versions=[],
            links=[],
        )
        self.repository.documents.append(document)
        return DocumentRead.model_validate(document)

    def add_document_version(self, tenant_id: str, document_id: str, payload: DocumentVersionCreate, actor) -> DocumentVersionRead:  # noqa: ANN001
        document = next(document for document in self.repository.documents if document.id == document_id and document.tenant_id == tenant_id)
        version_no = document.current_version_no + 1
        version = DocumentVersion(
            id=f"version-{document_id}-{version_no}",
            tenant_id=tenant_id,
            document_id=document_id,
            version_no=version_no,
            file_name=payload.file_name,
            content_type=payload.content_type,
            object_bucket="bucket",
            object_key=f"{document_id}/{version_no}",
            checksum_sha256="checksum",
            file_size_bytes=10,
            uploaded_by_user_id=actor.user_id,
            uploaded_at=datetime.now(UTC),
            is_revision_safe_pdf=False,
            metadata_json=payload.metadata_json,
        )
        document.versions.append(version)
        document.current_version_no = version_no
        document.updated_at = datetime.now(UTC)
        return DocumentVersionRead.model_validate(version)

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        document = next(document for document in self.repository.documents if document.id == document_id and document.tenant_id == tenant_id)
        link = DocumentLink(
            id=f"link-{document_id}-{len(document.links) + 1}",
            tenant_id=tenant_id,
            document_id=document_id,
            owner_type=payload.owner_type,
            owner_id=payload.owner_id,
            relation_type=payload.relation_type,
            label=payload.label,
            linked_by_user_id=actor.user_id,
            linked_at=datetime.now(UTC),
            metadata_json=payload.metadata_json,
        )
        document.links.append(link)
        return link


@dataclass
class FakeCompensationRepository:
    tenant_id: str = "tenant-1"
    branch_id: str = "branch-1"
    mandate_id: str = "mandate-1"
    employees: dict[str, Employee] = field(default_factory=dict)
    function_types: dict[str, FunctionType] = field(default_factory=dict)
    qualification_types: dict[str, QualificationType] = field(default_factory=dict)
    time_accounts: dict[str, EmployeeTimeAccount] = field(default_factory=dict)
    allowances: dict[str, EmployeeAllowance] = field(default_factory=dict)
    advances: dict[str, EmployeeAdvance] = field(default_factory=dict)
    credentials: dict[str, EmployeeIdCredential] = field(default_factory=dict)

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
        employee = Employee(
            id="employee-1",
            tenant_id=self.tenant_id,
            personnel_no="EMP-1001",
            first_name="Anna",
            last_name="Wagner",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.employees[employee.id] = employee
        self.function_types["function-1"] = FunctionType(
            id="function-1",
            tenant_id=self.tenant_id,
            code="SHIFT_LEAD",
            label="Schichtleitung",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
            is_active=True,
            planning_relevant=True,
        )
        self.qualification_types["qualification-1"] = QualificationType(
            id="qualification-1",
            tenant_id=self.tenant_id,
            code="GSSK",
            label="GSSK",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
            is_active=True,
            planning_relevant=True,
            compliance_relevant=True,
            expiry_required=False,
            proof_required=False,
        )

    @staticmethod
    def _stamp(row) -> None:  # noqa: ANN001
        now = datetime.now(UTC)
        if getattr(row, "id", None) is None:
            row.id = str(uuid4())
        if getattr(row, "created_at", None) is None:
            row.created_at = now
        row.updated_at = now
        if getattr(row, "version_no", None) is None:
            row.version_no = 1
        if getattr(row, "status", None) is None:
            row.status = "active"

    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None:
        row = self.employees.get(employee_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def get_function_type(self, tenant_id: str, function_type_id: str) -> FunctionType | None:
        row = self.function_types.get(function_type_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def get_qualification_type(self, tenant_id: str, qualification_type_id: str) -> QualificationType | None:
        row = self.qualification_types.get(qualification_type_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def list_time_accounts(self, tenant_id: str, filters: EmployeeTimeAccountFilter | None = None) -> list[EmployeeTimeAccount]:
        rows = [row for row in self.time_accounts.values() if row.tenant_id == tenant_id]
        if filters is not None:
            if filters.employee_id is not None:
                rows = [row for row in rows if row.employee_id == filters.employee_id]
            if filters.account_type is not None:
                rows = [row for row in rows if row.account_type == filters.account_type]
            if not filters.include_archived:
                rows = [row for row in rows if row.archived_at is None]
        return rows

    def get_time_account(self, tenant_id: str, account_id: str) -> EmployeeTimeAccount | None:
        row = self.time_accounts.get(account_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def find_time_account(self, tenant_id: str, employee_id: str, account_type: str) -> EmployeeTimeAccount | None:
        for row in self.time_accounts.values():
            if row.tenant_id == tenant_id and row.employee_id == employee_id and row.account_type == account_type:
                return row
        return None

    def create_time_account(self, row: EmployeeTimeAccount) -> EmployeeTimeAccount:
        self._stamp(row)
        row.transactions = []
        self.time_accounts[row.id] = row
        return row

    def update_time_account(self, row: EmployeeTimeAccount) -> EmployeeTimeAccount:
        self._stamp(row)
        self.time_accounts[row.id] = row
        return row

    def add_time_account_txn(self, row: EmployeeTimeAccountTxn) -> EmployeeTimeAccountTxn:
        if row.id is None:
            row.id = str(uuid4())
        if row.posted_at is None:
            row.posted_at = datetime.now(UTC)
        self.time_accounts[row.time_account_id].transactions.append(row)
        return row

    def list_allowances(self, tenant_id: str, filters: EmployeeAllowanceFilter | None = None) -> list[EmployeeAllowance]:
        rows = [row for row in self.allowances.values() if row.tenant_id == tenant_id]
        if filters is not None:
            if filters.employee_id is not None:
                rows = [row for row in rows if row.employee_id == filters.employee_id]
            if filters.basis_code is not None:
                rows = [row for row in rows if row.basis_code == filters.basis_code]
            if filters.function_type_id is not None:
                rows = [row for row in rows if row.function_type_id == filters.function_type_id]
            if filters.qualification_type_id is not None:
                rows = [row for row in rows if row.qualification_type_id == filters.qualification_type_id]
            if filters.active_on is not None:
                rows = [
                    row
                    for row in rows
                    if row.effective_from <= filters.active_on and (row.effective_until is None or row.effective_until >= filters.active_on)
                ]
            if not filters.include_archived:
                rows = [row for row in rows if row.archived_at is None]
        return rows

    def get_allowance(self, tenant_id: str, allowance_id: str) -> EmployeeAllowance | None:
        row = self.allowances.get(allowance_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_allowance(self, row: EmployeeAllowance) -> EmployeeAllowance:
        self._stamp(row)
        row.function_type = self.get_function_type(row.tenant_id, row.function_type_id) if row.function_type_id else None
        row.qualification_type = self.get_qualification_type(row.tenant_id, row.qualification_type_id) if row.qualification_type_id else None
        self.allowances[row.id] = row
        return row

    def update_allowance(self, row: EmployeeAllowance) -> EmployeeAllowance:
        self._stamp(row)
        row.function_type = self.get_function_type(row.tenant_id, row.function_type_id) if row.function_type_id else None
        row.qualification_type = self.get_qualification_type(row.tenant_id, row.qualification_type_id) if row.qualification_type_id else None
        self.allowances[row.id] = row
        return row

    def list_advances(self, tenant_id: str, filters: EmployeeAdvanceFilter | None = None) -> list[EmployeeAdvance]:
        rows = [row for row in self.advances.values() if row.tenant_id == tenant_id]
        if filters is not None:
            if filters.employee_id is not None:
                rows = [row for row in rows if row.employee_id == filters.employee_id]
            if filters.status is not None:
                rows = [row for row in rows if row.status == filters.status]
            if not filters.include_archived:
                rows = [row for row in rows if row.archived_at is None]
        return rows

    def get_advance(self, tenant_id: str, advance_id: str) -> EmployeeAdvance | None:
        row = self.advances.get(advance_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def find_advance_by_no(self, tenant_id: str, advance_no: str, *, exclude_id: str | None = None) -> EmployeeAdvance | None:
        for row in self.advances.values():
            if row.tenant_id == tenant_id and row.advance_no == advance_no and row.id != exclude_id:
                return row
        return None

    def create_advance(self, row: EmployeeAdvance) -> EmployeeAdvance:
        self._stamp(row)
        self.advances[row.id] = row
        return row

    def update_advance(self, row: EmployeeAdvance) -> EmployeeAdvance:
        self._stamp(row)
        self.advances[row.id] = row
        return row

    def list_credentials(self, tenant_id: str, filters: EmployeeCredentialFilter | None = None) -> list[EmployeeIdCredential]:
        rows = [row for row in self.credentials.values() if row.tenant_id == tenant_id]
        if filters is not None:
            if filters.employee_id is not None:
                rows = [row for row in rows if row.employee_id == filters.employee_id]
            if filters.credential_type is not None:
                rows = [row for row in rows if row.credential_type == filters.credential_type]
            if filters.status is not None:
                rows = [row for row in rows if row.status == filters.status]
            if filters.active_on is not None:
                rows = [row for row in rows if row.valid_from <= filters.active_on and (row.valid_until is None or row.valid_until >= filters.active_on)]
            if not filters.include_archived:
                rows = [row for row in rows if row.archived_at is None]
        return rows

    def get_credential(self, tenant_id: str, credential_id: str) -> EmployeeIdCredential | None:
        row = self.credentials.get(credential_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def find_credential_by_no(self, tenant_id: str, credential_no: str, *, exclude_id: str | None = None) -> EmployeeIdCredential | None:
        for row in self.credentials.values():
            if row.tenant_id == tenant_id and row.credential_no == credential_no and row.id != exclude_id:
                return row
        return None

    def find_credential_by_encoded_value(self, tenant_id: str, encoded_value: str, *, exclude_id: str | None = None) -> EmployeeIdCredential | None:
        for row in self.credentials.values():
            if row.tenant_id == tenant_id and row.encoded_value == encoded_value and row.id != exclude_id:
                return row
        return None

    def create_credential(self, row: EmployeeIdCredential) -> EmployeeIdCredential:
        self._stamp(row)
        self.credentials[row.id] = row
        return row

    def update_credential(self, row: EmployeeIdCredential) -> EmployeeIdCredential:
        self._stamp(row)
        self.credentials[row.id] = row
        return row


class EmployeeCompensationServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeCompensationRepository()
        self.document_repository = FakeDocumentRepo()
        self.audit_repository = RecordingAuditRepository()
        self.service = EmployeeCompensationService(
            repository=self.repository,
            document_repository=self.document_repository,
            document_service=FakeDocumentService(self.document_repository),
            audit_service=AuditService(self.audit_repository),
        )

    def test_time_account_transactions_are_append_only_and_balance_aggregates(self) -> None:
        account = self.service.create_time_account(
            "tenant-1",
            EmployeeTimeAccountCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                account_type="work_time",
            ),
            _context("employees.private.write"),
        )
        self.service.add_time_account_txn(
            "tenant-1",
            account.id,
            EmployeeTimeAccountTxnCreate(tenant_id="tenant-1", txn_type="opening", amount_minutes=120),
            _context("employees.private.write"),
        )
        self.service.add_time_account_txn(
            "tenant-1",
            account.id,
            EmployeeTimeAccountTxnCreate(tenant_id="tenant-1", txn_type="debit", amount_minutes=-30),
            _context("employees.private.write"),
        )

        listed = self.service.list_time_accounts(
            "tenant-1",
            EmployeeTimeAccountFilter(employee_id="employee-1"),
            _context("employees.private.read"),
        )
        self.assertEqual(listed[0].balance_minutes, 90)
        self.assertEqual(len(self.repository.time_accounts[account.id].transactions), 2)

    def test_allowance_overlap_is_blocked_for_same_basis_tuple(self) -> None:
        self.service.create_allowance(
            "tenant-1",
            EmployeeAllowanceCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                basis_code="NIGHT",
                amount=25,
                function_type_id="function-1",
                effective_from=date(2026, 1, 1),
                effective_until=date(2026, 1, 31),
            ),
            _context("employees.private.write"),
        )
        with self.assertRaises(ApiException) as raised:
            self.service.create_allowance(
                "tenant-1",
                EmployeeAllowanceCreate(
                    tenant_id="tenant-1",
                    employee_id="employee-1",
                    basis_code="NIGHT",
                    amount=30,
                    function_type_id="function-1",
                    effective_from=date(2026, 1, 15),
                    effective_until=date(2026, 2, 15),
                ),
                _context("employees.private.write"),
            )
        self.assertEqual(raised.exception.message_key, "errors.employees.allowance.overlap")

    def test_advance_lifecycle_tracks_outstanding_amount(self) -> None:
        advance = self.service.create_advance(
            "tenant-1",
            EmployeeAdvanceCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                advance_no="ADV-1",
                amount=500,
                requested_on=date(2026, 3, 1),
            ),
            _context("employees.private.write"),
        )
        updated = self.service.update_advance(
            "tenant-1",
            advance.id,
            EmployeeAdvanceUpdate(
                status="disbursed",
                outstanding_amount=200,
                disbursed_on=date(2026, 3, 3),
                version_no=advance.version_no,
            ),
            _context("employees.private.write"),
        )
        self.assertEqual(updated.status, "disbursed")
        self.assertEqual(updated.outstanding_amount, 200.0)

    def test_credentials_enforce_uniqueness_and_badge_output_uses_docs_service(self) -> None:
        credential = self.service.create_credential(
            "tenant-1",
            EmployeeCredentialCreate(
                tenant_id="tenant-1",
                employee_id="employee-1",
                credential_no="ID-100",
                credential_type="work_badge",
                encoded_value="QR-100",
                valid_from=date(2026, 1, 1),
            ),
            _context("employees.employee.write"),
        )
        with self.assertRaises(ApiException) as duplicate:
            self.service.create_credential(
                "tenant-1",
                EmployeeCredentialCreate(
                    tenant_id="tenant-1",
                    employee_id="employee-1",
                    credential_no="ID-100",
                    credential_type="work_badge",
                    encoded_value="QR-101",
                    valid_from=date(2026, 1, 1),
                ),
                _context("employees.employee.write"),
            )
        self.assertEqual(duplicate.exception.message_key, "errors.employees.credential.duplicate_no")

        badge = self.service.issue_badge_output(
            "tenant-1",
            credential.id,
            EmployeeCredentialBadgeIssue(title="Dienstausweis"),
            _context("employees.employee.write"),
        )
        self.assertEqual(badge.relation_type, "badge_output")
        self.assertEqual(self.document_repository.documents[0].links[0].owner_type, "hr.employee")

    def test_metadata_exposes_expected_constraints(self) -> None:
        time_account_table = Base.metadata.tables["hr.employee_time_account"]
        txn_table = Base.metadata.tables["hr.employee_time_account_txn"]
        credential_table = Base.metadata.tables["hr.employee_id_credential"]

        time_account_checks = {c.name for c in time_account_table.constraints if isinstance(c, CheckConstraint)}
        credential_uniques = {
            tuple(constraint.columns.keys())
            for constraint in credential_table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        txn_checks = {c.name for c in txn_table.constraints if isinstance(c, CheckConstraint)}

        self.assertIn("ck_employee_time_account_employee_time_account_type_valid", time_account_checks)
        self.assertIn("ck_employee_time_account_txn_employee_time_account_txn_type_valid", txn_checks)
        self.assertIn(("tenant_id", "credential_no"), credential_uniques)
        self.assertIn(("tenant_id", "encoded_value"), credential_uniques)


if __name__ == "__main__":
    unittest.main()
