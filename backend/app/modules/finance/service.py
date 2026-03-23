"""Finance-owned derivation, approval, and reconciliation of actual bridge records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.finance.models import ActualAllowance, ActualApproval, ActualComment, ActualExpense, ActualReconciliation, ActualRecord
from app.modules.finance.schemas import (
    ActualAllowanceCreate,
    ActualAllowanceRead,
    ActualApprovalActionRequest,
    ActualApprovalRead,
    ActualCommentCreate,
    ActualCommentRead,
    ActualExpenseCreate,
    ActualExpenseRead,
    ActualRecordDiscrepancyIssueRead,
    ActualRecordListFilter,
    ActualRecordListItem,
    ActualRecordRead,
    ActualReconciliationCreate,
    ActualReconciliationRead,
)
from app.modules.iam.audit_schemas import AuditEventRead
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext


class FinanceRepository(Protocol):
    def get_assignment(self, tenant_id: str, assignment_id: str): ...  # noqa: ANN001
    def get_attendance_record(self, tenant_id: str, attendance_record_id: str): ...  # noqa: ANN001
    def get_current_attendance_for_assignment(self, tenant_id: str, assignment_id: str): ...  # noqa: ANN001
    def get_actual_record(self, tenant_id: str, actual_record_id: str): ...  # noqa: ANN001
    def get_current_actual_for_assignment(self, tenant_id: str, assignment_id: str): ...  # noqa: ANN001
    def list_actual_records(self, tenant_id: str, filters: ActualRecordListFilter): ...  # noqa: ANN001
    def get_employee(self, tenant_id: str, employee_id: str): ...  # noqa: ANN001
    def get_subcontractor_worker(self, tenant_id: str, worker_id: str): ...  # noqa: ANN001
    def create_actual_record(self, row: ActualRecord) -> ActualRecord: ...
    def save_actual_record(self, row: ActualRecord) -> ActualRecord: ...
    def create_actual_approval(self, row: ActualApproval) -> ActualApproval: ...
    def create_actual_reconciliation(self, row: ActualReconciliation) -> ActualReconciliation: ...
    def create_actual_allowance(self, row: ActualAllowance) -> ActualAllowance: ...
    def create_actual_expense(self, row: ActualExpense) -> ActualExpense: ...
    def create_actual_comment(self, row: ActualComment) -> ActualComment: ...
    def list_audit_events_for_actual_record(self, tenant_id: str, actual_record_id: str) -> list[AuditEventRead]: ...


class FinanceActualService:
    def __init__(self, repository: FinanceRepository, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_actual_records(
        self,
        tenant_id: str,
        filters: ActualRecordListFilter,
        actor: RequestAuthorizationContext,
    ) -> list[ActualRecordListItem]:
        self._require_view_access(actor, tenant_id)
        rows = [row for row in self.repository.list_actual_records(tenant_id, filters) if self._can_view_actual(actor, row)]
        return [self._map_list_item(row) for row in rows]

    def get_actual_record(
        self,
        tenant_id: str,
        actual_record_id: str,
        actor: RequestAuthorizationContext,
    ) -> ActualRecordRead:
        row = self._require_actual(tenant_id, actual_record_id)
        self._require_actual_visibility(actor, row)
        return self._map_read(row, actor)

    def derive_for_assignment(
        self,
        tenant_id: str,
        assignment_id: str,
        actor: RequestAuthorizationContext,
    ) -> ActualRecordRead:
        self._require_finance_write(actor, tenant_id)
        assignment = self.repository.get_assignment(tenant_id, assignment_id)
        if assignment is None:
            raise ApiException(404, "finance.actual.assignment.not_found", "errors.finance.actual.assignment.not_found")
        if assignment.shift.release_state != "released":
            raise ApiException(409, "finance.actual.shift.not_released", "errors.finance.actual.shift.not_released")
        attendance = self.repository.get_current_attendance_for_assignment(tenant_id, assignment_id)
        derived = self._build_record(assignment, attendance)
        current = self.repository.get_current_actual_for_assignment(tenant_id, assignment_id)
        if current is not None and self._matches(current, derived):
            return self._map_read(current, actor)
        before = None if current is None else self._snapshot(current)
        if current is not None:
            current.is_current = False
            current.derivation_status_code = "superseded"
            current.superseded_at = datetime.now(UTC)
            current.updated_by_user_id = actor.user_id
            current.version_no += 1
            self.repository.save_actual_record(current)
        row = self.repository.create_actual_record(
            ActualRecord(
                tenant_id=tenant_id,
                assignment_id=assignment.id,
                shift_id=assignment.shift_id,
                attendance_record_id=None if attendance is None else attendance.id,
                actor_type_code="employee" if assignment.employee_id is not None else "subcontractor_worker",
                employee_id=assignment.employee_id,
                subcontractor_worker_id=assignment.subcontractor_worker_id,
                planned_start_at=assignment.shift.starts_at,
                planned_end_at=assignment.shift.ends_at,
                actual_start_at=derived["actual_start_at"],
                actual_end_at=derived["actual_end_at"],
                planned_break_minutes=assignment.shift.break_minutes,
                actual_break_minutes=derived["actual_break_minutes"],
                payable_minutes=derived["payable_minutes"],
                billable_minutes=derived["billable_minutes"],
                customer_adjustment_minutes=0,
                discrepancy_state_code=derived["discrepancy_state_code"],
                discrepancy_codes_json=derived["discrepancy_codes_json"],
                discrepancy_details_json=derived["discrepancy_details_json"],
                derivation_status_code=derived["derivation_status_code"],
                approval_stage_code="draft",
                derived_at=datetime.now(UTC),
                is_current=True,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        if current is not None:
            current.superseded_by_actual_id = row.id
            self.repository.save_actual_record(current)
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="finance.actual.derived",
            entity_id=row.id,
            before_json=before,
            after_json=self._snapshot(row),
        )
        return self._map_read(row, actor)

    def submit_preliminary_actual(
        self,
        tenant_id: str,
        actual_record_id: str,
        payload: ActualApprovalActionRequest,
        actor: RequestAuthorizationContext,
    ) -> ActualRecordRead:
        row = self._require_actual(tenant_id, actual_record_id)
        actor_scope_code = self._resolve_preliminary_actor_scope(actor, row)
        if row.approval_stage_code != "draft":
            raise ApiException(409, "finance.actual.approval.invalid_stage", "errors.finance.actual.approval.invalid_stage")
        approval = self.repository.create_actual_approval(
            ActualApproval(
                tenant_id=tenant_id,
                actual_record_id=row.id,
                stage_code="preliminary_submitted",
                actor_scope_code=actor_scope_code,
                note_text=self._normalize_optional(payload.note_text),
                source_ref_json=self._approval_source_ref(row, actor_scope_code),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        before = self._snapshot(row)
        row.approval_stage_code = "preliminary_submitted"
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        row = self.repository.save_actual_record(row)
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="finance.actual.preliminary_submitted",
            entity_id=row.id,
            before_json=before,
            after_json=self._snapshot(row),
            metadata_json={"approval_id": approval.id, "actor_scope_code": actor_scope_code},
        )
        return self._map_read(row, actor)

    def confirm_operational_actual(
        self,
        tenant_id: str,
        actual_record_id: str,
        payload: ActualApprovalActionRequest,
        actor: RequestAuthorizationContext,
    ) -> ActualRecordRead:
        row = self._require_actual(tenant_id, actual_record_id)
        self._require_operational_scope(actor, row)
        if row.approval_stage_code != "preliminary_submitted":
            raise ApiException(409, "finance.actual.approval.invalid_stage", "errors.finance.actual.approval.invalid_stage")
        approval = self.repository.create_actual_approval(
            ActualApproval(
                tenant_id=tenant_id,
                actual_record_id=row.id,
                stage_code="operational_confirmed",
                actor_scope_code="operational_lead",
                note_text=self._normalize_optional(payload.note_text),
                source_ref_json=self._approval_source_ref(row, "operational_lead"),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        before = self._snapshot(row)
        row.approval_stage_code = "operational_confirmed"
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        row = self.repository.save_actual_record(row)
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="finance.actual.operational_confirmed",
            entity_id=row.id,
            before_json=before,
            after_json=self._snapshot(row),
            metadata_json={"approval_id": approval.id},
        )
        return self._map_read(row, actor)

    def finance_signoff_actual(
        self,
        tenant_id: str,
        actual_record_id: str,
        payload: ActualApprovalActionRequest,
        actor: RequestAuthorizationContext,
    ) -> ActualRecordRead:
        row = self._require_actual(tenant_id, actual_record_id)
        self._require_finance_signoff(actor, tenant_id)
        if row.approval_stage_code != "operational_confirmed":
            raise ApiException(409, "finance.actual.approval.invalid_stage", "errors.finance.actual.approval.invalid_stage")
        approval = self.repository.create_actual_approval(
            ActualApproval(
                tenant_id=tenant_id,
                actual_record_id=row.id,
                stage_code="finance_signed_off",
                actor_scope_code="finance",
                note_text=self._normalize_optional(payload.note_text),
                source_ref_json=self._approval_source_ref(row, "finance"),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        before = self._snapshot(row)
        row.approval_stage_code = "finance_signed_off"
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        row = self.repository.save_actual_record(row)
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="finance.actual.finance_signed_off",
            entity_id=row.id,
            before_json=before,
            after_json=self._snapshot(row),
            metadata_json={"approval_id": approval.id},
        )
        return self._map_read(row, actor)

    def add_reconciliation(
        self,
        tenant_id: str,
        actual_record_id: str,
        payload: ActualReconciliationCreate,
        actor: RequestAuthorizationContext,
    ) -> ActualRecordRead:
        row = self._require_actual(tenant_id, actual_record_id)
        self._require_finance_write(actor, tenant_id)
        self._validate_reconciliation_payload(tenant_id, payload)
        reconciliation = self.repository.create_actual_reconciliation(
            ActualReconciliation(
                tenant_id=tenant_id,
                actual_record_id=row.id,
                reconciliation_kind_code=payload.reconciliation_kind_code,
                reason_code=payload.reason_code.strip(),
                note_text=self._normalize_optional(payload.note_text),
                payroll_minutes_delta=payload.payroll_minutes_delta,
                billable_minutes_delta=payload.billable_minutes_delta,
                customer_adjustment_minutes_delta=payload.customer_adjustment_minutes_delta,
                replacement_actor_type_code=payload.replacement_actor_type_code,
                replacement_employee_id=payload.replacement_employee_id,
                replacement_subcontractor_worker_id=payload.replacement_subcontractor_worker_id,
                source_ref_json=dict(payload.source_ref_json),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        before = self._snapshot(row)
        row.payable_minutes = max(row.payable_minutes + payload.payroll_minutes_delta, 0)
        row.billable_minutes = max(row.billable_minutes + payload.billable_minutes_delta, 0)
        row.customer_adjustment_minutes = max(row.customer_adjustment_minutes + payload.customer_adjustment_minutes_delta, 0)
        row.discrepancy_state_code = "needs_review" if row.approval_stage_code != "finance_signed_off" else row.discrepancy_state_code
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        row = self.repository.save_actual_record(row)
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type=f"finance.actual.reconciliation.{payload.reconciliation_kind_code}",
            entity_id=row.id,
            before_json=before,
            after_json=self._snapshot(row),
            metadata_json={"reconciliation_id": reconciliation.id, "reason_code": payload.reason_code},
        )
        return self._map_read(row, actor)

    def add_allowance(
        self,
        tenant_id: str,
        actual_record_id: str,
        payload: ActualAllowanceCreate,
        actor: RequestAuthorizationContext,
    ) -> ActualRecordRead:
        row = self._require_actual(tenant_id, actual_record_id)
        self._require_finance_write(actor, tenant_id)
        allowance = self.repository.create_actual_allowance(
            ActualAllowance(
                tenant_id=tenant_id,
                actual_record_id=row.id,
                line_type_code=payload.line_type_code,
                reason_code=payload.reason_code.strip(),
                quantity=payload.quantity,
                unit_code=self._normalize_optional(payload.unit_code),
                amount_total=payload.amount_total,
                currency_code=payload.currency_code.upper(),
                source_ref_json=dict(payload.source_ref_json),
                note_text=self._normalize_optional(payload.note_text),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="finance.actual.allowance_added",
            entity_id=row.id,
            metadata_json={"allowance_id": allowance.id, "line_type_code": allowance.line_type_code},
        )
        return self._map_read(self._require_actual(tenant_id, actual_record_id), actor)

    def add_expense(
        self,
        tenant_id: str,
        actual_record_id: str,
        payload: ActualExpenseCreate,
        actor: RequestAuthorizationContext,
    ) -> ActualRecordRead:
        row = self._require_actual(tenant_id, actual_record_id)
        self._require_finance_write(actor, tenant_id)
        expense = self.repository.create_actual_expense(
            ActualExpense(
                tenant_id=tenant_id,
                actual_record_id=row.id,
                expense_type_code=payload.expense_type_code,
                reason_code=payload.reason_code.strip(),
                quantity=payload.quantity,
                unit_code=self._normalize_optional(payload.unit_code),
                amount_total=payload.amount_total,
                currency_code=payload.currency_code.upper(),
                source_ref_json=dict(payload.source_ref_json),
                note_text=self._normalize_optional(payload.note_text),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="finance.actual.expense_added",
            entity_id=row.id,
            metadata_json={"expense_id": expense.id, "expense_type_code": expense.expense_type_code},
        )
        return self._map_read(self._require_actual(tenant_id, actual_record_id), actor)

    def add_comment(
        self,
        tenant_id: str,
        actual_record_id: str,
        payload: ActualCommentCreate,
        actor: RequestAuthorizationContext,
    ) -> ActualRecordRead:
        row = self._require_actual(tenant_id, actual_record_id)
        self._require_comment_access(actor, row, payload.visibility_code)
        comment = self.repository.create_actual_comment(
            ActualComment(
                tenant_id=tenant_id,
                actual_record_id=row.id,
                visibility_code=payload.visibility_code,
                note_text=payload.note_text.strip(),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="finance.actual.comment_added",
            entity_id=row.id,
            metadata_json={"comment_id": comment.id, "visibility_code": comment.visibility_code},
        )
        return self._map_read(self._require_actual(tenant_id, actual_record_id), actor)

    def submit_employee_preliminary_actual(
        self,
        actual_record_id: str,
        payload: ActualApprovalActionRequest,
        actor: RequestAuthorizationContext,
    ) -> ActualRecordRead:
        row = self._require_actual(actor.tenant_id, actual_record_id)
        if row.employee is None or row.employee.user_id != actor.user_id:
            raise ApiException(403, "finance.actual.self_scope_denied", "errors.finance.actual.self_scope_denied")
        if "portal.employee.access" not in actor.permission_keys or "employee_user" not in actor.role_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
        return self.submit_preliminary_actual(actor.tenant_id, actual_record_id, payload, actor)

    def get_audit_history(
        self,
        tenant_id: str,
        actual_record_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[AuditEventRead]:
        row = self._require_actual(tenant_id, actual_record_id)
        self._require_actual_visibility(actor, row)
        return self.repository.list_audit_events_for_actual_record(tenant_id, actual_record_id)

    def _build_record(self, assignment, attendance):  # noqa: ANN001
        discrepancy_codes: list[str] = []
        discrepancy_details: dict[str, object] = {"issues": []}
        discrepancy_state = "clean"

        def add_issue(code: str, severity: str, message_key: str, *, attendance_record_id: str | None = None, source_event_ids: list[str] | None = None, **extra: object) -> None:
            nonlocal discrepancy_state
            if code not in discrepancy_codes:
                discrepancy_codes.append(code)
            discrepancy_details["issues"].append(
                {
                    "code": code,
                    "severity": severity,
                    "message_key": message_key,
                    "attendance_record_id": attendance_record_id,
                    "source_event_ids": source_event_ids or [],
                    "details": extra,
                }
            )
            if severity == "needs_review":
                discrepancy_state = "needs_review"
            elif discrepancy_state == "clean":
                discrepancy_state = "warning"

        actual_start_at = None if attendance is None else attendance.check_in_at
        actual_end_at = None if attendance is None else attendance.check_out_at
        actual_break_minutes = 0 if attendance is None else attendance.break_minutes
        payable_minutes = 0
        billable_minutes = 0
        derivation_status_code = "derived"

        if attendance is None:
            add_issue("missing_attendance_record", "needs_review", "errors.finance.actual.missing_attendance_record")
            derivation_status_code = "draft"
        else:
            for issue in attendance.discrepancy_details_json.get("issues", []):
                if not isinstance(issue, dict):
                    continue
                add_issue(
                    str(issue.get("code", "attendance_issue")),
                    "needs_review" if issue.get("severity") == "needs_review" else "warning",
                    str(issue.get("message_key", "errors.finance.actual.attendance_issue")),
                    attendance_record_id=attendance.id,
                    source_event_ids=list(issue.get("source_event_ids", [])),
                    **dict(issue.get("details", {})),
                )
            if actual_start_at is not None and actual_end_at is not None and actual_end_at >= actual_start_at:
                payable_minutes = max(int((actual_end_at - actual_start_at).total_seconds() // 60) - actual_break_minutes, 0)
                billable_minutes = payable_minutes
            elif actual_start_at is not None or actual_end_at is not None:
                add_issue(
                    "incomplete_attendance_window",
                    "needs_review",
                    "errors.finance.actual.incomplete_attendance_window",
                    attendance_record_id=attendance.id,
                    source_event_ids=list(attendance.source_event_ids_json or []),
                )
            if assignment.employee_id != attendance.employee_id or assignment.subcontractor_worker_id != attendance.subcontractor_worker_id:
                add_issue(
                    "attendance_assignment_actor_mismatch",
                    "needs_review",
                    "errors.finance.actual.attendance_assignment_actor_mismatch",
                    attendance_record_id=attendance.id,
                )
        if discrepancy_state != "clean" and derivation_status_code == "derived":
            derivation_status_code = "needs_review"
        return {
            "actual_start_at": actual_start_at,
            "actual_end_at": actual_end_at,
            "actual_break_minutes": actual_break_minutes,
            "payable_minutes": payable_minutes,
            "billable_minutes": billable_minutes,
            "discrepancy_state_code": discrepancy_state,
            "discrepancy_codes_json": discrepancy_codes,
            "discrepancy_details_json": discrepancy_details,
            "derivation_status_code": derivation_status_code,
        }

    @staticmethod
    def _matches(current: ActualRecord, derived: dict[str, object]) -> bool:
        return (
            current.actual_start_at == derived["actual_start_at"]
            and current.actual_end_at == derived["actual_end_at"]
            and current.actual_break_minutes == derived["actual_break_minutes"]
            and current.payable_minutes == derived["payable_minutes"]
            and current.billable_minutes == derived["billable_minutes"]
            and current.discrepancy_state_code == derived["discrepancy_state_code"]
            and current.discrepancy_codes_json == derived["discrepancy_codes_json"]
            and current.discrepancy_details_json == derived["discrepancy_details_json"]
            and current.derivation_status_code == derived["derivation_status_code"]
            and current.is_current
        )

    def _map_list_item(self, row: ActualRecord) -> ActualRecordListItem:
        return ActualRecordListItem(
            id=row.id,
            assignment_id=row.assignment_id,
            shift_id=row.shift_id,
            attendance_record_id=row.attendance_record_id,
            actor_type_code=row.actor_type_code,
            employee_id=row.employee_id,
            subcontractor_worker_id=row.subcontractor_worker_id,
            planned_start_at=row.planned_start_at,
            planned_end_at=row.planned_end_at,
            actual_start_at=row.actual_start_at,
            actual_end_at=row.actual_end_at,
            payable_minutes=row.payable_minutes,
            billable_minutes=row.billable_minutes,
            discrepancy_state_code=row.discrepancy_state_code,
            discrepancy_codes_json=list(row.discrepancy_codes_json or []),
            derivation_status_code=row.derivation_status_code,
            approval_stage_code=row.approval_stage_code,
            is_current=row.is_current,
            derived_at=row.derived_at,
        )

    def _map_read(self, row: ActualRecord, actor: RequestAuthorizationContext) -> ActualRecordRead:
        issues = [
            ActualRecordDiscrepancyIssueRead(
                code=issue.get("code", ""),
                severity=issue.get("severity", "warning"),
                message_key=issue.get("message_key", ""),
                attendance_record_id=issue.get("attendance_record_id"),
                source_event_ids=list(issue.get("source_event_ids", [])),
                details=dict(issue.get("details", {})),
            )
            for issue in row.discrepancy_details_json.get("issues", [])
            if isinstance(issue, dict)
        ]
        can_view_finance_only = self._can_view_finance_only(actor)
        comments = [ActualCommentRead.model_validate(comment) for comment in row.comments if can_view_finance_only or comment.visibility_code == "shared"]
        return ActualRecordRead(
            **self._map_list_item(row).model_dump(),
            tenant_id=row.tenant_id,
            planned_break_minutes=row.planned_break_minutes,
            actual_break_minutes=row.actual_break_minutes,
            customer_adjustment_minutes=row.customer_adjustment_minutes,
            discrepancy_details_json=dict(row.discrepancy_details_json or {}),
            discrepancies=issues,
            superseded_at=row.superseded_at,
            superseded_by_actual_id=row.superseded_by_actual_id,
            status=row.status,
            archived_at=row.archived_at,
            version_no=row.version_no,
            created_at=row.created_at,
            updated_at=row.updated_at,
            approvals=[ActualApprovalRead.model_validate(item) for item in row.approvals],
            reconciliations=[ActualReconciliationRead.model_validate(item) for item in row.reconciliations],
            allowances=[ActualAllowanceRead.model_validate(item) for item in row.allowances],
            expenses=[ActualExpenseRead.model_validate(item) for item in row.expenses],
            comments=comments,
            audit_history=self.repository.list_audit_events_for_actual_record(row.tenant_id, row.id),
        )

    @staticmethod
    def _snapshot(row: ActualRecord) -> dict[str, object]:
        return {
            "assignment_id": row.assignment_id,
            "shift_id": row.shift_id,
            "attendance_record_id": row.attendance_record_id,
            "planned_start_at": None if row.planned_start_at is None else row.planned_start_at.isoformat(),
            "planned_end_at": None if row.planned_end_at is None else row.planned_end_at.isoformat(),
            "actual_start_at": None if row.actual_start_at is None else row.actual_start_at.isoformat(),
            "actual_end_at": None if row.actual_end_at is None else row.actual_end_at.isoformat(),
            "planned_break_minutes": row.planned_break_minutes,
            "actual_break_minutes": row.actual_break_minutes,
            "payable_minutes": row.payable_minutes,
            "billable_minutes": row.billable_minutes,
            "customer_adjustment_minutes": row.customer_adjustment_minutes,
            "discrepancy_state_code": row.discrepancy_state_code,
            "discrepancy_codes_json": list(row.discrepancy_codes_json or []),
            "derivation_status_code": row.derivation_status_code,
            "approval_stage_code": row.approval_stage_code,
            "is_current": row.is_current,
            "superseded_at": None if row.superseded_at is None else row.superseded_at.isoformat(),
            "superseded_by_actual_id": row.superseded_by_actual_id,
            "version_no": row.version_no,
        }

    def _require_actual(self, tenant_id: str, actual_record_id: str) -> ActualRecord:
        row = self.repository.get_actual_record(tenant_id, actual_record_id)
        if row is None:
            raise ApiException(404, "finance.actual.not_found", "errors.finance.actual.not_found")
        return row

    def _require_view_access(self, actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if "finance.actual.read" not in actor.permission_keys and "portal.employee.access" not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
        if actor.tenant_id != tenant_id and not actor.is_platform_admin:
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")

    def _require_finance_write(self, actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if "finance.actual.write" not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
        if actor.tenant_id != tenant_id and not actor.is_platform_admin:
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")

    def _require_finance_signoff(self, actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if "finance.approval.signoff" not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
        if actor.tenant_id != tenant_id and not actor.is_platform_admin:
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")

    def _require_actual_visibility(self, actor: RequestAuthorizationContext, row: ActualRecord) -> None:
        self._require_view_access(actor, row.tenant_id)
        if not self._can_view_actual(actor, row):
            raise ApiException(403, "finance.actual.scope_denied", "errors.finance.actual.scope_denied")

    def _can_view_actual(self, actor: RequestAuthorizationContext, row: ActualRecord) -> bool:
        if actor.is_platform_admin or actor.is_tenant_admin or "accounting" in actor.role_keys or "controller_qm" in actor.role_keys:
            return True
        if "dispatcher" in actor.role_keys:
            planning_record = getattr(getattr(getattr(row.shift, "shift_plan", None), "planning_record", None), "dispatcher_user_id", None)
            return planning_record is None or planning_record == actor.user_id
        if "employee_user" in actor.role_keys and "portal.employee.access" in actor.permission_keys:
            return row.employee is not None and row.employee.user_id == actor.user_id
        return False

    def _resolve_preliminary_actor_scope(self, actor: RequestAuthorizationContext, row: ActualRecord) -> str:
        if "employee_user" in actor.role_keys and "portal.employee.access" in actor.permission_keys:
            if row.employee is None or row.employee.user_id != actor.user_id:
                raise ApiException(403, "finance.actual.self_scope_denied", "errors.finance.actual.self_scope_denied")
            return "employee_self"
        self._require_operational_scope(actor, row)
        return "field_lead"

    def _require_operational_scope(self, actor: RequestAuthorizationContext, row: ActualRecord) -> None:
        if "finance.approval.write" not in actor.permission_keys and "finance.actual.write" not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
        if actor.is_platform_admin or actor.is_tenant_admin:
            return
        if "dispatcher" not in actor.role_keys:
            raise ApiException(403, "finance.actual.scope_denied", "errors.finance.actual.scope_denied")
        planning_record = getattr(getattr(getattr(row.shift, "shift_plan", None), "planning_record", None), "dispatcher_user_id", None)
        if planning_record is not None and planning_record != actor.user_id:
            raise ApiException(403, "finance.actual.scope_denied", "errors.finance.actual.scope_denied")

    def _require_comment_access(self, actor: RequestAuthorizationContext, row: ActualRecord, visibility_code: str) -> None:
        if visibility_code == "finance_only":
            self._require_finance_write(actor, row.tenant_id)
            return
        if "employee_user" in actor.role_keys:
            if row.employee is None or row.employee.user_id != actor.user_id:
                raise ApiException(403, "finance.actual.self_scope_denied", "errors.finance.actual.self_scope_denied")
            return
        if "finance.actual.write" in actor.permission_keys or "finance.approval.write" in actor.permission_keys:
            if self._can_view_actual(actor, row):
                return
        raise ApiException(403, "finance.actual.scope_denied", "errors.finance.actual.scope_denied")

    def _validate_reconciliation_payload(self, tenant_id: str, payload: ActualReconciliationCreate) -> None:
        kind = payload.reconciliation_kind_code
        if kind not in {"sickness", "cancellation", "replacement", "customer_adjustment", "flat_rate"}:
            raise ApiException(422, "finance.actual.reconciliation.invalid_kind", "errors.finance.actual.reconciliation.invalid_kind")
        if kind == "replacement":
            if payload.replacement_actor_type_code == "employee":
                if payload.replacement_employee_id is None or self.repository.get_employee(tenant_id, payload.replacement_employee_id) is None:
                    raise ApiException(404, "finance.actual.reconciliation.replacement_not_found", "errors.finance.actual.reconciliation.replacement_not_found")
            elif payload.replacement_actor_type_code == "subcontractor_worker":
                if (
                    payload.replacement_subcontractor_worker_id is None
                    or self.repository.get_subcontractor_worker(tenant_id, payload.replacement_subcontractor_worker_id) is None
                ):
                    raise ApiException(404, "finance.actual.reconciliation.replacement_not_found", "errors.finance.actual.reconciliation.replacement_not_found")
            else:
                raise ApiException(422, "finance.actual.reconciliation.replacement_actor_required", "errors.finance.actual.reconciliation.replacement_actor_required")
        if kind == "customer_adjustment" and payload.customer_adjustment_minutes_delta == 0 and payload.billable_minutes_delta == 0:
            raise ApiException(
                422,
                "finance.actual.reconciliation.customer_adjustment_required",
                "errors.finance.actual.reconciliation.customer_adjustment_required",
            )
        if kind == "flat_rate" and payload.note_text is None:
            raise ApiException(422, "finance.actual.reconciliation.note_required", "errors.finance.actual.reconciliation.note_required")

    def _approval_source_ref(self, row: ActualRecord, actor_scope_code: str) -> dict[str, object]:
        return {
            "assignment_id": row.assignment_id,
            "shift_id": row.shift_id,
            "attendance_record_id": row.attendance_record_id,
            "actor_scope_code": actor_scope_code,
        }

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    def _can_view_finance_only(self, actor: RequestAuthorizationContext) -> bool:
        return bool(actor.is_platform_admin or actor.is_tenant_admin or "accounting" in actor.role_keys or "finance.approval.signoff" in actor.permission_keys)

    def _record_audit(
        self,
        actor: RequestAuthorizationContext,
        *,
        tenant_id: str,
        event_type: str,
        entity_id: str,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
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
            entity_type="finance.actual_record",
            entity_id=entity_id,
            before_json=before_json or {},
            after_json=after_json or {},
            metadata_json=metadata_json or {},
        )
