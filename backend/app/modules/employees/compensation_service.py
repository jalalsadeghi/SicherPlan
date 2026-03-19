"""Service layer for employee time accounts, allowances, advances, and credentials."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol

from app.errors import ApiException
from app.modules.employees.models import (
    EMPLOYEE_ADVANCE_STATUSES,
    EMPLOYEE_CREDENTIAL_STATUSES,
    EMPLOYEE_CREDENTIAL_TYPES,
    EMPLOYEE_TIME_ACCOUNT_TXN_TYPES,
    EMPLOYEE_TIME_ACCOUNT_TYPES,
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
    EmployeeAdvanceFilter,
    EmployeeAdvanceRead,
    EmployeeAdvanceUpdate,
    EmployeeAllowanceCreate,
    EmployeeAllowanceFilter,
    EmployeeAllowanceRead,
    EmployeeAllowanceUpdate,
    EmployeeCredentialBadgeIssue,
    EmployeeCredentialBadgeRead,
    EmployeeCredentialCreate,
    EmployeeCredentialFilter,
    EmployeeCredentialRead,
    EmployeeCredentialUpdate,
    EmployeeDocumentListItemRead,
    EmployeeTimeAccountCreate,
    EmployeeTimeAccountFilter,
    EmployeeTimeAccountRead,
    EmployeeTimeAccountTxnCreate,
    EmployeeTimeAccountTxnRead,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext, enforce_scope
from app.modules.platform_services.docs_models import Document
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService


class EmployeeCompensationRepository(Protocol):
    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None: ...
    def get_function_type(self, tenant_id: str, function_type_id: str) -> FunctionType | None: ...
    def get_qualification_type(self, tenant_id: str, qualification_type_id: str) -> QualificationType | None: ...
    def list_time_accounts(self, tenant_id: str, filters: EmployeeTimeAccountFilter | None = None) -> list[EmployeeTimeAccount]: ...
    def get_time_account(self, tenant_id: str, account_id: str) -> EmployeeTimeAccount | None: ...
    def find_time_account(self, tenant_id: str, employee_id: str, account_type: str) -> EmployeeTimeAccount | None: ...
    def create_time_account(self, row: EmployeeTimeAccount) -> EmployeeTimeAccount: ...
    def update_time_account(self, row: EmployeeTimeAccount) -> EmployeeTimeAccount: ...
    def add_time_account_txn(self, row: EmployeeTimeAccountTxn) -> EmployeeTimeAccountTxn: ...
    def list_allowances(self, tenant_id: str, filters: EmployeeAllowanceFilter | None = None) -> list[EmployeeAllowance]: ...
    def get_allowance(self, tenant_id: str, allowance_id: str) -> EmployeeAllowance | None: ...
    def create_allowance(self, row: EmployeeAllowance) -> EmployeeAllowance: ...
    def update_allowance(self, row: EmployeeAllowance) -> EmployeeAllowance: ...
    def list_advances(self, tenant_id: str, filters: EmployeeAdvanceFilter | None = None) -> list[EmployeeAdvance]: ...
    def get_advance(self, tenant_id: str, advance_id: str) -> EmployeeAdvance | None: ...
    def find_advance_by_no(self, tenant_id: str, advance_no: str, *, exclude_id: str | None = None) -> EmployeeAdvance | None: ...
    def create_advance(self, row: EmployeeAdvance) -> EmployeeAdvance: ...
    def update_advance(self, row: EmployeeAdvance) -> EmployeeAdvance: ...
    def list_credentials(self, tenant_id: str, filters: EmployeeCredentialFilter | None = None) -> list[EmployeeIdCredential]: ...
    def get_credential(self, tenant_id: str, credential_id: str) -> EmployeeIdCredential | None: ...
    def find_credential_by_no(self, tenant_id: str, credential_no: str, *, exclude_id: str | None = None) -> EmployeeIdCredential | None: ...
    def find_credential_by_encoded_value(
        self,
        tenant_id: str,
        encoded_value: str,
        *,
        exclude_id: str | None = None,
    ) -> EmployeeIdCredential | None: ...
    def create_credential(self, row: EmployeeIdCredential) -> EmployeeIdCredential: ...
    def update_credential(self, row: EmployeeIdCredential) -> EmployeeIdCredential: ...


class EmployeeCompensationDocumentRepository(Protocol):
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]: ...


class EmployeeCompensationService:
    def __init__(
        self,
        *,
        repository: EmployeeCompensationRepository,
        document_repository: EmployeeCompensationDocumentRepository,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.document_repository = document_repository
        self.document_service = document_service
        self.audit_service = audit_service

    def list_time_accounts(
        self,
        tenant_id: str,
        filters: EmployeeTimeAccountFilter | None,
        context: RequestAuthorizationContext,
    ) -> list[EmployeeTimeAccountRead]:
        self._require_private_read(tenant_id, context)
        rows = self.repository.list_time_accounts(tenant_id, filters or EmployeeTimeAccountFilter())
        return [EmployeeTimeAccountRead(**self._time_account_to_read(row).model_dump()) for row in rows]

    def create_time_account(
        self,
        tenant_id: str,
        payload: EmployeeTimeAccountCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeTimeAccountRead:
        self._require_private_write(tenant_id, context)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "employees.time_account.tenant_mismatch", "errors.employees.time_account.tenant_mismatch")
        self._require_employee(tenant_id, payload.employee_id)
        if payload.account_type not in EMPLOYEE_TIME_ACCOUNT_TYPES:
            raise ApiException(400, "employees.time_account.invalid_type", "errors.employees.time_account.invalid_type")
        existing = self.repository.find_time_account(tenant_id, payload.employee_id, payload.account_type)
        if existing is not None:
            raise ApiException(409, "employees.time_account.duplicate", "errors.employees.time_account.duplicate")
        row = self.repository.create_time_account(
            EmployeeTimeAccount(
                tenant_id=tenant_id,
                employee_id=payload.employee_id,
                account_type=payload.account_type,
                unit_code=payload.unit_code,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(context, "employees.time_account.created", "hr.employee_time_account", row.id, tenant_id, after_json=self._time_account_snapshot(row))
        return self._time_account_to_read(row)

    def add_time_account_txn(
        self,
        tenant_id: str,
        account_id: str,
        payload: EmployeeTimeAccountTxnCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeTimeAccountTxnRead:
        self._require_private_write(tenant_id, context)
        account = self._require_time_account(tenant_id, account_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "employees.time_account_txn.tenant_mismatch", "errors.employees.time_account_txn.tenant_mismatch")
        if payload.txn_type not in EMPLOYEE_TIME_ACCOUNT_TXN_TYPES:
            raise ApiException(400, "employees.time_account_txn.invalid_type", "errors.employees.time_account_txn.invalid_type")
        txn = self.repository.add_time_account_txn(
            EmployeeTimeAccountTxn(
                tenant_id=tenant_id,
                time_account_id=account_id,
                txn_type=payload.txn_type,
                posted_at=payload.posted_at or datetime.now(UTC),
                amount_minutes=payload.amount_minutes,
                reference_type=self._normalize_optional(payload.reference_type),
                reference_id=payload.reference_id,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=context.user_id,
            )
        )
        self._record_event(
            context,
            "employees.time_account.transaction_posted",
            "hr.employee_time_account_txn",
            txn.id,
            tenant_id,
            after_json=self._time_account_txn_snapshot(txn),
            metadata_json={"time_account_id": account_id},
        )
        return EmployeeTimeAccountTxnRead.model_validate(txn)

    def list_allowances(
        self,
        tenant_id: str,
        filters: EmployeeAllowanceFilter | None,
        context: RequestAuthorizationContext,
    ) -> list[EmployeeAllowanceRead]:
        self._require_private_read(tenant_id, context)
        rows = self.repository.list_allowances(tenant_id, filters or EmployeeAllowanceFilter())
        return [EmployeeAllowanceRead.model_validate(row) for row in rows]

    def create_allowance(
        self,
        tenant_id: str,
        payload: EmployeeAllowanceCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAllowanceRead:
        self._require_private_write(tenant_id, context)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "employees.allowance.tenant_mismatch", "errors.employees.allowance.tenant_mismatch")
        self._require_employee(tenant_id, payload.employee_id)
        self._validate_allowance_target(tenant_id, payload.function_type_id, payload.qualification_type_id)
        self._validate_allowance_window(payload.effective_from, payload.effective_until)
        self._ensure_allowance_overlap_free(
            tenant_id,
            payload.employee_id,
            payload.basis_code,
            payload.function_type_id,
            payload.qualification_type_id,
            payload.effective_from,
            payload.effective_until,
            exclude_id=None,
        )
        row = self.repository.create_allowance(
            EmployeeAllowance(
                tenant_id=tenant_id,
                employee_id=payload.employee_id,
                basis_code=payload.basis_code,
                amount=Decimal(str(payload.amount)),
                currency_code=payload.currency_code.upper(),
                function_type_id=payload.function_type_id,
                qualification_type_id=payload.qualification_type_id,
                effective_from=payload.effective_from,
                effective_until=payload.effective_until,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(context, "employees.allowance.created", "hr.employee_allowance", row.id, tenant_id, after_json=self._allowance_snapshot(row))
        return EmployeeAllowanceRead.model_validate(row)

    def update_allowance(
        self,
        tenant_id: str,
        allowance_id: str,
        payload: EmployeeAllowanceUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAllowanceRead:
        self._require_private_write(tenant_id, context)
        row = self._require_allowance(tenant_id, allowance_id)
        before = self._allowance_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "allowance")
        next_basis = payload.basis_code if payload.basis_code is not None else row.basis_code
        next_function = payload.function_type_id if payload.function_type_id is not None else row.function_type_id
        next_qualification = payload.qualification_type_id if payload.qualification_type_id is not None else row.qualification_type_id
        next_from = payload.effective_from if payload.effective_from is not None else row.effective_from
        next_until = payload.effective_until if payload.effective_until is not None else row.effective_until
        self._validate_allowance_target(tenant_id, next_function, next_qualification)
        self._validate_allowance_window(next_from, next_until)
        self._ensure_allowance_overlap_free(
            tenant_id,
            row.employee_id,
            next_basis,
            next_function,
            next_qualification,
            next_from,
            next_until,
            exclude_id=allowance_id,
        )
        row.basis_code = next_basis
        if payload.amount is not None:
            row.amount = Decimal(str(payload.amount))
        if payload.currency_code is not None:
            row.currency_code = payload.currency_code.upper()
        row.function_type_id = next_function
        row.qualification_type_id = next_qualification
        row.effective_from = next_from
        row.effective_until = next_until
        row.notes = self._effective_optional(payload.notes, row.notes)
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_allowance(row)
        self._record_event(context, "employees.allowance.updated", "hr.employee_allowance", allowance_id, tenant_id, before_json=before, after_json=self._allowance_snapshot(updated))
        return EmployeeAllowanceRead.model_validate(updated)

    def list_advances(self, tenant_id: str, filters: EmployeeAdvanceFilter | None, context: RequestAuthorizationContext) -> list[EmployeeAdvanceRead]:
        self._require_private_read(tenant_id, context)
        return [EmployeeAdvanceRead.model_validate(row) for row in self.repository.list_advances(tenant_id, filters or EmployeeAdvanceFilter())]

    def create_advance(
        self,
        tenant_id: str,
        payload: EmployeeAdvanceCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAdvanceRead:
        self._require_private_write(tenant_id, context)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "employees.advance.tenant_mismatch", "errors.employees.advance.tenant_mismatch")
        self._require_employee(tenant_id, payload.employee_id)
        if self.repository.find_advance_by_no(tenant_id, payload.advance_no) is not None:
            raise ApiException(409, "employees.advance.duplicate_no", "errors.employees.advance.duplicate_no")
        amount = Decimal(str(payload.amount))
        row = self.repository.create_advance(
            EmployeeAdvance(
                tenant_id=tenant_id,
                employee_id=payload.employee_id,
                advance_no=payload.advance_no,
                amount=amount,
                outstanding_amount=amount,
                currency_code=payload.currency_code.upper(),
                requested_on=payload.requested_on,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(context, "employees.advance.created", "hr.employee_advance", row.id, tenant_id, after_json=self._advance_snapshot(row))
        return EmployeeAdvanceRead.model_validate(row)

    def update_advance(
        self,
        tenant_id: str,
        advance_id: str,
        payload: EmployeeAdvanceUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAdvanceRead:
        self._require_private_write(tenant_id, context)
        row = self._require_advance(tenant_id, advance_id)
        before = self._advance_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "advance")
        if payload.status is not None:
            if payload.status not in EMPLOYEE_ADVANCE_STATUSES:
                raise ApiException(400, "employees.advance.invalid_status", "errors.employees.advance.invalid_status")
            row.status = payload.status
        if payload.outstanding_amount is not None:
            row.outstanding_amount = Decimal(str(payload.outstanding_amount))
        if payload.disbursed_on is not None:
            row.disbursed_on = payload.disbursed_on
        if payload.settled_on is not None:
            row.settled_on = payload.settled_on
        row.notes = self._effective_optional(payload.notes, row.notes)
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_advance(row)
        self._record_event(context, "employees.advance.updated", "hr.employee_advance", advance_id, tenant_id, before_json=before, after_json=self._advance_snapshot(updated))
        return EmployeeAdvanceRead.model_validate(updated)

    def list_credentials(self, tenant_id: str, filters: EmployeeCredentialFilter | None, context: RequestAuthorizationContext) -> list[EmployeeCredentialRead]:
        self._require_employee_read(tenant_id, context)
        return [EmployeeCredentialRead.model_validate(row) for row in self.repository.list_credentials(tenant_id, filters or EmployeeCredentialFilter())]

    def create_credential(
        self,
        tenant_id: str,
        payload: EmployeeCredentialCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeCredentialRead:
        self._require_employee_write(tenant_id, context)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "employees.credential.tenant_mismatch", "errors.employees.credential.tenant_mismatch")
        self._require_employee(tenant_id, payload.employee_id)
        self._validate_credential_shape(payload.credential_type, payload.valid_from, payload.valid_until)
        self._ensure_credential_unique(tenant_id, payload.credential_no, payload.encoded_value)
        row = self.repository.create_credential(
            EmployeeIdCredential(
                tenant_id=tenant_id,
                employee_id=payload.employee_id,
                credential_no=payload.credential_no,
                credential_type=payload.credential_type,
                encoded_value=payload.encoded_value,
                valid_from=payload.valid_from,
                valid_until=payload.valid_until,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(context, "employees.credential.created", "hr.employee_id_credential", row.id, tenant_id, after_json=self._credential_snapshot(row))
        return EmployeeCredentialRead.model_validate(row)

    def update_credential(
        self,
        tenant_id: str,
        credential_id: str,
        payload: EmployeeCredentialUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeCredentialRead:
        self._require_employee_write(tenant_id, context)
        row = self._require_credential(tenant_id, credential_id)
        before = self._credential_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "credential")
        next_encoded = payload.encoded_value if payload.encoded_value is not None else row.encoded_value
        next_from = payload.valid_from if payload.valid_from is not None else row.valid_from
        next_until = payload.valid_until if payload.valid_until is not None else row.valid_until
        self._validate_credential_shape(row.credential_type, next_from, next_until)
        self._ensure_credential_unique(tenant_id, row.credential_no, next_encoded, exclude_id=credential_id)
        row.encoded_value = next_encoded
        row.valid_from = next_from
        row.valid_until = next_until
        row.notes = self._effective_optional(payload.notes, row.notes)
        if payload.status is not None:
            if payload.status not in EMPLOYEE_CREDENTIAL_STATUSES:
                raise ApiException(400, "employees.credential.invalid_status", "errors.employees.credential.invalid_status")
            row.status = payload.status
            now = datetime.now(UTC)
            if payload.status == "issued":
                row.issued_at = now
                row.revoked_at = None
            elif payload.status in {"revoked", "expired"}:
                row.revoked_at = now
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_credential(row)
        self._record_event(context, "employees.credential.updated", "hr.employee_id_credential", credential_id, tenant_id, before_json=before, after_json=self._credential_snapshot(updated))
        return EmployeeCredentialRead.model_validate(updated)

    def issue_badge_output(
        self,
        tenant_id: str,
        credential_id: str,
        payload: EmployeeCredentialBadgeIssue,
        context: RequestAuthorizationContext,
    ) -> EmployeeCredentialBadgeRead:
        self._require_employee_write(tenant_id, context)
        credential = self._require_credential(tenant_id, credential_id)
        employee = self._require_employee(tenant_id, credential.employee_id)
        title = (payload.title or "").strip() or f"Badge {credential.credential_no}"
        badge_content = "\n".join(
            [
                f"credential_no={credential.credential_no}",
                f"employee_id={employee.id}",
                f"name={employee.first_name} {employee.last_name}",
                f"credential_type={credential.credential_type}",
                f"encoded_value={credential.encoded_value}",
                f"valid_from={credential.valid_from.isoformat()}",
                f"valid_until={credential.valid_until.isoformat() if credential.valid_until else ''}",
            ]
        ).encode("utf-8")
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=title,
                source_module="employees",
                source_label="id_badge_output",
                metadata_json={"employee_id": employee.id, "credential_id": credential_id},
            ),
            context,
        )
        self.document_service.add_document_version(
            tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=f"{credential.credential_no}.txt",
                content_type="text/plain",
                content_base64=base64.b64encode(badge_content).decode("ascii"),
                metadata_json={"credential_id": credential_id, "kind": "badge_output"},
            ),
            context,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type="hr.employee",
                owner_id=employee.id,
                relation_type="badge_output",
                label=title,
                metadata_json={"credential_id": credential_id},
            ),
            context,
        )
        proof_document = next(
            doc
            for doc in self.document_repository.list_documents_for_owner(tenant_id, "hr.employee", employee.id)
            if doc.id == document.id
        )
        self._record_event(
            context,
            "employees.credential.badge_generated",
            "hr.employee_id_credential",
            credential_id,
            tenant_id,
            metadata_json={"document_id": document.id, "employee_id": employee.id},
        )
        return EmployeeCredentialBadgeRead(**self._map_document(proof_document).model_dump())

    def _time_account_to_read(self, row: EmployeeTimeAccount) -> EmployeeTimeAccountRead:
        balance = sum(txn.amount_minutes for txn in row.transactions)
        return EmployeeTimeAccountRead(
            id=row.id,
            tenant_id=row.tenant_id,
            employee_id=row.employee_id,
            account_type=row.account_type,
            unit_code=row.unit_code,
            notes=row.notes,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
            archived_at=row.archived_at,
            version_no=row.version_no,
            balance_minutes=balance,
        )

    def _ensure_allowance_overlap_free(
        self,
        tenant_id: str,
        employee_id: str,
        basis_code: str,
        function_type_id: str | None,
        qualification_type_id: str | None,
        effective_from: date,
        effective_until: date | None,
        *,
        exclude_id: str | None,
    ) -> None:
        rows = self.repository.list_allowances(
            tenant_id,
            EmployeeAllowanceFilter(
                employee_id=employee_id,
                basis_code=basis_code,
                function_type_id=function_type_id,
                qualification_type_id=qualification_type_id,
                include_archived=False,
            ),
        )
        for row in rows:
            if row.id == exclude_id:
                continue
            row_end = row.effective_until or date.max
            next_end = effective_until or date.max
            if row.effective_from <= next_end and effective_from <= row_end:
                raise ApiException(409, "employees.allowance.overlap", "errors.employees.allowance.overlap")

    def _validate_allowance_target(self, tenant_id: str, function_type_id: str | None, qualification_type_id: str | None) -> None:
        if function_type_id is not None and self.repository.get_function_type(tenant_id, function_type_id) is None:
            raise ApiException(404, "employees.function_type.not_found", "errors.employees.function_type.not_found")
        if qualification_type_id is not None and self.repository.get_qualification_type(tenant_id, qualification_type_id) is None:
            raise ApiException(404, "employees.qualification_type.not_found", "errors.employees.qualification_type.not_found")

    @staticmethod
    def _validate_allowance_window(effective_from: date, effective_until: date | None) -> None:
        if effective_until is not None and effective_until < effective_from:
            raise ApiException(400, "employees.allowance.invalid_window", "errors.employees.allowance.invalid_window")

    def _validate_credential_shape(self, credential_type: str, valid_from: date, valid_until: date | None) -> None:
        if credential_type not in EMPLOYEE_CREDENTIAL_TYPES:
            raise ApiException(400, "employees.credential.invalid_type", "errors.employees.credential.invalid_type")
        if valid_until is not None and valid_until < valid_from:
            raise ApiException(400, "employees.credential.invalid_window", "errors.employees.credential.invalid_window")

    def _ensure_credential_unique(
        self,
        tenant_id: str,
        credential_no: str,
        encoded_value: str,
        *,
        exclude_id: str | None = None,
    ) -> None:
        if self.repository.find_credential_by_no(tenant_id, credential_no, exclude_id=exclude_id) is not None:
            raise ApiException(409, "employees.credential.duplicate_no", "errors.employees.credential.duplicate_no")
        if self.repository.find_credential_by_encoded_value(tenant_id, encoded_value, exclude_id=exclude_id) is not None:
            raise ApiException(409, "employees.credential.duplicate_encoded_value", "errors.employees.credential.duplicate_encoded_value")

    def _require_employee(self, tenant_id: str, employee_id: str) -> Employee:
        employee = self.repository.get_employee(tenant_id, employee_id)
        if employee is None:
            raise ApiException(404, "employees.employee.not_found", "errors.employees.employee.not_found")
        return employee

    def _require_time_account(self, tenant_id: str, account_id: str) -> EmployeeTimeAccount:
        row = self.repository.get_time_account(tenant_id, account_id)
        if row is None:
            raise ApiException(404, "employees.time_account.not_found", "errors.employees.time_account.not_found")
        return row

    def _require_allowance(self, tenant_id: str, allowance_id: str) -> EmployeeAllowance:
        row = self.repository.get_allowance(tenant_id, allowance_id)
        if row is None:
            raise ApiException(404, "employees.allowance.not_found", "errors.employees.allowance.not_found")
        return row

    def _require_advance(self, tenant_id: str, advance_id: str) -> EmployeeAdvance:
        row = self.repository.get_advance(tenant_id, advance_id)
        if row is None:
            raise ApiException(404, "employees.advance.not_found", "errors.employees.advance.not_found")
        return row

    def _require_credential(self, tenant_id: str, credential_id: str) -> EmployeeIdCredential:
        row = self.repository.get_credential(tenant_id, credential_id)
        if row is None:
            raise ApiException(404, "employees.credential.not_found", "errors.employees.credential.not_found")
        return row

    def _require_employee_read(self, tenant_id: str, context: RequestAuthorizationContext) -> None:
        if "employees.employee.read" not in context.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied", {"permission_key": "employees.employee.read"})
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)

    def _require_employee_write(self, tenant_id: str, context: RequestAuthorizationContext) -> None:
        if "employees.employee.write" not in context.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied", {"permission_key": "employees.employee.write"})
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)

    def _require_private_read(self, tenant_id: str, context: RequestAuthorizationContext) -> None:
        if "employees.private.read" not in context.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied", {"permission_key": "employees.private.read"})
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)

    def _require_private_write(self, tenant_id: str, context: RequestAuthorizationContext) -> None:
        if "employees.private.write" not in context.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied", {"permission_key": "employees.private.write"})
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)

    @staticmethod
    def _require_version(current: int, incoming: int | None, resource: str) -> None:
        if incoming is None or incoming != current:
            raise ApiException(409, f"employees.{resource}.stale_version", f"errors.employees.{resource}.stale_version")

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @staticmethod
    def _effective_optional(value: str | None, current: str | None) -> str | None:
        if value is None:
            return current
        value = value.strip()
        return value or None

    def _record_event(
        self,
        context: RequestAuthorizationContext,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        *,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=tenant_id,
                user_id=context.user_id,
                session_id=context.session_id,
                request_id=context.request_id,
            ),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=after_json,
            metadata_json=metadata_json,
        )

    @staticmethod
    def _map_document(document: Document) -> EmployeeDocumentListItemRead:
        latest_version = max(document.versions, key=lambda version: version.version_no) if document.versions else None
        employee_links = [link for link in document.links if link.owner_type == "hr.employee"]
        employee_links.sort(key=lambda link: link.linked_at, reverse=True)
        link = employee_links[0] if employee_links else None
        return EmployeeDocumentListItemRead(
            document_id=document.id,
            relation_type=link.relation_type if link else "badge_output",
            label=link.label if link else None,
            title=document.title,
            document_type_key=document.document_type.key if document.document_type else None,
            file_name=latest_version.file_name if latest_version else None,
            content_type=latest_version.content_type if latest_version else None,
            current_version_no=document.current_version_no if document.current_version_no > 0 else None,
            linked_at=link.linked_at if link else None,
        )

    @staticmethod
    def _time_account_snapshot(row: EmployeeTimeAccount) -> dict[str, object]:
        return {"employee_id": row.employee_id, "account_type": row.account_type, "unit_code": row.unit_code, "version_no": row.version_no}

    @staticmethod
    def _time_account_txn_snapshot(row: EmployeeTimeAccountTxn) -> dict[str, object]:
        return {"time_account_id": row.time_account_id, "txn_type": row.txn_type, "amount_minutes": row.amount_minutes, "posted_at": row.posted_at.isoformat()}

    @staticmethod
    def _allowance_snapshot(row: EmployeeAllowance) -> dict[str, object]:
        return {"employee_id": row.employee_id, "basis_code": row.basis_code, "amount": str(row.amount), "function_type_id": row.function_type_id, "qualification_type_id": row.qualification_type_id, "effective_from": row.effective_from.isoformat(), "effective_until": row.effective_until.isoformat() if row.effective_until else None, "version_no": row.version_no}

    @staticmethod
    def _advance_snapshot(row: EmployeeAdvance) -> dict[str, object]:
        return {"employee_id": row.employee_id, "advance_no": row.advance_no, "amount": str(row.amount), "outstanding_amount": str(row.outstanding_amount), "status": row.status, "version_no": row.version_no}

    @staticmethod
    def _credential_snapshot(row: EmployeeIdCredential) -> dict[str, object]:
        return {"employee_id": row.employee_id, "credential_no": row.credential_no, "credential_type": row.credential_type, "encoded_value": row.encoded_value, "status": row.status, "valid_from": row.valid_from.isoformat(), "valid_until": row.valid_until.isoformat() if row.valid_until else None, "version_no": row.version_no}
