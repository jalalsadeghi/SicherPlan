"""Applicant workflow state machine and append-only activity trail."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.recruiting.models import Applicant, ApplicantStatusEvent
from app.modules.recruiting.schemas import (
    ApplicantActivityCreate,
    ApplicantActivityEventRead,
    ApplicantAttachmentRead,
    ApplicantConsentEvidenceRead,
    ApplicantDetailRead,
    ApplicantListItem,
    ApplicantTimelineRead,
    ApplicantTransitionRequest,
)


APPLICANT_STATUSES: tuple[str, ...] = (
    "submitted",
    "in_review",
    "interview_scheduled",
    "accepted",
    "rejected",
    "ready_for_conversion",
)

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "submitted": frozenset({"in_review", "rejected"}),
    "in_review": frozenset({"interview_scheduled", "accepted", "rejected"}),
    "interview_scheduled": frozenset({"in_review", "accepted", "rejected"}),
    "accepted": frozenset({"in_review", "ready_for_conversion"}),
    "rejected": frozenset({"in_review"}),
    "ready_for_conversion": frozenset(),
}

AUDITED_TRANSITIONS = frozenset({"accepted", "rejected", "ready_for_conversion"})
NOTE_ACTIVITY_TYPES = frozenset({"recruiter_note", "interview_note"})


class RecruitingWorkflowRepository(Protocol):
    def list_applicants(
        self,
        tenant_id: str,
        *,
        status: str | None = None,
        source_channel: str | None = None,
        search: str | None = None,
    ) -> list[Applicant]: ...
    def get_applicant(self, tenant_id: str, applicant_id: str) -> Applicant | None: ...
    def list_applicant_status_events(self, tenant_id: str, applicant_id: str) -> list[ApplicantStatusEvent]: ...
    def list_applicant_documents(self, tenant_id: str, applicant_id: str): ...  # noqa: ANN001
    def apply_applicant_transition(self, applicant: Applicant, event: ApplicantStatusEvent) -> Applicant: ...
    def create_applicant_status_event(self, event: ApplicantStatusEvent) -> ApplicantStatusEvent: ...


@dataclass(frozen=True, slots=True)
class RecruiterActor:
    tenant_id: str
    user_id: str
    session_id: str | None
    request_id: str | None

    @classmethod
    def from_context(cls, context: RequestAuthorizationContext) -> "RecruiterActor":
        return cls(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            session_id=context.session_id,
            request_id=context.request_id,
        )


class ApplicantWorkflowService:
    def __init__(
        self,
        repository: RecruitingWorkflowRepository,
        *,
        audit_service: AuditService,
    ) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_applicants(
        self,
        tenant_id: str,
        context: RequestAuthorizationContext,
        *,
        status: str | None = None,
        source_channel: str | None = None,
        search: str | None = None,
    ) -> list[ApplicantListItem]:
        self._ensure_tenant_scope(tenant_id, context)
        if status is not None:
            self._validate_status(status)
        return [
            ApplicantListItem.model_validate(row)
            for row in self.repository.list_applicants(
                tenant_id,
                status=status,
                source_channel=source_channel,
                search=search,
            )
        ]

    def get_detail(
        self,
        tenant_id: str,
        applicant_id: str,
        context: RequestAuthorizationContext,
    ) -> ApplicantDetailRead:
        self._ensure_tenant_scope(tenant_id, context)
        applicant = self._require_applicant(tenant_id, applicant_id)
        events = self.repository.list_applicant_status_events(tenant_id, applicant.id)
        documents = self.repository.list_applicant_documents(tenant_id, applicant.id)
        return ApplicantDetailRead(
            applicant=self._build_applicant_read(applicant),
            consent=ApplicantConsentEvidenceRead(
                consent_granted=applicant.gdpr_consent_granted,
                consent_at=applicant.gdpr_consent_at,
                policy_ref=applicant.gdpr_policy_ref,
                policy_version=applicant.gdpr_policy_version,
                submitted_origin=applicant.submitted_origin,
                submitted_ip=applicant.submitted_ip,
                submitted_user_agent=applicant.submitted_user_agent,
            ),
            attachments=[self._build_attachment_read(document) for document in documents],
            events=[ApplicantActivityEventRead.model_validate(event) for event in events],
            next_allowed_statuses=sorted(ALLOWED_TRANSITIONS.get(applicant.status, frozenset())),
        )

    def transition_applicant(
        self,
        tenant_id: str,
        applicant_id: str,
        payload: ApplicantTransitionRequest,
        context: RequestAuthorizationContext,
    ) -> ApplicantTimelineRead:
        self._ensure_tenant_scope(tenant_id, context)
        applicant = self._require_applicant(tenant_id, applicant_id)
        to_status = payload.to_status.strip()
        self._validate_status(to_status)
        self._assert_transition_allowed(applicant.status, to_status)
        self._validate_transition_payload(applicant.status, payload)

        now = datetime.now(UTC)
        actor = RecruiterActor.from_context(context)
        previous_status = applicant.status
        applicant.status = to_status
        applicant.updated_by_user_id = actor.user_id
        applicant.updated_at = now
        applicant.version_no += 1

        event = ApplicantStatusEvent(
            tenant_id=tenant_id,
            applicant_id=applicant.id,
            event_type=self._derive_transition_event_type(previous_status, to_status),
            from_status=previous_status,
            to_status=to_status,
            note=self._normalize_optional(payload.note),
            decision_reason=self._normalize_optional(payload.decision_reason),
            interview_scheduled_at=payload.interview_scheduled_at,
            hiring_target_date=payload.hiring_target_date,
            metadata_json=self._transition_metadata(payload),
            actor_user_id=actor.user_id,
        )
        updated = self.repository.apply_applicant_transition(applicant, event)
        self._record_transition_audit(updated, event, actor)
        timeline = self.get_detail(tenant_id, applicant.id, context)
        return ApplicantTimelineRead(
            applicant=ApplicantListItem.model_validate(timeline.applicant),
            events=timeline.events,
        )

    def add_activity(
        self,
        tenant_id: str,
        applicant_id: str,
        payload: ApplicantActivityCreate,
        context: RequestAuthorizationContext,
    ) -> ApplicantActivityEventRead:
        self._ensure_tenant_scope(tenant_id, context)
        applicant = self._require_applicant(tenant_id, applicant_id)
        if payload.activity_type not in NOTE_ACTIVITY_TYPES:
            raise ApiException(
                422,
                "recruiting.applicant.invalid_activity_type",
                "errors.recruiting.applicant.invalid_activity_type",
                {"activity_type": payload.activity_type},
            )
        actor = RecruiterActor.from_context(context)
        event = ApplicantStatusEvent(
            tenant_id=tenant_id,
            applicant_id=applicant.id,
            event_type=payload.activity_type,
            from_status=applicant.status,
            to_status=applicant.status,
            note=self._normalize_required_note(payload.note),
            decision_reason=self._normalize_optional(payload.decision_reason),
            interview_scheduled_at=payload.interview_scheduled_at,
            hiring_target_date=payload.hiring_target_date,
            metadata_json={},
            actor_user_id=actor.user_id,
        )
        created = self.repository.create_applicant_status_event(event)
        return ApplicantActivityEventRead.model_validate(created)

    @staticmethod
    def _build_applicant_read(applicant: Applicant):
        from app.modules.recruiting.public_service import applicant_to_read

        return applicant_to_read(applicant)

    @staticmethod
    def _build_attachment_read(document) -> ApplicantAttachmentRead:  # noqa: ANN001
        version = None
        if document.current_version_no:
            version = next(
                (item for item in document.versions if item.version_no == document.current_version_no),
                None,
            )
        link = next(
            (
                item
                for item in document.links
                if item.owner_type == "hr.applicant"
            ),
            None,
        )
        return ApplicantAttachmentRead(
            document_id=document.id,
            relation_type=link.relation_type if link else "attachment",
            label=link.label if link else None,
            title=document.title,
            document_type_key=document.document_type.key if document.document_type else None,
            file_name=version.file_name if version else None,
            content_type=version.content_type if version else None,
            current_version_no=document.current_version_no or None,
            linked_at=link.linked_at if link else None,
        )

    def _ensure_tenant_scope(self, tenant_id: str, context: RequestAuthorizationContext) -> None:
        if not context.is_platform_admin and context.tenant_id != tenant_id:
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

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in APPLICANT_STATUSES:
            raise ApiException(
                422,
                "recruiting.applicant.invalid_status",
                "errors.recruiting.applicant.invalid_status",
                {"status": status},
            )

    def _assert_transition_allowed(self, from_status: str, to_status: str) -> None:
        if to_status not in ALLOWED_TRANSITIONS.get(from_status, frozenset()):
            raise ApiException(
                409,
                "recruiting.applicant.transition_not_allowed",
                "errors.recruiting.applicant.transition_not_allowed",
                {"from_status": from_status, "to_status": to_status},
            )

    def _validate_transition_payload(self, from_status: str, payload: ApplicantTransitionRequest) -> None:
        if payload.to_status == "interview_scheduled" and payload.interview_scheduled_at is None:
            raise ApiException(
                422,
                "recruiting.applicant.interview_time_required",
                "errors.recruiting.applicant.interview_time_required",
            )
        if payload.to_status in {"accepted", "rejected"} and self._normalize_optional(payload.decision_reason) is None:
            raise ApiException(
                422,
                "recruiting.applicant.decision_reason_required",
                "errors.recruiting.applicant.decision_reason_required",
                {"to_status": payload.to_status},
            )
        if from_status in {"accepted", "rejected"} and payload.to_status == "in_review" and self._normalize_optional(payload.note) is None:
            raise ApiException(
                422,
                "recruiting.applicant.reopen_note_required",
                "errors.recruiting.applicant.reopen_note_required",
            )
        if payload.to_status == "ready_for_conversion" and payload.hiring_target_date is None:
            raise ApiException(
                422,
                "recruiting.applicant.hiring_target_required",
                "errors.recruiting.applicant.hiring_target_required",
            )

    @staticmethod
    def _derive_transition_event_type(from_status: str, to_status: str) -> str:
        if to_status == "interview_scheduled":
            return "interview_scheduled"
        if to_status in {"accepted", "rejected"}:
            return "decision"
        if from_status in {"accepted", "rejected"} and to_status == "in_review":
            return "reopened"
        if to_status == "ready_for_conversion":
            return "ready_for_conversion"
        return "status_transition"

    @staticmethod
    def _transition_metadata(payload: ApplicantTransitionRequest) -> dict[str, object]:
        metadata: dict[str, object] = {}
        if payload.interview_scheduled_at is not None:
            metadata["interview_scheduled_at"] = payload.interview_scheduled_at.isoformat()
        if payload.hiring_target_date is not None:
            metadata["hiring_target_date"] = payload.hiring_target_date.isoformat()
        return metadata

    def _record_transition_audit(self, applicant: Applicant, event: ApplicantStatusEvent, actor: RecruiterActor) -> None:
        if event.event_type not in {"reopened", "ready_for_conversion"} and event.to_status not in AUDITED_TRANSITIONS:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=actor.tenant_id,
                user_id=actor.user_id,
                session_id=actor.session_id,
                request_id=actor.request_id,
                source="api",
            ),
            event_type=f"recruiting.applicant.{event.event_type}",
            entity_type="hr.applicant",
            entity_id=applicant.id,
            tenant_id=applicant.tenant_id,
            before_json={"status": event.from_status},
            after_json={"status": event.to_status},
            metadata_json={
                "application_no": applicant.application_no,
                "decision_reason": event.decision_reason,
                "note": event.note,
                "interview_scheduled_at": event.interview_scheduled_at.isoformat() if event.interview_scheduled_at else None,
                "hiring_target_date": event.hiring_target_date.isoformat() if event.hiring_target_date else None,
            },
        )

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def _normalize_required_note(self, value: str | None) -> str:
        normalized = self._normalize_optional(value)
        if normalized is None:
            raise ApiException(
                422,
                "recruiting.applicant.note_required",
                "errors.recruiting.applicant.note_required",
            )
        return normalized
