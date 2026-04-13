"""Service-layer guards and validations for employee operational/private separation."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime
from typing import Protocol
from uuid import UUID

from app.errors import ApiException
from app.modules.core.models import Address, Branch, Mandate
from app.modules.core.schemas import LookupValueRead
from app.modules.employees.models import (
    EMPLOYEE_ADDRESS_TYPES,
    EMPLOYEE_NOTE_TYPES,
    Employee,
    EmployeeAddressHistory,
    EmployeeGroup,
    EmployeeGroupMember,
    EmployeeNote,
    EmployeePrivateProfile,
)
from app.modules.employees.schemas import (
    EmployeeAddressHistoryCreate,
    EmployeeAddressHistoryRead,
    EmployeeAddressHistoryUpdate,
    EmployeeAddressWriteAddress,
    EmployeeFilter,
    EmployeeGroupCreate,
    EmployeeGroupMemberCreate,
    EmployeeGroupMemberRead,
    EmployeeGroupMemberUpdate,
    EmployeeGroupRead,
    EmployeeGroupUpdate,
    EmployeeListItem,
    EmployeeNoteCreate,
    EmployeeNoteRead,
    EmployeeNoteUpdate,
    EmployeeOperationalCreate,
    EmployeeOperationalRead,
    EmployeeOperationalUpdate,
    EmployeeLifecycleTransitionRequest,
    EmployeePrivateProfileCreate,
    EmployeePrivateProfileRead,
    EmployeePrivateProfileUpdate,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext, enforce_scope
from app.modules.iam.models import UserAccount, UserRoleAssignment


class EmployeeRepository(Protocol):
    def list_employees(self, tenant_id: str, filters: EmployeeFilter | None = None) -> list[Employee]: ...
    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None: ...
    def update_employee(self, row: Employee) -> Employee: ...
    def get_employee_private_profile(self, tenant_id: str, employee_id: str) -> EmployeePrivateProfile | None: ...
    def list_employee_address_history(self, tenant_id: str, employee_id: str) -> list[EmployeeAddressHistory]: ...
    def get_employee_address_history(
        self,
        tenant_id: str,
        employee_id: str,
        history_id: str,
    ) -> EmployeeAddressHistory | None: ...
    def list_groups(self, tenant_id: str) -> list[EmployeeGroup]: ...
    def get_group(self, tenant_id: str, group_id: str) -> EmployeeGroup | None: ...
    def get_group_member(self, tenant_id: str, member_id: str) -> EmployeeGroupMember | None: ...
    def list_notes(self, tenant_id: str, employee_id: str) -> list[EmployeeNote]: ...
    def get_note(self, tenant_id: str, employee_id: str, note_id: str) -> EmployeeNote | None: ...
    def create_employee(self, row: Employee) -> Employee: ...
    def create_private_profile(self, row: EmployeePrivateProfile) -> EmployeePrivateProfile: ...
    def update_private_profile(self, row: EmployeePrivateProfile) -> EmployeePrivateProfile: ...
    def create_address_history(self, row: EmployeeAddressHistory) -> EmployeeAddressHistory: ...
    def update_address_history(self, row: EmployeeAddressHistory) -> EmployeeAddressHistory: ...
    def create_group(self, row: EmployeeGroup) -> EmployeeGroup: ...
    def update_group(self, row: EmployeeGroup) -> EmployeeGroup: ...
    def create_group_member(self, row: EmployeeGroupMember) -> EmployeeGroupMember: ...
    def update_group_member(self, row: EmployeeGroupMember) -> EmployeeGroupMember: ...
    def create_note(self, row: EmployeeNote) -> EmployeeNote: ...
    def update_note(self, row: EmployeeNote) -> EmployeeNote: ...
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
    def find_group_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> EmployeeGroup | None: ...
    def get_user_account(self, tenant_id: str, user_id: str) -> UserAccount | None: ...
    def find_role_assignment(self, tenant_id: str, user_id: str, role_key: str) -> UserRoleAssignment | None: ...
    def update_role_assignment(self, row: UserRoleAssignment) -> UserRoleAssignment: ...
    def get_branch(self, tenant_id: str, branch_id: str) -> Branch | None: ...
    def get_mandate(self, tenant_id: str, mandate_id: str) -> Mandate | None: ...
    def get_address(self, address_id: str) -> Address | None: ...
    def create_address(self, row: Address) -> Address: ...
    def list_lookup_values(self, tenant_id: str, domain: str) -> list[LookupValueRead]: ...


class EmployeeService:
    def __init__(self, repository: EmployeeRepository, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_operational_employees(
        self,
        tenant_id: str,
        context: RequestAuthorizationContext,
        filters: EmployeeFilter | None = None,
    ) -> list[EmployeeListItem]:
        self._require_permission(context, "employees.employee.read")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        rows = self.repository.list_employees(tenant_id, filters or EmployeeFilter())
        return [EmployeeListItem.model_validate(row) for row in rows]

    def get_operational_employee(
        self,
        tenant_id: str,
        employee_id: str,
        context: RequestAuthorizationContext,
    ) -> EmployeeOperationalRead:
        self._require_permission(context, "employees.employee.read")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        row = self._require_employee(tenant_id, employee_id)
        return EmployeeOperationalRead.model_validate(row)

    def create_employee(
        self,
        tenant_id: str,
        payload: EmployeeOperationalCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeOperationalRead:
        self._require_permission(context, "employees.employee.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "employees.employee.tenant_mismatch", "errors.employees.employee.tenant_mismatch")
        normalized = self._normalize_employee_create(payload)
        self._validate_employee_payload(tenant_id, normalized)
        row = self.repository.create_employee(
            Employee(
                tenant_id=tenant_id,
                personnel_no=normalized.personnel_no,
                first_name=normalized.first_name,
                last_name=normalized.last_name,
                preferred_name=normalized.preferred_name,
                work_email=normalized.work_email,
                work_phone=normalized.work_phone,
                mobile_phone=normalized.mobile_phone,
                default_branch_id=normalized.default_branch_id,
                default_mandate_id=normalized.default_mandate_id,
                hire_date=normalized.hire_date,
                termination_date=normalized.termination_date,
                employment_type_code=normalized.employment_type_code,
                target_weekly_hours=normalized.target_weekly_hours,
                target_monthly_hours=normalized.target_monthly_hours,
                user_id=normalized.user_id,
                notes=normalized.notes,
                status=normalized.status or "active",
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(
            context,
            event_type="employees.employee.created",
            entity_type="hr.employee",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._employee_snapshot(row),
        )
        return EmployeeOperationalRead.model_validate(row)

    def update_employee(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeOperationalUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeOperationalRead:
        self._require_permission(context, "employees.employee.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        row = self._require_employee(tenant_id, employee_id)
        before = self._employee_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "employee")

        next_personnel_no = self._effective_text(payload.personnel_no, row.personnel_no)
        next_first_name = self._effective_text(payload.first_name, row.first_name)
        next_last_name = self._effective_text(payload.last_name, row.last_name)
        next_preferred_name = self._effective_optional(payload.preferred_name, row.preferred_name)
        next_work_email = self._effective_optional(payload.work_email, row.work_email)
        next_work_phone = self._effective_optional(payload.work_phone, row.work_phone)
        next_mobile_phone = self._effective_optional(payload.mobile_phone, row.mobile_phone)
        next_user_id = self._normalize_user_id(payload.user_id) if payload.user_id is not None else row.user_id
        next_branch_id = self._normalize_branch_id(payload.default_branch_id) if payload.default_branch_id is not None else row.default_branch_id
        next_mandate_id = (
            self._normalize_mandate_id(payload.default_mandate_id) if payload.default_mandate_id is not None else row.default_mandate_id
        )
        next_hire_date = payload.hire_date if payload.hire_date is not None else row.hire_date
        next_termination_date = payload.termination_date if payload.termination_date is not None else row.termination_date
        next_employment_type_code = (
            self._normalize_optional(payload.employment_type_code)
            if payload.employment_type_code is not None
            else row.employment_type_code
        )
        next_target_weekly_hours = (
            self._normalize_target_hours(payload.target_weekly_hours, "weekly")
            if payload.target_weekly_hours is not None
            else row.target_weekly_hours
        )
        next_target_monthly_hours = (
            self._normalize_target_hours(payload.target_monthly_hours, "monthly")
            if payload.target_monthly_hours is not None
            else row.target_monthly_hours
        )
        next_notes = self._effective_optional(payload.notes, row.notes)

        self._validate_employee_payload(
            tenant_id,
            EmployeeOperationalCreate(
                tenant_id=tenant_id,
                personnel_no=next_personnel_no,
                first_name=next_first_name,
                last_name=next_last_name,
                preferred_name=next_preferred_name,
                work_email=next_work_email,
                work_phone=next_work_phone,
                mobile_phone=next_mobile_phone,
                default_branch_id=next_branch_id,
                default_mandate_id=next_mandate_id,
                hire_date=next_hire_date,
                termination_date=next_termination_date,
                status=payload.status or row.status,
                employment_type_code=next_employment_type_code,
                target_weekly_hours=next_target_weekly_hours,
                target_monthly_hours=next_target_monthly_hours,
                user_id=next_user_id,
                notes=next_notes,
            ),
            exclude_id=employee_id,
        )

        row.personnel_no = next_personnel_no
        row.first_name = next_first_name
        row.last_name = next_last_name
        row.preferred_name = next_preferred_name
        row.work_email = next_work_email
        row.work_phone = next_work_phone
        row.mobile_phone = next_mobile_phone
        row.default_branch_id = next_branch_id
        row.default_mandate_id = next_mandate_id
        row.hire_date = next_hire_date
        row.termination_date = next_termination_date
        row.employment_type_code = next_employment_type_code
        row.target_weekly_hours = next_target_weekly_hours
        row.target_monthly_hours = next_target_monthly_hours
        row.user_id = next_user_id
        row.notes = next_notes
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        self._normalize_employee_lifecycle(row)
        self._sync_archived_employee_access(row, context)
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_employee(row)
        after = self._employee_snapshot(updated)
        event_type = "employees.employee.updated"
        if before.get("status") != after.get("status") or before.get("archived_at") != after.get("archived_at"):
            event_type = "employees.employee.lifecycle_changed"
        elif before.get("user_id") != after.get("user_id"):
            event_type = "employees.employee.access_link_changed"
        self._record_event(
            context,
            event_type=event_type,
            entity_type="hr.employee",
            entity_id=employee_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=after,
        )
        return EmployeeOperationalRead.model_validate(updated)

    def get_private_profile(
        self,
        tenant_id: str,
        employee_id: str,
        context: RequestAuthorizationContext,
    ) -> EmployeePrivateProfileRead:
        self._require_permission(context, "employees.private.read")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        self._require_employee(tenant_id, employee_id)
        row = self.repository.get_employee_private_profile(tenant_id, employee_id)
        if row is None:
            raise ApiException(404, "employees.private_profile.not_found", "errors.employees.private_profile.not_found")
        return EmployeePrivateProfileRead.model_validate(row)

    def list_private_profile_marital_status_options(
        self,
        tenant_id: str,
        context: RequestAuthorizationContext,
    ) -> list[LookupValueRead]:
        self._require_permission(context, "employees.private.read")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        return self.repository.list_lookup_values(tenant_id, "marital_status")

    def upsert_private_profile(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeePrivateProfileCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeePrivateProfileRead:
        self._require_permission(context, "employees.private.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        self._require_employee(tenant_id, employee_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "employees.private_profile.tenant_mismatch",
                "errors.employees.private_profile.tenant_mismatch",
            )
        if payload.employee_id != employee_id:
            raise ApiException(
                400,
                "employees.private_profile.employee_mismatch",
                "errors.employees.private_profile.employee_mismatch",
            )
        existing = self.repository.get_employee_private_profile(tenant_id, employee_id)
        if existing is None:
            row = self.repository.create_private_profile(
                EmployeePrivateProfile(
                    tenant_id=tenant_id,
                    employee_id=employee_id,
                    private_email=self._normalize_optional(payload.private_email),
                    private_phone=self._normalize_optional(payload.private_phone),
                    birth_date=payload.birth_date,
                    place_of_birth=self._normalize_optional(payload.place_of_birth),
                    nationality_country_code=self._normalize_optional(payload.nationality_country_code),
                    marital_status_code=self._normalize_optional(payload.marital_status_code),
                    tax_id=self._normalize_optional(payload.tax_id),
                    social_security_no=self._normalize_optional(payload.social_security_no),
                    bank_account_holder=self._normalize_optional(payload.bank_account_holder),
                    bank_iban=self._normalize_optional(payload.bank_iban),
                    bank_bic=self._normalize_optional(payload.bank_bic),
                    emergency_contact_name=self._normalize_optional(payload.emergency_contact_name),
                    emergency_contact_phone=self._normalize_optional(payload.emergency_contact_phone),
                    notes=self._normalize_optional(payload.notes),
                    created_by_user_id=context.user_id,
                    updated_by_user_id=context.user_id,
                )
            )
            self._record_event(
                context,
                event_type="employees.private_profile.created",
                entity_type="hr.employee_private_profile",
                entity_id=row.id,
                tenant_id=tenant_id,
                after_json=self._private_profile_snapshot(row),
                metadata_json={"employee_id": employee_id},
            )
            return EmployeePrivateProfileRead.model_validate(row)

        updated = self._apply_private_profile_update(existing, payload, context)
        return EmployeePrivateProfileRead.model_validate(updated)

    def update_private_profile(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeePrivateProfileUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeePrivateProfileRead:
        self._require_permission(context, "employees.private.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        self._require_employee(tenant_id, employee_id)
        row = self.repository.get_employee_private_profile(tenant_id, employee_id)
        if row is None:
            raise ApiException(404, "employees.private_profile.not_found", "errors.employees.private_profile.not_found")
        before = self._private_profile_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "private_profile")
        row.private_email = self._effective_optional(payload.private_email, row.private_email)
        row.private_phone = self._effective_optional(payload.private_phone, row.private_phone)
        row.birth_date = payload.birth_date if payload.birth_date is not None else row.birth_date
        row.place_of_birth = self._effective_optional(payload.place_of_birth, row.place_of_birth)
        row.nationality_country_code = self._effective_optional(
            payload.nationality_country_code,
            row.nationality_country_code,
        )
        row.marital_status_code = self._effective_optional(payload.marital_status_code, row.marital_status_code)
        row.tax_id = self._effective_optional(payload.tax_id, row.tax_id)
        row.social_security_no = self._effective_optional(payload.social_security_no, row.social_security_no)
        row.bank_account_holder = self._effective_optional(payload.bank_account_holder, row.bank_account_holder)
        row.bank_iban = self._effective_optional(payload.bank_iban, row.bank_iban)
        row.bank_bic = self._effective_optional(payload.bank_bic, row.bank_bic)
        row.emergency_contact_name = self._effective_optional(payload.emergency_contact_name, row.emergency_contact_name)
        row.emergency_contact_phone = self._effective_optional(
            payload.emergency_contact_phone,
            row.emergency_contact_phone,
        )
        row.notes = self._effective_optional(payload.notes, row.notes)
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_private_profile(row)
        self._record_event(
            context,
            event_type="employees.private_profile.updated",
            entity_type="hr.employee_private_profile",
            entity_id=row.id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._private_profile_snapshot(updated),
            metadata_json={"employee_id": employee_id},
        )
        return EmployeePrivateProfileRead.model_validate(updated)

    def list_address_history(
        self,
        tenant_id: str,
        employee_id: str,
        context: RequestAuthorizationContext,
    ) -> list[EmployeeAddressHistoryRead]:
        self._require_permission(context, "employees.private.read")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        self._require_employee(tenant_id, employee_id)
        rows = self.repository.list_employee_address_history(tenant_id, employee_id)
        return [EmployeeAddressHistoryRead.model_validate(row) for row in rows]

    def add_address_history(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeAddressHistoryCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAddressHistoryRead:
        self._require_permission(context, "employees.private.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        self._require_employee(tenant_id, employee_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "employees.address_history.tenant_mismatch",
                "errors.employees.address_history.tenant_mismatch",
            )
        if payload.employee_id != employee_id:
            raise ApiException(
                400,
                "employees.address_history.employee_mismatch",
                "errors.employees.address_history.employee_mismatch",
            )
        resolved_address_id = self._resolve_address_id(payload.address_id, payload.address)
        self._validate_address_history_payload(
            tenant_id,
            employee_id,
            resolved_address_id,
            payload.address_type,
            payload.valid_from,
            payload.valid_to,
        )
        row = self.repository.create_address_history(
            EmployeeAddressHistory(
                tenant_id=tenant_id,
                employee_id=employee_id,
                address_id=resolved_address_id,
                address_type=payload.address_type,
                valid_from=payload.valid_from,
                valid_to=payload.valid_to,
                is_primary=payload.is_primary,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        self._record_event(
            context,
            event_type="employees.address_history.created",
            entity_type="hr.employee_address_history",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._address_history_snapshot(row),
            metadata_json={"employee_id": employee_id},
        )
        return EmployeeAddressHistoryRead.model_validate(row)

    def update_address_history(
        self,
        tenant_id: str,
        employee_id: str,
        history_id: str,
        payload: EmployeeAddressHistoryUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeAddressHistoryRead:
        self._require_permission(context, "employees.private.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        self._require_employee(tenant_id, employee_id)
        row = self.repository.get_employee_address_history(tenant_id, employee_id, history_id)
        if row is None:
            raise ApiException(404, "employees.address_history.not_found", "errors.employees.address_history.not_found")
        before = self._address_history_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "address_history")
        next_address_id = (
            self._resolve_address_id(payload.address_id, payload.address)
            if payload.address_id is not None or payload.address is not None
            else row.address_id
        )
        next_address_type = payload.address_type if payload.address_type is not None else row.address_type
        next_valid_from = payload.valid_from if payload.valid_from is not None else row.valid_from
        next_valid_to = payload.valid_to if payload.valid_to is not None else row.valid_to
        self._validate_address_history_payload(
            tenant_id,
            employee_id,
            next_address_id,
            next_address_type,
            next_valid_from,
            next_valid_to,
            exclude_id=history_id,
        )
        row.address_id = next_address_id
        row.address_type = next_address_type
        row.valid_from = next_valid_from
        row.valid_to = next_valid_to
        if payload.is_primary is not None:
            row.is_primary = payload.is_primary
        row.notes = self._effective_optional(payload.notes, row.notes)
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_address_history(row)
        self._record_event(
            context,
            event_type="employees.address_history.updated",
            entity_type="hr.employee_address_history",
            entity_id=history_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._address_history_snapshot(updated),
            metadata_json={"employee_id": employee_id},
        )
        return EmployeeAddressHistoryRead.model_validate(updated)

    def list_groups(self, tenant_id: str, context: RequestAuthorizationContext) -> list[EmployeeGroupRead]:
        self._require_permission(context, "employees.employee.read")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        rows = self.repository.list_groups(tenant_id)
        return [EmployeeGroupRead.model_validate(row) for row in rows]

    def create_group(
        self,
        tenant_id: str,
        payload: EmployeeGroupCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeGroupRead:
        self._require_permission(context, "employees.employee.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "employees.group.tenant_mismatch", "errors.employees.group.tenant_mismatch")
        code = payload.code.strip()
        if self.repository.find_group_by_code(tenant_id, code) is not None:
            raise ApiException(409, "employees.group.duplicate_code", "errors.employees.group.duplicate_code")
        row = self.repository.create_group(
            EmployeeGroup(
                tenant_id=tenant_id,
                code=code,
                name=payload.name.strip(),
                description=self._normalize_optional(payload.description),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        return EmployeeGroupRead.model_validate(row)

    def update_group(
        self,
        tenant_id: str,
        group_id: str,
        payload: EmployeeGroupUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeGroupRead:
        self._require_permission(context, "employees.employee.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        row = self.repository.get_group(tenant_id, group_id)
        if row is None:
            raise ApiException(404, "employees.group.not_found", "errors.employees.group.not_found")
        self._require_version(row.version_no, payload.version_no, "group")
        next_code = self._effective_text(payload.code, row.code)
        if self.repository.find_group_by_code(tenant_id, next_code, exclude_id=group_id) is not None:
            raise ApiException(409, "employees.group.duplicate_code", "errors.employees.group.duplicate_code")
        row.code = next_code
        row.name = self._effective_text(payload.name, row.name)
        row.description = self._effective_optional(payload.description, row.description)
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_group(row)
        return EmployeeGroupRead.model_validate(updated)

    def add_group_member(
        self,
        tenant_id: str,
        payload: EmployeeGroupMemberCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeGroupMemberRead:
        self._require_permission(context, "employees.employee.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "employees.group_member.tenant_mismatch",
                "errors.employees.group_member.tenant_mismatch",
            )
        self._require_employee(tenant_id, payload.employee_id)
        if self.repository.get_group(tenant_id, payload.group_id) is None:
            raise ApiException(404, "employees.group.not_found", "errors.employees.group.not_found")
        self._validate_group_member_window(payload.valid_from, payload.valid_until)
        row = self.repository.create_group_member(
            EmployeeGroupMember(
                tenant_id=tenant_id,
                employee_id=payload.employee_id,
                group_id=payload.group_id,
                valid_from=payload.valid_from,
                valid_until=payload.valid_until,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        return EmployeeGroupMemberRead.model_validate(row)

    def update_group_member(
        self,
        tenant_id: str,
        member_id: str,
        payload: EmployeeGroupMemberUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeGroupMemberRead:
        self._require_permission(context, "employees.employee.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        row = self.repository.get_group_member(tenant_id, member_id)
        if row is None:
            raise ApiException(404, "employees.group_member.not_found", "errors.employees.group_member.not_found")
        self._require_version(row.version_no, payload.version_no, "group_member")
        next_valid_from = payload.valid_from if payload.valid_from is not None else row.valid_from
        next_valid_until = payload.valid_until if payload.valid_until is not None else row.valid_until
        self._validate_group_member_window(next_valid_from, next_valid_until)
        row.valid_from = next_valid_from
        row.valid_until = next_valid_until
        row.notes = self._effective_optional(payload.notes, row.notes)
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_group_member(row)
        return EmployeeGroupMemberRead.model_validate(updated)

    def list_notes(
        self,
        tenant_id: str,
        employee_id: str,
        context: RequestAuthorizationContext,
    ) -> list[EmployeeNoteRead]:
        self._require_permission(context, "employees.employee.read")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        self._require_employee(tenant_id, employee_id)
        rows = self.repository.list_notes(tenant_id, employee_id)
        return [EmployeeNoteRead.model_validate(row) for row in rows]

    def create_note(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeNoteCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeeNoteRead:
        self._require_permission(context, "employees.employee.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        self._require_employee(tenant_id, employee_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "employees.note.tenant_mismatch", "errors.employees.note.tenant_mismatch")
        if payload.employee_id != employee_id:
            raise ApiException(400, "employees.note.employee_mismatch", "errors.employees.note.employee_mismatch")
        note_type = payload.note_type.strip()
        self._validate_note_payload(note_type, payload.reminder_at, None)
        row = self.repository.create_note(
            EmployeeNote(
                tenant_id=tenant_id,
                employee_id=employee_id,
                note_type=note_type,
                title=payload.title.strip(),
                body=self._normalize_optional(payload.body),
                reminder_at=payload.reminder_at,
                completed_at=None,
                completed_by_user_id=None,
                created_by_user_id=context.user_id,
                updated_by_user_id=context.user_id,
            )
        )
        return EmployeeNoteRead.model_validate(row)

    def update_note(
        self,
        tenant_id: str,
        employee_id: str,
        note_id: str,
        payload: EmployeeNoteUpdate,
        context: RequestAuthorizationContext,
    ) -> EmployeeNoteRead:
        self._require_permission(context, "employees.employee.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        self._require_employee(tenant_id, employee_id)
        row = self.repository.get_note(tenant_id, employee_id, note_id)
        if row is None:
            raise ApiException(404, "employees.note.not_found", "errors.employees.note.not_found")
        self._require_version(row.version_no, payload.version_no, "note")
        next_reminder_at = payload.reminder_at if payload.reminder_at is not None else row.reminder_at
        next_completed_at = payload.completed_at if payload.completed_at is not None else row.completed_at
        self._validate_note_payload(row.note_type, next_reminder_at, next_completed_at)
        row.title = self._effective_text(payload.title, row.title)
        row.body = self._effective_optional(payload.body, row.body)
        row.reminder_at = next_reminder_at
        row.completed_at = next_completed_at
        row.completed_by_user_id = context.user_id if next_completed_at is not None else None
        if payload.status is not None:
            row.status = payload.status
        if payload.archived_at is not None:
            row.archived_at = payload.archived_at
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_note(row)
        return EmployeeNoteRead.model_validate(updated)

    def archive_employee(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeLifecycleTransitionRequest,
        context: RequestAuthorizationContext,
    ) -> EmployeeOperationalRead:
        self._require_permission(context, "employees.employee.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        row = self._require_employee(tenant_id, employee_id)
        before = self._employee_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "employee")
        row.status = "archived"
        row.archived_at = row.archived_at or datetime.now(UTC)
        self._sync_archived_employee_access(row, context)
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_employee(row)
        self._record_event(
            context,
            event_type="employees.employee.archived",
            entity_type="hr.employee",
            entity_id=employee_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._employee_snapshot(updated),
        )
        return EmployeeOperationalRead.model_validate(updated)

    def reactivate_employee(
        self,
        tenant_id: str,
        employee_id: str,
        payload: EmployeeLifecycleTransitionRequest,
        context: RequestAuthorizationContext,
    ) -> EmployeeOperationalRead:
        self._require_permission(context, "employees.employee.write")
        enforce_scope(context, scope="tenant", tenant_id=tenant_id)
        row = self._require_employee(tenant_id, employee_id)
        before = self._employee_snapshot(row)
        self._require_version(row.version_no, payload.version_no, "employee")
        row.status = "active"
        row.archived_at = None
        self._sync_archived_employee_access(row, context)
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_employee(row)
        self._record_event(
            context,
            event_type="employees.employee.reactivated",
            entity_type="hr.employee",
            entity_id=employee_id,
            tenant_id=tenant_id,
            before_json=before,
            after_json=self._employee_snapshot(updated),
        )
        return EmployeeOperationalRead.model_validate(updated)

    def _require_employee(self, tenant_id: str, employee_id: str) -> Employee:
        row = self.repository.get_employee(tenant_id, employee_id)
        if row is None:
            raise ApiException(404, "employees.employee.not_found", "errors.employees.employee.not_found")
        return row

    def _validate_employee_payload(
        self,
        tenant_id: str,
        payload: EmployeeOperationalCreate,
        *,
        exclude_id: str | None = None,
    ) -> None:
        if payload.termination_date is not None and payload.hire_date is not None and payload.termination_date < payload.hire_date:
            raise ApiException(422, "employees.employee.invalid_dates", "errors.employees.employee.invalid_dates")
        if payload.target_weekly_hours is not None and payload.target_weekly_hours < 0:
            raise ApiException(
                422,
                "employees.employee.invalid_target_weekly_hours",
                "errors.employees.employee.invalid_target_weekly_hours",
            )
        if payload.target_monthly_hours is not None and payload.target_monthly_hours < 0:
            raise ApiException(
                422,
                "employees.employee.invalid_target_monthly_hours",
                "errors.employees.employee.invalid_target_monthly_hours",
            )
        if self.repository.find_employee_by_personnel_no(tenant_id, payload.personnel_no, exclude_id=exclude_id) is not None:
            raise ApiException(409, "employees.employee.duplicate_personnel_no", "errors.employees.employee.duplicate_personnel_no")
        if payload.user_id is not None:
            if self.repository.get_user_account(tenant_id, payload.user_id) is None:
                raise ApiException(404, "employees.user.not_found", "errors.employees.user.not_found")
            if self.repository.find_employee_by_user_id(tenant_id, payload.user_id, exclude_id=exclude_id) is not None:
                raise ApiException(409, "employees.employee.duplicate_user_link", "errors.employees.employee.duplicate_user_link")
        branch = self._resolve_branch(tenant_id, payload.default_branch_id)
        mandate = self._resolve_mandate(tenant_id, payload.default_mandate_id)
        if branch is not None and mandate is not None and mandate.branch_id != branch.id:
            raise ApiException(
                422,
                "employees.employee.mandate_branch_mismatch",
                "errors.employees.employee.mandate_branch_mismatch",
            )

    def _validate_address_history_payload(
        self,
        tenant_id: str,
        employee_id: str,
        address_id: str,
        address_type: str,
        valid_from: date,
        valid_to: date | None,
        *,
        exclude_id: str | None = None,
    ) -> None:
        if address_type not in EMPLOYEE_ADDRESS_TYPES:
            raise ApiException(
                422,
                "employees.address_history.invalid_type",
                "errors.employees.address_history.invalid_type",
                {"address_type": address_type},
            )
        if valid_to is not None and valid_to < valid_from:
            raise ApiException(
                422,
                "employees.address_history.invalid_window",
                "errors.employees.address_history.invalid_window",
            )
        if self.repository.get_address(address_id) is None:
            raise ApiException(404, "employees.address_history.address_not_found", "errors.employees.address_history.address_not_found")
        self._ensure_no_address_overlap(
            existing=self.repository.list_employee_address_history(tenant_id, employee_id),
            address_type=address_type,
            valid_from=valid_from,
            valid_to=valid_to,
            exclude_id=exclude_id,
        )

    def _resolve_address_id(self, address_id: str | None, address_payload: EmployeeAddressWriteAddress | None) -> str:
        if address_payload is not None:
            normalized = EmployeeAddressWriteAddress(
                street_line_1=address_payload.street_line_1.strip(),
                street_line_2=self._normalize_optional(address_payload.street_line_2),
                postal_code=address_payload.postal_code.strip(),
                city=address_payload.city.strip(),
                state_region=self._normalize_optional(address_payload.state_region),
                country_code=address_payload.country_code.strip().upper(),
            )
            created = self.repository.create_address(
                Address(
                    street_line_1=normalized.street_line_1,
                    street_line_2=normalized.street_line_2,
                    postal_code=normalized.postal_code,
                    city=normalized.city,
                    state=normalized.state_region,
                    country_code=normalized.country_code,
                )
            )
            return created.id

        normalized_address_id = self._normalize_optional(address_id)
        if normalized_address_id is None:
            raise ApiException(
                400,
                "employees.address_history.address_required",
                "errors.employees.address_history.address_required",
            )
        return normalized_address_id

    def _apply_private_profile_update(
        self,
        row: EmployeePrivateProfile,
        payload: EmployeePrivateProfileCreate,
        context: RequestAuthorizationContext,
    ) -> EmployeePrivateProfile:
        before = self._private_profile_snapshot(row)
        row.private_email = self._normalize_optional(payload.private_email)
        row.private_phone = self._normalize_optional(payload.private_phone)
        row.birth_date = payload.birth_date
        row.place_of_birth = self._normalize_optional(payload.place_of_birth)
        row.nationality_country_code = self._normalize_optional(payload.nationality_country_code)
        row.marital_status_code = self._normalize_optional(payload.marital_status_code)
        row.tax_id = self._normalize_optional(payload.tax_id)
        row.social_security_no = self._normalize_optional(payload.social_security_no)
        row.bank_account_holder = self._normalize_optional(payload.bank_account_holder)
        row.bank_iban = self._normalize_optional(payload.bank_iban)
        row.bank_bic = self._normalize_optional(payload.bank_bic)
        row.emergency_contact_name = self._normalize_optional(payload.emergency_contact_name)
        row.emergency_contact_phone = self._normalize_optional(payload.emergency_contact_phone)
        row.notes = self._normalize_optional(payload.notes)
        row.updated_by_user_id = context.user_id
        row.version_no += 1
        updated = self.repository.update_private_profile(row)
        self._record_event(
            context,
            event_type="employees.private_profile.updated",
            entity_type="hr.employee_private_profile",
            entity_id=row.id,
            tenant_id=row.tenant_id,
            before_json=before,
            after_json=self._private_profile_snapshot(updated),
            metadata_json={"employee_id": row.employee_id},
        )
        return updated

    def _sync_archived_employee_access(self, row: Employee, context: RequestAuthorizationContext) -> None:
        if row.user_id is None:
            return
        assignment = self.repository.find_role_assignment(row.tenant_id, row.user_id, "employee_user")
        if assignment is None:
            return
        if row.archived_at is not None or row.status == "archived":
            assignment.status = "inactive"
            assignment.archived_at = row.archived_at or datetime.now(UTC)
        else:
            assignment.status = "active"
            assignment.archived_at = None
        assignment.updated_by_user_id = context.user_id
        assignment.version_no += 1
        self.repository.update_role_assignment(assignment)

    @staticmethod
    def _normalize_employee_lifecycle(row: Employee) -> None:
        if row.archived_at is not None and row.status == "active":
            row.status = "archived"
        if row.status == "archived" and row.archived_at is None:
            row.archived_at = datetime.now(UTC)
        if row.status != "archived" and row.archived_at is not None:
            row.archived_at = None

    @staticmethod
    def _require_permission(context: RequestAuthorizationContext, permission_key: str) -> None:
        if permission_key not in context.permission_keys:
            raise ApiException(
                403,
                "iam.authorization.permission_denied",
                "errors.iam.authorization.permission_denied",
                {"permission_key": permission_key},
            )

    @staticmethod
    def _require_version(current: int, provided: int | None, entity: str) -> None:
        if provided is None:
            raise ApiException(409, f"employees.{entity}.stale_version", f"errors.employees.{entity}.stale_version")
        if current != provided:
            raise ApiException(409, f"employees.{entity}.stale_version", f"errors.employees.{entity}.stale_version")

    def _resolve_branch(self, tenant_id: str, branch_id: str | None) -> Branch | None:
        if branch_id is None:
            return None
        branch = self.repository.get_branch(tenant_id, branch_id)
        if branch is None:
            raise ApiException(404, "employees.employee.branch_not_found", "errors.employees.employee.branch_not_found")
        return branch

    def _resolve_mandate(self, tenant_id: str, mandate_id: str | None) -> Mandate | None:
        if mandate_id is None:
            return None
        mandate = self.repository.get_mandate(tenant_id, mandate_id)
        if mandate is None:
            raise ApiException(404, "employees.employee.mandate_not_found", "errors.employees.employee.mandate_not_found")
        return mandate

    @staticmethod
    def _validate_note_payload(note_type: str, reminder_at: date | None, completed_at: date | None) -> None:
        if note_type not in EMPLOYEE_NOTE_TYPES:
            raise ApiException(422, "employees.note.invalid_type", "errors.employees.note.invalid_type")
        if note_type == "reminder" and reminder_at is None:
            raise ApiException(422, "employees.note.reminder_date_required", "errors.employees.note.reminder_date_required")
        if note_type != "reminder" and completed_at is not None and reminder_at is None:
            raise ApiException(
                422,
                "employees.note.invalid_completion",
                "errors.employees.note.invalid_completion",
            )
        if completed_at is not None and reminder_at is not None and completed_at < reminder_at:
            raise ApiException(
                422,
                "employees.note.invalid_completion",
                "errors.employees.note.invalid_completion",
            )

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None

    def _normalize_employee_create(self, payload: EmployeeOperationalCreate) -> EmployeeOperationalCreate:
        return EmployeeOperationalCreate(
            tenant_id=payload.tenant_id,
            personnel_no=payload.personnel_no.strip(),
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            preferred_name=self._normalize_optional(payload.preferred_name),
            work_email=self._normalize_optional(payload.work_email),
            work_phone=self._normalize_optional(payload.work_phone),
            mobile_phone=self._normalize_optional(payload.mobile_phone),
            default_branch_id=self._normalize_branch_id(payload.default_branch_id),
            default_mandate_id=self._normalize_mandate_id(payload.default_mandate_id),
            hire_date=payload.hire_date,
            termination_date=payload.termination_date,
            status=self._normalize_optional(payload.status),
            employment_type_code=self._normalize_optional(payload.employment_type_code),
            target_weekly_hours=self._normalize_target_hours(payload.target_weekly_hours, "weekly"),
            target_monthly_hours=self._normalize_target_hours(payload.target_monthly_hours, "monthly"),
            user_id=self._normalize_user_id(payload.user_id),
            notes=self._normalize_optional(payload.notes),
        )

    def _effective_optional(self, candidate: str | None, current: str | None) -> str | None:
        if candidate is None:
            return current
        return self._normalize_optional(candidate)

    @staticmethod
    def _normalize_target_hours(value: float | None, period: str) -> float | None:
        if value is None:
            return None
        normalized = float(value)
        if normalized < 0:
            raise ApiException(
                422,
                f"employees.employee.invalid_target_{period}_hours",
                f"errors.employees.employee.invalid_target_{period}_hours",
            )
        return normalized

    def _normalize_user_id(self, user_id: str | None) -> str | None:
        return self._normalize_uuid_reference(
            user_id,
            error_code="employees.user.invalid_id_format",
            error_message_key="errors.employees.user.invalid_id_format",
        )

    def _normalize_branch_id(self, branch_id: str | None) -> str | None:
        return self._normalize_uuid_reference(
            branch_id,
            error_code="employees.employee.invalid_branch_id_format",
            error_message_key="errors.employees.employee.invalid_branch_id_format",
        )

    def _normalize_mandate_id(self, mandate_id: str | None) -> str | None:
        return self._normalize_uuid_reference(
            mandate_id,
            error_code="employees.employee.invalid_mandate_id_format",
            error_message_key="errors.employees.employee.invalid_mandate_id_format",
        )

    def _normalize_uuid_reference(
        self,
        value: str | None,
        *,
        error_code: str,
        error_message_key: str,
    ) -> str | None:
        normalized = self._normalize_optional(value)
        if normalized is None:
            return None
        try:
            return str(UUID(normalized))
        except ValueError as exc:
            raise ApiException(422, error_code, error_message_key) from exc

    def _effective_text(self, candidate: str | None, current: str) -> str:
        if candidate is None:
            return current
        trimmed = candidate.strip()
        return trimmed or current

    @staticmethod
    def _ensure_no_address_overlap(
        *,
        existing: Iterable[EmployeeAddressHistory],
        address_type: str,
        valid_from: date,
        valid_to: date | None,
        exclude_id: str | None = None,
    ) -> None:
        for row in existing:
            if row.archived_at is not None or row.address_type != address_type:
                continue
            if exclude_id is not None and row.id == exclude_id:
                continue
            existing_end = row.valid_to or date.max
            new_end = valid_to or date.max
            if valid_from <= existing_end and row.valid_from <= new_end:
                raise ApiException(
                    409,
                    "employees.address_history.overlap",
                    "errors.employees.address_history.overlap",
                    {"address_type": address_type},
                )

    @staticmethod
    def _validate_group_member_window(valid_from: date, valid_until: date | None) -> None:
        if valid_until is not None and valid_until < valid_from:
            raise ApiException(
                422,
                "employees.group_member.invalid_window",
                "errors.employees.group_member.invalid_window",
            )

    @staticmethod
    def _employee_snapshot(row: Employee) -> dict[str, object]:
        return {
            "personnel_no": row.personnel_no,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "preferred_name": row.preferred_name,
            "work_email": row.work_email,
            "work_phone": row.work_phone,
            "mobile_phone": row.mobile_phone,
            "default_branch_id": row.default_branch_id,
            "default_mandate_id": row.default_mandate_id,
            "hire_date": row.hire_date.isoformat() if row.hire_date else None,
            "termination_date": row.termination_date.isoformat() if row.termination_date else None,
            "employment_type_code": row.employment_type_code,
            "target_weekly_hours": row.target_weekly_hours,
            "target_monthly_hours": row.target_monthly_hours,
            "user_id": row.user_id,
            "status": row.status,
            "archived_at": row.archived_at.isoformat() if row.archived_at else None,
        }

    @staticmethod
    def _private_profile_snapshot(row: EmployeePrivateProfile) -> dict[str, object]:
        return {
            "private_email": row.private_email,
            "private_phone": row.private_phone,
            "birth_date": row.birth_date.isoformat() if row.birth_date else None,
            "place_of_birth": row.place_of_birth,
            "nationality_country_code": row.nationality_country_code,
            "marital_status_code": row.marital_status_code,
            "tax_id": row.tax_id,
            "social_security_no": row.social_security_no,
            "bank_account_holder": row.bank_account_holder,
            "bank_iban": row.bank_iban,
            "bank_bic": row.bank_bic,
            "emergency_contact_name": row.emergency_contact_name,
            "emergency_contact_phone": row.emergency_contact_phone,
            "status": row.status,
            "archived_at": row.archived_at.isoformat() if row.archived_at else None,
        }

    @staticmethod
    def _address_history_snapshot(row: EmployeeAddressHistory) -> dict[str, object]:
        return {
            "address_id": row.address_id,
            "address_type": row.address_type,
            "valid_from": row.valid_from.isoformat(),
            "valid_to": row.valid_to.isoformat() if row.valid_to else None,
            "is_primary": row.is_primary,
            "notes": row.notes,
            "status": row.status,
            "archived_at": row.archived_at.isoformat() if row.archived_at else None,
        }

    def _record_event(
        self,
        context: RequestAuthorizationContext,
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
