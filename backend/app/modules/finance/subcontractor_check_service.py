from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Protocol

from app.errors import ApiException
from app.modules.finance.models import SubcontractorInvoiceCheck, SubcontractorInvoiceCheckLine, SubcontractorInvoiceCheckNote
from app.modules.finance.subcontractor_check_schemas import (
    SubcontractorInvoiceCheckGenerateRequest,
    SubcontractorInvoiceCheckLineRead,
    SubcontractorInvoiceCheckListFilter,
    SubcontractorInvoiceCheckListItem,
    SubcontractorInvoiceCheckNoteCreate,
    SubcontractorInvoiceCheckNoteRead,
    SubcontractorInvoiceCheckRead,
    SubcontractorInvoiceCheckStatusRequest,
    SubcontractorInvoiceSubmissionUpdateRequest,
    SubcontractorPortalInvoiceCheckDetailRead,
    SubcontractorPortalInvoiceCheckLineRead,
    SubcontractorPortalInvoiceCheckRead,
)
from app.modules.iam.audit_schemas import AuditEventRead
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext


class SubcontractorInvoiceCheckRepository(Protocol):
    def list_invoice_checks(self, tenant_id: str, filters: SubcontractorInvoiceCheckListFilter): ...
    def get_invoice_check(self, tenant_id: str, invoice_check_id: str): ...
    def find_by_period(self, tenant_id: str, subcontractor_id: str, period_start: date, period_end: date): ...
    def create_invoice_check(self, row: SubcontractorInvoiceCheck) -> SubcontractorInvoiceCheck: ...
    def save_invoice_check(self, row: SubcontractorInvoiceCheck) -> SubcontractorInvoiceCheck: ...
    def create_note(self, row: SubcontractorInvoiceCheckNote) -> SubcontractorInvoiceCheckNote: ...
    def list_signed_off_actuals_for_subcontractor(self, tenant_id: str, subcontractor_id: str, period_start: date, period_end: date): ...  # noqa: ANN001
    def list_active_subcontractor_rate_cards(self, tenant_id: str, subcontractor_id: str, on_date: date): ...  # noqa: ANN001
    def get_subcontractor_finance_profile(self, tenant_id: str, subcontractor_id: str): ...  # noqa: ANN001
    def list_audit_events_for_invoice_check(self, tenant_id: str, invoice_check_id: str) -> list[AuditEventRead]: ...


@dataclass
class _ResolvedRate:
    rate_card_id: str
    rate_line_id: str
    billing_unit_code: str
    unit_price: Decimal
    minimum_quantity: Decimal | None


