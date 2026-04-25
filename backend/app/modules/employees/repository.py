"""SQLAlchemy persistence helpers for the employee aggregate foundation."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.modules.core.models import Address, Branch, LookupValue, Mandate, Tenant
from app.modules.core.schemas import LookupValueRead
from app.modules.employees.models import (
    Employee,
    EmployeeAddressHistory,
    EmployeeAdvance,
    EmployeeAllowance,
    EmployeeAvailabilityRule,
    EmployeeAbsence,
    EmployeeEventApplication,
    EmployeeIdCredential,
    EmployeeGroup,
    EmployeeGroupMember,
    EmployeeLeaveBalance,
    EmployeeQualification,
    EmployeeNote,
    EmployeePrivateProfile,
    EmployeeTimeAccount,
    EmployeeTimeAccountTxn,
    FunctionType,
    QualificationType,
)
from app.modules.employees.schemas import (
    EmployeeAdvanceFilter,
    EmployeeAllowanceFilter,
    EmployeeAbsenceFilter,
    EmployeeAvailabilityRuleFilter,
    EmployeeCredentialFilter,
    EmployeeEventApplicationFilter,
    EmployeeFilter,
    EmployeeLeaveBalanceFilter,
    EmployeeQualificationFilter,
    EmployeeTimeAccountFilter,
)
from app.modules.iam.models import Permission, Role, RolePermission, UserAccount, UserRoleAssignment, UserSession
from app.modules.platform_services.docs_models import Document, DocumentLink, DocumentVersion
from app.modules.platform_services.integration_models import ImportExportJob


class SqlAlchemyEmployeeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        statement = select(Tenant).where(Tenant.id == tenant_id)
        return self.session.scalars(statement).one_or_none()

    def list_employees(self, tenant_id: str, filters: EmployeeFilter | None = None) -> list[Employee]:
        statement = (
            select(Employee)
            .where(Employee.tenant_id == tenant_id)
            .options(
                selectinload(Employee.private_profile),
                selectinload(Employee.address_history).selectinload(EmployeeAddressHistory.address),
                selectinload(Employee.group_memberships).selectinload(EmployeeGroupMember.group),
                selectinload(Employee.activity_notes),
            )
            .order_by(Employee.personnel_no)
        )
        if filters is not None:
            if not filters.include_archived:
                statement = statement.where(Employee.archived_at.is_(None))
            if filters.status is not None:
                statement = statement.where(Employee.status == filters.status)
            if filters.default_branch_id is not None:
                statement = statement.where(Employee.default_branch_id == filters.default_branch_id)
            if filters.default_mandate_id is not None:
                statement = statement.where(Employee.default_mandate_id == filters.default_mandate_id)
            if filters.search:
                like_term = f"%{filters.search.strip().lower()}%"
                statement = statement.where(
                    or_(
                        func.lower(Employee.personnel_no).like(like_term),
                        func.lower(Employee.first_name).like(like_term),
                        func.lower(Employee.last_name).like(like_term),
                        func.lower(func.coalesce(Employee.preferred_name, "")).like(like_term),
                        func.lower(func.coalesce(Employee.work_email, "")).like(like_term),
                )
        )
        rows = list(self.session.scalars(statement).all())
        self._attach_profile_photo_metadata(tenant_id, rows)
        return rows

    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None:
        statement = (
            select(Employee)
            .where(Employee.tenant_id == tenant_id, Employee.id == employee_id)
            .options(
                selectinload(Employee.private_profile),
                selectinload(Employee.address_history).selectinload(EmployeeAddressHistory.address),
                selectinload(Employee.group_memberships).selectinload(EmployeeGroupMember.group),
                selectinload(Employee.activity_notes),
            )
        )
        return self.session.scalars(statement).one_or_none()

    def _attach_profile_photo_metadata(self, tenant_id: str, employees: list[Employee]) -> None:
        if not employees:
            return

        employee_ids = [employee.id for employee in employees]
        photo_rows = self.session.execute(
            select(
                DocumentLink.owner_id.label("employee_id"),
                Document.id.label("photo_document_id"),
                Document.current_version_no.label("photo_current_version_no"),
                DocumentVersion.content_type.label("photo_content_type"),
            )
            .join(
                Document,
                and_(
                    Document.tenant_id == DocumentLink.tenant_id,
                    Document.id == DocumentLink.document_id,
                ),
            )
            .outerjoin(
                DocumentVersion,
                and_(
                    DocumentVersion.tenant_id == Document.tenant_id,
                    DocumentVersion.document_id == Document.id,
                    DocumentVersion.version_no == Document.current_version_no,
                ),
            )
            .where(
                DocumentLink.tenant_id == tenant_id,
                DocumentLink.owner_type == "hr.employee",
                DocumentLink.relation_type == "profile_photo",
                DocumentLink.owner_id.in_(employee_ids),
                Document.archived_at.is_(None),
                Document.current_version_no > 0,
            )
            .order_by(
                DocumentLink.owner_id,
                Document.updated_at.desc(),
                DocumentLink.linked_at.desc(),
                Document.current_version_no.desc(),
            )
        ).all()

        latest_photo_by_employee_id: dict[str, object] = {}
        for row in photo_rows:
            if row.employee_id not in latest_photo_by_employee_id:
                latest_photo_by_employee_id[row.employee_id] = row

        for employee in employees:
            photo = latest_photo_by_employee_id.get(employee.id)
            setattr(employee, "photo_document_id", None if photo is None else photo.photo_document_id)
            setattr(employee, "photo_current_version_no", None if photo is None else photo.photo_current_version_no)
            setattr(employee, "photo_content_type", None if photo is None else photo.photo_content_type)

    def get_employee_private_profile(self, tenant_id: str, employee_id: str) -> EmployeePrivateProfile | None:
        statement = select(EmployeePrivateProfile).where(
            EmployeePrivateProfile.tenant_id == tenant_id,
            EmployeePrivateProfile.employee_id == employee_id,
        )
        return self.session.scalars(statement).one_or_none()

    def list_employee_address_history(self, tenant_id: str, employee_id: str) -> list[EmployeeAddressHistory]:
        statement = (
            select(EmployeeAddressHistory)
            .where(
                EmployeeAddressHistory.tenant_id == tenant_id,
                EmployeeAddressHistory.employee_id == employee_id,
            )
            .options(selectinload(EmployeeAddressHistory.address))
            .order_by(EmployeeAddressHistory.valid_from)
        )
        return list(self.session.scalars(statement).all())

    def get_employee_address_history(
        self,
        tenant_id: str,
        employee_id: str,
        history_id: str,
    ) -> EmployeeAddressHistory | None:
        statement = (
            select(EmployeeAddressHistory)
            .where(
                EmployeeAddressHistory.tenant_id == tenant_id,
                EmployeeAddressHistory.employee_id == employee_id,
                EmployeeAddressHistory.id == history_id,
            )
            .options(selectinload(EmployeeAddressHistory.address))
        )
        return self.session.scalars(statement).one_or_none()

    def list_groups(self, tenant_id: str) -> list[EmployeeGroup]:
        statement = select(EmployeeGroup).where(EmployeeGroup.tenant_id == tenant_id).order_by(EmployeeGroup.code)
        return list(self.session.scalars(statement).all())

    def get_group(self, tenant_id: str, group_id: str) -> EmployeeGroup | None:
        statement = (
            select(EmployeeGroup)
            .where(EmployeeGroup.tenant_id == tenant_id, EmployeeGroup.id == group_id)
            .options(selectinload(EmployeeGroup.members).selectinload(EmployeeGroupMember.employee))
        )
        return self.session.scalars(statement).one_or_none()

    def get_group_member(self, tenant_id: str, member_id: str) -> EmployeeGroupMember | None:
        statement = select(EmployeeGroupMember).where(
            EmployeeGroupMember.tenant_id == tenant_id,
            EmployeeGroupMember.id == member_id,
        )
        return self.session.scalars(statement).one_or_none()

    def list_notes(self, tenant_id: str, employee_id: str) -> list[EmployeeNote]:
        statement = (
            select(EmployeeNote)
            .where(EmployeeNote.tenant_id == tenant_id, EmployeeNote.employee_id == employee_id)
            .order_by(EmployeeNote.reminder_at.is_(None), EmployeeNote.reminder_at, EmployeeNote.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def list_availability_rules(
        self,
        tenant_id: str,
        filters: EmployeeAvailabilityRuleFilter | None = None,
    ) -> list[EmployeeAvailabilityRule]:
        statement = (
            select(EmployeeAvailabilityRule)
            .where(EmployeeAvailabilityRule.tenant_id == tenant_id)
            .options(selectinload(EmployeeAvailabilityRule.employee))
            .order_by(EmployeeAvailabilityRule.starts_at)
        )
        if filters is not None:
            if filters.employee_id is not None:
                statement = statement.where(EmployeeAvailabilityRule.employee_id == filters.employee_id)
            if filters.rule_kind is not None:
                statement = statement.where(EmployeeAvailabilityRule.rule_kind == filters.rule_kind)
            if filters.status is not None:
                statement = statement.where(EmployeeAvailabilityRule.status == filters.status)
            if filters.active_on is not None:
                statement = statement.where(
                    EmployeeAvailabilityRule.starts_at <= filters.active_on,
                    EmployeeAvailabilityRule.ends_at >= filters.active_on,
                )
            if not filters.include_archived:
                statement = statement.where(EmployeeAvailabilityRule.archived_at.is_(None))
        return list(self.session.scalars(statement).all())

    def get_availability_rule(self, tenant_id: str, rule_id: str) -> EmployeeAvailabilityRule | None:
        statement = (
            select(EmployeeAvailabilityRule)
            .where(EmployeeAvailabilityRule.tenant_id == tenant_id, EmployeeAvailabilityRule.id == rule_id)
            .options(selectinload(EmployeeAvailabilityRule.employee))
        )
        return self.session.scalars(statement).one_or_none()

    def create_availability_rule(self, row: EmployeeAvailabilityRule) -> EmployeeAvailabilityRule:
        self.session.add(row)
        self._commit()
        return self.get_availability_rule(row.tenant_id, row.id) or row

    def update_availability_rule(self, row: EmployeeAvailabilityRule) -> EmployeeAvailabilityRule:
        self.session.add(row)
        self._commit()
        return self.get_availability_rule(row.tenant_id, row.id) or row

    def list_absences(
        self,
        tenant_id: str,
        filters: EmployeeAbsenceFilter | None = None,
    ) -> list[EmployeeAbsence]:
        statement = (
            select(EmployeeAbsence)
            .where(EmployeeAbsence.tenant_id == tenant_id)
            .options(selectinload(EmployeeAbsence.employee))
            .order_by(EmployeeAbsence.starts_on, EmployeeAbsence.ends_on)
        )
        if filters is not None:
            if filters.employee_id is not None:
                statement = statement.where(EmployeeAbsence.employee_id == filters.employee_id)
            if filters.absence_type is not None:
                statement = statement.where(EmployeeAbsence.absence_type == filters.absence_type)
            if filters.status is not None:
                statement = statement.where(EmployeeAbsence.status == filters.status)
            if filters.starts_on_or_after is not None:
                statement = statement.where(EmployeeAbsence.starts_on >= filters.starts_on_or_after)
            if filters.ends_on_or_before is not None:
                statement = statement.where(EmployeeAbsence.ends_on <= filters.ends_on_or_before)
            if not filters.include_archived:
                statement = statement.where(EmployeeAbsence.archived_at.is_(None))
        return list(self.session.scalars(statement).all())

    def get_absence(self, tenant_id: str, absence_id: str) -> EmployeeAbsence | None:
        statement = (
            select(EmployeeAbsence)
            .where(EmployeeAbsence.tenant_id == tenant_id, EmployeeAbsence.id == absence_id)
            .options(selectinload(EmployeeAbsence.employee))
        )
        return self.session.scalars(statement).one_or_none()

    def create_absence(self, row: EmployeeAbsence) -> EmployeeAbsence:
        self.session.add(row)
        self._commit()
        return self.get_absence(row.tenant_id, row.id) or row

    def update_absence(self, row: EmployeeAbsence) -> EmployeeAbsence:
        self.session.add(row)
        self._commit()
        return self.get_absence(row.tenant_id, row.id) or row

    def list_leave_balances(
        self,
        tenant_id: str,
        filters: EmployeeLeaveBalanceFilter | None = None,
    ) -> list[EmployeeLeaveBalance]:
        statement = (
            select(EmployeeLeaveBalance)
            .where(EmployeeLeaveBalance.tenant_id == tenant_id)
            .options(selectinload(EmployeeLeaveBalance.employee))
            .order_by(EmployeeLeaveBalance.balance_year)
        )
        if filters is not None:
            if filters.employee_id is not None:
                statement = statement.where(EmployeeLeaveBalance.employee_id == filters.employee_id)
            if filters.balance_year is not None:
                statement = statement.where(EmployeeLeaveBalance.balance_year == filters.balance_year)
            if not filters.include_archived:
                statement = statement.where(EmployeeLeaveBalance.archived_at.is_(None))
        return list(self.session.scalars(statement).all())

    def get_leave_balance(self, tenant_id: str, balance_id: str) -> EmployeeLeaveBalance | None:
        statement = (
            select(EmployeeLeaveBalance)
            .where(EmployeeLeaveBalance.tenant_id == tenant_id, EmployeeLeaveBalance.id == balance_id)
            .options(selectinload(EmployeeLeaveBalance.employee))
        )
        return self.session.scalars(statement).one_or_none()

    def get_leave_balance_for_year(self, tenant_id: str, employee_id: str, balance_year: int) -> EmployeeLeaveBalance | None:
        statement = select(EmployeeLeaveBalance).where(
            EmployeeLeaveBalance.tenant_id == tenant_id,
            EmployeeLeaveBalance.employee_id == employee_id,
            EmployeeLeaveBalance.balance_year == balance_year,
        )
        return self.session.scalars(statement).one_or_none()

    def create_leave_balance(self, row: EmployeeLeaveBalance) -> EmployeeLeaveBalance:
        self.session.add(row)
        self._commit()
        return self.get_leave_balance(row.tenant_id, row.id) or row

    def update_leave_balance(self, row: EmployeeLeaveBalance) -> EmployeeLeaveBalance:
        self.session.add(row)
        self._commit()
        return self.get_leave_balance(row.tenant_id, row.id) or row

    def list_event_applications(
        self,
        tenant_id: str,
        filters: EmployeeEventApplicationFilter | None = None,
    ) -> list[EmployeeEventApplication]:
        statement = (
            select(EmployeeEventApplication)
            .where(EmployeeEventApplication.tenant_id == tenant_id)
            .options(selectinload(EmployeeEventApplication.employee))
            .order_by(EmployeeEventApplication.applied_at.desc())
        )
        if filters is not None:
            if filters.employee_id is not None:
                statement = statement.where(EmployeeEventApplication.employee_id == filters.employee_id)
            if filters.planning_record_id is not None:
                statement = statement.where(EmployeeEventApplication.planning_record_id == filters.planning_record_id)
            if filters.status is not None:
                statement = statement.where(EmployeeEventApplication.status == filters.status)
            if not filters.include_archived:
                statement = statement.where(EmployeeEventApplication.archived_at.is_(None))
        return list(self.session.scalars(statement).all())

    def get_event_application(self, tenant_id: str, application_id: str) -> EmployeeEventApplication | None:
        statement = (
            select(EmployeeEventApplication)
            .where(EmployeeEventApplication.tenant_id == tenant_id, EmployeeEventApplication.id == application_id)
            .options(selectinload(EmployeeEventApplication.employee))
        )
        return self.session.scalars(statement).one_or_none()

    def find_event_application(
        self,
        tenant_id: str,
        employee_id: str,
        planning_record_id: str,
        *,
        exclude_id: str | None = None,
    ) -> EmployeeEventApplication | None:
        statement = select(EmployeeEventApplication).where(
            EmployeeEventApplication.tenant_id == tenant_id,
            EmployeeEventApplication.employee_id == employee_id,
            EmployeeEventApplication.planning_record_id == planning_record_id,
        )
        if exclude_id is not None:
            statement = statement.where(EmployeeEventApplication.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_event_application(self, row: EmployeeEventApplication) -> EmployeeEventApplication:
        self.session.add(row)
        self._commit()
        return self.get_event_application(row.tenant_id, row.id) or row

    def update_event_application(self, row: EmployeeEventApplication) -> EmployeeEventApplication:
        self.session.add(row)
        self._commit()
        return self.get_event_application(row.tenant_id, row.id) or row

    def list_time_accounts(self, tenant_id: str, filters: EmployeeTimeAccountFilter | None = None) -> list[EmployeeTimeAccount]:
        statement = (
            select(EmployeeTimeAccount)
            .where(EmployeeTimeAccount.tenant_id == tenant_id)
            .options(selectinload(EmployeeTimeAccount.employee), selectinload(EmployeeTimeAccount.transactions))
            .order_by(EmployeeTimeAccount.account_type)
        )
        if filters is not None:
            if filters.employee_id is not None:
                statement = statement.where(EmployeeTimeAccount.employee_id == filters.employee_id)
            if filters.account_type is not None:
                statement = statement.where(EmployeeTimeAccount.account_type == filters.account_type)
            if not filters.include_archived:
                statement = statement.where(EmployeeTimeAccount.archived_at.is_(None))
        return list(self.session.scalars(statement).all())

    def get_time_account(self, tenant_id: str, account_id: str) -> EmployeeTimeAccount | None:
        statement = (
            select(EmployeeTimeAccount)
            .where(EmployeeTimeAccount.tenant_id == tenant_id, EmployeeTimeAccount.id == account_id)
            .options(selectinload(EmployeeTimeAccount.employee), selectinload(EmployeeTimeAccount.transactions))
        )
        return self.session.scalars(statement).one_or_none()

    def find_time_account(self, tenant_id: str, employee_id: str, account_type: str) -> EmployeeTimeAccount | None:
        statement = select(EmployeeTimeAccount).where(
            EmployeeTimeAccount.tenant_id == tenant_id,
            EmployeeTimeAccount.employee_id == employee_id,
            EmployeeTimeAccount.account_type == account_type,
        )
        return self.session.scalars(statement).one_or_none()

    def create_time_account(self, row: EmployeeTimeAccount) -> EmployeeTimeAccount:
        self.session.add(row)
        self._commit()
        return self.get_time_account(row.tenant_id, row.id) or row

    def update_time_account(self, row: EmployeeTimeAccount) -> EmployeeTimeAccount:
        self.session.add(row)
        self._commit()
        return self.get_time_account(row.tenant_id, row.id) or row

    def add_time_account_txn(self, row: EmployeeTimeAccountTxn) -> EmployeeTimeAccountTxn:
        self.session.add(row)
        self._commit()
        self.session.refresh(row)
        return row

    def list_allowances(self, tenant_id: str, filters: EmployeeAllowanceFilter | None = None) -> list[EmployeeAllowance]:
        statement = (
            select(EmployeeAllowance)
            .where(EmployeeAllowance.tenant_id == tenant_id)
            .options(
                selectinload(EmployeeAllowance.employee),
                selectinload(EmployeeAllowance.function_type),
                selectinload(EmployeeAllowance.qualification_type),
            )
            .order_by(EmployeeAllowance.effective_from)
        )
        if filters is not None:
            if filters.employee_id is not None:
                statement = statement.where(EmployeeAllowance.employee_id == filters.employee_id)
            if filters.basis_code is not None:
                statement = statement.where(EmployeeAllowance.basis_code == filters.basis_code)
            if filters.function_type_id is not None:
                statement = statement.where(EmployeeAllowance.function_type_id == filters.function_type_id)
            if filters.qualification_type_id is not None:
                statement = statement.where(EmployeeAllowance.qualification_type_id == filters.qualification_type_id)
            if filters.active_on is not None:
                statement = statement.where(
                    EmployeeAllowance.effective_from <= filters.active_on,
                    (EmployeeAllowance.effective_until.is_(None)) | (EmployeeAllowance.effective_until >= filters.active_on),
                )
            if not filters.include_archived:
                statement = statement.where(EmployeeAllowance.archived_at.is_(None))
        return list(self.session.scalars(statement).all())

    def get_allowance(self, tenant_id: str, allowance_id: str) -> EmployeeAllowance | None:
        statement = (
            select(EmployeeAllowance)
            .where(EmployeeAllowance.tenant_id == tenant_id, EmployeeAllowance.id == allowance_id)
            .options(
                selectinload(EmployeeAllowance.employee),
                selectinload(EmployeeAllowance.function_type),
                selectinload(EmployeeAllowance.qualification_type),
            )
        )
        return self.session.scalars(statement).one_or_none()

    def create_allowance(self, row: EmployeeAllowance) -> EmployeeAllowance:
        self.session.add(row)
        self._commit()
        return self.get_allowance(row.tenant_id, row.id) or row

    def update_allowance(self, row: EmployeeAllowance) -> EmployeeAllowance:
        self.session.add(row)
        self._commit()
        return self.get_allowance(row.tenant_id, row.id) or row

    def list_advances(self, tenant_id: str, filters: EmployeeAdvanceFilter | None = None) -> list[EmployeeAdvance]:
        statement = (
            select(EmployeeAdvance)
            .where(EmployeeAdvance.tenant_id == tenant_id)
            .options(selectinload(EmployeeAdvance.employee))
            .order_by(EmployeeAdvance.requested_on.desc())
        )
        if filters is not None:
            if filters.employee_id is not None:
                statement = statement.where(EmployeeAdvance.employee_id == filters.employee_id)
            if filters.status is not None:
                statement = statement.where(EmployeeAdvance.status == filters.status)
            if not filters.include_archived:
                statement = statement.where(EmployeeAdvance.archived_at.is_(None))
        return list(self.session.scalars(statement).all())

    def get_advance(self, tenant_id: str, advance_id: str) -> EmployeeAdvance | None:
        statement = (
            select(EmployeeAdvance)
            .where(EmployeeAdvance.tenant_id == tenant_id, EmployeeAdvance.id == advance_id)
            .options(selectinload(EmployeeAdvance.employee))
        )
        return self.session.scalars(statement).one_or_none()

    def find_advance_by_no(self, tenant_id: str, advance_no: str, *, exclude_id: str | None = None) -> EmployeeAdvance | None:
        statement = select(EmployeeAdvance).where(EmployeeAdvance.tenant_id == tenant_id, EmployeeAdvance.advance_no == advance_no)
        if exclude_id is not None:
            statement = statement.where(EmployeeAdvance.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_advance(self, row: EmployeeAdvance) -> EmployeeAdvance:
        self.session.add(row)
        self._commit()
        return self.get_advance(row.tenant_id, row.id) or row

    def update_advance(self, row: EmployeeAdvance) -> EmployeeAdvance:
        self.session.add(row)
        self._commit()
        return self.get_advance(row.tenant_id, row.id) or row

    def list_credentials(self, tenant_id: str, filters: EmployeeCredentialFilter | None = None) -> list[EmployeeIdCredential]:
        statement = (
            select(EmployeeIdCredential)
            .where(EmployeeIdCredential.tenant_id == tenant_id)
            .options(selectinload(EmployeeIdCredential.employee))
            .order_by(EmployeeIdCredential.valid_from.desc())
        )
        if filters is not None:
            if filters.employee_id is not None:
                statement = statement.where(EmployeeIdCredential.employee_id == filters.employee_id)
            if filters.credential_type is not None:
                statement = statement.where(EmployeeIdCredential.credential_type == filters.credential_type)
            if filters.status is not None:
                statement = statement.where(EmployeeIdCredential.status == filters.status)
            if filters.active_on is not None:
                statement = statement.where(
                    EmployeeIdCredential.valid_from <= filters.active_on,
                    (EmployeeIdCredential.valid_until.is_(None)) | (EmployeeIdCredential.valid_until >= filters.active_on),
                )
            if not filters.include_archived:
                statement = statement.where(EmployeeIdCredential.archived_at.is_(None))
        return list(self.session.scalars(statement).all())

    def get_credential(self, tenant_id: str, credential_id: str) -> EmployeeIdCredential | None:
        statement = (
            select(EmployeeIdCredential)
            .where(EmployeeIdCredential.tenant_id == tenant_id, EmployeeIdCredential.id == credential_id)
            .options(selectinload(EmployeeIdCredential.employee))
        )
        return self.session.scalars(statement).one_or_none()

    def find_credential_by_no(self, tenant_id: str, credential_no: str, *, exclude_id: str | None = None) -> EmployeeIdCredential | None:
        statement = select(EmployeeIdCredential).where(
            EmployeeIdCredential.tenant_id == tenant_id,
            EmployeeIdCredential.credential_no == credential_no,
        )
        if exclude_id is not None:
            statement = statement.where(EmployeeIdCredential.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def find_credential_by_encoded_value(
        self,
        tenant_id: str,
        encoded_value: str,
        *,
        exclude_id: str | None = None,
    ) -> EmployeeIdCredential | None:
        statement = select(EmployeeIdCredential).where(
            EmployeeIdCredential.tenant_id == tenant_id,
            EmployeeIdCredential.encoded_value == encoded_value,
        )
        if exclude_id is not None:
            statement = statement.where(EmployeeIdCredential.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_credential(self, row: EmployeeIdCredential) -> EmployeeIdCredential:
        self.session.add(row)
        self._commit()
        return self.get_credential(row.tenant_id, row.id) or row

    def update_credential(self, row: EmployeeIdCredential) -> EmployeeIdCredential:
        self.session.add(row)
        self._commit()
        return self.get_credential(row.tenant_id, row.id) or row

    def list_function_types(self, tenant_id: str) -> list[FunctionType]:
        statement = select(FunctionType).where(FunctionType.tenant_id == tenant_id).order_by(FunctionType.code)
        return list(self.session.scalars(statement).all())

    def get_function_type(self, tenant_id: str, function_type_id: str) -> FunctionType | None:
        statement = select(FunctionType).where(
            FunctionType.tenant_id == tenant_id,
            FunctionType.id == function_type_id,
        )
        return self.session.scalars(statement).one_or_none()

    def find_function_type_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> FunctionType | None:
        statement = select(FunctionType).where(FunctionType.tenant_id == tenant_id, FunctionType.code == code)
        if exclude_id is not None:
            statement = statement.where(FunctionType.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_function_type(self, row: FunctionType) -> FunctionType:
        self.session.add(row)
        self._commit()
        return self.get_function_type(row.tenant_id, row.id) or row

    def update_function_type(self, row: FunctionType) -> FunctionType:
        self.session.add(row)
        self._commit()
        return self.get_function_type(row.tenant_id, row.id) or row

    def list_qualification_types(self, tenant_id: str) -> list[QualificationType]:
        statement = select(QualificationType).where(QualificationType.tenant_id == tenant_id).order_by(QualificationType.code)
        return list(self.session.scalars(statement).all())

    def get_qualification_type(self, tenant_id: str, qualification_type_id: str) -> QualificationType | None:
        statement = select(QualificationType).where(
            QualificationType.tenant_id == tenant_id,
            QualificationType.id == qualification_type_id,
        )
        return self.session.scalars(statement).one_or_none()

    def find_qualification_type_by_code(
        self,
        tenant_id: str,
        code: str,
        *,
        exclude_id: str | None = None,
    ) -> QualificationType | None:
        statement = select(QualificationType).where(QualificationType.tenant_id == tenant_id, QualificationType.code == code)
        if exclude_id is not None:
            statement = statement.where(QualificationType.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_qualification_type(self, row: QualificationType) -> QualificationType:
        self.session.add(row)
        self._commit()
        return self.get_qualification_type(row.tenant_id, row.id) or row

    def update_qualification_type(self, row: QualificationType) -> QualificationType:
        self.session.add(row)
        self._commit()
        return self.get_qualification_type(row.tenant_id, row.id) or row

    def list_lookup_values(self, tenant_id: str, domain: str) -> list[LookupValueRead]:
        rows = self.session.scalars(
            select(LookupValue)
            .where(
                LookupValue.domain == domain,
                LookupValue.archived_at.is_(None),
                (LookupValue.tenant_id.is_(None)) | (LookupValue.tenant_id == tenant_id),
            )
            .order_by(LookupValue.sort_order.asc(), LookupValue.label.asc())
        ).all()
        return [LookupValueRead.model_validate(row) for row in rows]

    def list_employee_qualifications(
        self,
        tenant_id: str,
        filters: EmployeeQualificationFilter | None = None,
    ) -> list[EmployeeQualification]:
        statement = (
            select(EmployeeQualification)
            .where(EmployeeQualification.tenant_id == tenant_id)
            .options(
                selectinload(EmployeeQualification.function_type),
                selectinload(EmployeeQualification.qualification_type),
                selectinload(EmployeeQualification.employee),
            )
            .order_by(EmployeeQualification.valid_until, EmployeeQualification.created_at)
        )
        if filters is not None:
            if filters.employee_id is not None:
                statement = statement.where(EmployeeQualification.employee_id == filters.employee_id)
            if filters.record_kind is not None:
                statement = statement.where(EmployeeQualification.record_kind == filters.record_kind)
            if filters.qualification_type_id is not None:
                statement = statement.where(EmployeeQualification.qualification_type_id == filters.qualification_type_id)
            if filters.function_type_id is not None:
                statement = statement.where(EmployeeQualification.function_type_id == filters.function_type_id)
            if not filters.include_archived:
                statement = statement.where(EmployeeQualification.archived_at.is_(None))
            if not filters.include_expired:
                cutoff = filters.valid_on or func.current_date()
                statement = statement.where(
                    (EmployeeQualification.valid_until.is_(None)) | (EmployeeQualification.valid_until >= cutoff)
                )
        return list(self.session.scalars(statement).all())

    def get_employee_qualification(self, tenant_id: str, qualification_id: str) -> EmployeeQualification | None:
        statement = (
            select(EmployeeQualification)
            .where(EmployeeQualification.tenant_id == tenant_id, EmployeeQualification.id == qualification_id)
            .options(
                selectinload(EmployeeQualification.function_type),
                selectinload(EmployeeQualification.qualification_type),
                selectinload(EmployeeQualification.employee),
            )
        )
        return self.session.scalars(statement).one_or_none()

    def create_employee_qualification(self, row: EmployeeQualification) -> EmployeeQualification:
        self.session.add(row)
        self._commit()
        return self.get_employee_qualification(row.tenant_id, row.id) or row

    def update_employee_qualification(self, row: EmployeeQualification) -> EmployeeQualification:
        self.session.add(row)
        self._commit()
        return self.get_employee_qualification(row.tenant_id, row.id) or row

    def get_note(self, tenant_id: str, employee_id: str, note_id: str) -> EmployeeNote | None:
        statement = select(EmployeeNote).where(
            EmployeeNote.tenant_id == tenant_id,
            EmployeeNote.employee_id == employee_id,
            EmployeeNote.id == note_id,
        )
        return self.session.scalars(statement).one_or_none()

    def create_employee(self, row: Employee) -> Employee:
        self.session.add(row)
        self._commit()
        return self.get_employee(row.tenant_id, row.id) or row

    def update_employee(self, row: Employee) -> Employee:
        self.session.add(row)
        self._commit()
        return self.get_employee(row.tenant_id, row.id) or row

    def create_private_profile(self, row: EmployeePrivateProfile) -> EmployeePrivateProfile:
        self.session.add(row)
        self._commit()
        return self.get_employee_private_profile(row.tenant_id, row.employee_id) or row

    def update_private_profile(self, row: EmployeePrivateProfile) -> EmployeePrivateProfile:
        self.session.add(row)
        self._commit()
        return self.get_employee_private_profile(row.tenant_id, row.employee_id) or row

    def create_address_history(self, row: EmployeeAddressHistory) -> EmployeeAddressHistory:
        self.session.add(row)
        self._commit()
        return self.get_employee_address_history(row.tenant_id, row.employee_id, row.id) or row

    def update_address_history(self, row: EmployeeAddressHistory) -> EmployeeAddressHistory:
        self.session.add(row)
        self._commit()
        return self.get_employee_address_history(row.tenant_id, row.employee_id, row.id) or row

    def create_group(self, row: EmployeeGroup) -> EmployeeGroup:
        self.session.add(row)
        self._commit()
        return self.get_group(row.tenant_id, row.id) or row

    def update_group(self, row: EmployeeGroup) -> EmployeeGroup:
        self.session.add(row)
        self._commit()
        return self.get_group(row.tenant_id, row.id) or row

    def create_group_member(self, row: EmployeeGroupMember) -> EmployeeGroupMember:
        self.session.add(row)
        self._commit()
        return self.get_group_member(row.tenant_id, row.id) or row

    def update_group_member(self, row: EmployeeGroupMember) -> EmployeeGroupMember:
        self.session.add(row)
        self._commit()
        return self.get_group_member(row.tenant_id, row.id) or row

    def create_note(self, row: EmployeeNote) -> EmployeeNote:
        self.session.add(row)
        self._commit()
        return self.get_note(row.tenant_id, row.employee_id, row.id) or row

    def update_note(self, row: EmployeeNote) -> EmployeeNote:
        self.session.add(row)
        self._commit()
        return self.get_note(row.tenant_id, row.employee_id, row.id) or row

    def find_employee_by_personnel_no(
        self,
        tenant_id: str,
        personnel_no: str,
        *,
        exclude_id: str | None = None,
    ) -> Employee | None:
        statement = select(Employee).where(Employee.tenant_id == tenant_id, Employee.personnel_no == personnel_no)
        if exclude_id is not None:
            statement = statement.where(Employee.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def find_employee_by_user_id(
        self,
        tenant_id: str,
        user_id: str,
        *,
        exclude_id: str | None = None,
    ) -> Employee | None:
        statement = select(Employee).where(
            Employee.tenant_id == tenant_id,
            Employee.user_id == user_id,
            Employee.archived_at.is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(Employee.id != exclude_id)
        employee = self.session.scalars(statement).one_or_none()
        if employee is not None:
            self._attach_profile_photo_metadata(tenant_id, [employee])
        return employee

    def find_group_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> EmployeeGroup | None:
        statement = select(EmployeeGroup).where(EmployeeGroup.tenant_id == tenant_id, EmployeeGroup.code == code)
        if exclude_id is not None:
            statement = statement.where(EmployeeGroup.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def get_user_account(self, tenant_id: str, user_id: str) -> UserAccount | None:
        statement = (
            select(UserAccount)
            .where(UserAccount.tenant_id == tenant_id, UserAccount.id == user_id)
            .options(selectinload(UserAccount.role_assignments).selectinload(UserRoleAssignment.role))
        )
        return self.session.scalars(statement).one_or_none()

    def find_user_account_by_username(self, tenant_id: str, username: str) -> UserAccount | None:
        statement = (
            select(UserAccount)
            .where(UserAccount.tenant_id == tenant_id, func.lower(UserAccount.username) == username.lower())
            .options(selectinload(UserAccount.role_assignments).selectinload(UserRoleAssignment.role))
        )
        return self.session.scalars(statement).one_or_none()

    def find_user_account_by_email(self, tenant_id: str, email: str) -> UserAccount | None:
        statement = (
            select(UserAccount)
            .where(UserAccount.tenant_id == tenant_id, func.lower(UserAccount.email) == email.lower())
            .options(selectinload(UserAccount.role_assignments).selectinload(UserRoleAssignment.role))
        )
        return self.session.scalars(statement).one_or_none()

    def create_user_account(self, row: UserAccount) -> UserAccount:
        self.session.add(row)
        self._commit()
        return self.get_user_account(row.tenant_id, row.id) or row

    def update_user_account(self, row: UserAccount) -> UserAccount:
        self.session.add(row)
        self._commit()
        return self.get_user_account(row.tenant_id, row.id) or row

    def revoke_active_sessions_for_user(self, user_id: str, *, reason: str, at_time) -> None:  # noqa: ANN001
        sessions = self.session.scalars(
            select(UserSession).where(
                UserSession.user_account_id == user_id,
                UserSession.revoked_at.is_(None),
            )
        ).all()
        changed = False
        for session_row in sessions:
            session_row.status = "revoked"
            session_row.revoked_at = at_time
            session_row.revoked_reason = reason
            session_row.last_seen_at = at_time
            self.session.add(session_row)
            changed = True
        if changed:
            self._commit()

    def get_role_by_key(self, role_key: str) -> Role | None:
        statement = select(Role).where(Role.key == role_key)
        return self.session.scalars(statement).one_or_none()

    def find_role_assignment(
        self,
        tenant_id: str,
        user_id: str,
        role_key: str,
    ) -> UserRoleAssignment | None:
        statement = (
            select(UserRoleAssignment)
            .join(Role, UserRoleAssignment.role_id == Role.id)
            .where(
                UserRoleAssignment.tenant_id == tenant_id,
                UserRoleAssignment.user_account_id == user_id,
                UserRoleAssignment.scope_type == "tenant",
                Role.key == role_key,
            )
            .options(selectinload(UserRoleAssignment.role))
        )
        return self.session.scalars(statement).one_or_none()

    def list_permission_keys_for_user(self, user_id: str, *, at_time: datetime | None = None) -> list[str]:
        now = at_time or datetime.now(UTC)
        statement = (
            select(Permission.key)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(
                UserRoleAssignment.user_account_id == user_id,
                UserRoleAssignment.status == "active",
                UserRoleAssignment.archived_at.is_(None),
                Role.status == "active",
                Role.archived_at.is_(None),
                or_(UserRoleAssignment.valid_from.is_(None), UserRoleAssignment.valid_from <= now),
                or_(UserRoleAssignment.valid_until.is_(None), UserRoleAssignment.valid_until >= now),
            )
            .distinct()
        )
        return list(self.session.scalars(statement).all())

    def create_role_assignment(self, row: UserRoleAssignment) -> UserRoleAssignment:
        self.session.add(row)
        self._commit()
        self.session.refresh(row)
        return row

    def update_role_assignment(self, row: UserRoleAssignment) -> UserRoleAssignment:
        self.session.add(row)
        self._commit()
        self.session.refresh(row)
        return row

    def create_job(self, row: ImportExportJob) -> ImportExportJob:
        self.session.add(row)
        self._commit()
        self.session.refresh(row)
        return row

    def save_job(self, row: ImportExportJob) -> ImportExportJob:
        self.session.add(row)
        self._commit()
        self.session.refresh(row)
        return row

    def get_branch(self, tenant_id: str, branch_id: str) -> Branch | None:
        statement = select(Branch).where(Branch.tenant_id == tenant_id, Branch.id == branch_id)
        return self.session.scalars(statement).one_or_none()

    def get_mandate(self, tenant_id: str, mandate_id: str) -> Mandate | None:
        statement = select(Mandate).where(Mandate.tenant_id == tenant_id, Mandate.id == mandate_id)
        return self.session.scalars(statement).one_or_none()

    def get_address(self, address_id: str) -> Address | None:
        statement = select(Address).where(Address.id == address_id)
        return self.session.scalars(statement).one_or_none()

    def create_address(self, row: Address) -> Address:
        self.session.add(row)
        self._commit()
        self.session.refresh(row)
        return row

    @staticmethod
    def employee_query() -> Select[tuple[Employee]]:
        return select(Employee).order_by(Employee.personnel_no)

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
