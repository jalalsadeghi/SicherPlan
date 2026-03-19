from __future__ import annotations

import unittest
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import uuid4

from app.errors import ApiException
from app.modules.employees.models import Employee
from app.modules.iam.audit_models import AuditEvent
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_models import DocumentLink
from app.modules.recruiting.conversion_service import ApplicantConversionService
from app.modules.recruiting.models import Applicant, ApplicantStatusEvent


def make_context(*, tenant_id: str = "tenant-1", user_id: str = "user-1") -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id=user_id,
        tenant_id=tenant_id,
        request_id="req-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"recruiting.applicant.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
    )


@dataclass
class FakeConversionRepository:
    applicant_status: str = "ready_for_conversion"
    hiring_target_date: date | None = date(2026, 4, 1)
    fail_conversion: bool = False
    applicant: Applicant = field(init=False)
    employees: dict[str, Employee] = field(default_factory=dict)
    events: list[ApplicantStatusEvent] = field(default_factory=list)
    audit_events: list[AuditEvent] = field(default_factory=list)
    document_links: list[DocumentLink] = field(default_factory=list)

    def __post_init__(self) -> None:
        now = datetime.now(UTC)
        self.applicant = Applicant(
            id=str(uuid4()),
            tenant_id="tenant-1",
            application_no="APP-1001",
            submission_key="submission-1",
            source_channel="public_form",
            source_detail="landing-page",
            locale="de",
            first_name="Anna",
            last_name="Wagner",
            email="anna@example.de",
            phone="+491701234567",
            desired_role="Objektschutz",
            availability_date=date(2026, 4, 15),
            message="Motivated",
            gdpr_consent_granted=True,
            gdpr_consent_at=now,
            gdpr_policy_ref="privacy-policy",
            gdpr_policy_version="v2",
            custom_fields_json={},
            metadata_json={},
            submitted_ip="127.0.0.1",
            submitted_origin="https://example.de",
            submitted_user_agent="pytest",
            status=self.applicant_status,
            created_at=now,
            updated_at=now,
            version_no=1,
        )
        self.document_links = [
            DocumentLink(
                id=str(uuid4()),
                tenant_id="tenant-1",
                document_id="document-1",
                owner_type="hr.applicant",
                owner_id=self.applicant.id,
                relation_type="attachment",
                label="Lebenslauf",
                linked_by_user_id="user-1",
                linked_at=now,
                metadata_json={},
            )
        ]

    def get_applicant(self, tenant_id: str, applicant_id: str) -> Applicant | None:
        if tenant_id == self.applicant.tenant_id and applicant_id == self.applicant.id:
            return self.applicant
        return None

    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None:
        employee = self.employees.get(employee_id)
        if employee is None or employee.tenant_id != tenant_id:
            return None
        return employee

    def list_applicant_document_links(self, tenant_id: str, applicant_id: str) -> list[DocumentLink]:
        return [
            link
            for link in self.document_links
            if link.tenant_id == tenant_id and link.owner_type == "hr.applicant" and link.owner_id == applicant_id
        ]

    def get_latest_hiring_target_date(self, tenant_id: str, applicant_id: str):
        if tenant_id == self.applicant.tenant_id and applicant_id == self.applicant.id:
            return self.hiring_target_date
        return None

    def next_employee_personnel_no(self, tenant_id: str) -> str:
        assert tenant_id == self.applicant.tenant_id
        return f"EMP-{len(self.employees) + 1:05d}"

    def convert_applicant(
        self,
        *,
        applicant: Applicant,
        employee: Employee,
        event: ApplicantStatusEvent,
        audit_event: AuditEvent,
        employee_document_links: list[DocumentLink],
    ) -> tuple[Applicant, Employee]:
        snapshot = (
            deepcopy(self.applicant),
            deepcopy(self.employees),
            deepcopy(self.events),
            deepcopy(self.audit_events),
            deepcopy(self.document_links),
        )
        try:
            employee.id = employee.id or str(uuid4())
            employee.status = employee.status or "active"
            employee.created_at = employee.created_at or datetime.now(UTC)
            employee.updated_at = employee.updated_at or employee.created_at
            employee.version_no = employee.version_no or 1
            event.id = event.id or str(uuid4())
            event.metadata_json["employee_id"] = employee.id
            event.metadata_json["personnel_no"] = employee.personnel_no
            audit_event.id = audit_event.id or str(uuid4())
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
                link.id = link.id or str(uuid4())
                link.owner_id = employee.id
            applicant.converted_employee_id = employee.id
            applicant.updated_by_user_id = employee.created_by_user_id
            applicant.updated_at = datetime.now(UTC)
            applicant.version_no += 1
            if self.fail_conversion:
                raise RuntimeError("simulated conversion failure")
            self.employees[employee.id] = employee
            self.events.append(event)
            self.audit_events.append(audit_event)
            self.document_links.extend(employee_document_links)
            return applicant, employee
        except Exception:
            self.applicant, self.employees, self.events, self.audit_events, self.document_links = snapshot
            raise


