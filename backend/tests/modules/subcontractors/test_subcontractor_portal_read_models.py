from __future__ import annotations

import unittest
from datetime import UTC, date, datetime
from decimal import Decimal

from app.modules.subcontractors.portal_read_service import (
    ReleasedPortalActualSummaryRecord,
    ReleasedPortalAttendanceRecord,
    ReleasedPortalInvoiceCheckRecord,
    ReleasedPortalPositionRecord,
    ReleasedPortalScheduleRecord,
    SubcontractorPortalReadService,
)
from app.modules.subcontractors.schemas import (
    SubcontractorPortalCompanyRead,
    SubcontractorPortalContactRead,
    SubcontractorPortalContextRead,
    SubcontractorPortalScopeRead,
)


def _context() -> SubcontractorPortalContextRead:
    return SubcontractorPortalContextRead(
        tenant_id="tenant-1",
        user_id="user-portal",
        subcontractor_id="subcontractor-1",
        contact_id="contact-1",
        company=SubcontractorPortalCompanyRead(
            id="subcontractor-1",
            tenant_id="tenant-1",
            subcontractor_number="SU-1000",
            legal_name="Partnerwache GmbH",
            display_name="Partnerwache",
            status="active",
        ),
        contact=SubcontractorPortalContactRead(
            id="contact-1",
            tenant_id="tenant-1",
            subcontractor_id="subcontractor-1",
            full_name="Pat Portal",
            function_label="Disposition",
            email="portal@example.invalid",
            phone=None,
            mobile=None,
            portal_enabled=True,
            status="active",
        ),
        scopes=[
            SubcontractorPortalScopeRead(
                role_key="subcontractor_user",
                scope_type="subcontractor",
                subcontractor_id="subcontractor-1",
            )
        ],
    )


class _PositionAdapter:
    def list_released_positions(self, context: SubcontractorPortalContextRead) -> list[ReleasedPortalPositionRecord]:
        return [
            ReleasedPortalPositionRecord(
                id="position-1",
                subcontractor_id=context.subcontractor_id,
                reference_no="REL-100",
                title="Objekt Nord Eingangsdienst",
                branch_label="Berlin",
                mandate_label="Mandat 1",
                work_start=datetime(2026, 3, 20, 8, 0, tzinfo=UTC),
                work_end=datetime(2026, 3, 20, 16, 0, tzinfo=UTC),
                location_label="Objekt Nord",
                readiness_status="ready",
                confirmation_status="released",
            ),
            ReleasedPortalPositionRecord(
                id="position-hidden",
                subcontractor_id=context.subcontractor_id,
                reference_no="DRAFT-1",
                title="Hidden",
                branch_label=None,
                mandate_label=None,
                work_start=datetime(2026, 3, 21, 8, 0, tzinfo=UTC),
                work_end=datetime(2026, 3, 21, 16, 0, tzinfo=UTC),
                location_label=None,
                readiness_status="ready",
                confirmation_status="draft",
                is_released=False,
            ),
            ReleasedPortalPositionRecord(
                id="position-cross",
                subcontractor_id="subcontractor-2",
                reference_no="REL-999",
                title="Cross tenant scope",
                branch_label=None,
                mandate_label=None,
                work_start=datetime(2026, 3, 22, 8, 0, tzinfo=UTC),
                work_end=datetime(2026, 3, 22, 16, 0, tzinfo=UTC),
                location_label=None,
                readiness_status="ready",
                confirmation_status="released",
            ),
        ]


class _ScheduleAdapter:
    def list_released_schedules(self, context: SubcontractorPortalContextRead) -> list[ReleasedPortalScheduleRecord]:
        return [
            ReleasedPortalScheduleRecord(
                id="schedule-1",
                subcontractor_id=context.subcontractor_id,
                position_id="position-1",
                shift_label="Fruehschicht",
                schedule_date=date(2026, 3, 20),
                work_start=datetime(2026, 3, 20, 8, 0, tzinfo=UTC),
                work_end=datetime(2026, 3, 20, 16, 0, tzinfo=UTC),
                location_label="Objekt Nord",
                confirmation_status="released",
            )
        ]


