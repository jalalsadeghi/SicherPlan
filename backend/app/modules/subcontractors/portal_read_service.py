"""Contract-first subcontractor portal read models for released work and status views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from app.modules.subcontractors.schemas import (
    SubcontractorPortalActualSummaryCollectionRead,
    SubcontractorPortalActualSummaryRead,
    SubcontractorPortalAttendanceCollectionRead,
    SubcontractorPortalAttendanceRead,
    SubcontractorPortalCollectionSourceRead,
    SubcontractorPortalContextRead,
    SubcontractorPortalInvoiceCheckCollectionRead,
    SubcontractorPortalInvoiceCheckRead,
    SubcontractorPortalPositionCollectionRead,
    SubcontractorPortalPositionRead,
    SubcontractorPortalScheduleCollectionRead,
    SubcontractorPortalScheduleRead,
)


@dataclass(frozen=True, slots=True)
class ReleasedPortalPositionRecord:
    id: str
    subcontractor_id: str
    reference_no: str
    title: str
    branch_label: str | None
    mandate_label: str | None
    work_start: datetime
    work_end: datetime
    location_label: str | None
    readiness_status: str
    confirmation_status: str
    is_released: bool = True
    is_visible_to_partner: bool = True


@dataclass(frozen=True, slots=True)
class ReleasedPortalScheduleRecord:
    id: str
    subcontractor_id: str
    position_id: str
    shift_label: str
    schedule_date: date
    work_start: datetime
    work_end: datetime
    location_label: str | None
    confirmation_status: str
    is_released: bool = True
    is_visible_to_partner: bool = True


@dataclass(frozen=True, slots=True)
class ReleasedPortalActualSummaryRecord:
    id: str
    subcontractor_id: str
    period_start: date
    period_end: date
    confirmed_minutes: int
    open_minutes: int
    status: str
    attendance_status: str
    is_released: bool = True
    is_visible_to_partner: bool = True


@dataclass(frozen=True, slots=True)
class ReleasedPortalAttendanceRecord:
    id: str
    subcontractor_id: str
    schedule_id: str
    work_date: date
    status: str
    confirmed_at: datetime | None
    location_label: str | None
    document_count: int = 0
    is_released: bool = True
    is_visible_to_partner: bool = True


@dataclass(frozen=True, slots=True)
class ReleasedPortalInvoiceCheckRecord:
    id: str
    subcontractor_id: str
    period_label: str
    status: str
    submitted_invoice_ref: str | None = None
    approved_minutes: int = 0
    approved_amount: Decimal = Decimal("0.00")
    submitted_invoice_amount: Decimal | None = None
    last_checked_at: datetime | None = None
    variance_minutes: int | None = None
    variance_amount: Decimal | None = None
    is_released: bool = True
    is_visible_to_partner: bool = True


class PortalPositionAdapter(Protocol):
    def list_released_positions(self, context: SubcontractorPortalContextRead) -> list[ReleasedPortalPositionRecord]: ...


class PortalScheduleAdapter(Protocol):
    def list_released_schedules(self, context: SubcontractorPortalContextRead) -> list[ReleasedPortalScheduleRecord]: ...


class PortalActualSummaryAdapter(Protocol):
    def list_actual_summaries(
        self,
        context: SubcontractorPortalContextRead,
    ) -> list[ReleasedPortalActualSummaryRecord]: ...


class PortalAttendanceAdapter(Protocol):
    def list_attendance_visibility(
        self,
        context: SubcontractorPortalContextRead,
    ) -> list[ReleasedPortalAttendanceRecord]: ...


class PortalInvoiceCheckAdapter(Protocol):
    def list_invoice_checks(
        self,
        context: SubcontractorPortalContextRead,
    ) -> list[ReleasedPortalInvoiceCheckRecord]: ...


class SubcontractorPortalReadService:
    def __init__(
        self,
        *,
        position_adapter: PortalPositionAdapter | None = None,
        schedule_adapter: PortalScheduleAdapter | None = None,
        actual_summary_adapter: PortalActualSummaryAdapter | None = None,
        attendance_adapter: PortalAttendanceAdapter | None = None,
        invoice_check_adapter: PortalInvoiceCheckAdapter | None = None,
    ) -> None:
        self.position_adapter = position_adapter
        self.schedule_adapter = schedule_adapter
        self.actual_summary_adapter = actual_summary_adapter
        self.attendance_adapter = attendance_adapter
        self.invoice_check_adapter = invoice_check_adapter

    def list_positions(self, context: SubcontractorPortalContextRead) -> SubcontractorPortalPositionCollectionRead:
        if self.position_adapter is None:
            return SubcontractorPortalPositionCollectionRead(
                subcontractor_id=context.subcontractor_id,
                source=self._build_source(
                    domain_key="positions",
                    source_module_key="planning",
                    message_key="portalSubcontractor.datasets.positions.pending",
                ),
            )
        items = [
            SubcontractorPortalPositionRead(
                id=row.id,
                subcontractor_id=row.subcontractor_id,
                reference_no=row.reference_no,
                title=row.title,
                branch_label=row.branch_label,
                mandate_label=row.mandate_label,
                work_start=row.work_start,
                work_end=row.work_end,
                location_label=row.location_label,
                readiness_status=row.readiness_status,
                confirmation_status=row.confirmation_status,
            )
            for row in self.position_adapter.list_released_positions(context)
            if self._is_visible(row.subcontractor_id, context, row.is_released, row.is_visible_to_partner)
        ]
        return SubcontractorPortalPositionCollectionRead(
            subcontractor_id=context.subcontractor_id,
            source=self._build_source(
                domain_key="positions",
                source_module_key="planning",
                availability_status="ready",
                message_key="portalSubcontractor.datasets.positions.pending",
            ),
            items=items,
        )

    def list_schedules(self, context: SubcontractorPortalContextRead) -> SubcontractorPortalScheduleCollectionRead:
        if self.schedule_adapter is None:
            return SubcontractorPortalScheduleCollectionRead(
                subcontractor_id=context.subcontractor_id,
                source=self._build_source(
                    domain_key="schedules",
                    source_module_key="planning",
                    message_key="portalSubcontractor.datasets.schedules.pending",
                ),
            )
        items = [
            SubcontractorPortalScheduleRead(
                id=row.id,
                subcontractor_id=row.subcontractor_id,
                position_id=row.position_id,
                shift_label=row.shift_label,
                schedule_date=row.schedule_date,
                work_start=row.work_start,
                work_end=row.work_end,
                location_label=row.location_label,
                confirmation_status=row.confirmation_status,
            )
            for row in self.schedule_adapter.list_released_schedules(context)
            if self._is_visible(row.subcontractor_id, context, row.is_released, row.is_visible_to_partner)
        ]
        return SubcontractorPortalScheduleCollectionRead(
            subcontractor_id=context.subcontractor_id,
            source=self._build_source(
                domain_key="schedules",
                source_module_key="planning",
                availability_status="ready",
                message_key="portalSubcontractor.datasets.schedules.pending",
            ),
            items=items,
        )

    def list_actual_summaries(
        self,
        context: SubcontractorPortalContextRead,
    ) -> SubcontractorPortalActualSummaryCollectionRead:
        if self.actual_summary_adapter is None:
            return SubcontractorPortalActualSummaryCollectionRead(
                subcontractor_id=context.subcontractor_id,
                source=self._build_source(
                    domain_key="actuals",
                    source_module_key="finance",
                    message_key="portalSubcontractor.datasets.actuals.pending",
                ),
            )
        items = [
            SubcontractorPortalActualSummaryRead(
                id=row.id,
                subcontractor_id=row.subcontractor_id,
                period_start=row.period_start,
                period_end=row.period_end,
                confirmed_minutes=row.confirmed_minutes,
                open_minutes=row.open_minutes,
                status=row.status,
                attendance_status=row.attendance_status,
            )
            for row in self.actual_summary_adapter.list_actual_summaries(context)
            if self._is_visible(row.subcontractor_id, context, row.is_released, row.is_visible_to_partner)
        ]
        return SubcontractorPortalActualSummaryCollectionRead(
            subcontractor_id=context.subcontractor_id,
            source=self._build_source(
                domain_key="actuals",
                source_module_key="finance",
                availability_status="ready",
                message_key="portalSubcontractor.datasets.actuals.pending",
            ),
            items=items,
        )

    def list_attendance_visibility(
        self,
        context: SubcontractorPortalContextRead,
    ) -> SubcontractorPortalAttendanceCollectionRead:
        if self.attendance_adapter is None:
            return SubcontractorPortalAttendanceCollectionRead(
                subcontractor_id=context.subcontractor_id,
                source=self._build_source(
                    domain_key="attendance",
                    source_module_key="field_execution",
                    message_key="portalSubcontractor.datasets.attendance.pending",
                ),
            )
        items = [
            SubcontractorPortalAttendanceRead(
                id=row.id,
                subcontractor_id=row.subcontractor_id,
                schedule_id=row.schedule_id,
                work_date=row.work_date,
                status=row.status,
                confirmed_at=row.confirmed_at,
                location_label=row.location_label,
                document_count=row.document_count,
            )
            for row in self.attendance_adapter.list_attendance_visibility(context)
            if self._is_visible(row.subcontractor_id, context, row.is_released, row.is_visible_to_partner)
        ]
        return SubcontractorPortalAttendanceCollectionRead(
            subcontractor_id=context.subcontractor_id,
            source=self._build_source(
                domain_key="attendance",
                source_module_key="field_execution",
                availability_status="ready",
                message_key="portalSubcontractor.datasets.attendance.pending",
            ),
            items=items,
        )

    def list_invoice_checks(
        self,
        context: SubcontractorPortalContextRead,
    ) -> SubcontractorPortalInvoiceCheckCollectionRead:
        if self.invoice_check_adapter is None:
            return SubcontractorPortalInvoiceCheckCollectionRead(
                subcontractor_id=context.subcontractor_id,
                source=self._build_source(
                    domain_key="invoice_checks",
                    source_module_key="finance",
                    message_key="portalSubcontractor.datasets.invoiceChecks.pending",
                ),
            )
        items = [
            SubcontractorPortalInvoiceCheckRead(
                id=row.id,
                subcontractor_id=row.subcontractor_id,
                period_label=row.period_label,
                status=row.status,
                submitted_invoice_ref=row.submitted_invoice_ref,
                approved_minutes=row.approved_minutes,
                approved_amount=row.approved_amount,
                submitted_invoice_amount=row.submitted_invoice_amount,
                last_checked_at=row.last_checked_at,
                variance_minutes=row.variance_minutes,
                variance_amount=row.variance_amount,
            )
            for row in self.invoice_check_adapter.list_invoice_checks(context)
            if self._is_visible(row.subcontractor_id, context, row.is_released, row.is_visible_to_partner)
        ]
        return SubcontractorPortalInvoiceCheckCollectionRead(
            subcontractor_id=context.subcontractor_id,
            source=self._build_source(
                domain_key="invoice_checks",
                source_module_key="finance",
                availability_status="ready",
                message_key="portalSubcontractor.datasets.invoiceChecks.pending",
            ),
            items=items,
        )

    def _build_source(
        self,
        *,
        domain_key: str,
        source_module_key: str,
        message_key: str,
        availability_status: str = "pending_source_module",
        docs_backed_outputs: bool = False,
    ) -> SubcontractorPortalCollectionSourceRead:
        return SubcontractorPortalCollectionSourceRead(
            domain_key=domain_key,
            source_module_key=source_module_key,
            availability_status=availability_status,
            released_only=True,
            subcontractor_scoped=True,
            docs_backed_outputs=docs_backed_outputs,
            message_key=message_key,
        )

    @staticmethod
    def _is_visible(
        subcontractor_id: str,
        context: SubcontractorPortalContextRead,
        is_released: bool,
        is_visible_to_partner: bool,
    ) -> bool:
        return (
            subcontractor_id == context.subcontractor_id
            and is_released
            and is_visible_to_partner
        )
