"""Employee import/export and IAM access-link coordination."""

from __future__ import annotations

import base64
import csv
import io
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.employees.models import Employee
from app.modules.employees.schemas import (
    EmployeeAccessAttachExistingRequest,
    EmployeeAccessCreateUserRequest,
    EmployeeAccessDetachRequest,
    EmployeeAccessLinkRead,
    EmployeeAccessResetPasswordRequest,
    EmployeeAccessUpdateUserRequest,
    EmployeeExportRequest,
    EmployeeExportResult,
    EmployeeFilter,
    EmployeeImportDryRunRequest,
    EmployeeImportDryRunResult,
    EmployeeImportExecuteRequest,
    EmployeeImportExecuteResult,
    EmployeeImportRowResult,
    EmployeeOperationalCreate,
    EmployeeOperationalUpdate,
)
from app.modules.employees.service import EmployeeService
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext, enforce_scope
from app.modules.iam.models import Role, UserAccount, UserRoleAssignment
from app.modules.iam.security import hash_password
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.integration_models import ImportExportJob


IMPORT_HEADERS = (
    "personnel_no",
    "first_name",
    "last_name",
    "preferred_name",
    "work_email",
    "work_phone",
    "mobile_phone",
    "default_branch_id",
    "default_mandate_id",
    "hire_date",
    "termination_date",
    "status",
    "user_id",
    "notes",
)


class EmployeeOpsRepository(Protocol):
    def list_employees(self, tenant_id: str, filters: EmployeeFilter | None = None) -> list[Employee]: ...
    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None: ...
    def find_employee_by_personnel_no(
        self,
        tenant_id: str,
        personnel_no: str,
        *,
        exclude_id: str | None = None,
    ) -> Employee | None: ...
    def find_employee_by_user_id(
        self,
        tenant_id: str,
        user_id: str,
        *,
        exclude_id: str | None = None,
    ) -> Employee | None: ...
    def get_user_account(self, tenant_id: str, user_id: str) -> UserAccount | None: ...
    def find_user_account_by_username(self, tenant_id: str, username: str) -> UserAccount | None: ...
    def find_user_account_by_email(self, tenant_id: str, email: str) -> UserAccount | None: ...
    def create_user_account(self, row: UserAccount) -> UserAccount: ...
    def update_user_account(self, row: UserAccount) -> UserAccount: ...
    def revoke_active_sessions_for_user(self, user_id: str, *, reason: str, at_time: datetime) -> None: ...
    def get_role_by_key(self, role_key: str) -> Role | None: ...
    def find_role_assignment(self, tenant_id: str, user_id: str, role_key: str) -> UserRoleAssignment | None: ...
    def create_role_assignment(self, row: UserRoleAssignment) -> UserRoleAssignment: ...
    def update_role_assignment(self, row: UserRoleAssignment) -> UserRoleAssignment: ...
    def create_job(self, row: ImportExportJob) -> ImportExportJob: ...
    def save_job(self, row: ImportExportJob) -> ImportExportJob: ...


@dataclass(slots=True)
class ParsedImportRow:
    row_no: int
    data: dict[str, str]