class _ActualAdapter:
    def list_actual_summaries(
        self,
        context: SubcontractorPortalContextRead,
    ) -> list[ReleasedPortalActualSummaryRecord]:
        return [
            ReleasedPortalActualSummaryRecord(
                id="actual-1",
                subcontractor_id=context.subcontractor_id,
                period_start=date(2026, 3, 1),
                period_end=date(2026, 3, 15),
                confirmed_minutes=960,
                open_minutes=60,
                status="partially_confirmed",
                attendance_status="open_discrepancy",
            )
        ]


class _AttendanceAdapter:
    def list_attendance_visibility(
        self,
        context: SubcontractorPortalContextRead,
    ) -> list[ReleasedPortalAttendanceRecord]:
        return [
            ReleasedPortalAttendanceRecord(
                id="attendance-1",
                subcontractor_id=context.subcontractor_id,
                schedule_id="schedule-1",
                work_date=date(2026, 3, 20),
                status="confirmed",
                confirmed_at=datetime(2026, 3, 20, 16, 15, tzinfo=UTC),
                location_label="Objekt Nord",
                document_count=1,
            )
        ]


class _InvoiceAdapter:
    def list_invoice_checks(
        self,
        context: SubcontractorPortalContextRead,
    ) -> list[ReleasedPortalInvoiceCheckRecord]:
        return [
            ReleasedPortalInvoiceCheckRecord(
                id="invoice-check-1",
                subcontractor_id=context.subcontractor_id,
                period_label="KW 12 / 2026",
                status="ready_for_review",
                last_checked_at=datetime(2026, 3, 21, 9, 0, tzinfo=UTC),
                variance_minutes=15,
                variance_amount=Decimal("42.50"),
            )
        ]


class TestSubcontractorPortalReadModels(unittest.TestCase):
    def test_empty_state_contracts_stay_stable_without_upstream_adapters(self) -> None:
        service = SubcontractorPortalReadService()
        context = _context()

        positions = service.list_positions(context)
        schedules = service.list_schedules(context)
        actuals = service.list_actual_summaries(context)
        attendance = service.list_attendance_visibility(context)
        invoice_checks = service.list_invoice_checks(context)

        self.assertEqual(positions.source.availability_status, "pending_source_module")
        self.assertEqual(schedules.source.availability_status, "pending_source_module")
        self.assertEqual(actuals.source.availability_status, "pending_source_module")
        self.assertEqual(attendance.source.availability_status, "pending_source_module")
        self.assertEqual(invoice_checks.source.availability_status, "pending_source_module")
        self.assertEqual(positions.items, [])
        self.assertEqual(invoice_checks.items, [])

    def test_released_data_is_filtered_to_current_subcontractor_and_visible_rows(self) -> None:
        service = SubcontractorPortalReadService(
            position_adapter=_PositionAdapter(),
            schedule_adapter=_ScheduleAdapter(),
            actual_summary_adapter=_ActualAdapter(),
            attendance_adapter=_AttendanceAdapter(),
            invoice_check_adapter=_InvoiceAdapter(),
        )
        context = _context()

        positions = service.list_positions(context)
        schedules = service.list_schedules(context)
        actuals = service.list_actual_summaries(context)
        attendance = service.list_attendance_visibility(context)
        invoice_checks = service.list_invoice_checks(context)

        self.assertEqual(positions.source.availability_status, "ready")
        self.assertEqual(len(positions.items), 1)
        self.assertEqual(positions.items[0].reference_no, "REL-100")
        self.assertEqual(len(schedules.items), 1)
        self.assertEqual(schedules.items[0].confirmation_status, "released")
        self.assertEqual(actuals.items[0].confirmed_minutes, 960)
        self.assertEqual(attendance.items[0].document_count, 1)
        self.assertEqual(invoice_checks.items[0].period_label, "KW 12 / 2026")


if __name__ == "__main__":
    unittest.main()