class SubcontractorInvoiceCheckService:
    def __init__(self, repository: SubcontractorInvoiceCheckRepository, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_invoice_checks(
        self,
        tenant_id: str,
        filters: SubcontractorInvoiceCheckListFilter,
        actor: RequestAuthorizationContext,
    ) -> list[SubcontractorInvoiceCheckListItem]:
        self._require_read(actor, tenant_id)
        return [self._map_list_item(row) for row in self.repository.list_invoice_checks(tenant_id, filters)]

    def get_invoice_check(
        self,
        tenant_id: str,
        invoice_check_id: str,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorInvoiceCheckRead:
        self._require_read(actor, tenant_id)
        return self._map_read(self._require_check(tenant_id, invoice_check_id))

    def generate_invoice_check(
        self,
        tenant_id: str,
        payload: SubcontractorInvoiceCheckGenerateRequest,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorInvoiceCheckRead:
        self._require_write(actor, tenant_id)
        if payload.period_end < payload.period_start:
            raise ApiException(400, "finance.subcontractor_invoice_check.period.invalid", "errors.finance.subcontractor_invoice_check.period.invalid")
        existing = self.repository.find_by_period(tenant_id, payload.subcontractor_id, payload.period_start, payload.period_end)
        current_status = existing.status_code if existing is not None else "draft"
        row = existing or SubcontractorInvoiceCheck(
            tenant_id=tenant_id,
            subcontractor_id=payload.subcontractor_id,
            check_no=self._build_check_no(payload.subcontractor_id, payload.period_start, payload.period_end),
            period_start=payload.period_start,
            period_end=payload.period_end,
            period_label=f"{payload.period_start.isoformat()} - {payload.period_end.isoformat()}",
            created_by_user_id=actor.user_id,
            updated_by_user_id=actor.user_id,
        )
        before = None if existing is None else self._snapshot(existing)
        line_rows = self._build_lines(tenant_id, payload.subcontractor_id, payload.period_start, payload.period_end)
        row.lines = line_rows
        row.assigned_minutes_total = sum(line.assigned_minutes for line in line_rows)
        row.actual_minutes_total = sum(line.actual_minutes for line in line_rows)
        row.approved_minutes_total = sum(line.approved_minutes for line in line_rows)
        row.expected_amount_total = self._q(sum((Decimal(str(line.expected_amount)) for line in line_rows), Decimal("0")))
        row.approved_amount_total = self._q(sum((Decimal(str(line.approved_amount)) for line in line_rows), Decimal("0")))
        row.comparison_variance_amount = self._q(Decimal(str(row.approved_amount_total)) - Decimal(str(row.expected_amount_total)))
        row.review_reason_codes_json = sorted({reason for line in line_rows for reason in line.variance_reason_codes_json})
        row.last_generated_at = datetime.now(UTC)
        row.updated_by_user_id = actor.user_id
        row.version_no = (row.version_no or 0) + (0 if existing is None else 1)
        if current_status in {"approved", "released"}:
            row.status_code = current_status
        else:
            row.status_code = "review_required" if any(reason in {"missing_rate", "ambiguous_rate"} for reason in row.review_reason_codes_json) else "draft"
        if row.submitted_invoice_amount is not None:
            row.submitted_variance_amount = self._q(Decimal(str(row.submitted_invoice_amount)) - Decimal(str(row.approved_amount_total)))
        saved = self.repository.create_invoice_check(row) if existing is None else self.repository.save_invoice_check(row)
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="finance.subcontractor_invoice_check.generated",
            entity_id=saved.id,
            before_json=before,
            after_json=self._snapshot(saved),
        )
        return self._map_read(saved)

    def update_submitted_invoice(
        self,
        tenant_id: str,
        invoice_check_id: str,
        payload: SubcontractorInvoiceSubmissionUpdateRequest,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorInvoiceCheckRead:
        self._require_write(actor, tenant_id)
        row = self._require_check(tenant_id, invoice_check_id)
        before = self._snapshot(row)
        row.submitted_invoice_ref = self._normalize_optional(payload.submitted_invoice_ref)
        row.submitted_invoice_amount = payload.submitted_invoice_amount
        row.submitted_invoice_currency_code = self._normalize_optional(payload.submitted_invoice_currency_code)
        row.submitted_variance_amount = (
            self._q(Decimal(str(payload.submitted_invoice_amount)) - Decimal(str(row.approved_amount_total)))
            if payload.submitted_invoice_amount is not None
            else None
        )
        reasons = set(row.review_reason_codes_json)
        if row.submitted_variance_amount not in (None, Decimal("0.00")):
            reasons.add("submitted_amount_discrepancy")
        else:
            reasons.discard("submitted_amount_discrepancy")
        row.review_reason_codes_json = sorted(reasons)
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        saved = self.repository.save_invoice_check(row)
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="finance.subcontractor_invoice_check.submitted_invoice_updated",
            entity_id=saved.id,
            before_json=before,
            after_json=self._snapshot(saved),
        )
        return self._map_read(saved)

    def add_note(
        self,
        tenant_id: str,
        invoice_check_id: str,
        payload: SubcontractorInvoiceCheckNoteCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorInvoiceCheckRead:
        self._require_write(actor, tenant_id)
        row = self._require_check(tenant_id, invoice_check_id)
        note = self.repository.create_note(
            SubcontractorInvoiceCheckNote(
                tenant_id=tenant_id,
                invoice_check_id=row.id,
                note_kind_code=payload.note_kind_code,
                note_text=payload.note_text.strip(),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type="finance.subcontractor_invoice_check.note_added",
            entity_id=row.id,
            metadata_json={"note_id": note.id, "note_kind_code": note.note_kind_code},
        )
        return self._map_read(self._require_check(tenant_id, invoice_check_id))

    def change_status(
        self,
        tenant_id: str,
        invoice_check_id: str,
        payload: SubcontractorInvoiceCheckStatusRequest,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorInvoiceCheckRead:
        self._require_write(actor, tenant_id)
        row = self._require_check(tenant_id, invoice_check_id)
        self._validate_status_transition(row.status_code, payload.status_code)
        before = self._snapshot(row)
        row.status_code = payload.status_code
        if payload.status_code == "approved":
            row.approved_at = datetime.now(UTC)
        if payload.status_code == "released":
            row.released_at = datetime.now(UTC)
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        saved = self.repository.save_invoice_check(row)
        if payload.note_text:
            self.repository.create_note(
                SubcontractorInvoiceCheckNote(
                    tenant_id=tenant_id,
                    invoice_check_id=row.id,
                    note_kind_code="approval" if payload.status_code in {"approved", "released"} else "exception",
                    note_text=payload.note_text.strip(),
                    created_by_user_id=actor.user_id,
                    updated_by_user_id=actor.user_id,
                )
            )
        self._record_audit(
            actor,
            tenant_id=tenant_id,
            event_type=f"finance.subcontractor_invoice_check.status.{payload.status_code}",
            entity_id=saved.id,
            before_json=before,
            after_json=self._snapshot(saved),
        )
        return self._map_read(saved)

    def get_audit_history(self, tenant_id: str, invoice_check_id: str, actor: RequestAuthorizationContext) -> list[AuditEventRead]:
        self._require_read(actor, tenant_id)
        self._require_check(tenant_id, invoice_check_id)
        return self.repository.list_audit_events_for_invoice_check(tenant_id, invoice_check_id)

    def list_portal_invoice_checks(self, tenant_id: str, subcontractor_id: str) -> list[SubcontractorPortalInvoiceCheckRead]:
        rows = self.repository.list_invoice_checks(
            tenant_id,
            SubcontractorInvoiceCheckListFilter(subcontractor_id=subcontractor_id),
        )
        return [
            self._map_portal_item(row)
            for row in rows
            if row.status_code == "released"
        ]

    def get_portal_invoice_check_detail(self, tenant_id: str, subcontractor_id: str, invoice_check_id: str) -> SubcontractorPortalInvoiceCheckDetailRead:
        row = self._require_check(tenant_id, invoice_check_id)
        if row.subcontractor_id != subcontractor_id or row.status_code != "released":
            raise ApiException(404, "subcontractors.portal.invoice_check.not_found", "errors.subcontractors.portal.invoice_check.not_found")
        return SubcontractorPortalInvoiceCheckDetailRead(
            **self._map_portal_item(row).model_dump(),
            period_start=row.period_start,
            period_end=row.period_end,
            released_at=row.released_at,
            lines=[
                SubcontractorPortalInvoiceCheckLineRead(
                    id=line.id,
                    service_date=line.service_date,
                    label=line.label,
                    billing_unit_code=line.billing_unit_code,
                    approved_quantity=Decimal(str(line.approved_quantity)),
                    unit_price=None if line.unit_price is None else Decimal(str(line.unit_price)),
                    approved_amount=Decimal(str(line.approved_amount)),
                    variance_amount=Decimal(str(line.variance_amount)),
                    variance_reason_codes_json=list(line.variance_reason_codes_json),
                )
                for line in row.lines
            ],
        )

    def _build_lines(self, tenant_id: str, subcontractor_id: str, period_start: date, period_end: date) -> list[SubcontractorInvoiceCheckLine]:
        actuals = self.repository.list_signed_off_actuals_for_subcontractor(tenant_id, subcontractor_id, period_start, period_end)
        lines: list[SubcontractorInvoiceCheckLine] = []
        for index, actual in enumerate(actuals, start=1):
            assignment = actual.assignment
            shift = actual.shift
            worker = actual.subcontractor_worker
            if assignment is None or shift is None or worker is None:
                continue
            assigned_minutes = self._planned_minutes(shift)
            actual_minutes = self._actual_minutes(actual)
            approved_minutes = max(int(actual.payable_minutes or 0), 0)
            service_date = (actual.planned_start_at or shift.starts_at).date()
            resolved_rate, rate_reasons = self._resolve_rate(
                tenant_id=tenant_id,
                subcontractor_id=subcontractor_id,
                on_date=service_date,
                function_type_id=getattr(assignment.demand_group, "function_type_id", None),
                qualification_type_id=getattr(assignment.demand_group, "qualification_type_id", None),
            )
            billing_unit_code = "hour" if resolved_rate is None else resolved_rate.billing_unit_code
            expected_quantity = self._derive_quantity(assigned_minutes, billing_unit_code, resolved_rate.minimum_quantity if resolved_rate else None)
            actual_quantity = self._derive_quantity(actual_minutes, billing_unit_code, resolved_rate.minimum_quantity if resolved_rate else None)
            approved_quantity = self._derive_quantity(approved_minutes, billing_unit_code, resolved_rate.minimum_quantity if resolved_rate else None)
            unit_price = None if resolved_rate is None else resolved_rate.unit_price
            expected_amount = Decimal("0.00") if unit_price is None else self._q(expected_quantity * unit_price)
            approved_amount = Decimal("0.00") if unit_price is None else self._q(approved_quantity * unit_price)
            variance_amount = self._q(approved_amount - expected_amount)
            reasons = set(rate_reasons)
            if approved_quantity != expected_quantity:
                reasons.add("quantity_mismatch")
            if approved_minutes == 0:
                reasons.add("canceled_shift")
            if any(getattr(item, "reconciliation_kind_code", None) == "replacement" for item in getattr(actual, "reconciliations", [])):
                reasons.add("replaced_shift")
            comparison_state_code = self._comparison_state(reasons)
            lines.append(
                SubcontractorInvoiceCheckLine(
                    tenant_id=tenant_id,
                    assignment_id=assignment.id,
                    actual_record_id=actual.id,
                    shift_id=shift.id,
                    subcontractor_worker_id=worker.id,
                    rate_card_id=None if resolved_rate is None else resolved_rate.rate_card_id,
                    rate_line_id=None if resolved_rate is None else resolved_rate.rate_line_id,
                    function_type_id=getattr(assignment.demand_group, "function_type_id", None),
                    qualification_type_id=getattr(assignment.demand_group, "qualification_type_id", None),
                    sort_order=index * 100,
                    service_date=service_date,
                    label=self._line_label(actual),
                    billing_unit_code=billing_unit_code,
                    assigned_minutes=assigned_minutes,
                    actual_minutes=actual_minutes,
                    approved_minutes=approved_minutes,
                    expected_quantity=expected_quantity,
                    actual_quantity=actual_quantity,
                    approved_quantity=approved_quantity,
                    unit_price=unit_price,
                    expected_amount=expected_amount,
                    approved_amount=approved_amount,
                    variance_amount=variance_amount,
                    comparison_state_code=comparison_state_code,
                    variance_reason_codes_json=sorted(reasons),
                    source_ref_json={
                        "assignment_id": assignment.id,
                        "actual_record_id": actual.id,
                        "shift_id": shift.id,
                    },
                )
            )
        return lines

    def _resolve_rate(
        self,
        *,
        tenant_id: str,
        subcontractor_id: str,
        on_date: date,
        function_type_id: str | None,
        qualification_type_id: str | None,
    ) -> tuple[_ResolvedRate | None, set[str]]:
        rate_cards = self.repository.list_active_subcontractor_rate_cards(tenant_id, subcontractor_id, on_date)
        matches: list[_ResolvedRate] = []
        for card in rate_cards:
            for line in card.rate_lines:
                if line.function_type_id is not None and line.function_type_id != function_type_id:
                    continue
                if line.qualification_type_id is not None and line.qualification_type_id != qualification_type_id:
                    continue
                matches.append(
                    _ResolvedRate(
                        rate_card_id=card.id,
                        rate_line_id=line.id,
                        billing_unit_code=line.billing_unit_code,
                        unit_price=Decimal(str(line.unit_price)),
                        minimum_quantity=None if line.minimum_quantity is None else Decimal(str(line.minimum_quantity)),
                    )
                )
        if not matches:
            return None, {"missing_rate"}
        if len(matches) > 1:
            return None, {"ambiguous_rate"}
        return matches[0], set()

    def _validate_status_transition(self, current: str, target: str) -> None:
        allowed = {
            "draft": {"review_required", "approved", "exception"},
            "review_required": {"approved", "exception"},
            "approved": {"released", "exception", "review_required"},
            "exception": {"review_required", "approved"},
            "released": {"approved"},
        }
        if target not in allowed.get(current, set()):
            raise ApiException(409, "finance.subcontractor_invoice_check.invalid_status", "errors.finance.subcontractor_invoice_check.invalid_status")

    def _require_check(self, tenant_id: str, invoice_check_id: str) -> SubcontractorInvoiceCheck:
        row = self.repository.get_invoice_check(tenant_id, invoice_check_id)
        if row is None:
            raise ApiException(404, "finance.subcontractor_invoice_check.not_found", "errors.finance.subcontractor_invoice_check.not_found")
        return row

    def _require_read(self, actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.tenant_id != tenant_id or not actor.has_permission("finance.subcontractor_control.read"):
            raise ApiException(403, "finance.subcontractor_invoice_check.permission_denied", "errors.iam.authorization.permission_denied")

    def _require_write(self, actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.tenant_id != tenant_id or not actor.has_permission("finance.subcontractor_control.write"):
            raise ApiException(403, "finance.subcontractor_invoice_check.permission_denied", "errors.iam.authorization.permission_denied")

    def _planned_minutes(self, shift) -> int:  # noqa: ANN001
        if shift.starts_at is None or shift.ends_at is None:
            return 0
        total = int((shift.ends_at - shift.starts_at).total_seconds() // 60)
        return max(total - int(shift.break_minutes or 0), 0)

    def _actual_minutes(self, actual) -> int:  # noqa: ANN001
        if actual.actual_start_at is None or actual.actual_end_at is None:
            return max(int(actual.payable_minutes or 0), 0)
        total = int((actual.actual_end_at - actual.actual_start_at).total_seconds() // 60)
        return max(total - int(actual.actual_break_minutes or 0), 0)

    def _derive_quantity(self, minutes: int, billing_unit_code: str, minimum_quantity: Decimal | None) -> Decimal:
        if billing_unit_code == "flat":
            quantity = Decimal("1.00") if minutes > 0 else Decimal("0.00")
        elif billing_unit_code == "day":
            quantity = Decimal(minutes) / Decimal("480")
        else:
            quantity = Decimal(minutes) / Decimal("60")
        quantity = self._q(quantity)
        if minimum_quantity is not None:
            quantity = max(quantity, self._q(minimum_quantity))
        return quantity

    def _comparison_state(self, reasons: set[str]) -> str:
        if {"missing_rate", "ambiguous_rate"} & reasons:
            return "needs_review"
        if reasons:
            return "warning"
        return "clean"

    def _line_label(self, actual) -> str:  # noqa: ANN001
        shift = actual.shift
        worker = actual.subcontractor_worker
        shift_label = getattr(getattr(shift, "shift_plan", None), "planning_record", None)
        record_name = getattr(shift_label, "name", None) if shift_label is not None else None
        worker_name = f"{worker.first_name} {worker.last_name}" if worker is not None else "Partner worker"
        return f"{record_name or shift.id} · {worker_name}"

    def _map_list_item(self, row: SubcontractorInvoiceCheck) -> SubcontractorInvoiceCheckListItem:
        return SubcontractorInvoiceCheckListItem(
            id=row.id,
            subcontractor_id=row.subcontractor_id,
            check_no=row.check_no,
            period_start=row.period_start,
            period_end=row.period_end,
            period_label=row.period_label,
            status_code=row.status_code,
            assigned_minutes_total=row.assigned_minutes_total,
            actual_minutes_total=row.actual_minutes_total,
            approved_minutes_total=row.approved_minutes_total,
            expected_amount_total=Decimal(str(row.expected_amount_total)),
            approved_amount_total=Decimal(str(row.approved_amount_total)),
            comparison_variance_amount=Decimal(str(row.comparison_variance_amount)),
            submitted_invoice_ref=row.submitted_invoice_ref,
            submitted_invoice_amount=None if row.submitted_invoice_amount is None else Decimal(str(row.submitted_invoice_amount)),
            submitted_variance_amount=None if row.submitted_variance_amount is None else Decimal(str(row.submitted_variance_amount)),
            review_reason_codes_json=list(row.review_reason_codes_json),
            last_generated_at=row.last_generated_at,
        )

    def _map_read(self, row: SubcontractorInvoiceCheck) -> SubcontractorInvoiceCheckRead:
        return SubcontractorInvoiceCheckRead(
            **self._map_list_item(row).model_dump(),
            submitted_invoice_currency_code=row.submitted_invoice_currency_code,
            approved_at=row.approved_at,
            released_at=row.released_at,
            metadata_json=dict(row.metadata_json or {}),
            lines=[
                SubcontractorInvoiceCheckLineRead(
                    id=line.id,
                    assignment_id=line.assignment_id,
                    actual_record_id=line.actual_record_id,
                    shift_id=line.shift_id,
                    subcontractor_worker_id=line.subcontractor_worker_id,
                    function_type_id=line.function_type_id,
                    qualification_type_id=line.qualification_type_id,
                    service_date=line.service_date,
                    label=line.label,
                    billing_unit_code=line.billing_unit_code,
                    assigned_minutes=line.assigned_minutes,
                    actual_minutes=line.actual_minutes,
                    approved_minutes=line.approved_minutes,
                    expected_quantity=Decimal(str(line.expected_quantity)),
                    actual_quantity=Decimal(str(line.actual_quantity)),
                    approved_quantity=Decimal(str(line.approved_quantity)),
                    unit_price=None if line.unit_price is None else Decimal(str(line.unit_price)),
                    expected_amount=Decimal(str(line.expected_amount)),
                    approved_amount=Decimal(str(line.approved_amount)),
                    variance_amount=Decimal(str(line.variance_amount)),
                    comparison_state_code=line.comparison_state_code,
                    variance_reason_codes_json=list(line.variance_reason_codes_json),
                    source_ref_json=dict(line.source_ref_json or {}),
                )
                for line in row.lines
            ],
            notes=[
                SubcontractorInvoiceCheckNoteRead(
                    id=note.id,
                    note_kind_code=note.note_kind_code,
                    note_text=note.note_text,
                    created_at=note.created_at,
                    created_by_user_id=note.created_by_user_id,
                )
                for note in row.notes
            ],
        )

    def _map_portal_item(self, row: SubcontractorInvoiceCheck) -> SubcontractorPortalInvoiceCheckRead:
        variance = row.submitted_variance_amount if row.submitted_variance_amount is not None else row.comparison_variance_amount
        return SubcontractorPortalInvoiceCheckRead(
            id=row.id,
            subcontractor_id=row.subcontractor_id,
            period_label=row.period_label,
            status=row.status_code,
            submitted_invoice_ref=row.submitted_invoice_ref,
            approved_minutes=row.approved_minutes_total,
            approved_amount=Decimal(str(row.approved_amount_total)),
            submitted_invoice_amount=None if row.submitted_invoice_amount is None else Decimal(str(row.submitted_invoice_amount)),
            variance_amount=None if variance is None else Decimal(str(variance)),
            last_checked_at=row.last_generated_at,
        )

    def _build_check_no(self, subcontractor_id: str, period_start: date, period_end: date) -> str:
        return f"SIC-{period_start.strftime('%Y%m%d')}-{period_end.strftime('%Y%m%d')}-{subcontractor_id[:8]}"

    def _q(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _normalize_optional(self, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def _snapshot(self, row: SubcontractorInvoiceCheck) -> dict[str, object]:
        return {
            "status_code": row.status_code,
            "period_start": row.period_start.isoformat(),
            "period_end": row.period_end.isoformat(),
            "assigned_minutes_total": row.assigned_minutes_total,
            "actual_minutes_total": row.actual_minutes_total,
            "approved_minutes_total": row.approved_minutes_total,
            "expected_amount_total": str(row.expected_amount_total),
            "approved_amount_total": str(row.approved_amount_total),
            "comparison_variance_amount": str(row.comparison_variance_amount),
            "submitted_invoice_ref": row.submitted_invoice_ref,
            "submitted_invoice_amount": None if row.submitted_invoice_amount is None else str(row.submitted_invoice_amount),
            "submitted_variance_amount": None if row.submitted_variance_amount is None else str(row.submitted_variance_amount),
            "review_reason_codes_json": list(row.review_reason_codes_json),
        }

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
        self.audit_service.record_event(
            tenant_id=tenant_id,
            actor=AuditActor.from_request_context(actor),
            entity_type="finance.subcontractor_invoice_check",
            entity_id=entity_id,
            event_type=event_type,
            before_json=before_json,
            after_json=after_json,
            metadata_json=metadata_json,
        )
