from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import uuid4

from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.recruiting.models import Applicant, ApplicantStatusEvent
from app.modules.recruiting.schemas import ApplicantActivityCreate, ApplicantTransitionRequest
from app.modules.recruiting.workflow_service import ApplicantWorkflowService


class FakeAuditService:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record_business_event(self, **kwargs):
        self.events.append(kwargs)
        return None


@dataclass
class FakeWorkflowRepository:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.applicant = Applicant(
            id=str(uuid4()),
            tenant_id="tenant-1",
            application_no="APP-1001",
            submission_key="submission-1",
            source_channel="public_form",
            source_detail="site",
            locale="de",
            first_name="Anna",
            last_name="Wagner",
            email="anna@example.de",
            desired_role="Objektschutz",
            gdpr_consent_granted=True,
            gdpr_consent_at=datetime.now(UTC),
            gdpr_policy_ref="privacy",
            gdpr_policy_version="2026-03",
            custom_fields_json={},
            metadata_json={},
            status="submitted",
            created_at=now,
            updated_at=now,
            version_no=1,
        )
        self.events: list[ApplicantStatusEvent] = []

    def list_applicants(self, tenant_id: str, *, status: str | None = None) -> list[Applicant]:
        if tenant_id != self.applicant.tenant_id:
            return []
        if status and self.applicant.status != status:
            return []
        return [self.applicant]

    def get_applicant(self, tenant_id: str, applicant_id: str) -> Applicant | None:
        if tenant_id == self.applicant.tenant_id and applicant_id == self.applicant.id:
            return self.applicant
        return None

    def list_applicant_status_events(self, tenant_id: str, applicant_id: str) -> list[ApplicantStatusEvent]:
        if tenant_id != self.applicant.tenant_id or applicant_id != self.applicant.id:
            return []
        return list(sorted(self.events, key=lambda item: (item.created_at, item.id)))

    def list_applicant_documents(self, tenant_id: str, applicant_id: str) -> list[object]:
        if tenant_id != self.applicant.tenant_id or applicant_id != self.applicant.id:
            return []
        return []

    def apply_applicant_transition(self, applicant: Applicant, event: ApplicantStatusEvent) -> Applicant:
        if event.id is None:
            event.id = str(uuid4())
        if event.created_at is None:
            event.created_at = datetime.now(UTC)
        self.applicant = applicant
        self.events.append(event)
        return applicant

    def create_applicant_status_event(self, event: ApplicantStatusEvent) -> ApplicantStatusEvent:
        if event.id is None:
            event.id = str(uuid4())
        if event.created_at is None:
            event.created_at = datetime.now(UTC)
        self.events.append(event)
        return event


def make_context(*, tenant_id: str = "tenant-1", user_id: str = "user-1") -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id=user_id,
        tenant_id=tenant_id,
        request_id="req-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"recruiting.applicant.read", "recruiting.applicant.write"}),
        scopes=(),
    )


class ApplicantWorkflowServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeWorkflowRepository()
        self.audit_service = FakeAuditService()
        self.service = ApplicantWorkflowService(self.repository, audit_service=self.audit_service)
        self.context = make_context()

    def test_valid_transition_writes_append_only_event_with_actor(self) -> None:
        timeline = self.service.transition_applicant(
            "tenant-1",
            self.repository.applicant.id,
            ApplicantTransitionRequest(to_status="in_review"),
            self.context,
        )

        self.assertEqual(timeline.applicant.status, "in_review")
        self.assertEqual(len(timeline.events), 1)
        self.assertEqual(timeline.events[0].event_type, "status_transition")
        self.assertEqual(timeline.events[0].actor_user_id, "user-1")
        self.assertEqual(timeline.events[0].from_status, "submitted")
        self.assertEqual(timeline.events[0].to_status, "in_review")

    def test_detail_exposes_consent_evidence_and_next_allowed_statuses(self) -> None:
        detail = self.service.get_detail("tenant-1", self.repository.applicant.id, self.context)

        self.assertEqual(detail.applicant.application_no, "APP-1001")
        self.assertEqual(detail.consent.policy_version, "2026-03")
        self.assertEqual(detail.next_allowed_statuses, ["in_review", "rejected"])
        self.assertEqual(detail.attachments, [])

    def test_invalid_transition_is_blocked(self) -> None:
        with self.assertRaises(ApiException) as ctx:
            self.service.transition_applicant(
                "tenant-1",
                self.repository.applicant.id,
                ApplicantTransitionRequest(to_status="ready_for_conversion", hiring_target_date=date(2026, 4, 1)),
                self.context,
            )

        self.assertEqual(ctx.exception.message_key, "errors.recruiting.applicant.transition_not_allowed")
        self.assertEqual(len(self.repository.events), 0)

    def test_interview_transition_requires_schedule_and_preserves_order(self) -> None:
        self.service.transition_applicant(
            "tenant-1",
            self.repository.applicant.id,
            ApplicantTransitionRequest(to_status="in_review"),
            self.context,
        )
        scheduled_at = datetime(2026, 3, 20, 9, 30, tzinfo=UTC)
        timeline = self.service.transition_applicant(
            "tenant-1",
            self.repository.applicant.id,
            ApplicantTransitionRequest(
                to_status="interview_scheduled",
                interview_scheduled_at=scheduled_at,
                note="Telefonisches Erstgespraech",
            ),
            self.context,
        )

        self.assertEqual(len(timeline.events), 2)
        self.assertEqual(timeline.events[-1].event_type, "interview_scheduled")
        self.assertEqual(timeline.events[-1].interview_scheduled_at, scheduled_at)
        self.assertEqual([event.to_status for event in timeline.events], ["in_review", "interview_scheduled"])

    def test_accept_reject_reopen_and_ready_for_conversion_are_audited(self) -> None:
        self.service.transition_applicant(
            "tenant-1",
            self.repository.applicant.id,
            ApplicantTransitionRequest(to_status="in_review"),
            self.context,
        )
        self.service.transition_applicant(
            "tenant-1",
            self.repository.applicant.id,
            ApplicantTransitionRequest(to_status="accepted", decision_reason="Qualifikation passt"),
            self.context,
        )
        self.service.transition_applicant(
            "tenant-1",
            self.repository.applicant.id,
            ApplicantTransitionRequest(to_status="in_review", note="Unterlagen erneut pruefen"),
            self.context,
        )
        self.service.transition_applicant(
            "tenant-1",
            self.repository.applicant.id,
            ApplicantTransitionRequest(to_status="accepted", decision_reason="Final bestaetigt"),
            self.context,
        )
        self.service.transition_applicant(
            "tenant-1",
            self.repository.applicant.id,
            ApplicantTransitionRequest(to_status="ready_for_conversion", hiring_target_date=date(2026, 4, 1)),
            self.context,
        )

        self.assertEqual(
            [event["event_type"] for event in self.audit_service.events],
            [
                "recruiting.applicant.decision",
                "recruiting.applicant.reopened",
                "recruiting.applicant.decision",
                "recruiting.applicant.ready_for_conversion",
            ],
        )

    def test_reject_requires_decision_reason(self) -> None:
        self.service.transition_applicant(
            "tenant-1",
            self.repository.applicant.id,
            ApplicantTransitionRequest(to_status="in_review"),
            self.context,
        )

        with self.assertRaises(ApiException) as ctx:
            self.service.transition_applicant(
                "tenant-1",
                self.repository.applicant.id,
                ApplicantTransitionRequest(to_status="rejected"),
                self.context,
            )

        self.assertEqual(ctx.exception.message_key, "errors.recruiting.applicant.decision_reason_required")

    def test_recruiter_note_and_interview_note_are_append_only(self) -> None:
        first = self.service.add_activity(
            "tenant-1",
            self.repository.applicant.id,
            ApplicantActivityCreate(activity_type="recruiter_note", note="Rueckruf angefragt"),
            self.context,
        )
        second = self.service.add_activity(
            "tenant-1",
            self.repository.applicant.id,
            ApplicantActivityCreate(
                activity_type="interview_note",
                note="Interview gut verlaufen",
                interview_scheduled_at=datetime(2026, 3, 21, 8, 0, tzinfo=UTC),
            ),
            self.context,
        )

        self.assertEqual(first.event_type, "recruiter_note")
        self.assertEqual(second.event_type, "interview_note")
        self.assertEqual(len(self.repository.events), 2)
        self.assertEqual([event.note for event in self.repository.events], ["Rueckruf angefragt", "Interview gut verlaufen"])

    def test_cross_tenant_scope_is_blocked(self) -> None:
        with self.assertRaises(ApiException) as ctx:
            self.service.list_applicants("tenant-2", make_context(), status=None)

        self.assertEqual(ctx.exception.message_key, "errors.recruiting.applicant.scope_denied")


if __name__ == "__main__":
    unittest.main()
