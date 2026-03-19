"""SQLAlchemy persistence for recruiting applicant intake and workflow."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.core.models import Tenant, TenantSetting
from app.modules.employees.models import Employee
from app.modules.iam.audit_models import AuditEvent
from app.modules.platform_services.docs_models import Document, DocumentLink
from app.modules.recruiting.models import Applicant, ApplicantStatusEvent


APPLICANT_FORM_SETTING_KEY = "recruiting.applicant_form"


class SqlAlchemyRecruitingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_tenant_by_code(self, tenant_code: str) -> Tenant | None:
        statement = select(Tenant).where(Tenant.code == tenant_code)
        return self.session.scalars(statement).one_or_none()

    def get_tenant_setting_value(self, tenant_id: str, key: str) -> dict[str, object] | None:
        statement = select(TenantSetting).where(TenantSetting.tenant_id == tenant_id, TenantSetting.key == key)
        row = self.session.scalars(statement).one_or_none()
        return None if row is None else row.value_json

    def find_applicant_by_submission_key(self, tenant_id: str, submission_key: str) -> Applicant | None:
        statement = select(Applicant).where(
            Applicant.tenant_id == tenant_id,
            Applicant.submission_key == submission_key,
        )
        return self.session.scalars(statement).one_or_none()

    def find_applicant_by_application_no(self, tenant_id: str, application_no: str) -> Applicant | None:
        statement = select(Applicant).where(
            Applicant.tenant_id == tenant_id,
            Applicant.application_no == application_no,
        )
        return self.session.scalars(statement).one_or_none()

    def create_applicant(self, row: Applicant) -> Applicant:
        self.session.add(row)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(row)
        return row

    @staticmethod
    def applicant_query() -> Select[tuple[Applicant]]:
        return select(Applicant).order_by(Applicant.created_at.desc())

    def list_applicants(
        self,
        tenant_id: str,
        *,
        status: str | None = None,
        source_channel: str | None = None,
        search: str | None = None,
    ) -> list[Applicant]:
        statement = self.applicant_query().where(Applicant.tenant_id == tenant_id)
        if status is not None:
            statement = statement.where(Applicant.status == status)
        if source_channel is not None:
            statement = statement.where(Applicant.source_channel == source_channel)
        if search is not None:
            normalized = f"%{search.strip().lower()}%"
            statement = statement.where(
                Applicant.application_no.ilike(normalized)
                | Applicant.first_name.ilike(normalized)
                | Applicant.last_name.ilike(normalized)
                | Applicant.email.ilike(normalized)
                | Applicant.desired_role.ilike(normalized)
            )
        return list(self.session.scalars(statement).all())

    def get_applicant(self, tenant_id: str, applicant_id: str) -> Applicant | None:
        statement = select(Applicant).where(Applicant.tenant_id == tenant_id, Applicant.id == applicant_id)
        return self.session.scalars(statement).one_or_none()

    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None:
        statement = select(Employee).where(Employee.tenant_id == tenant_id, Employee.id == employee_id)
        return self.session.scalars(statement).one_or_none()

    def list_applicant_status_events(self, tenant_id: str, applicant_id: str) -> list[ApplicantStatusEvent]:
        statement = (
            select(ApplicantStatusEvent)
            .where(
                ApplicantStatusEvent.tenant_id == tenant_id,
                ApplicantStatusEvent.applicant_id == applicant_id,
            )
            .order_by(ApplicantStatusEvent.created_at.asc(), ApplicantStatusEvent.id.asc())
        )
        return list(self.session.scalars(statement).all())

    def list_applicant_documents(self, tenant_id: str, applicant_id: str) -> list[Document]:
        statement = (
            select(Document)
            .join(DocumentLink, DocumentLink.document_id == Document.id)
            .where(
                Document.tenant_id == tenant_id,
                DocumentLink.tenant_id == tenant_id,
                DocumentLink.owner_type == "hr.applicant",
                DocumentLink.owner_id == applicant_id,
            )
            .order_by(Document.created_at.asc())
        )
        return list(self.session.scalars(statement).unique().all())

    def list_applicant_document_links(self, tenant_id: str, applicant_id: str) -> list[DocumentLink]:
        statement = (
            select(DocumentLink)
            .where(
                DocumentLink.tenant_id == tenant_id,
                DocumentLink.owner_type == "hr.applicant",
                DocumentLink.owner_id == applicant_id,
            )
            .order_by(DocumentLink.linked_at.asc(), DocumentLink.id.asc())
        )
        return list(self.session.scalars(statement).all())

    def get_latest_hiring_target_date(self, tenant_id: str, applicant_id: str):
        statement = (
            select(ApplicantStatusEvent)
            .where(
                ApplicantStatusEvent.tenant_id == tenant_id,
                ApplicantStatusEvent.applicant_id == applicant_id,
                ApplicantStatusEvent.hiring_target_date.is_not(None),
            )
            .order_by(ApplicantStatusEvent.created_at.desc(), ApplicantStatusEvent.id.desc())
        )
        row = self.session.scalars(statement).first()
        return None if row is None else row.hiring_target_date

    def next_employee_personnel_no(self, tenant_id: str) -> str:
        statement = select(Employee.personnel_no).where(Employee.tenant_id == tenant_id)
        max_number = 0
        for value in self.session.scalars(statement).all():
            if value is None:
                continue
            match = re.fullmatch(r"EMP-(\d{5})", value)
            if match is None:
                continue
            max_number = max(max_number, int(match.group(1)))
        return f"EMP-{max_number + 1:05d}"

    def convert_applicant(
        self,
        *,
        applicant: Applicant,
        employee: Employee,
        event: ApplicantStatusEvent,
        audit_event: AuditEvent,
        employee_document_links: list[DocumentLink],
    ) -> tuple[Applicant, Employee]:
        now = datetime.now(UTC)
        self.session.add(employee)
        try:
            self.session.flush()
            event.metadata_json["employee_id"] = employee.id
            event.metadata_json["personnel_no"] = employee.personnel_no
            audit_event.after_json = {
                "status": applicant.status,
                "converted_employee_id": employee.id,
            }
            audit_event.metadata_json = {
                **audit_event.metadata_json,
                "employee_id": employee.id,
                "personnel_no": employee.personnel_no,
            }
            for link in employee_document_links:
                link.owner_id = employee.id
            applicant.converted_employee_id = employee.id
            applicant.updated_at = now
            applicant.version_no += 1
            self.session.add(applicant)
            self.session.add(event)
            self.session.add(audit_event)
            for link in employee_document_links:
                self.session.add(link)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.session.refresh(applicant)
        self.session.refresh(employee)
        return applicant, employee

    def apply_applicant_transition(self, applicant: Applicant, event: ApplicantStatusEvent) -> Applicant:
        self.session.add(applicant)
        self.session.add(event)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(applicant)
        return applicant

    def create_applicant_status_event(self, event: ApplicantStatusEvent) -> ApplicantStatusEvent:
        self.session.add(event)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(event)
        return event
