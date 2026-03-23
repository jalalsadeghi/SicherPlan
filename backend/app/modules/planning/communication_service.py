"""Planning-context outbound communication built on the shared communication backbone."""

from __future__ import annotations

from typing import Protocol

from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.comm_schemas import MessageRecipientCreate, MessageTemplateUpsert, OutboundMessageRead, RenderedMessageCreate
from app.modules.platform_services.comm_service import CommunicationService
from app.modules.planning.schemas import PlanningDispatchCreate, PlanningDispatchPreviewRead, PlanningDispatchRecipientPreviewRead


class PlanningCommunicationRepository(Protocol):
    def get_shift(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[object]: ...
    def get_team(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def list_team_members(self, tenant_id: str, filters): ...  # noqa: ANN001
    def list_subcontractor_releases_for_shift(self, tenant_id: str, shift_id: str) -> list[object]: ...


class PlanningCommunicationService:
    DEFAULT_TEMPLATE_KEY = "planning.dispatch.shift_update"

    def __init__(self, repository: PlanningCommunicationRepository, *, communication_service: CommunicationService) -> None:
        self.repository = repository
        self.communication_service = communication_service

    def preview_message(
        self,
        tenant_id: str,
        payload: PlanningDispatchCreate,
        actor: RequestAuthorizationContext,
    ) -> PlanningDispatchPreviewRead:
        self._ensure_tenant_scope(tenant_id, payload.tenant_id)
        shift = self._require_shift(tenant_id, payload.shift_id)
        recipients = self._build_recipients(tenant_id, shift, payload)
        placeholders = self._placeholders_for_shift(shift, audience_codes=payload.audience_codes)
        return PlanningDispatchPreviewRead(
            tenant_id=tenant_id,
            shift_id=shift.id,
            channel=payload.channel,
            template_key=payload.template_key,
            language_code=payload.language_code,
            audience_codes=payload.audience_codes,
            subject_preview=f"{placeholders['shift_label']} {placeholders['schedule_date']}",
            body_preview=self._preview_body(placeholders),
            redacted=bool(shift.stealth_mode_flag and "subcontractor_release" in payload.audience_codes),
            recipients=recipients,
        )

    def queue_message(
        self,
        tenant_id: str,
        payload: PlanningDispatchCreate,
        actor: RequestAuthorizationContext,
    ) -> OutboundMessageRead:
        self._ensure_tenant_scope(tenant_id, payload.tenant_id)
        shift = self._require_shift(tenant_id, payload.shift_id)
        if shift.release_state != "released":
            raise ApiException(409, "planning.communication.release_required", "errors.planning.communication.release_required")
        recipients = self._build_recipients(tenant_id, shift, payload)
        if not recipients:
            raise ApiException(409, "planning.communication.no_recipients", "errors.planning.communication.no_recipients")
        self._ensure_templates(tenant_id, actor, payload.template_key)
        comm_payload = RenderedMessageCreate(
            tenant_id=tenant_id,
            channel=payload.channel,
            template_key=payload.template_key,
            language_code=payload.language_code,
            placeholders=self._placeholders_for_shift(shift, audience_codes=payload.audience_codes) | payload.extra_placeholders,
            recipients=[
                MessageRecipientCreate(
                    recipient_kind=item.recipient_kind,
                    destination=item.destination,
                    display_name=item.display_name,
                    metadata_json=item.metadata_json,
                )
                for item in recipients
            ],
            attachment_document_ids=payload.attachment_document_ids,
            related_entity_type="ops.shift",
            related_entity_id=shift.id,
            metadata_json={
                "planning_context": "shift_dispatch",
                "shift_id": shift.id,
                "audience_codes": payload.audience_codes,
                "stealth_mode": shift.stealth_mode_flag,
            },
        )
        return self.communication_service.render_outbound_message(tenant_id, comm_payload, actor)

    def get_message(
        self,
        tenant_id: str,
        message_id: str,
        actor: RequestAuthorizationContext,
    ) -> OutboundMessageRead:
        return self.communication_service.get_outbound_message(tenant_id, message_id, actor)

    def _build_recipients(
        self,
        tenant_id: str,
        shift,
        payload: PlanningDispatchCreate,  # noqa: ANN001
    ) -> list[PlanningDispatchRecipientPreviewRead]:
        recipients: list[PlanningDispatchRecipientPreviewRead] = []
        if "assigned_employees" in payload.audience_codes:
            for assignment in self.repository.list_assignments_in_shift(tenant_id, shift.id):
                if getattr(assignment, "employee_id", None) is None:
                    continue
                recipients.append(
                    PlanningDispatchRecipientPreviewRead(
                        recipient_kind="to",
                        audience_code="assigned_employees",
                        audience_ref=str(assignment.employee_id),
                        destination=f"employee:{assignment.employee_id}",
                        display_name=f"employee:{assignment.employee_id}",
                        redacted=False,
                        metadata_json={"assignment_id": assignment.id},
                    )
                )
        if "teams" in payload.audience_codes:
            from app.modules.planning.schemas import StaffingFilter

            for team_id in payload.team_ids:
                team = self.repository.get_team(tenant_id, team_id)
                if team is None:
                    continue
                for member in self.repository.list_team_members(tenant_id, StaffingFilter(team_id=team_id, include_archived=False)):
                    audience_ref = member.employee_id or member.subcontractor_worker_id
                    if audience_ref is None:
                        continue
                    destination_prefix = "employee" if member.employee_id else "worker"
                    recipients.append(
                        PlanningDispatchRecipientPreviewRead(
                            recipient_kind="to",
                            audience_code="teams",
                            audience_ref=str(audience_ref),
                            destination=f"{destination_prefix}:{audience_ref}",
                            display_name=f"{team.name}:{audience_ref}",
                            redacted=False,
                            metadata_json={"team_id": team_id, "team_member_id": member.id},
                        )
                    )
        if "subcontractor_release" in payload.audience_codes:
            for release in self.repository.list_subcontractor_releases_for_shift(tenant_id, shift.id):
                recipients.append(
                    PlanningDispatchRecipientPreviewRead(
                        recipient_kind="to",
                        audience_code="subcontractor_release",
                        audience_ref=str(release.subcontractor_id),
                        destination=f"subcontractor:{release.subcontractor_id}",
                        display_name=f"subcontractor:{release.subcontractor_id}",
                        redacted=bool(shift.stealth_mode_flag),
                        metadata_json={"release_id": release.id},
                    )
                )
        deduped: dict[tuple[str, str], PlanningDispatchRecipientPreviewRead] = {}
        for item in recipients:
            deduped[(item.audience_code, item.destination)] = item
        return list(deduped.values())

    def _placeholders_for_shift(self, shift, *, audience_codes: list[str]) -> dict[str, object]:  # noqa: ANN001
        redacted = bool(shift.stealth_mode_flag and "subcontractor_release" in audience_codes)
        return {
            "shift_label": shift.shift_type_code,
            "schedule_date": shift.starts_at.date().isoformat(),
            "starts_at": shift.starts_at.isoformat(),
            "ends_at": shift.ends_at.isoformat(),
            "location_label": "redacted" if redacted else (shift.location_text or ""),
            "meeting_point": "redacted" if redacted else (shift.meeting_point or ""),
            "stealth_mode": redacted,
        }

    @staticmethod
    def _preview_body(placeholders: dict[str, object]) -> str:
        return (
            f"shift={placeholders['shift_label']}\n"
            f"date={placeholders['schedule_date']}\n"
            f"start={placeholders['starts_at']}\n"
            f"end={placeholders['ends_at']}\n"
            f"location={placeholders['location_label']}\n"
            f"meeting_point={placeholders['meeting_point']}"
        )

    def _ensure_templates(self, tenant_id: str, actor: RequestAuthorizationContext, template_key: str) -> None:
        self.communication_service.upsert_template(
            tenant_id,
            MessageTemplateUpsert(
                tenant_id=tenant_id,
                channel="email",
                template_key=template_key,
                language_code="de",
                subject_template="{{shift_label}} {{schedule_date}}",
                body_template="Schicht {{shift_label}} am {{schedule_date}} von {{starts_at}} bis {{ends_at}}. Ort: {{location_label}}. Treffpunkt: {{meeting_point}}.",
            ),
            actor,
        )
        self.communication_service.upsert_template(
            tenant_id,
            MessageTemplateUpsert(
                tenant_id=tenant_id,
                channel="email",
                template_key=template_key,
                language_code="en",
                subject_template="{{shift_label}} {{schedule_date}}",
                body_template="Shift {{shift_label}} on {{schedule_date}} from {{starts_at}} to {{ends_at}}. Location: {{location_label}}. Meeting point: {{meeting_point}}.",
            ),
            actor,
        )

    def _require_shift(self, tenant_id: str, shift_id: str):
        row = self.repository.get_shift(tenant_id, shift_id)
        if row is None:
            raise ApiException(404, "planning.shift.not_found", "errors.planning.shift.not_found")
        return row

    @staticmethod
    def _ensure_tenant_scope(tenant_id: str, payload_tenant_id: str) -> None:
        if tenant_id != payload_tenant_id:
            raise ApiException(400, "planning.shift.scope_mismatch", "errors.planning.shift.scope_mismatch")
