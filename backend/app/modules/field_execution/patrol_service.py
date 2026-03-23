"""Patrol round lifecycle, capture, replay, and linkage services."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.field_execution.models import PatrolRound, PatrolRoundEvent
from app.modules.field_execution.schemas import (
    PatrolAvailableRouteRead,
    PatrolCheckpointProgressRead,
    PatrolEvaluationRead,
    PatrolRoundAbortRequest,
    PatrolRoundCaptureRequest,
    PatrolRoundCompleteRequest,
    PatrolRoundEventRead,
    PatrolRoundRead,
    PatrolRoundStartRequest,
    PatrolSyncEnvelope,
    ReleasedWatchbookDocumentRead,
    WatchbookEntryCreate,
    WatchbookOpenRequest,
)
from app.modules.field_execution.watchbook_service import WatchbookService
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService


class PatrolRepository(Protocol):
    def find_employee_by_user_id(self, tenant_id: str, user_id: str): ...  # noqa: ANN001
    def list_released_employee_patrol_shifts(self, tenant_id: str, employee_id: str): ...  # noqa: ANN001
    def get_shift(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def get_patrol_route(self, tenant_id: str, patrol_route_id: str): ...  # noqa: ANN001
    def list_patrol_checkpoints(self, tenant_id: str, patrol_route_id: str): ...  # noqa: ANN001
    def find_active_patrol_round(self, tenant_id: str, employee_id: str): ...  # noqa: ANN001
    def find_patrol_round_by_sync_token(self, tenant_id: str, offline_sync_token: str): ...  # noqa: ANN001
    def create_patrol_round(self, row: PatrolRound): ...  # noqa: ANN001
    def save_patrol_round(self, row: PatrolRound): ...  # noqa: ANN001
    def get_patrol_round(self, tenant_id: str, patrol_round_id: str): ...  # noqa: ANN001
    def get_patrol_event_by_client_id(self, tenant_id: str, patrol_round_id: str, client_event_id: str): ...  # noqa: ANN001
    def next_patrol_event_sequence(self, tenant_id: str, patrol_round_id: str) -> int: ...
    def create_patrol_event(self, row: PatrolRoundEvent): ...  # noqa: ANN001
    def get_document(self, tenant_id: str, document_id: str): ...  # noqa: ANN001
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str): ...  # noqa: ANN001


POLICY_SCAN_TYPES = frozenset({"qr", "barcode", "nfc"})


@dataclass(frozen=True, slots=True)
class PatrolService:
    repository: PatrolRepository
    document_service: DocumentService
    audit_service: AuditService
    watchbook_service: WatchbookService

    def list_available_routes(self, actor: RequestAuthorizationContext) -> list[PatrolAvailableRouteRead]:
        employee = self._require_employee(actor)
        items: list[PatrolAvailableRouteRead] = []
        for shift in self.repository.list_released_employee_patrol_shifts(actor.tenant_id, employee.id):
            route = self._resolve_shift_route(shift)
            if route is None:
                continue
            checkpoints = self.repository.list_patrol_checkpoints(actor.tenant_id, route.id)
            active_round = self.repository.find_active_patrol_round(actor.tenant_id, employee.id)
            completed_ids = {
                event.checkpoint_id
                for event in (active_round.events if active_round and active_round.patrol_route_id == route.id else [])
                if event.event_type_code == "checkpoint_scanned" and event.checkpoint_id is not None
            }
            items.append(
                PatrolAvailableRouteRead(
                    shift_id=shift.id,
                    planning_record_id=shift.shift_plan.planning_record_id,
                    patrol_route_id=route.id,
                    route_no=route.route_no,
                    route_name=route.name,
                    schedule_date=shift.starts_at.date(),
                    work_start=shift.starts_at,
                    work_end=shift.ends_at,
                    meeting_point=shift.meeting_point,
                    location_label=shift.location_text,
                    checkpoint_count=len(checkpoints),
                    checkpoints=[
                        PatrolCheckpointProgressRead(
                            checkpoint_id=item.id,
                            sequence_no=item.sequence_no,
                            checkpoint_code=item.checkpoint_code,
                            label=item.label,
                            scan_type_code=item.scan_type_code,
                            minimum_dwell_seconds=item.minimum_dwell_seconds,
                            is_completed=item.id in completed_ids,
                            last_event_at=next(
                                (
                                    event.occurred_at
                                    for event in (active_round.events if active_round else [])
                                    if event.checkpoint_id == item.id
                                ),
                                None,
                            ),
                        )
                        for item in checkpoints
                    ],
                )
            )
        return items

    def get_active_round(self, actor: RequestAuthorizationContext) -> PatrolRoundRead | None:
        employee = self._require_employee(actor)
        row = self.repository.find_active_patrol_round(actor.tenant_id, employee.id)
        if row is None:
            return None
        return self._to_round_read(actor.tenant_id, row)

    def get_round(self, actor: RequestAuthorizationContext, patrol_round_id: str) -> PatrolRoundRead:
        row = self._require_round(actor, patrol_round_id)
        return self._to_round_read(actor.tenant_id, row)

    def start_round(self, actor: RequestAuthorizationContext, payload: PatrolRoundStartRequest) -> PatrolRoundRead:
        employee = self._require_employee(actor)
        if payload.offline_sync_token:
            existing = self.repository.find_patrol_round_by_sync_token(actor.tenant_id, payload.offline_sync_token)
            if existing is not None:
                self._ensure_round_access(actor, employee.id, existing)
                return self._to_round_read(actor.tenant_id, existing)
        active = self.repository.find_active_patrol_round(actor.tenant_id, employee.id)
        if active is not None:
            if active.shift_id == payload.shift_id and active.patrol_route_id == payload.patrol_route_id:
                return self._to_round_read(actor.tenant_id, active)
            raise ApiException(409, "field.patrol_round.active_exists", "errors.field.patrol_round.active_exists")
        shift = self.repository.get_shift(actor.tenant_id, payload.shift_id)
        if shift is None or shift.release_state != "released":
            raise ApiException(404, "field.patrol_round.shift_not_found", "errors.field.patrol_round.shift_not_found")
        self._ensure_employee_assigned_to_shift(employee.id, shift)
        route = self._resolve_shift_route(shift)
        if route is None or route.id != payload.patrol_route_id:
            raise ApiException(404, "field.patrol_round.route_not_found", "errors.field.patrol_round.route_not_found")
        checkpoints = self.repository.list_patrol_checkpoints(actor.tenant_id, route.id)
        row = self.repository.create_patrol_round(
            PatrolRound(
                tenant_id=actor.tenant_id,
                employee_id=employee.id,
                shift_id=shift.id,
                planning_record_id=shift.shift_plan.planning_record_id,
                patrol_route_id=route.id,
                offline_sync_token=payload.offline_sync_token,
                total_checkpoint_count=len(checkpoints),
                completed_checkpoint_count=0,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._append_event(
            actor,
            row,
            PatrolRoundEvent(
                tenant_id=actor.tenant_id,
                patrol_round_id=row.id,
                sequence_no=1,
                checkpoint_id=None,
                occurred_at=row.started_at,
                event_type_code="round_started",
                scan_method_code="system",
                token_value=None,
                note=None,
                reason_code=None,
                client_event_id=f"{row.offline_sync_token or row.id}:start",
                actor_user_id=actor.user_id,
                is_policy_compliant=True,
                metadata_json={"shift_id": shift.id, "patrol_route_id": route.id},
            ),
        )
        self._record_business_event(actor, "field.patrol_round.started", row.id, {"patrol_route_id": route.id, "shift_id": shift.id})
        return self._to_round_read(actor.tenant_id, self.repository.get_patrol_round(actor.tenant_id, row.id) or row)

    def capture_checkpoint(self, actor: RequestAuthorizationContext, patrol_round_id: str, payload: PatrolRoundCaptureRequest) -> PatrolRoundRead:
        row = self._require_round(actor, patrol_round_id)
        if payload.client_event_id:
            existing = self.repository.get_patrol_event_by_client_id(actor.tenant_id, patrol_round_id, payload.client_event_id)
            if existing is not None:
                refreshed = self.repository.get_patrol_round(actor.tenant_id, patrol_round_id) or row
                return self._to_round_read(actor.tenant_id, refreshed)
        if row.round_status_code != "active":
            raise ApiException(409, "field.patrol_round.not_active", "errors.field.patrol_round.not_active")
        checkpoints = self.repository.list_patrol_checkpoints(actor.tenant_id, row.patrol_route_id)
        next_checkpoint = self._next_expected_checkpoint(checkpoints, row)
        checkpoint = None
        if payload.checkpoint_id is not None:
            checkpoint = next((item for item in checkpoints if item.id == payload.checkpoint_id), None)
            if checkpoint is None:
                raise ApiException(404, "field.patrol_round.checkpoint_not_found", "errors.field.patrol_round.checkpoint_not_found")
        if checkpoint is None:
            checkpoint = next_checkpoint
        if checkpoint is None:
            raise ApiException(409, "field.patrol_round.already_complete", "errors.field.patrol_round.already_complete")
        is_policy_compliant = self._validate_capture_policy(checkpoint, payload)
        event_type_code = "checkpoint_scanned" if is_policy_compliant else "checkpoint_exception"
        if payload.scan_method_code == "manual" and is_policy_compliant:
            event_type_code = "checkpoint_scanned"
        existing_scanned_checkpoint_ids = {
            item.checkpoint_id for item in row.events if item.event_type_code == "checkpoint_scanned" and item.checkpoint_id is not None
        }
        sequence_no = self.repository.next_patrol_event_sequence(actor.tenant_id, patrol_round_id)
        event = self._append_event(
            actor,
            row,
            PatrolRoundEvent(
                tenant_id=actor.tenant_id,
                patrol_round_id=patrol_round_id,
                sequence_no=sequence_no,
                checkpoint_id=checkpoint.id,
                occurred_at=payload.occurred_at or datetime.now(UTC),
                event_type_code=event_type_code,
                scan_method_code=payload.scan_method_code,
                token_value=payload.token_value,
                latitude=payload.latitude,
                longitude=payload.longitude,
                note=payload.note,
                reason_code=payload.reason_code,
                client_event_id=payload.client_event_id,
                actor_user_id=actor.user_id,
                is_policy_compliant=is_policy_compliant,
                metadata_json={
                    "checkpoint_code": checkpoint.checkpoint_code,
                    "expected_token_value": checkpoint.expected_token_value,
                },
            ),
            attachments=payload.attachments,
        )
        if event.event_type_code == "checkpoint_scanned" and checkpoint.id not in existing_scanned_checkpoint_ids:
            row.completed_checkpoint_count += 1
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        self.repository.save_patrol_round(row)
        self._record_business_event(
            actor,
            "field.patrol_round.checkpoint_captured",
            row.id,
            {
                "checkpoint_id": checkpoint.id,
                "event_type_code": event.event_type_code,
                "scan_method_code": payload.scan_method_code,
                "is_policy_compliant": is_policy_compliant,
            },
        )
        return self._to_round_read(actor.tenant_id, self.repository.get_patrol_round(actor.tenant_id, row.id) or row)

    def complete_round(self, actor: RequestAuthorizationContext, patrol_round_id: str, payload: PatrolRoundCompleteRequest) -> PatrolRoundRead:
        row = self._require_round(actor, patrol_round_id)
        if payload.client_event_id:
            existing = self.repository.get_patrol_event_by_client_id(actor.tenant_id, patrol_round_id, payload.client_event_id)
            if existing is not None:
                refreshed = self.repository.get_patrol_round(actor.tenant_id, patrol_round_id) or row
                return self._to_round_read(actor.tenant_id, refreshed)
        if row.round_status_code != "active":
            raise ApiException(409, "field.patrol_round.not_active", "errors.field.patrol_round.not_active")
        row.round_status_code = "completed"
        row.completed_at = payload.occurred_at or datetime.now(UTC)
        row.completion_note = payload.note
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        self._append_event(
            actor,
            row,
            PatrolRoundEvent(
                tenant_id=actor.tenant_id,
                patrol_round_id=patrol_round_id,
                sequence_no=self.repository.next_patrol_event_sequence(actor.tenant_id, patrol_round_id),
                checkpoint_id=None,
                occurred_at=row.completed_at,
                event_type_code="round_completed",
                scan_method_code="system",
                token_value=None,
                note=payload.note,
                reason_code=None,
                client_event_id=payload.client_event_id,
                actor_user_id=actor.user_id,
                is_policy_compliant=row.completed_checkpoint_count >= row.total_checkpoint_count,
                metadata_json={},
            ),
        )
        saved = self.repository.save_patrol_round(row)
        self._ensure_watchbook_link(actor, saved, aborted=False)
        self._ensure_summary_document(actor, saved)
        self._record_business_event(actor, "field.patrol_round.completed", row.id, {"completed_checkpoint_count": row.completed_checkpoint_count})
        return self._to_round_read(actor.tenant_id, self.repository.get_patrol_round(actor.tenant_id, row.id) or saved)

    def abort_round(self, actor: RequestAuthorizationContext, patrol_round_id: str, payload: PatrolRoundAbortRequest) -> PatrolRoundRead:
        row = self._require_round(actor, patrol_round_id)
        if payload.client_event_id:
            existing = self.repository.get_patrol_event_by_client_id(actor.tenant_id, patrol_round_id, payload.client_event_id)
            if existing is not None:
                refreshed = self.repository.get_patrol_round(actor.tenant_id, patrol_round_id) or row
                return self._to_round_read(actor.tenant_id, refreshed)
        if row.round_status_code != "active":
            raise ApiException(409, "field.patrol_round.not_active", "errors.field.patrol_round.not_active")
        row.round_status_code = "aborted"
        row.aborted_at = payload.occurred_at or datetime.now(UTC)
        row.abort_reason_code = payload.abort_reason_code
        row.completion_note = payload.note
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        self._append_event(
            actor,
            row,
            PatrolRoundEvent(
                tenant_id=actor.tenant_id,
                patrol_round_id=patrol_round_id,
                sequence_no=self.repository.next_patrol_event_sequence(actor.tenant_id, patrol_round_id),
                checkpoint_id=None,
                occurred_at=row.aborted_at,
                event_type_code="round_aborted",
                scan_method_code="manual",
                token_value=None,
                note=payload.note,
                reason_code=payload.abort_reason_code,
                client_event_id=payload.client_event_id,
                actor_user_id=actor.user_id,
                is_policy_compliant=False,
                metadata_json={},
            ),
            attachments=payload.attachments,
        )
        saved = self.repository.save_patrol_round(row)
        self._ensure_watchbook_link(actor, saved, aborted=True)
        self._ensure_summary_document(actor, saved)
        self._record_business_event(actor, "field.patrol_round.aborted", row.id, {"abort_reason_code": row.abort_reason_code})
        return self._to_round_read(actor.tenant_id, self.repository.get_patrol_round(actor.tenant_id, row.id) or saved)

    def sync_round(self, actor: RequestAuthorizationContext, payload: PatrolSyncEnvelope) -> PatrolRoundRead:
        round_read = self.start_round(actor, payload.round)
        ordered_events = sorted(
            payload.events,
            key=lambda item: (item.offline_sequence_no is None, item.offline_sequence_no or 0, item.occurred_at or datetime.min.replace(tzinfo=UTC)),
        )
        for item in ordered_events:
            round_read = self.capture_checkpoint(actor, round_read.id, item)
        if payload.complete_request is not None and payload.abort_request is not None:
            raise ApiException(400, "field.patrol_round.sync_invalid", "errors.field.patrol_round.sync_invalid")
        if payload.complete_request is not None:
            round_read = self.complete_round(actor, round_read.id, payload.complete_request)
        if payload.abort_request is not None:
            round_read = self.abort_round(actor, round_read.id, payload.abort_request)
        return round_read

    def get_evaluation(self, actor: RequestAuthorizationContext, patrol_round_id: str) -> PatrolEvaluationRead:
        row = self._require_round(actor, patrol_round_id)
        events = row.events
        exception_count = len([item for item in events if item.event_type_code == "checkpoint_exception"])
        manual_capture_count = len([item for item in events if item.scan_method_code == "manual" and item.event_type_code == "checkpoint_scanned"])
        mismatch_count = len([item for item in events if item.event_type_code == "checkpoint_exception" and item.scan_method_code in POLICY_SCAN_TYPES])
        ratio = 1.0 if row.total_checkpoint_count == 0 else row.completed_checkpoint_count / row.total_checkpoint_count
        compliance_status_code = "compliant" if row.round_status_code == "completed" and exception_count == 0 and ratio >= 1.0 else "attention_required"
        return PatrolEvaluationRead(
            patrol_round_id=row.id,
            tenant_id=row.tenant_id,
            employee_id=row.employee_id,
            patrol_route_id=row.patrol_route_id,
            round_status_code=row.round_status_code,
            total_checkpoint_count=row.total_checkpoint_count,
            completed_checkpoint_count=row.completed_checkpoint_count,
            exception_count=exception_count,
            manual_capture_count=manual_capture_count,
            mismatch_count=mismatch_count,
            watchbook_id=row.watchbook_id,
            summary_document=self._summary_document_read(actor.tenant_id, row.summary_document_id),
            completion_ratio=ratio,
            compliance_status_code=compliance_status_code,
        )

    def _append_event(
        self,
        actor: RequestAuthorizationContext,
        row: PatrolRound,
        event: PatrolRoundEvent,
        *,
        attachments: list | None = None,  # noqa: ANN401
    ) -> PatrolRoundEvent:
        created = self.repository.create_patrol_event(event)
        for attachment in attachments or []:
            document = self.document_service.create_document(
                actor.tenant_id,
                DocumentCreate(
                    tenant_id=actor.tenant_id,
                    title=attachment.title or attachment.file_name,
                    source_module="field_execution",
                    source_label="patrol_round_event_attachment",
                    metadata_json={"patrol_round_id": row.id, "event_id": created.id},
                ),
                actor,
            )
            self.document_service.add_document_version(
                actor.tenant_id,
                document.id,
                DocumentVersionCreate(
                    file_name=attachment.file_name,
                    content_type=attachment.content_type,
                    content_base64=attachment.content_base64,
                    is_revision_safe_pdf=False,
                    metadata_json={"patrol_round_id": row.id, "event_id": created.id},
                ),
                actor,
            )
            self.document_service.add_document_link(
                actor.tenant_id,
                document.id,
                DocumentLinkCreate(owner_type="field.patrol_round_event", owner_id=created.id, relation_type="attachment"),
                actor,
            )
        return created

    def _ensure_watchbook_link(self, actor: RequestAuthorizationContext, row: PatrolRound, *, aborted: bool) -> None:
        if row.watchbook_id is not None:
            return
        shift = self.repository.get_shift(actor.tenant_id, row.shift_id)
        if shift is None:
            return
        planning_record = shift.shift_plan.planning_record
        context_type = "planning_record"
        payload = WatchbookOpenRequest(
            tenant_id=actor.tenant_id,
            context_type=context_type,
            log_date=row.started_at.date(),
            planning_record_id=planning_record.id if planning_record is not None else None,
            order_id=None if planning_record is not None else shift.shift_plan.planning_record.order_id,
            site_id=planning_record.site_detail.site_id if planning_record is not None and planning_record.site_detail is not None else None,
            shift_id=row.shift_id,
            headline=f"Patrol {row.patrol_route.route_no if row.patrol_route is not None else row.patrol_route_id}",
            summary="Patrol evidence generated from mobile execution",
        )
        watchbook = self.watchbook_service.open_or_create_watchbook(actor.tenant_id, payload, actor)
        row.watchbook_id = watchbook.id
        self.repository.save_patrol_round(row)
        self.watchbook_service.create_entry(
            actor.tenant_id,
            watchbook.id,
            WatchbookEntryCreate(
                entry_type_code="incident" if aborted else "status",
                narrative=(
                    f"Patrol round {'aborted' if aborted else 'completed'}: "
                    f"{row.completed_checkpoint_count}/{row.total_checkpoint_count} checkpoints."
                ),
                traffic_light_code="red" if aborted else "green",
            ),
            actor,
            author_actor_type="employee",
        )

    def _ensure_summary_document(self, actor: RequestAuthorizationContext, row: PatrolRound) -> None:
        if row.summary_document_id is not None:
            return
        content = self._render_summary_bytes(row)
        document = self.document_service.create_document(
            actor.tenant_id,
            DocumentCreate(
                tenant_id=actor.tenant_id,
                title=f"Patrol {row.started_at.date().isoformat()}",
                source_module="field_execution",
                source_label="patrol_summary_pdf",
                metadata_json={"patrol_round_id": row.id},
            ),
            actor,
        )
        self.document_service.add_document_version(
            actor.tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=f"patrol-{row.started_at.date().isoformat()}.pdf",
                content_type="application/pdf",
                content_base64=base64.b64encode(content).decode("ascii"),
                is_revision_safe_pdf=True,
                metadata_json={"patrol_round_id": row.id, "event_count": len(row.events)},
            ),
            actor,
        )
        self.document_service.add_document_link(
            actor.tenant_id,
            document.id,
            DocumentLinkCreate(owner_type="field.patrol_round", owner_id=row.id, relation_type="summary_pdf"),
            actor,
        )
        row.summary_document_id = document.id
        self.repository.save_patrol_round(row)

    def _validate_capture_policy(self, checkpoint, payload: PatrolRoundCaptureRequest) -> bool:  # noqa: ANN001
        if payload.scan_method_code not in {"qr", "barcode", "nfc", "manual"}:
            raise ApiException(400, "field.patrol_round.scan_method_invalid", "errors.field.patrol_round.scan_method_invalid")
        if payload.scan_method_code == "manual":
            if not (payload.note or payload.reason_code):
                raise ApiException(400, "field.patrol_round.manual_reason_required", "errors.field.patrol_round.manual_reason_required")
            return True
        if checkpoint.scan_type_code != payload.scan_method_code:
            return False
        if checkpoint.expected_token_value and payload.token_value != checkpoint.expected_token_value:
            return False
        return True

    def _to_round_read(self, tenant_id: str, row: PatrolRound) -> PatrolRoundRead:
        checkpoints = self.repository.list_patrol_checkpoints(tenant_id, row.patrol_route_id)
        completed_ids = {
            item.checkpoint_id
            for item in row.events
            if item.event_type_code == "checkpoint_scanned" and item.checkpoint_id is not None
        }
        return PatrolRoundRead(
            id=row.id,
            tenant_id=row.tenant_id,
            employee_id=row.employee_id,
            shift_id=row.shift_id,
            planning_record_id=row.planning_record_id,
            patrol_route_id=row.patrol_route_id,
            watchbook_id=row.watchbook_id,
            summary_document_id=row.summary_document_id,
            offline_sync_token=row.offline_sync_token,
            round_status_code=row.round_status_code,
            started_at=row.started_at,
            completed_at=row.completed_at,
            aborted_at=row.aborted_at,
            abort_reason_code=row.abort_reason_code,
            completion_note=row.completion_note,
            total_checkpoint_count=row.total_checkpoint_count,
            completed_checkpoint_count=row.completed_checkpoint_count,
            version_no=row.version_no,
            events=[self._to_event_read(tenant_id, item) for item in row.events],
            checkpoints=[
                PatrolCheckpointProgressRead(
                    checkpoint_id=item.id,
                    sequence_no=item.sequence_no,
                    checkpoint_code=item.checkpoint_code,
                    label=item.label,
                    scan_type_code=item.scan_type_code,
                    minimum_dwell_seconds=item.minimum_dwell_seconds,
                    is_completed=item.id in completed_ids,
                    last_event_at=next((event.occurred_at for event in row.events if event.checkpoint_id == item.id), None),
                )
                for item in checkpoints
            ],
        )

    def _to_event_read(self, tenant_id: str, row: PatrolRoundEvent) -> PatrolRoundEventRead:
        attachments = self.repository.list_documents_for_owner(tenant_id, "field.patrol_round_event", row.id)
        return PatrolRoundEventRead(
            id=row.id,
            patrol_round_id=row.patrol_round_id,
            sequence_no=row.sequence_no,
            checkpoint_id=row.checkpoint_id,
            occurred_at=row.occurred_at,
            event_type_code=row.event_type_code,
            scan_method_code=row.scan_method_code,
            token_value=row.token_value,
            note=row.note,
            reason_code=row.reason_code,
            actor_user_id=row.actor_user_id,
            is_policy_compliant=row.is_policy_compliant,
            client_event_id=row.client_event_id,
            attachment_document_ids=[item.id for item in attachments],
        )

    def _summary_document_read(self, tenant_id: str, document_id: str | None) -> ReleasedWatchbookDocumentRead | None:
        if document_id is None:
            return None
        document = self.repository.get_document(tenant_id, document_id)
        if document is None:
            return None
        version = next((item for item in document.versions if item.version_no == document.current_version_no), None)
        return ReleasedWatchbookDocumentRead(
            document_id=document.id,
            title=document.title,
            file_name=version.file_name if version is not None else None,
            content_type=version.content_type if version is not None else None,
            current_version_no=document.current_version_no,
        )

    def _require_employee(self, actor: RequestAuthorizationContext):
        employee = self.repository.find_employee_by_user_id(actor.tenant_id, actor.user_id)
        if employee is None:
            raise ApiException(404, "field.patrol_round.employee_not_found", "errors.field.patrol_round.employee_not_found")
        return employee

    def _require_round(self, actor: RequestAuthorizationContext, patrol_round_id: str) -> PatrolRound:
        employee = self._require_employee(actor)
        row = self.repository.get_patrol_round(actor.tenant_id, patrol_round_id)
        if row is None:
            raise ApiException(404, "field.patrol_round.not_found", "errors.field.patrol_round.not_found")
        self._ensure_round_access(actor, employee.id, row)
        return row

    @staticmethod
    def _ensure_round_access(actor: RequestAuthorizationContext, employee_id: str, row: PatrolRound) -> None:
        if actor.tenant_id != row.tenant_id or row.employee_id != employee_id:
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")

    @staticmethod
    def _ensure_employee_assigned_to_shift(employee_id: str, shift) -> None:  # noqa: ANN001
        assignments = getattr(shift, "assignments", []) or []
        if not any(item.employee_id == employee_id and item.assignment_status_code in {"assigned", "confirmed"} for item in assignments):
            raise ApiException(403, "field.patrol_round.shift_not_assigned", "errors.field.patrol_round.shift_not_assigned")

    @staticmethod
    def _resolve_shift_route(shift):  # noqa: ANN001
        planning_record = shift.shift_plan.planning_record
        if planning_record is not None and planning_record.patrol_detail is not None:
            return planning_record.patrol_detail.patrol_route
        if planning_record is not None and planning_record.order is not None:
            return planning_record.order.patrol_route
        return None

    @staticmethod
    def _next_expected_checkpoint(checkpoints, row: PatrolRound):  # noqa: ANN001
        completed_ids = {
            item.checkpoint_id for item in row.events if item.event_type_code == "checkpoint_scanned" and item.checkpoint_id is not None
        }
        for checkpoint in checkpoints:
            if checkpoint.id not in completed_ids:
                return checkpoint
        return None

    def _record_business_event(self, actor: RequestAuthorizationContext, event_type: str, entity_id: str, after_json: dict[str, object]) -> None:
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=actor.tenant_id,
                user_id=actor.user_id,
                session_id=actor.session_id,
                request_id=actor.request_id,
            ),
            event_type=event_type,
            entity_type="field.patrol_round",
            entity_id=entity_id,
            tenant_id=actor.tenant_id,
            after_json=after_json,
        )

    @staticmethod
    def _render_summary_bytes(row: PatrolRound) -> bytes:
        lines = [
            "%PDF-1.4",
            f"patrol_round_id={row.id}",
            f"patrol_route_id={row.patrol_route_id}",
            f"status={row.round_status_code}",
            f"checkpoints={row.completed_checkpoint_count}/{row.total_checkpoint_count}",
        ]
        for event in row.events:
            lines.append(
                f"{event.sequence_no}|{event.event_type_code}|{event.scan_method_code or '-'}|"
                f"{event.checkpoint_id or '-'}|{event.reason_code or '-'}"
            )
        return "\n".join(lines).encode("utf-8")
