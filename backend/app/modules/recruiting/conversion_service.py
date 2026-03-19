"""Accepted-applicant to employee conversion with idempotent provenance preservation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.employees.models import Employee
from app.modules.iam.audit_models import AuditEvent
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_models import DocumentLink
from app.modules.recruiting.models import Applicant, ApplicantStatusEvent
from app.modules.recruiting.schemas import ApplicantConversionRead


CONVERTIBLE_APPLICANT_STATUSES = frozenset({"accepted", "ready_for_conversion"})


class RecruitingConversionRepository(Protocol):
    def get_applicant(self, tenant_id: str, applicant_id: str) -> Applicant | None: ...
    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None: ...
    def list_applicant_document_links(self, tenant_id: str, applicant_id: str) -> list[DocumentLink]: ...
    def get_latest_hiring_target_date(self, tenant_id: str, applicant_id: str): ...  # noqa: ANN001
    def convert_applicant(
        self,
        *,
        applicant: Applicant,
        employee: Employee,
        event: ApplicantStatusEvent,
        audit_event: AuditEvent,
        employee_document_links: list[DocumentLink],
    ) -> tuple[Applicant, Employee]: ...


@dataclass(frozen=True, slots=True)
class RecruitingConversionActor:
    tenant_id: str
    user_id: str
    session_id: str | None
    request_id: str | None

    @classmethod
    def from_context(cls, context: RequestAuthorizationContext) -> "RecruitingConversionActor":
        return cls(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            session_id=context.session_id,
            request_id=context.request_id,
        )


class ApplicantConversionService:
    def __init__(self, repository: RecruitingConversionRepository) -> None:
        self.repository = repository

    def convert_applicant(
        self,
        tenant_id: str,
        applicant_id: str,
        context: RequestAuthorizationContext,
    ) -> ApplicantConversionRead:
        self._ensure_tenant_scope(tenant_id, context)
        applicant = self._require_applicant(tenant_id, applicant_id)
        if applicant.converted_employee_id is not None:
            employee = self.repository.get_employee(tenant_id, applicant.converted_employee_id)
            if employee is None:
                raise ApiException(
                    409,
                    "recruiting.applicant.converted_employee_missing",
                    "errors.recruiting.applicant.converted_employee_missing",
                )
            return ApplicantConversionRead(
                applicant_id=applicant.id,
                employee_id=employee.id,
                personnel_no=employee.personnel_no,
                applicant_status=applicant.status,
                already_converted=True,
            )

        if applicant.status not in CONVERTIBLE_APPLICANT_STATUSES:
            raise ApiException(
                409,
                "recruiting.applicant.transition_not_allowed",
                "errors.recruiting.applicant.transition_not_allowed",
                {"from_status": applicant.status, "to_status": "converted"},
            )

        actor = RecruitingConversionActor.from_context(context)
        now = datetime.now(UTC)
        hire_date = self.repository.get_latest_hiring_target_date(tenant_id, applicant.id)
        employee = Employee(
            tenant_id=tenant_id,
            personnel_no=self._derive_personnel_no(applicant.application_no),
            first_name=applicant.first_name.strip(),
            last_name=applicant.last_name.strip(),
            preferred_name=None,
            work_email=None,
            work_phone=None,
            mobile_phone=self._normalize_optional(applicant.phone),
            hire_date=hire_date,
            notes=None,
            created_by_user_id=actor.user_id,
            updated_by_user_id=actor.user_id,
        )

        event = ApplicantStatusEvent(
            tenant_id=tenant_id,
            applicant_id=applicant.id,
            event_type="converted",
            from_status=applicant.status,
            to_status=applicant.status,
            note="Applicant converted to employee aggregate.",
            metadata_json={
                "conversion_status": applicant.status,
                "policy_ref": applicant.gdpr_policy_ref,
                "policy_version": applicant.gdpr_policy_version,
                "consent_at": applicant.gdpr_consent_at.isoformat(),
                "hiring_target_date": hire_date.isoformat() if hire_date else None,
            },
            actor_user_id=actor.user_id,
            created_at=now,
        )

        employee_links = [
            DocumentLink(
                tenant_id=tenant_id,
                document_id=link.document_id,
                owner_type="hr.employee",
                owner_id="__pending_employee_id__",
                relation_type=link.relation_type,
                label=link.label,
                linked_by_user_id=actor.user_id,
                linked_at=now,
                metadata_json={
                    "transferred_from_owner_type": "hr.applicant",
                    "transferred_from_owner_id": applicant.id,
                    "applicant_application_no": applicant.application_no,
                    "consent_policy_ref": applicant.gdpr_policy_ref,
                    "consent_policy_version": applicant.gdpr_policy_version,
                },
            )
            for link in self.repository.list_applicant_document_links(tenant_id, applicant.id)
        ]

        audit_event = AuditEvent(
            tenant_id=tenant_id,
            actor_user_id=actor.user_id,
            actor_session_id=actor.session_id,
            event_type="recruiting.applicant.converted",
            entity_type="hr.applicant",
            entity_id=applicant.id,
            request_id=actor.request_id,
            source="api",
            before_json={"status": applicant.status, "converted_employee_id": None},
            after_json={"status": applicant.status, "converted_employee_id": None},
            metadata_json={
                "application_no": applicant.application_no,
                "consent_policy_ref": applicant.gdpr_policy_ref,
                "consent_policy_version": applicant.gdpr_policy_version,
                "consent_at": applicant.gdpr_consent_at.isoformat(),
                "document_count": len(employee_links),
            },
            created_at=now,
        )

        applicant.updated_by_user_id = actor.user_id
        converted_applicant, converted_employee = self.repository.convert_applicant(
            applicant=applicant,
            employee=employee,
            event=event,
            audit_event=audit_event,
            employee_document_links=employee_links,
        )

        return ApplicantConversionRead(
            applicant_id=converted_applicant.id,
            employee_id=converted_employee.id,
            personnel_no=converted_employee.personnel_no,
            applicant_status=converted_applicant.status,
            already_converted=False,
            converted_event_id=event.id,
        )

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _derive_personnel_no(application_no: str) -> str:
        return f"EMP-{application_no.strip()}"

    @staticmethod
    def _ensure_tenant_scope(tenant_id: str, context: RequestAuthorizationContext) -> None:
        if context.is_platform_admin or context.tenant_id == tenant_id:
            return
        raise ApiException(
            403,
            "recruiting.applicant.scope_denied",
            "errors.recruiting.applicant.scope_denied",
            {"tenant_id": tenant_id},
        )

    def _require_applicant(self, tenant_id: str, applicant_id: str) -> Applicant:
        applicant = self.repository.get_applicant(tenant_id, applicant_id)
        if applicant is None:
            raise ApiException(404, "recruiting.applicant.not_found", "errors.recruiting.applicant.not_found")
        return applicant