class EmployeeOpsService:
    def __init__(
        self,
        *,
        employee_service: EmployeeService,
        repository: EmployeeOpsRepository,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.employee_service = employee_service
        self.repository = repository
        self.document_service = document_service
        self.audit_service = audit_service

    def import_dry_run(
        self,
        tenant_id: str,
        payload: EmployeeImportDryRunRequest,
        actor: RequestAuthorizationContext,
    ) -> EmployeeImportDryRunResult:
        self._require_write_access(actor, tenant_id)
        self._ensure_payload_tenant(tenant_id, payload.tenant_id)
        rows = self._parse_import_csv(payload.csv_content_base64)
        results = [self._validate_import_row(tenant_id, row) for row in rows]
        invalid_rows = sum(1 for row in results if row.status == "invalid")
        self._record_event(
            actor,
            event_type="employees.import.dry_run_requested",
            entity_type="hr.employee_import",
            entity_id=tenant_id,
            tenant_id=tenant_id,
            metadata_json={"row_count": len(rows), "invalid_rows": invalid_rows},
        )
        return EmployeeImportDryRunResult(
            tenant_id=tenant_id,
            total_rows=len(results),
            valid_rows=len(results) - invalid_rows,
            invalid_rows=invalid_rows,
            rows=results,
        )

    def execute_import(
        self,
        tenant_id: str,
        payload: EmployeeImportExecuteRequest,
        actor: RequestAuthorizationContext,
    ) -> EmployeeImportExecuteResult:
        self._require_write_access(actor, tenant_id)
        self._ensure_payload_tenant(tenant_id, payload.tenant_id)
        rows = self._parse_import_csv(payload.csv_content_base64)
        job = self.repository.create_job(
            ImportExportJob(
                tenant_id=tenant_id,
                endpoint_id=None,
                job_direction="import",
                job_type="employees.employee_csv",
                request_payload_json={"row_count": len(rows), "continue_on_error": payload.continue_on_error},
                requested_by_user_id=actor.user_id,
                status="started",
                started_at=datetime.now(UTC),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        row_results: list[EmployeeImportRowResult] = []
        counts = {"created_employees": 0, "updated_employees": 0, "linked_users": 0}
        for row in rows:
            preview = self._validate_import_row(tenant_id, row)
            if preview.status == "invalid":
                row_results.append(preview)
                if not payload.continue_on_error:
                    break
                continue
            try:
                result = self._execute_import_row(tenant_id, row, actor)
            except ApiException as exc:
                row_results.append(
                    EmployeeImportRowResult(
                        row_no=row.row_no,
                        personnel_no=row.data.get("personnel_no") or None,
                        status="invalid",
                        messages=[exc.code],
                    )
                )
                if not payload.continue_on_error:
                    break
                continue
            row_results.append(result)
            for key in counts:
                counts[key] += int(key in result.messages)

        invalid_rows = sum(1 for row in row_results if row.status == "invalid")
        report_document_id = self._create_result_document(
            tenant_id=tenant_id,
            actor=actor,
            owner_id=job.id,
            file_name=f"employees-import-{job.id}.csv",
            title="Employee import result",
            source_label="employee-import-result",
            content=self._build_import_result_csv(row_results).encode("utf-8"),
        )
        job.completed_at = datetime.now(UTC)
        job.status = "completed"
        job.error_summary = None if invalid_rows == 0 else f"Import completed with {invalid_rows} invalid rows."
        job.result_summary_json = {
            "total_rows": len(row_results),
            "invalid_rows": invalid_rows,
            "report_document_id": report_document_id,
        }
        job.version_no += 1
        job.updated_by_user_id = actor.user_id
        self.repository.save_job(job)
        self._record_event(
            actor,
            event_type="employees.import.executed",
            entity_type="integration.import_export_job",
            entity_id=job.id,
            tenant_id=tenant_id,
            metadata_json={"invalid_rows": invalid_rows, "report_document_id": report_document_id},
        )
        return EmployeeImportExecuteResult(
            tenant_id=tenant_id,
            job_id=job.id,
            job_status=job.status,
            total_rows=len(row_results),
            invalid_rows=invalid_rows,
            result_document_ids=[report_document_id],
            rows=row_results,
            **counts,
        )

    def export_employees(
        self,
        tenant_id: str,
        payload: EmployeeExportRequest,
        actor: RequestAuthorizationContext,
    ) -> EmployeeExportResult:
        self._require_read_access(actor, tenant_id)
        self._ensure_payload_tenant(tenant_id, payload.tenant_id)
        rows = self.repository.list_employees(
            tenant_id,
            EmployeeFilter(search=payload.search, include_archived=payload.include_archived),
        )
        job = self.repository.create_job(
            ImportExportJob(
                tenant_id=tenant_id,
                endpoint_id=None,
                job_direction="export",
                job_type="employees.employee_csv",
                request_payload_json={"search": payload.search, "include_archived": payload.include_archived},
                requested_by_user_id=actor.user_id,
                status="started",
                started_at=datetime.now(UTC),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        csv_content, row_count = self._build_export_csv(rows)
        document_id = self._create_result_document(
            tenant_id=tenant_id,
            actor=actor,
            owner_id=job.id,
            file_name=f"employees-export-{job.id}.csv",
            title="Employee export",
            source_label="employee-export",
            content=csv_content.encode("utf-8"),
        )
        job.completed_at = datetime.now(UTC)
        job.status = "completed"
        job.result_summary_json = {"row_count": row_count, "document_id": document_id}
        job.version_no += 1
        job.updated_by_user_id = actor.user_id
        self.repository.save_job(job)
        self._record_event(
            actor,
            event_type="employees.export.executed",
            entity_type="integration.import_export_job",
            entity_id=job.id,
            tenant_id=tenant_id,
            metadata_json={"row_count": row_count, "document_id": document_id},
        )
        return EmployeeExportResult(
            tenant_id=tenant_id,
            job_id=job.id,
            document_id=document_id,
            file_name=f"employees-export-{job.id}.csv",
            row_count=row_count,
        )

    def get_access_link(
        self,
        tenant_id: str,
        employee_id: str,
        actor: RequestAuthorizationContext,
    ) -> EmployeeAccessLinkRead:
        self._require_write_access(actor, tenant_id)
        employee = self._require_employee(tenant_id, employee_id)
        return self._build_access_link_read(employee)

    def create_access_user(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeAccessCreateUserRequest,
        actor: RequestAuthorizationContext,
    ) -> EmployeeAccessLinkRead:
        self._require_write_access(actor, tenant_id)
        self._ensure_payload_tenant(tenant_id, payload.tenant_id)
        employee = self._require_employee(tenant_id, employee_id)
        if employee.user_id:
            raise ApiException(409, "employees.access.already_linked", "errors.employees.access.already_linked")
        username = payload.username.strip()
        email = payload.email.strip().lower()
        if self.repository.find_user_account_by_username(tenant_id, username) is not None:
            raise ApiException(409, "employees.access.username_taken", "errors.employees.access.username_taken")
        if self.repository.find_user_account_by_email(tenant_id, email) is not None:
            raise ApiException(409, "employees.access.email_taken", "errors.employees.access.email_taken")
        full_name = (payload.full_name or f"{employee.first_name} {employee.last_name}").strip()
        user = self.repository.create_user_account(
            UserAccount(
                tenant_id=tenant_id,
                username=username,
                email=email,
                full_name=full_name,
                password_hash=hash_password(payload.password),
                locale=(payload.locale or "de").strip() or "de",
                timezone=(payload.timezone or "Europe/Berlin").strip() or "Europe/Berlin",
                is_platform_user=False,
                is_password_login_enabled=True,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        linked = self._link_user_to_employee(employee, user, actor)
        self._record_event(
            actor,
            event_type="employees.access.user_created_and_linked",
            entity_type="hr.employee",
            entity_id=employee_id,
            tenant_id=tenant_id,
            after_json={"user_id": linked.user_id, "username": linked.username, "app_access_enabled": linked.app_access_enabled},
        )
        return linked

    def update_access_user(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeAccessUpdateUserRequest,
        actor: RequestAuthorizationContext,
    ) -> EmployeeAccessLinkRead:
        self._require_write_access(actor, tenant_id)
        self._ensure_payload_tenant(tenant_id, payload.tenant_id)
        employee = self._require_employee(tenant_id, employee_id)
        user = self._require_linked_user(employee)
        username = payload.username.strip()
        email = payload.email.strip().lower()
        full_name = payload.full_name.strip()
        if not full_name:
            raise ApiException(400, "employees.access.full_name_required", "errors.employees.access.full_name_required")
        username_owner = self.repository.find_user_account_by_username(tenant_id, username)
        if username_owner is not None and username_owner.id != user.id:
            raise ApiException(409, "employees.access.username_taken", "errors.employees.access.username_taken")
        email_owner = self.repository.find_user_account_by_email(tenant_id, email)
        if email_owner is not None and email_owner.id != user.id:
            raise ApiException(409, "employees.access.email_taken", "errors.employees.access.email_taken")
        before = self._build_access_link_read(employee)
        user.username = username
        user.email = email
        user.full_name = full_name
        user.updated_by_user_id = actor.user_id
        updated_user = self.repository.update_user_account(user)
        result = self._build_access_link_read(self._require_employee(tenant_id, employee_id))
        self._record_event(
            actor,
            event_type="employees.access.user_updated",
            entity_type="hr.employee",
            entity_id=employee_id,
            tenant_id=tenant_id,
            before_json={
                "user_id": before.user_id,
                "username": before.username,
                "email": before.email,
                "full_name": before.full_name,
            },
            after_json={
                "user_id": updated_user.id,
                "username": updated_user.username,
                "email": updated_user.email,
                "full_name": updated_user.full_name,
            },
        )
        return result

    def reset_access_user_password(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeAccessResetPasswordRequest,
        actor: RequestAuthorizationContext,
    ) -> EmployeeAccessLinkRead:
        self._require_write_access(actor, tenant_id)
        self._ensure_payload_tenant(tenant_id, payload.tenant_id)
        employee = self._require_employee(tenant_id, employee_id)
        user = self._require_linked_user(employee)
        user.password_hash = hash_password(payload.password)
        user.updated_by_user_id = actor.user_id
        self.repository.update_user_account(user)
        self.repository.revoke_active_sessions_for_user(
            user.id,
            reason="employee_access_password_reset",
            at_time=datetime.now(UTC),
        )
        result = self._build_access_link_read(self._require_employee(tenant_id, employee_id))
        self._record_event(
            actor,
            event_type="employees.access.password_reset",
            entity_type="hr.employee",
            entity_id=employee_id,
            tenant_id=tenant_id,
            after_json={"user_id": result.user_id, "username": result.username},
        )
        return result

    def attach_existing_user(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeAccessAttachExistingRequest,
        actor: RequestAuthorizationContext,
    ) -> EmployeeAccessLinkRead:
        self._require_write_access(actor, tenant_id)
        self._ensure_payload_tenant(tenant_id, payload.tenant_id)
        employee = self._require_employee(tenant_id, employee_id)
        user = self._resolve_attach_user(tenant_id, payload)
        linked = self._link_user_to_employee(employee, user, actor)
        self._record_event(
            actor,
            event_type="employees.access.user_attached",
            entity_type="hr.employee",
            entity_id=employee_id,
            tenant_id=tenant_id,
            after_json={"user_id": linked.user_id, "username": linked.username, "app_access_enabled": linked.app_access_enabled},
        )
        return linked

    def detach_access_user(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeAccessDetachRequest,
        actor: RequestAuthorizationContext,
    ) -> EmployeeAccessLinkRead:
        self._require_write_access(actor, tenant_id)
        self._ensure_payload_tenant(tenant_id, payload.tenant_id)
        employee = self._require_employee(tenant_id, employee_id)
        if not employee.user_id:
            return self._build_access_link_read(employee)
        assignment = self.repository.find_role_assignment(tenant_id, employee.user_id, "employee_user")
        if assignment is not None:
            assignment.status = "inactive"
            assignment.archived_at = datetime.now(UTC)
            assignment.updated_by_user_id = actor.user_id
            assignment.version_no += 1
            self.repository.update_role_assignment(assignment)
        previous_user_id = employee.user_id
        employee.user_id = None
        employee.updated_by_user_id = actor.user_id
        employee.version_no += 1
        updated = self.repository.update_employee(employee)
        result = self._build_access_link_read(updated)
        self._record_event(
            actor,
            event_type="employees.access.user_detached",
            entity_type="hr.employee",
            entity_id=employee_id,
            tenant_id=tenant_id,
            before_json={"user_id": previous_user_id},
            after_json={"user_id": None, "app_access_enabled": False},
        )
        return result

    def reconcile_access_user(
        self,
        tenant_id: str,
        employee_id: str,
        actor: RequestAuthorizationContext,
    ) -> EmployeeAccessLinkRead:
        self._require_write_access(actor, tenant_id)
        employee = self._require_employee(tenant_id, employee_id)
        if not employee.user_id:
            return self._build_access_link_read(employee)
        user = self.repository.get_user_account(tenant_id, employee.user_id)
        if user is None:
            raise ApiException(404, "employees.user.not_found", "errors.employees.user.not_found")
        self._ensure_employee_user_assignment(tenant_id, user.id, actor)
        refreshed = self._require_employee(tenant_id, employee_id)
        result = self._build_access_link_read(refreshed)
        self._record_event(
            actor,
            event_type="employees.access.user_reconciled",
            entity_type="hr.employee",
            entity_id=employee_id,
            tenant_id=tenant_id,
            after_json={"user_id": result.user_id, "app_access_enabled": result.app_access_enabled},
        )
        return result

    def _validate_import_row(self, tenant_id: str, row: ParsedImportRow) -> EmployeeImportRowResult:
        messages: list[str] = []
        personnel_no = (row.data.get("personnel_no") or "").strip()
        if not personnel_no:
            messages.append("employees.import.personnel_no_required")
        if not (row.data.get("first_name") or "").strip():
            messages.append("employees.import.first_name_required")
        if not (row.data.get("last_name") or "").strip():
            messages.append("employees.import.last_name_required")
        branch_id = (row.data.get("default_branch_id") or "").strip()
        mandate_id = (row.data.get("default_mandate_id") or "").strip()
        user_id = (row.data.get("user_id") or "").strip()
        hire_date = (row.data.get("hire_date") or "").strip()
        termination_date = (row.data.get("termination_date") or "").strip()

        if branch_id and self.employee_service.repository.get_branch(tenant_id, branch_id) is None:
            messages.append("errors.employees.employee.branch_not_found")
        if mandate_id:
            mandate = self.employee_service.repository.get_mandate(tenant_id, mandate_id)
            if mandate is None:
                messages.append("errors.employees.employee.mandate_not_found")
            elif branch_id and mandate.branch_id != branch_id:
                messages.append("errors.employees.employee.mandate_branch_mismatch")
        if user_id:
            user = self.repository.get_user_account(tenant_id, user_id)
            if user is None:
                messages.append("errors.employees.user.not_found")
            else:
                duplicate_employee = self.repository.find_employee_by_user_id(tenant_id, user_id)
                if duplicate_employee is not None and duplicate_employee.personnel_no != personnel_no:
                    messages.append("errors.employees.employee.duplicate_user_link")
        parsed_hire_date = self._parse_date(hire_date, "employees.import.invalid_hire_date", messages)
        parsed_termination_date = self._parse_date(
            termination_date,
            "employees.import.invalid_termination_date",
            messages,
        )
        if parsed_hire_date and parsed_termination_date and parsed_termination_date < parsed_hire_date:
            messages.append("errors.employees.employee.invalid_dates")
        return EmployeeImportRowResult(
            row_no=row.row_no,
            personnel_no=personnel_no or None,
            status="invalid" if messages else "valid",
            messages=messages or ["employees.import.valid"],
        )

    def _execute_import_row(
        self,
        tenant_id: str,
        row: ParsedImportRow,
        actor: RequestAuthorizationContext,
    ) -> EmployeeImportRowResult:
        personnel_no = row.data["personnel_no"].strip()
        existing = self.repository.find_employee_by_personnel_no(tenant_id, personnel_no)
        payload = EmployeeOperationalCreate(
            tenant_id=tenant_id,
            personnel_no=personnel_no,
            first_name=row.data["first_name"].strip(),
            last_name=row.data["last_name"].strip(),
            preferred_name=self._empty_to_none(row.data.get("preferred_name")),
            work_email=self._empty_to_none(row.data.get("work_email")),
            work_phone=self._empty_to_none(row.data.get("work_phone")),
            mobile_phone=self._empty_to_none(row.data.get("mobile_phone")),
            default_branch_id=self._empty_to_none(row.data.get("default_branch_id")),
            default_mandate_id=self._empty_to_none(row.data.get("default_mandate_id")),
            hire_date=self._parse_date(row.data.get("hire_date") or "", "employees.import.invalid_hire_date", []),
            termination_date=self._parse_date(
                row.data.get("termination_date") or "",
                "employees.import.invalid_termination_date",
                [],
            ),
            user_id=self._empty_to_none(row.data.get("user_id")),
            notes=self._empty_to_none(row.data.get("notes")),
        )
        messages: list[str] = []
        if existing is None:
            employee = self.employee_service.create_employee(tenant_id, payload, actor)
            messages.append("created_employees")
            status_value = self._empty_to_none(row.data.get("status"))
            if status_value and status_value != employee.status:
                employee = self.employee_service.update_employee(
                    tenant_id,
                    employee.id,
                    EmployeeOperationalUpdate(status=status_value, version_no=employee.version_no),
                    actor,
                )
        else:
            employee = self.employee_service.update_employee(
                tenant_id,
                existing.id,
                EmployeeOperationalUpdate(
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
                    user_id=payload.user_id,
                    notes=payload.notes,
                    status=self._empty_to_none(row.data.get("status")) or existing.status,
                    version_no=existing.version_no,
                ),
                actor,
            )
            messages.append("updated_employees")
        if payload.user_id:
            self._ensure_employee_user_assignment(tenant_id, payload.user_id, actor)
            messages.append("linked_users")
        return EmployeeImportRowResult(
            row_no=row.row_no,
            personnel_no=payload.personnel_no,
            employee_id=employee.id,
            status="applied",
            messages=messages,
        )

    def _build_export_csv(self, employees: list[Employee]) -> tuple[str, int]:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "personnel_no",
                "first_name",
                "last_name",
                "preferred_name",
                "work_email",
                "work_phone",
                "mobile_phone",
                "default_branch_id",
                "default_mandate_id",
                "hire_date",
                "termination_date",
                "status",
                "user_id",
                "app_access_enabled",
            ]
        )
        for employee in employees:
            writer.writerow(
                [
                    employee.personnel_no,
                    employee.first_name,
                    employee.last_name,
                    employee.preferred_name or "",
                    employee.work_email or "",
                    employee.work_phone or "",
                    employee.mobile_phone or "",
                    employee.default_branch_id or "",
                    employee.default_mandate_id or "",
                    employee.hire_date.isoformat() if employee.hire_date else "",
                    employee.termination_date.isoformat() if employee.termination_date else "",
                    employee.status,
                    employee.user_id or "",
                    "true" if employee.user_id else "false",
                ]
            )
        return buffer.getvalue(), len(employees)

    def _build_import_result_csv(self, rows: list[EmployeeImportRowResult]) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["row_no", "personnel_no", "status", "employee_id", "messages"])
        for row in rows:
            writer.writerow([row.row_no, row.personnel_no or "", row.status, row.employee_id or "", "|".join(row.messages)])
        return buffer.getvalue()

    def _parse_import_csv(self, content_base64: str) -> list[ParsedImportRow]:
        try:
            content = base64.b64decode(content_base64).decode("utf-8-sig")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ApiException(400, "employees.import.invalid_csv", "errors.employees.import.invalid_csv") from exc
        reader = csv.DictReader(io.StringIO(content))
        if reader.fieldnames is None:
            raise ApiException(400, "employees.import.invalid_csv", "errors.employees.import.invalid_csv")
        headers = tuple(name.strip() for name in reader.fieldnames)
        if headers != IMPORT_HEADERS:
            raise ApiException(400, "employees.import.invalid_headers", "errors.employees.import.invalid_headers")
        rows: list[ParsedImportRow] = []
        for index, data in enumerate(reader, start=2):
            rows.append(
                ParsedImportRow(
                    row_no=index,
                    data={key: (value or "").strip() for key, value in data.items() if key is not None},
                )
            )
        return rows

    def _resolve_attach_user(self, tenant_id: str, payload: EmployeeAccessAttachExistingRequest) -> UserAccount:
        match_count = sum(bool(value and str(value).strip()) for value in (payload.user_id, payload.username, payload.email))
        if match_count != 1:
            raise ApiException(
                400,
                "employees.access.ambiguous_match",
                "errors.employees.access.ambiguous_match",
            )
        user = None
        if payload.user_id:
            user = self.repository.get_user_account(tenant_id, payload.user_id.strip())
        elif payload.username:
            user = self.repository.find_user_account_by_username(tenant_id, payload.username.strip())
        elif payload.email:
            user = self.repository.find_user_account_by_email(tenant_id, payload.email.strip().lower())
        if user is None:
            raise ApiException(404, "employees.user.not_found", "errors.employees.user.not_found")
        return user

    def _require_linked_user(self, employee: Employee) -> UserAccount:
        if not employee.user_id:
            raise ApiException(409, "employees.access.not_linked", "errors.employees.access.not_linked")
        user = self.repository.get_user_account(employee.tenant_id, employee.user_id)
        if user is None:
            raise ApiException(404, "employees.user.not_found", "errors.employees.user.not_found")
        return user

    def _link_user_to_employee(
        self,
        employee: Employee,
        user: UserAccount,
        actor: RequestAuthorizationContext,
    ) -> EmployeeAccessLinkRead:
        if employee.user_id and employee.user_id != user.id:
            raise ApiException(409, "employees.access.already_linked", "errors.employees.access.already_linked")
        duplicate = self.repository.find_employee_by_user_id(employee.tenant_id, user.id, exclude_id=employee.id)
        if duplicate is not None:
            raise ApiException(409, "employees.employee.duplicate_user_link", "errors.employees.employee.duplicate_user_link")
        employee.user_id = user.id
        employee.updated_by_user_id = actor.user_id
        employee.version_no += 1
        updated = self.repository.update_employee(employee)
        self._ensure_employee_user_assignment(employee.tenant_id, user.id, actor)
        return self._build_access_link_read(updated)

    def _ensure_employee_user_assignment(self, tenant_id: str, user_id: str, actor: RequestAuthorizationContext) -> None:
        role = self.repository.get_role_by_key("employee_user")
        if role is None:
            raise ApiException(500, "employees.access.role_missing", "errors.employees.access.role_missing")
        assignment = self.repository.find_role_assignment(tenant_id, user_id, "employee_user")
        if assignment is None:
            self.repository.create_role_assignment(
                UserRoleAssignment(
                    tenant_id=tenant_id,
                    user_account_id=user_id,
                    role_id=role.id,
                    scope_type="tenant",
                    created_by_user_id=actor.user_id,
                    updated_by_user_id=actor.user_id,
                )
            )
            return
        assignment.status = "active"
        assignment.archived_at = None
        assignment.updated_by_user_id = actor.user_id
        assignment.version_no += 1
        self.repository.update_role_assignment(assignment)

    def _build_access_link_read(self, employee: Employee) -> EmployeeAccessLinkRead:
        user = None
        active_assignment = None
        if employee.user_id:
            user = self.repository.get_user_account(employee.tenant_id, employee.user_id)
            if user is not None:
                active_assignment = self.repository.find_role_assignment(employee.tenant_id, user.id, "employee_user")
        return EmployeeAccessLinkRead(
            employee_id=employee.id,
            tenant_id=employee.tenant_id,
            user_id=user.id if user else None,
            username=user.username if user else None,
            email=user.email if user else None,
            full_name=user.full_name if user else None,
            app_access_enabled=bool(user and user.is_password_login_enabled and active_assignment and active_assignment.archived_at is None),
            role_assignment_active=bool(active_assignment and active_assignment.archived_at is None and active_assignment.status == "active"),
        )

    def _create_result_document(
        self,
        *,
        tenant_id: str,
        actor: RequestAuthorizationContext,
        owner_id: str,
        file_name: str,
        title: str,
        source_label: str,
        content: bytes,
    ) -> str:
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=title,
                source_module="employees",
                source_label=source_label,
                metadata_json={},
            ),
            actor,
        )
        self.document_service.add_document_version(
            tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=file_name,
                content_type="text/csv",
                content_base64=base64.b64encode(content).decode("ascii"),
                metadata_json={},
            ),
            actor,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type="integration.import_export_job",
                owner_id=owner_id,
                relation_type="generated_output",
                label=title,
                metadata_json={},
            ),
            actor,
        )
        return document.id

    def _require_employee(self, tenant_id: str, employee_id: str) -> Employee:
        employee = self.repository.get_employee(tenant_id, employee_id)
        if employee is None:
            raise ApiException(404, "employees.employee.not_found", "errors.employees.employee.not_found")
        return employee

    def _require_read_access(self, actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if "employees.employee.read" not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
        enforce_scope(actor, scope="tenant", tenant_id=tenant_id)

    def _require_write_access(self, actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if "employees.employee.write" not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
        enforce_scope(actor, scope="tenant", tenant_id=tenant_id)

    @staticmethod
    def _ensure_payload_tenant(tenant_id: str, payload_tenant_id: str) -> None:
        if tenant_id != payload_tenant_id:
            raise ApiException(400, "employees.employee.tenant_mismatch", "errors.employees.employee.tenant_mismatch")

    @staticmethod
    def _parse_date(value: str, message: str, messages: list[str]) -> date | None:
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text).date()
        except ValueError:
            messages.append(message)
            return None

    @staticmethod
    def _empty_to_none(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=tenant_id,
                user_id=actor.user_id,
                session_id=actor.session_id,
                request_id=actor.request_id,
            ),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=after_json,
            metadata_json=metadata_json,
        )