class ApplicantConversionServiceTest(unittest.TestCase):
    def test_ready_for_conversion_creates_employee_and_preserves_document_provenance(self) -> None:
        repository = FakeConversionRepository(applicant_status="ready_for_conversion")
        service = ApplicantConversionService(repository)

        result = service.convert_applicant("tenant-1", repository.applicant.id, make_context())

        self.assertFalse(result.already_converted)
        self.assertEqual(result.personnel_no, "EMP-APP-1001")
        self.assertEqual(repository.applicant.converted_employee_id, result.employee_id)
        employee = repository.get_employee("tenant-1", result.employee_id)
        self.assertIsNotNone(employee)
        assert employee is not None
        self.assertEqual(employee.first_name, "Anna")
        self.assertEqual(employee.last_name, "Wagner")
        self.assertEqual(employee.mobile_phone, "+491701234567")
        self.assertIsNone(employee.work_email)
        self.assertEqual(employee.hire_date, date(2026, 4, 1))
        self.assertEqual(len(repository.events), 1)
        self.assertEqual(repository.events[0].event_type, "converted")
        self.assertEqual(repository.events[0].metadata_json["employee_id"], result.employee_id)
        self.assertEqual(len(repository.audit_events), 1)
        self.assertEqual(repository.audit_events[0].event_type, "recruiting.applicant.converted")
        employee_links = [link for link in repository.document_links if link.owner_type == "hr.employee"]
        applicant_links = [link for link in repository.document_links if link.owner_type == "hr.applicant"]
        self.assertEqual(len(employee_links), 1)
        self.assertEqual(len(applicant_links), 1)
        self.assertEqual(employee_links[0].document_id, applicant_links[0].document_id)
        self.assertEqual(employee_links[0].metadata_json["transferred_from_owner_id"], repository.applicant.id)

    def test_accepted_status_is_also_convertible(self) -> None:
        repository = FakeConversionRepository(applicant_status="accepted", hiring_target_date=None)
        service = ApplicantConversionService(repository)

        result = service.convert_applicant("tenant-1", repository.applicant.id, make_context())

        self.assertEqual(result.personnel_no, "EMP-APP-1001")
        employee = repository.get_employee("tenant-1", result.employee_id)
        assert employee is not None
        self.assertIsNone(employee.hire_date)

    def test_repeated_conversion_is_idempotent(self) -> None:
        repository = FakeConversionRepository(applicant_status="ready_for_conversion")
        service = ApplicantConversionService(repository)

        first = service.convert_applicant("tenant-1", repository.applicant.id, make_context())
        second = service.convert_applicant("tenant-1", repository.applicant.id, make_context())

        self.assertFalse(first.already_converted)
        self.assertTrue(second.already_converted)
        self.assertEqual(first.employee_id, second.employee_id)
        self.assertEqual(len(repository.employees), 1)
        self.assertEqual(len(repository.events), 1)
        self.assertEqual(len(repository.audit_events), 1)
        self.assertEqual(len([link for link in repository.document_links if link.owner_type == "hr.employee"]), 1)

    def test_non_convertible_status_is_blocked(self) -> None:
        repository = FakeConversionRepository(applicant_status="submitted")
        service = ApplicantConversionService(repository)

        with self.assertRaises(ApiException) as ctx:
            service.convert_applicant("tenant-1", repository.applicant.id, make_context())

        self.assertEqual(ctx.exception.message_key, "errors.recruiting.applicant.transition_not_allowed")
        self.assertEqual(len(repository.employees), 0)

    def test_repository_failure_rolls_back_partial_conversion_state(self) -> None:
        repository = FakeConversionRepository(applicant_status="ready_for_conversion", fail_conversion=True)
        service = ApplicantConversionService(repository)

        with self.assertRaises(RuntimeError):
            service.convert_applicant("tenant-1", repository.applicant.id, make_context())

        self.assertIsNone(repository.applicant.converted_employee_id)
        self.assertEqual(len(repository.employees), 0)
        self.assertEqual(len(repository.events), 0)
        self.assertEqual(len(repository.audit_events), 0)
        self.assertEqual(len([link for link in repository.document_links if link.owner_type == "hr.employee"]), 0)


if __name__ == "__main__":
    unittest.main()
