"""Derive normalized attendance summaries from append-only time evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.field_execution.models import AttendanceRecord, TimeEvent
from app.modules.field_execution.schemas import (
    AttendanceDiscrepancyIssueRead,
    AttendanceRecordListFilter,
    AttendanceRecordListItem,
    AttendanceRecordRead,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext


class AttendanceRepository(Protocol):
    def get_shift(self, tenant_id: str, shift_id: str): ...  # noqa: ANN001
    def get_assignment(self, tenant_id: str, assignment_id: str): ...  # noqa: ANN001
    def list_assignments_for_shift(self, tenant_id: str, shift_id: str): ...  # noqa: ANN001
    def list_events_for_actor_shift(
        self,
        tenant_id: str,
        *,
        shift_id: str,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
    ): ...  # noqa: ANN001
    def get_attendance_record(self, tenant_id: str, attendance_record_id: str): ...  # noqa: ANN001
    def get_current_attendance_for_actor_shift(
        self,
        tenant_id: str,
        *,
        shift_id: str,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
    ): ...  # noqa: ANN001
    def list_attendance_records(self, tenant_id: str, filters: AttendanceRecordListFilter): ...  # noqa: ANN001
    def create_attendance_record(self, row: AttendanceRecord) -> AttendanceRecord: ...
    def save_attendance_record(self, row: AttendanceRecord) -> AttendanceRecord: ...


@dataclass(frozen=True, slots=True)
class _DerivedAttendance:
    actor_type_code: str
    employee_id: str | None
    subcontractor_worker_id: str | None
    shift_id: str
    assignment_id: str | None
    check_in_at: datetime | None
    check_out_at: datetime | None
    break_minutes: int
    worked_minutes: int
    source_event_count: int
    first_time_event_id: str | None
    last_time_event_id: str | None
    source_event_ids: list[str]
    discrepancy_state_code: str
    discrepancy_codes: list[str]
    discrepancy_details: dict[str, object]
    derivation_status_code: str


class AttendanceService:
    def __init__(self, repository: AttendanceRepository, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_attendance_records(
        self,
        tenant_id: str,
        filters: AttendanceRecordListFilter,
        actor: RequestAuthorizationContext,
    ) -> list[AttendanceRecordListItem]:
        self._require_tenant_scope(actor, tenant_id, "field.attendance.read")
        return [self._map_list_item(row) for row in self.repository.list_attendance_records(tenant_id, filters)]

    def get_attendance_record(
        self,
        tenant_id: str,
        attendance_record_id: str,
        actor: RequestAuthorizationContext,
    ) -> AttendanceRecordRead:
        self._require_tenant_scope(actor, tenant_id, "field.attendance.read")
        row = self.repository.get_attendance_record(tenant_id, attendance_record_id)
        if row is None:
            raise ApiException(404, "field.attendance.not_found", "errors.field.attendance.not_found")
        return self._map_read(row)

    def derive_for_shift(
        self,
        tenant_id: str,
        shift_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[AttendanceRecordRead]:
        self._require_tenant_scope(actor, tenant_id, "field.attendance.write")
        shift = self.repository.get_shift(tenant_id, shift_id)
        if shift is None:
            raise ApiException(404, "field.attendance.shift.not_found", "errors.field.attendance.shift.not_found")
        if shift.release_state != "released":
            raise ApiException(409, "field.attendance.shift.not_released", "errors.field.attendance.shift.not_released")
        return [self._map_read(self._derive_for_assignment(tenant_id, assignment, actor)) for assignment in self.repository.list_assignments_for_shift(tenant_id, shift_id)]

    def derive_for_assignment(
        self,
        tenant_id: str,
        assignment_id: str,
        actor: RequestAuthorizationContext,
    ) -> AttendanceRecordRead:
        self._require_tenant_scope(actor, tenant_id, "field.attendance.write")
        assignment = self.repository.get_assignment(tenant_id, assignment_id)
        if assignment is None:
            raise ApiException(404, "field.attendance.assignment.not_found", "errors.field.attendance.assignment.not_found")
        if assignment.shift.release_state != "released":
            raise ApiException(409, "field.attendance.shift.not_released", "errors.field.attendance.shift.not_released")
        return self._map_read(self._derive_for_assignment(tenant_id, assignment, actor))

    def _derive_for_assignment(self, tenant_id: str, assignment, actor: RequestAuthorizationContext):  # noqa: ANN001
        derived = self._build_summary(
            assignment,
            self.repository.list_events_for_actor_shift(
                tenant_id,
                shift_id=assignment.shift_id,
                employee_id=assignment.employee_id,
                subcontractor_worker_id=assignment.subcontractor_worker_id,
            ),
        )
        current = self.repository.get_current_attendance_for_actor_shift(
            tenant_id,
            shift_id=assignment.shift_id,
            employee_id=assignment.employee_id,
            subcontractor_worker_id=assignment.subcontractor_worker_id,
        )
        if current is not None and self._matches(current, derived):
            return current
        before = None if current is None else self._snapshot(current)
        if current is not None:
            current.is_current = False
            current.derivation_status_code = "superseded"
            current.superseded_at = datetime.now(UTC)
            current.updated_by_user_id = actor.user_id
            current.version_no += 1
            self.repository.save_attendance_record(current)
        row = self.repository.create_attendance_record(
            AttendanceRecord(
                tenant_id=tenant_id,
                actor_type_code=derived.actor_type_code,
                employee_id=derived.employee_id,
                subcontractor_worker_id=derived.subcontractor_worker_id,
                shift_id=derived.shift_id,
                assignment_id=derived.assignment_id,
                check_in_at=derived.check_in_at,
                check_out_at=derived.check_out_at,
                break_minutes=derived.break_minutes,
                worked_minutes=derived.worked_minutes,
                source_event_count=derived.source_event_count,
                first_time_event_id=derived.first_time_event_id,
                last_time_event_id=derived.last_time_event_id,
                source_event_ids_json=derived.source_event_ids,
                discrepancy_state_code=derived.discrepancy_state_code,
                discrepancy_codes_json=derived.discrepancy_codes,
                discrepancy_details_json=derived.discrepancy_details,
                derivation_status_code=derived.derivation_status_code,
                derived_at=datetime.now(UTC),
                is_current=True,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        if current is not None:
            current.superseded_by_attendance_id = row.id
            current = self.repository.save_attendance_record(current)
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="field.attendance.derived",
            entity_type="field.attendance_record",
            entity_id=row.id,
            before_json=before,
            after_json=self._snapshot(row),
        )
        return row

    def _build_summary(self, assignment, events: list[TimeEvent]) -> _DerivedAttendance:  # noqa: ANN001
        source_ids = [row.id for row in events]
        first_event_id = source_ids[0] if source_ids else None
        last_event_id = source_ids[-1] if source_ids else None
        details: dict[str, object] = {"issues": [], "event_count": len(events)}
        codes: list[str] = []
        severity = "clean"

        def add_issue(code: str, issue_severity: str, message_key: str, *, source_event_ids: list[str] | None = None, **extra: object) -> None:
            nonlocal severity
            if code not in codes:
                codes.append(code)
            details["issues"].append(
                {
                    "code": code,
                    "severity": issue_severity,
                    "message_key": message_key,
                    "source_event_ids": source_event_ids or [],
                    "details": extra,
                }
            )
            if issue_severity == "needs_review":
                severity = "needs_review"
            elif severity == "clean":
                severity = "warning"

        usable_events = [row for row in events if row.validation_status_code != "rejected"]
        rejected_events = [row for row in events if row.validation_status_code == "rejected"]
        flagged_events = [row for row in usable_events if row.validation_status_code == "flagged"]
        if not events:
            add_issue("no_time_events", "needs_review", "errors.field.attendance.no_time_events")
        if rejected_events:
            add_issue(
                "rejected_events_present",
                "warning",
                "errors.field.attendance.rejected_events_present",
                source_event_ids=[row.id for row in rejected_events],
                count=len(rejected_events),
            )
        if flagged_events:
            add_issue(
                "flagged_events_present",
                "warning",
                "errors.field.attendance.flagged_events_present",
                source_event_ids=[row.id for row in flagged_events],
                count=len(flagged_events),
            )

        check_in_at: datetime | None = None
        check_out_at: datetime | None = None
        open_break_start: datetime | None = None
        break_minutes = 0
        assignment_mismatch_ids: list[str] = []
        for row in usable_events:
            if row.assignment_id is not None and row.assignment_id != assignment.id:
                assignment_mismatch_ids.append(row.id)
            if row.event_code == "clock_in":
                if check_in_at is None:
                    check_in_at = row.occurred_at
                else:
                    add_issue("duplicate_clock_in", "needs_review", "errors.field.attendance.duplicate_clock_in", source_event_ids=[row.id])
            elif row.event_code == "clock_out":
                if check_in_at is None:
                    add_issue("invalid_sequence", "needs_review", "errors.field.attendance.invalid_sequence", source_event_ids=[row.id], event_code=row.event_code)
                elif check_out_at is None:
                    if row.occurred_at < check_in_at:
                        add_issue("invalid_sequence", "needs_review", "errors.field.attendance.invalid_sequence", source_event_ids=[row.id], event_code=row.event_code)
                    else:
                        check_out_at = row.occurred_at
                else:
                    if row.occurred_at > check_out_at:
                        check_out_at = row.occurred_at
                    add_issue("duplicate_clock_out", "needs_review", "errors.field.attendance.duplicate_clock_out", source_event_ids=[row.id])
            elif row.event_code == "break_start":
                if check_in_at is None or check_out_at is not None:
                    add_issue("invalid_sequence", "needs_review", "errors.field.attendance.invalid_sequence", source_event_ids=[row.id], event_code=row.event_code)
                elif open_break_start is not None:
                    add_issue("duplicate_break_start", "needs_review", "errors.field.attendance.duplicate_break_start", source_event_ids=[row.id])
                else:
                    open_break_start = row.occurred_at
            elif row.event_code == "break_end":
                if open_break_start is None:
                    add_issue("invalid_sequence", "needs_review", "errors.field.attendance.invalid_sequence", source_event_ids=[row.id], event_code=row.event_code)
                elif row.occurred_at < open_break_start:
                    add_issue("invalid_sequence", "needs_review", "errors.field.attendance.invalid_sequence", source_event_ids=[row.id], event_code=row.event_code)
                else:
                    break_minutes += int((row.occurred_at - open_break_start).total_seconds() // 60)
                    open_break_start = None
        if assignment_mismatch_ids:
            add_issue(
                "assignment_context_mismatch",
                "warning",
                "errors.field.attendance.assignment_context_mismatch",
                source_event_ids=assignment_mismatch_ids,
            )
        if check_in_at is None and usable_events:
            add_issue("missing_check_in", "needs_review", "errors.field.attendance.missing_check_in", source_event_ids=source_ids)
        if check_in_at is not None and check_out_at is None:
            add_issue("missed_checkout", "needs_review", "errors.field.attendance.missed_checkout", source_event_ids=source_ids)
        if open_break_start is not None:
            add_issue("missing_break_end", "needs_review", "errors.field.attendance.missing_break_end", source_event_ids=source_ids)

        worked_minutes = 0
        if check_in_at is not None and check_out_at is not None and check_out_at >= check_in_at:
            worked_minutes = max(int((check_out_at - check_in_at).total_seconds() // 60) - break_minutes, 0)

        derivation_status = "derived" if severity == "clean" else "needs_review"
        return _DerivedAttendance(
            actor_type_code="employee" if assignment.employee_id is not None else "subcontractor_worker",
            employee_id=assignment.employee_id,
            subcontractor_worker_id=assignment.subcontractor_worker_id,
            shift_id=assignment.shift_id,
            assignment_id=assignment.id,
            check_in_at=check_in_at,
            check_out_at=check_out_at,
            break_minutes=break_minutes,
            worked_minutes=worked_minutes,
            source_event_count=len(events),
            first_time_event_id=first_event_id,
            last_time_event_id=last_event_id,
            source_event_ids=source_ids,
            discrepancy_state_code=severity,
            discrepancy_codes=codes,
            discrepancy_details=details,
            derivation_status_code=derivation_status,
        )

    @staticmethod
    def _matches(current: AttendanceRecord, derived: _DerivedAttendance) -> bool:
        return (
            current.assignment_id == derived.assignment_id
            and current.check_in_at == derived.check_in_at
            and current.check_out_at == derived.check_out_at
            and current.break_minutes == derived.break_minutes
            and current.worked_minutes == derived.worked_minutes
            and current.source_event_count == derived.source_event_count
            and current.first_time_event_id == derived.first_time_event_id
            and current.last_time_event_id == derived.last_time_event_id
            and current.source_event_ids_json == derived.source_event_ids
            and current.discrepancy_state_code == derived.discrepancy_state_code
            and current.discrepancy_codes_json == derived.discrepancy_codes
            and current.discrepancy_details_json == derived.discrepancy_details
            and current.derivation_status_code == derived.derivation_status_code
            and current.is_current
        )

    def _map_list_item(self, row: AttendanceRecord) -> AttendanceRecordListItem:
        return AttendanceRecordListItem(
            id=row.id,
            actor_type_code=row.actor_type_code,
            employee_id=row.employee_id,
            subcontractor_worker_id=row.subcontractor_worker_id,
            shift_id=row.shift_id,
            assignment_id=row.assignment_id,
            check_in_at=row.check_in_at,
            check_out_at=row.check_out_at,
            break_minutes=row.break_minutes,
            worked_minutes=row.worked_minutes,
            discrepancy_state_code=row.discrepancy_state_code,
            discrepancy_codes_json=list(row.discrepancy_codes_json or []),
            derivation_status_code=row.derivation_status_code,
            is_current=row.is_current,
            derived_at=row.derived_at,
        )

    def _map_read(self, row: AttendanceRecord) -> AttendanceRecordRead:
        issues = [
            AttendanceDiscrepancyIssueRead(
                code=issue.get("code", ""),
                severity=issue.get("severity", "warning"),
                message_key=issue.get("message_key", ""),
                source_event_ids=list(issue.get("source_event_ids", [])),
                details=dict(issue.get("details", {})),
            )
            for issue in row.discrepancy_details_json.get("issues", [])
            if isinstance(issue, dict)
        ]
        return AttendanceRecordRead(
            **self._map_list_item(row).model_dump(),
            tenant_id=row.tenant_id,
            source_event_count=row.source_event_count,
            first_time_event_id=row.first_time_event_id,
            last_time_event_id=row.last_time_event_id,
            source_event_ids_json=list(row.source_event_ids_json or []),
            discrepancy_details_json=dict(row.discrepancy_details_json or {}),
            discrepancies=issues,
            superseded_at=row.superseded_at,
            superseded_by_attendance_id=row.superseded_by_attendance_id,
            status=row.status,
            archived_at=row.archived_at,
            version_no=row.version_no,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _snapshot(row: AttendanceRecord) -> dict[str, object]:
        return {
            "assignment_id": row.assignment_id,
            "shift_id": row.shift_id,
            "employee_id": row.employee_id,
            "subcontractor_worker_id": row.subcontractor_worker_id,
            "check_in_at": None if row.check_in_at is None else row.check_in_at.isoformat(),
            "check_out_at": None if row.check_out_at is None else row.check_out_at.isoformat(),
            "break_minutes": row.break_minutes,
            "worked_minutes": row.worked_minutes,
            "source_event_count": row.source_event_count,
            "discrepancy_state_code": row.discrepancy_state_code,
            "discrepancy_codes_json": list(row.discrepancy_codes_json or []),
            "derivation_status_code": row.derivation_status_code,
            "is_current": row.is_current,
            "superseded_at": None if row.superseded_at is None else row.superseded_at.isoformat(),
            "superseded_by_attendance_id": row.superseded_by_attendance_id,
            "version_no": row.version_no,
        }

    @staticmethod
    def _require_tenant_scope(actor: RequestAuthorizationContext, tenant_id: str, permission_key: str) -> None:
        if permission_key not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
        if not actor.allows_tenant(tenant_id):
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")

    def _record_audit(
        self,
        actor: RequestAuthorizationContext,
        *,
        tenant_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
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
            tenant_id=tenant_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            before_json=before_json or {},
            after_json=after_json or {},
        )
