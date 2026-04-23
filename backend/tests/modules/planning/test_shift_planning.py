from __future__ import annotations

import json
import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.iam.audit_service import AuditService
from app.modules.planning.models import Shift, ShiftPlan, ShiftSeries, ShiftSeriesException, ShiftTemplate
from app.modules.planning.schemas import (
    OpsMasterFilter,
    PlanningBoardFilter,
    ShiftCopyRequest,
    ShiftPlanCreate,
    ShiftPlanFilter,
    ShiftSeriesCreate,
    ShiftSeriesExceptionCreate,
    ShiftSeriesGenerationRequest,
    ShiftSeriesUpdate,
    ShiftTemplateCreate,
)
from app.modules.planning.shift_service import ShiftPlanningService
from tests.modules.planning.test_ops_master_foundation import RecordingAuditRepository, _context
from tests.modules.planning.test_planning_records import FakePlanningRecordRepository


@dataclass
class FakeShiftPlanningRepository(FakePlanningRecordRepository):
    tenant_settings: dict[tuple[str, str], object] = field(default_factory=dict)
    shift_templates: dict[str, ShiftTemplate] = field(default_factory=dict)
    shift_plans: dict[str, ShiftPlan] = field(default_factory=dict)
    shift_series_rows: dict[str, ShiftSeries] = field(default_factory=dict)
    shift_series_exceptions: dict[str, ShiftSeriesException] = field(default_factory=dict)
    shifts: dict[str, Shift] = field(default_factory=dict)

    @staticmethod
    def _stamp(row) -> None:  # noqa: ANN001
        now = datetime.now(UTC)
        if getattr(row, "id", None) is None:
            row.id = str(uuid4())
        if getattr(row, "created_at", None) is None:
            row.created_at = now
        row.updated_at = now
        row.version_no = getattr(row, "version_no", 0) or 1
        row.status = getattr(row, "status", None) or "active"

    def get_tenant_setting_json(self, tenant_id: str, key: str):
        return self.tenant_settings.get((tenant_id, key))

    def list_shift_templates(self, tenant_id: str, filters: OpsMasterFilter) -> list[ShiftTemplate]:
        rows = [row for row in self.shift_templates.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        return sorted(rows, key=lambda row: row.code)

    def get_shift_template(self, tenant_id: str, row_id: str) -> ShiftTemplate | None:
        row = self.shift_templates.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def find_shift_template_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> ShiftTemplate | None:
        for row in self.shift_templates.values():
            if row.tenant_id == tenant_id and row.code == code and row.id != exclude_id:
                return row
        return None

    def create_shift_template(self, tenant_id: str, payload, actor_user_id: str | None):
        row = ShiftTemplate(
            tenant_id=tenant_id,
            code=payload.code,
            label=payload.label,
            local_start_time=payload.local_start_time,
            local_end_time=payload.local_end_time,
            default_break_minutes=payload.default_break_minutes,
            shift_type_code=payload.shift_type_code,
            meeting_point=payload.meeting_point,
            location_text=payload.location_text,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.shift_templates[row.id] = row
        return row

    def update_shift_template(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_shift_template(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.shift_template.stale_version", "errors.planning.shift_template.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def list_shift_plans(self, tenant_id: str, filters: ShiftPlanFilter) -> list[ShiftPlan]:
        rows = [row for row in self.shift_plans.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.planning_record_id is not None:
            rows = [row for row in rows if row.planning_record_id == filters.planning_record_id]
        if filters.workforce_scope_code is not None:
            rows = [row for row in rows if row.workforce_scope_code == filters.workforce_scope_code]
        return sorted(rows, key=lambda row: (row.planning_from, row.name))

    def get_shift_plan(self, tenant_id: str, row_id: str) -> ShiftPlan | None:
        row = self.shift_plans.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        row.series_rows = self.list_shift_series(tenant_id, row.id)
        row.shifts = self.list_shifts(tenant_id, type("ShiftFilter", (), {"shift_plan_id": row.id, "planning_record_id": None, "date_from": None, "date_to": None, "shift_type_code": None, "release_state": None, "visibility_state": None, "lifecycle_status": None, "include_archived": True})())
        return row

    def find_shift_plan_by_name(self, tenant_id: str, planning_record_id: str, name: str, *, exclude_id: str | None = None) -> ShiftPlan | None:
        for row in self.shift_plans.values():
            if row.tenant_id == tenant_id and row.planning_record_id == planning_record_id and row.name == name and row.id != exclude_id:
                return row
        return None

    def create_shift_plan(self, tenant_id: str, payload, actor_user_id: str | None):
        row = ShiftPlan(
            tenant_id=tenant_id,
            planning_record_id=payload.planning_record_id,
            name=payload.name,
            workforce_scope_code=payload.workforce_scope_code,
            planning_from=payload.planning_from,
            planning_to=payload.planning_to,
            remarks=payload.remarks,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        row.series_rows = []
        row.shifts = []
        self.shift_plans[row.id] = row
        return row

    def update_shift_plan(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_shift_plan(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.shift_plan.stale_version", "errors.planning.shift_plan.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def save_shift_plan(self, row: ShiftPlan) -> ShiftPlan:
        self.shift_plans[row.id] = row
        return row

    def list_shift_series(self, tenant_id: str, shift_plan_id: str) -> list[ShiftSeries]:
        rows = [row for row in self.shift_series_rows.values() if row.tenant_id == tenant_id and row.shift_plan_id == shift_plan_id]
        for row in rows:
            row.exceptions = self.list_shift_series_exceptions(tenant_id, row.id)
        return sorted(rows, key=lambda row: (row.date_from, row.label))

    def get_shift_series(self, tenant_id: str, row_id: str) -> ShiftSeries | None:
        row = self.shift_series_rows.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        row.exceptions = self.list_shift_series_exceptions(tenant_id, row.id)
        row.shift_template = self.get_shift_template(tenant_id, row.shift_template_id)
        return row

    def create_shift_series(self, tenant_id: str, payload, actor_user_id: str | None):
        row = ShiftSeries(
            tenant_id=tenant_id,
            shift_plan_id=payload.shift_plan_id,
            shift_template_id=payload.shift_template_id,
            label=payload.label,
            recurrence_code=payload.recurrence_code,
            interval_count=payload.interval_count,
            weekday_mask=payload.weekday_mask,
            timezone=payload.timezone,
            date_from=payload.date_from,
            date_to=payload.date_to,
            default_break_minutes=payload.default_break_minutes,
            shift_type_code=payload.shift_type_code,
            meeting_point=payload.meeting_point,
            location_text=payload.location_text,
            customer_visible_flag=payload.customer_visible_flag,
            subcontractor_visible_flag=payload.subcontractor_visible_flag,
            stealth_mode_flag=payload.stealth_mode_flag,
            release_state=payload.release_state,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        row.exceptions = []
        self.shift_series_rows[row.id] = row
        return row

    def update_shift_series(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_shift_series(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.shift_series.stale_version", "errors.planning.shift_series.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def save_shift_series(self, row: ShiftSeries) -> ShiftSeries:
        self.shift_series_rows[row.id] = row
        return row

    def list_shift_series_exceptions(self, tenant_id: str, shift_series_id: str) -> list[ShiftSeriesException]:
        rows = [row for row in self.shift_series_exceptions.values() if row.tenant_id == tenant_id and row.shift_series_id == shift_series_id]
        return sorted(rows, key=lambda row: row.exception_date)

    def get_shift_series_exception(self, tenant_id: str, row_id: str) -> ShiftSeriesException | None:
        row = self.shift_series_exceptions.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def get_shift_series_exception_by_date(self, tenant_id: str, shift_series_id: str, exception_date: date) -> ShiftSeriesException | None:
        for row in self.shift_series_exceptions.values():
            if row.tenant_id == tenant_id and row.shift_series_id == shift_series_id and row.exception_date == exception_date:
                return row
        return None

    def create_shift_series_exception(self, tenant_id: str, shift_series_id: str, payload, actor_user_id: str | None):
        row = ShiftSeriesException(
            tenant_id=tenant_id,
            shift_series_id=shift_series_id,
            exception_date=payload.exception_date,
            action_code=payload.action_code,
            override_local_start_time=payload.override_local_start_time,
            override_local_end_time=payload.override_local_end_time,
            override_break_minutes=payload.override_break_minutes,
            override_shift_type_code=payload.override_shift_type_code,
            override_meeting_point=payload.override_meeting_point,
            override_location_text=payload.override_location_text,
            customer_visible_flag=payload.customer_visible_flag,
            subcontractor_visible_flag=payload.subcontractor_visible_flag,
            stealth_mode_flag=payload.stealth_mode_flag,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.shift_series_exceptions[row.id] = row
        return row

    def update_shift_series_exception(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_shift_series_exception(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.shift_series_exception.stale_version", "errors.planning.shift_series_exception.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def delete_shift_series_exception(self, tenant_id: str, row_id: str) -> bool:
        row = self.get_shift_series_exception(tenant_id, row_id)
        if row is None:
            return False
        del self.shift_series_exceptions[row.id]
        return True

    def list_shifts(self, tenant_id: str, filters) -> list[Shift]:
        rows = [row for row in self.shifts.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.shift_plan_id is not None:
            rows = [row for row in rows if row.shift_plan_id == filters.shift_plan_id]
        if filters.planning_record_id is not None:
            rows = [row for row in rows if self.shift_plans[row.shift_plan_id].planning_record_id == filters.planning_record_id]
        if filters.date_from is not None:
            boundary = datetime.combine(filters.date_from, time.min, tzinfo=UTC) if isinstance(filters.date_from, date) and not isinstance(filters.date_from, datetime) else filters.date_from
            rows = [row for row in rows if row.starts_at >= boundary]
        if filters.date_to is not None:
            boundary = datetime.combine(filters.date_to, time.min, tzinfo=UTC) if isinstance(filters.date_to, date) and not isinstance(filters.date_to, datetime) else filters.date_to
            rows = [row for row in rows if row.starts_at < boundary]
        return sorted(rows, key=lambda row: (row.starts_at, row.id))

    def get_shift(self, tenant_id: str, row_id: str) -> Shift | None:
        row = self.shifts.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def find_shift_duplicate(self, tenant_id: str, shift_plan_id: str, starts_at: datetime, ends_at: datetime, shift_type_code: str, *, exclude_id: str | None = None) -> Shift | None:
        for row in self.shifts.values():
            if row.id == exclude_id:
                continue
            if row.tenant_id == tenant_id and row.shift_plan_id == shift_plan_id and row.starts_at == starts_at and row.ends_at == ends_at and row.shift_type_code == shift_type_code and row.archived_at is None:
                return row
        return None

    def create_shift(self, tenant_id: str, payload, actor_user_id: str | None):
        row = Shift(
            tenant_id=tenant_id,
            shift_plan_id=payload.shift_plan_id,
            shift_series_id=payload.shift_series_id,
            occurrence_date=payload.occurrence_date,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            break_minutes=payload.break_minutes,
            shift_type_code=payload.shift_type_code,
            location_text=payload.location_text,
            meeting_point=payload.meeting_point,
            release_state=payload.release_state,
            released_at=None,
            released_by_user_id=None,
            customer_visible_flag=payload.customer_visible_flag,
            subcontractor_visible_flag=payload.subcontractor_visible_flag,
            stealth_mode_flag=payload.stealth_mode_flag,
            source_kind_code=payload.source_kind_code,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.shifts[row.id] = row
        return row

    def update_shift(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_shift(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.shift.stale_version", "errors.planning.shift.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def save_shift(self, row: Shift) -> Shift:
        self.shifts[row.id] = row
        return row

    def delete_shift_by_series_occurrence(self, tenant_id: str, shift_series_id: str, occurrence_date: date) -> None:
        for row_id, row in list(self.shifts.items()):
            if row.tenant_id == tenant_id and row.shift_series_id == shift_series_id and row.occurrence_date == occurrence_date:
                del self.shifts[row_id]

    def list_board_shifts(self, tenant_id: str, filters: PlanningBoardFilter) -> list[dict[str, object]]:
        rows = []
        for row in self.shifts.values():
            if row.tenant_id != tenant_id or row.archived_at is not None:
                continue
            if row.starts_at < filters.date_from or row.starts_at >= filters.date_to:
                continue
            shift_plan = self.shift_plans[row.shift_plan_id]
            planning_record = self.planning_records[shift_plan.planning_record_id]
            order = self.orders[planning_record.order_id]
            rows.append(
                {
                    "id": row.id,
                    "tenant_id": tenant_id,
                    "planning_record_id": planning_record.id,
                    "shift_plan_id": shift_plan.id,
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "planning_record_name": planning_record.name,
                    "planning_mode_code": planning_record.planning_mode_code,
                    "workforce_scope_code": shift_plan.workforce_scope_code,
                    "starts_at": row.starts_at,
                    "ends_at": row.ends_at,
                    "shift_type_code": row.shift_type_code,
                    "release_state": row.release_state,
                    "status": row.status,
                    "customer_visible_flag": row.customer_visible_flag,
                    "subcontractor_visible_flag": row.subcontractor_visible_flag,
                    "stealth_mode_flag": row.stealth_mode_flag,
                    "location_text": row.location_text,
                    "meeting_point": row.meeting_point,
                }
            )
        return rows


class ShiftPlanningServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeShiftPlanningRepository()
        self.audit_repository = RecordingAuditRepository()
        self.service = ShiftPlanningService(self.repository, audit_service=AuditService(self.audit_repository))
        requirement = self.repository.create_requirement_type(
            "tenant-1",
            type(
                "RequirementPayload",
                (),
                {
                    "customer_id": "customer-1",
                    "code": "REQ-SHIFT",
                    "label": "Shift",
                    "default_planning_mode_code": "site",
                    "description": None,
                },
            )(),
            "user-1",
        )
        site = SimpleNamespace(id="site-shift", tenant_id="tenant-1", customer_id="customer-1")
        self.repository.sites[site.id] = site
        order = self.repository.create_customer_order(
            "tenant-1",
            type(
                "OrderPayload",
                (),
                {
                    "customer_id": "customer-1",
                    "requirement_type_id": requirement.id,
                    "patrol_route_id": None,
                    "order_no": "ORD-SHIFT-1",
                    "title": "Shift Order",
                    "service_category_code": "object_security",
                    "security_concept_text": None,
                    "service_from": date(2026, 4, 1),
                    "service_to": date(2026, 4, 30),
                    "release_state": "draft",
                    "notes": None,
                },
            )(),
            "user-1",
        )
        planning_record = self.repository.create_planning_record(
            "tenant-1",
            type(
                "PlanningPayload",
                (),
                {
                    "order_id": order.id,
                    "parent_planning_record_id": None,
                    "dispatcher_user_id": "dispatcher-1",
                    "planning_mode_code": "site",
                    "name": "Shift Planning",
                    "planning_from": date(2026, 4, 1),
                    "planning_to": date(2026, 4, 30),
                    "release_state": "draft",
                    "notes": None,
                },
            )(),
            "user-1",
        )
        self.repository.create_site_plan_detail(
            "tenant-1",
            planning_record.id,
            type("SiteDetailPayload", (), {"site_id": site.id, "watchbook_scope_note": None})(),
        )
        self.template = self.service.create_shift_template(
            "tenant-1",
            ShiftTemplateCreate(
                tenant_id="tenant-1",
                code="TPL-DAY",
                label="Tagdienst",
                local_start_time=time(8, 0),
                local_end_time=time(16, 0),
                default_break_minutes=30,
                shift_type_code="site_day",
                meeting_point="Tor A",
                location_text="Berlin Mitte",
            ),
            _context("planning.shift.write"),
        )
        self.shift_plan = self.service.create_shift_plan(
            "tenant-1",
            ShiftPlanCreate(
                tenant_id="tenant-1",
                planning_record_id=planning_record.id,
                name="Grundplan",
                workforce_scope_code="mixed",
                planning_from=date(2026, 4, 1),
                planning_to=date(2026, 4, 30),
            ),
            _context("planning.shift.write"),
        )

    def test_generates_timezone_aware_daily_shifts(self) -> None:
        series = self.service.create_shift_series(
            "tenant-1",
            ShiftSeriesCreate(
                tenant_id="tenant-1",
                shift_plan_id=self.shift_plan.id,
                shift_template_id=self.template.id,
                label="April Tage",
                recurrence_code="daily",
                interval_count=1,
                timezone="Europe/Berlin",
                date_from=date(2026, 4, 1),
                date_to=date(2026, 4, 2),
                customer_visible_flag=True,
            ),
            _context("planning.shift.write"),
        )

        rows = self.service.generate_shift_series(
            "tenant-1",
            series.id,
            ShiftSeriesGenerationRequest(),
            _context("planning.shift.write"),
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].starts_at.tzinfo, UTC)
        self.assertTrue(rows[0].customer_visible_flag)
        self.assertEqual(rows[0].break_minutes, 30)

    def test_shift_type_options_fall_back_when_setting_missing(self) -> None:
        options = self.service.list_shift_type_options("tenant-1", _context("planning.shift.read"))

        self.assertEqual(options[0].code, "site_day")
        self.assertGreaterEqual(len(options), 7)

    def test_shift_type_options_use_tenant_setting_when_present(self) -> None:
        self.repository.tenant_settings[("tenant-1", self.service.SHIFT_TYPE_OPTIONS_KEY)] = [
            {"code": "custom_day", "label": "Custom Day"},
            {"code": "custom_night", "label": "Custom Night"},
        ]

        options = self.service.list_shift_type_options("tenant-1", _context("planning.shift.read"))

        self.assertEqual([option.code for option in options], ["custom_day", "custom_night"])

    def test_shift_type_options_fall_back_when_setting_is_invalid(self) -> None:
        self.repository.tenant_settings[("tenant-1", self.service.SHIFT_TYPE_OPTIONS_KEY)] = {"options": "invalid"}

        options = self.service.list_shift_type_options("tenant-1", _context("planning.shift.read"))

        self.assertEqual(options[0].code, "site_day")

    def test_shift_template_rejects_unknown_shift_type_code(self) -> None:
        with self.assertRaises(ApiException) as captured:
            self.service.create_shift_template(
                "tenant-1",
                ShiftTemplateCreate(
                    tenant_id="tenant-1",
                    code="TPL-BAD",
                    label="Bad",
                    local_start_time=time(8, 0),
                    local_end_time=time(16, 0),
                    default_break_minutes=30,
                    shift_type_code="unknown_code",
                ),
                _context("planning.shift.write"),
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.shift_template.invalid_shift_type_code")

    def test_shift_series_rejects_unknown_shift_type_code(self) -> None:
        with self.assertRaises(ApiException) as captured:
            self.service.create_shift_series(
                "tenant-1",
                ShiftSeriesCreate(
                    tenant_id="tenant-1",
                    shift_plan_id=self.shift_plan.id,
                    shift_template_id=self.template.id,
                    label="Bad series",
                    recurrence_code="daily",
                    interval_count=1,
                    timezone="Europe/Berlin",
                    date_from=date(2026, 4, 1),
                    date_to=date(2026, 4, 2),
                    shift_type_code="unknown_code",
                ),
                _context("planning.shift.write"),
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.shift_series.invalid_shift_type_code")

    def test_shift_series_update_can_replace_template_for_manual_time_adapter(self) -> None:
        night_template = self.service.create_shift_template(
            "tenant-1",
            ShiftTemplateCreate(
                tenant_id="tenant-1",
                code="TPL-NIGHT",
                label="Nachtdienst",
                local_start_time=time(18, 0),
                local_end_time=time(22, 0),
                default_break_minutes=15,
                shift_type_code="site_day",
            ),
            _context("planning.shift.write"),
        )
        series = self.service.create_shift_series(
            "tenant-1",
            ShiftSeriesCreate(
                tenant_id="tenant-1",
                shift_plan_id=self.shift_plan.id,
                shift_template_id=self.template.id,
                label="April Tage",
                recurrence_code="daily",
                interval_count=1,
                timezone="Europe/Berlin",
                date_from=date(2026, 4, 1),
                date_to=date(2026, 4, 1),
            ),
            _context("planning.shift.write"),
        )

        updated = self.service.update_shift_series(
            "tenant-1",
            series.id,
            ShiftSeriesUpdate(shift_template_id=night_template.id, default_break_minutes=15, version_no=series.version_no),
            _context("planning.shift.write"),
        )
        rows = self.service.generate_shift_series(
            "tenant-1",
            updated.id,
            ShiftSeriesGenerationRequest(regenerate_existing=True),
            _context("planning.shift.write"),
        )

        self.assertEqual(updated.shift_template_id, night_template.id)
        self.assertEqual(rows[0].starts_at.hour, 16)
        self.assertEqual(rows[0].ends_at.hour, 20)
        self.assertEqual(rows[0].break_minutes, 15)

    def test_shift_rejects_unknown_shift_type_code(self) -> None:
        with self.assertRaises(ApiException) as captured:
            self.service.create_shift(
                "tenant-1",
                type(
                    "Payload",
                    (),
                    {
                        "tenant_id": "tenant-1",
                        "shift_plan_id": self.shift_plan.id,
                        "shift_series_id": None,
                        "occurrence_date": date(2026, 4, 10),
                        "starts_at": datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
                        "ends_at": datetime(2026, 4, 10, 16, 0, tzinfo=UTC),
                        "break_minutes": 30,
                        "shift_type_code": "unknown_code",
                        "location_text": "Berlin",
                        "meeting_point": "Tor A",
                        "release_state": "draft",
                        "customer_visible_flag": False,
                        "subcontractor_visible_flag": False,
                        "stealth_mode_flag": False,
                        "source_kind_code": "manual",
                        "notes": None,
                    },
                )(),
                _context("planning.shift.write"),
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.shift.invalid_shift_type_code")

    def test_weekly_generation_respects_weekday_mask_and_skip_exception(self) -> None:
        series = self.service.create_shift_series(
            "tenant-1",
            ShiftSeriesCreate(
                tenant_id="tenant-1",
                shift_plan_id=self.shift_plan.id,
                shift_template_id=self.template.id,
                label="Mo Mi",
                recurrence_code="weekly",
                interval_count=1,
                weekday_mask="1010000",
                timezone="Europe/Berlin",
                date_from=date(2026, 4, 6),
                date_to=date(2026, 4, 12),
            ),
            _context("planning.shift.write"),
        )
        self.service.create_shift_series_exception(
            "tenant-1",
            series.id,
            ShiftSeriesExceptionCreate(
                tenant_id="tenant-1",
                exception_date=date(2026, 4, 8),
                action_code="skip",
            ),
            _context("planning.shift.write"),
        )

        rows = self.service.generate_shift_series(
            "tenant-1",
            series.id,
            ShiftSeriesGenerationRequest(),
            _context("planning.shift.write"),
        )

        self.assertEqual([row.occurrence_date for row in rows], [date(2026, 4, 6)])

    def test_delete_shift_series_exception_removes_only_exception_row(self) -> None:
        series = self.service.create_shift_series(
            "tenant-1",
            ShiftSeriesCreate(
                tenant_id="tenant-1",
                shift_plan_id=self.shift_plan.id,
                shift_template_id=self.template.id,
                label="April Tage",
                recurrence_code="daily",
                interval_count=1,
                timezone="Europe/Berlin",
                date_from=date(2026, 4, 1),
                date_to=date(2026, 4, 10),
            ),
            _context("planning.shift.write"),
        )
        deleted_exception = self.service.create_shift_series_exception(
            "tenant-1",
            series.id,
            ShiftSeriesExceptionCreate(
                tenant_id="tenant-1",
                exception_date=date(2026, 4, 3),
                action_code="skip",
            ),
            _context("planning.shift.write"),
        )
        kept_exception = self.service.create_shift_series_exception(
            "tenant-1",
            series.id,
            ShiftSeriesExceptionCreate(
                tenant_id="tenant-1",
                exception_date=date(2026, 4, 4),
                action_code="skip",
            ),
            _context("planning.shift.write"),
        )

        self.service.delete_shift_series_exception("tenant-1", deleted_exception.id, _context("planning.shift.write"))

        rows = self.service.list_shift_series_exceptions("tenant-1", series.id, _context("planning.shift.read"))
        self.assertEqual([row.id for row in rows], [kept_exception.id])
        self.assertIsNotNone(self.repository.get_shift_series("tenant-1", series.id))
        self.assertTrue(
            any(event.event_type == "planning.shift_series_exception.deleted" for event in self.audit_repository.audit_events),
        )

    def test_copy_slice_skips_existing_duplicates(self) -> None:
        self.service.create_shift(
            "tenant-1",
            type(
                "Payload",
                (),
                {
                    "tenant_id": "tenant-1",
                    "shift_plan_id": self.shift_plan.id,
                    "shift_series_id": None,
                    "occurrence_date": date(2026, 4, 2),
                    "starts_at": datetime(2026, 4, 2, 8, 0, tzinfo=UTC),
                    "ends_at": datetime(2026, 4, 2, 16, 0, tzinfo=UTC),
                    "break_minutes": 30,
                    "shift_type_code": "site_day",
                    "location_text": "Berlin",
                    "meeting_point": "Tor A",
                    "release_state": "draft",
                    "customer_visible_flag": False,
                    "subcontractor_visible_flag": False,
                    "stealth_mode_flag": False,
                    "source_kind_code": "manual",
                    "notes": None,
                },
            )(),
            _context("planning.shift.write"),
        )
        self.service.create_shift(
            "tenant-1",
            type(
                "Payload",
                (),
                {
                    "tenant_id": "tenant-1",
                    "shift_plan_id": self.shift_plan.id,
                    "shift_series_id": None,
                    "occurrence_date": date(2026, 4, 9),
                    "starts_at": datetime(2026, 4, 9, 8, 0, tzinfo=UTC),
                    "ends_at": datetime(2026, 4, 9, 16, 0, tzinfo=UTC),
                    "break_minutes": 30,
                    "shift_type_code": "site_day",
                    "location_text": "Berlin",
                    "meeting_point": "Tor A",
                    "release_state": "draft",
                    "customer_visible_flag": False,
                    "subcontractor_visible_flag": False,
                    "stealth_mode_flag": False,
                    "source_kind_code": "manual",
                    "notes": None,
                },
            )(),
            _context("planning.shift.write"),
        )

        result = self.service.copy_shift_slice(
            "tenant-1",
            self.shift_plan.id,
            ShiftCopyRequest(
                source_from=date(2026, 4, 2),
                source_to=date(2026, 4, 2),
                target_from=date(2026, 4, 9),
                duplicate_mode="skip_existing",
            ),
            _context("planning.shift.write"),
        )

        self.assertEqual(result.copied_count, 0)
        self.assertEqual(result.skipped_count, 1)

    def test_invalid_workforce_scope_is_rejected(self) -> None:
        with self.assertRaises(ApiException) as captured:
            self.service.create_shift_plan(
                "tenant-1",
                ShiftPlanCreate(
                    tenant_id="tenant-1",
                    planning_record_id=self.shift_plan.planning_record_id,
                    name="Bad scope",
                    workforce_scope_code="unknown",
                    planning_from=date(2026, 4, 1),
                    planning_to=date(2026, 4, 10),
                ),
                _context("planning.shift.write"),
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.shift_plan.invalid_workforce_scope")

    def test_shift_plan_create_writes_json_safe_audit_snapshot(self) -> None:
        audit_count_before = len(self.audit_repository.audit_events)

        row = self.service.create_shift_plan(
            "tenant-1",
            ShiftPlanCreate(
                tenant_id="tenant-1",
                planning_record_id=self.shift_plan.planning_record_id,
                name="Audit-safe plan",
                workforce_scope_code="internal",
                planning_from=date(2026, 4, 2),
                planning_to=date(2026, 4, 5),
            ),
            _context("planning.shift.write"),
        )

        self.assertEqual(row.name, "Audit-safe plan")
        self.assertEqual(len(self.audit_repository.audit_events), audit_count_before + 1)
        event = self.audit_repository.audit_events[-1]
        self.assertEqual(event.event_type, "planning.shift_plan.created")
        self.assertIsInstance(event.after_json["planning_from"], str)
        self.assertIsInstance(event.after_json["planning_to"], str)
        self.assertIsInstance(event.after_json["created_at"], str)
        self.assertEqual(event.after_json["planning_from"], "2026-04-02")
        self.assertEqual(event.after_json["planning_to"], "2026-04-05")
        json.dumps(event.after_json)

    def test_manual_shift_outside_shift_plan_window_is_rejected(self) -> None:
        with self.assertRaises(ApiException) as captured:
            self.service.create_shift(
                "tenant-1",
                type(
                    "Payload",
                    (),
                    {
                        "tenant_id": "tenant-1",
                        "shift_plan_id": self.shift_plan.id,
                        "shift_series_id": None,
                        "occurrence_date": date(2026, 5, 1),
                        "starts_at": datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
                        "ends_at": datetime(2026, 5, 1, 16, 0, tzinfo=UTC),
                        "break_minutes": 30,
                        "shift_type_code": "site_day",
                        "location_text": "Berlin",
                        "meeting_point": "Tor A",
                        "release_state": "draft",
                        "customer_visible_flag": False,
                        "subcontractor_visible_flag": False,
                        "stealth_mode_flag": False,
                        "source_kind_code": "manual",
                        "notes": None,
                    },
                )(),
                _context("planning.shift.write"),
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.shift.plan_window_mismatch")

    def test_shift_update_outside_shift_plan_window_is_rejected(self) -> None:
        shift = self.service.create_shift(
            "tenant-1",
            type(
                "Payload",
                (),
                {
                    "tenant_id": "tenant-1",
                    "shift_plan_id": self.shift_plan.id,
                    "shift_series_id": None,
                    "occurrence_date": date(2026, 4, 10),
                    "starts_at": datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
                    "ends_at": datetime(2026, 4, 10, 16, 0, tzinfo=UTC),
                    "break_minutes": 30,
                    "shift_type_code": "site_day",
                    "location_text": "Berlin",
                    "meeting_point": "Tor A",
                    "release_state": "draft",
                    "customer_visible_flag": False,
                    "subcontractor_visible_flag": False,
                    "stealth_mode_flag": False,
                    "source_kind_code": "manual",
                    "notes": None,
                },
            )(),
            _context("planning.shift.write"),
        )

        with self.assertRaises(ApiException) as captured:
            self.service.update_shift(
                "tenant-1",
                shift.id,
                type(
                    "Payload",
                    (),
                    {
                        "starts_at": datetime(2026, 5, 1, 8, 0, tzinfo=UTC),
                        "ends_at": datetime(2026, 5, 1, 16, 0, tzinfo=UTC),
                        "version_no": shift.version_no,
                        "model_dump": lambda self, **kwargs: {
                            "starts_at": self.starts_at,
                            "ends_at": self.ends_at,
                            "version_no": self.version_no,
                        },
                    },
                )(),
                _context("planning.shift.write"),
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.shift.plan_window_mismatch")

    def test_draft_shift_cannot_be_customer_visible(self) -> None:
        with self.assertRaises(ApiException) as captured:
            self.service.create_shift(
                "tenant-1",
                type(
                    "Payload",
                    (),
                    {
                        "tenant_id": "tenant-1",
                        "shift_plan_id": self.shift_plan.id,
                        "shift_series_id": None,
                        "occurrence_date": date(2026, 4, 10),
                        "starts_at": datetime(2026, 4, 10, 8, 0, tzinfo=UTC),
                        "ends_at": datetime(2026, 4, 10, 16, 0, tzinfo=UTC),
                        "break_minutes": 30,
                        "shift_type_code": "site_day",
                        "location_text": "Berlin",
                        "meeting_point": "Tor A",
                        "release_state": "draft",
                        "customer_visible_flag": True,
                        "subcontractor_visible_flag": False,
                        "stealth_mode_flag": False,
                        "source_kind_code": "manual",
                        "notes": None,
                    },
                )(),
                _context("planning.shift.write"),
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.shift.visibility_requires_release")

    def test_copy_slice_rejects_target_shift_outside_plan_window(self) -> None:
        self.service.create_shift(
            "tenant-1",
            type(
                "Payload",
                (),
                {
                    "tenant_id": "tenant-1",
                    "shift_plan_id": self.shift_plan.id,
                    "shift_series_id": None,
                    "occurrence_date": date(2026, 4, 30),
                    "starts_at": datetime(2026, 4, 30, 8, 0, tzinfo=UTC),
                    "ends_at": datetime(2026, 4, 30, 16, 0, tzinfo=UTC),
                    "break_minutes": 30,
                    "shift_type_code": "site_day",
                    "location_text": "Berlin",
                    "meeting_point": "Tor A",
                    "release_state": "draft",
                    "customer_visible_flag": False,
                    "subcontractor_visible_flag": False,
                    "stealth_mode_flag": False,
                    "source_kind_code": "manual",
                    "notes": None,
                },
            )(),
            _context("planning.shift.write"),
        )

        with self.assertRaises(ApiException) as captured:
            self.service.copy_shift_slice(
                "tenant-1",
                self.shift_plan.id,
                ShiftCopyRequest(
                    source_from=date(2026, 4, 30),
                    source_to=date(2026, 4, 30),
                    target_from=date(2026, 5, 1),
                    duplicate_mode="skip_existing",
                ),
                _context("planning.shift.write"),
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.shift.plan_window_mismatch")

    def test_board_projection_returns_minimal_shift_rows(self) -> None:
        self.service.create_shift(
            "tenant-1",
            type(
                "Payload",
                (),
                {
                    "tenant_id": "tenant-1",
                    "shift_plan_id": self.shift_plan.id,
                    "shift_series_id": None,
                    "occurrence_date": date(2026, 4, 3),
                    "starts_at": datetime(2026, 4, 3, 8, 0, tzinfo=UTC),
                    "ends_at": datetime(2026, 4, 3, 16, 0, tzinfo=UTC),
                    "break_minutes": 30,
                    "shift_type_code": "site_day",
                    "location_text": "Berlin",
                    "meeting_point": "Tor A",
                    "release_state": "release_ready",
                    "customer_visible_flag": False,
                    "subcontractor_visible_flag": False,
                    "stealth_mode_flag": False,
                    "source_kind_code": "manual",
                    "notes": None,
                },
            )(),
            _context("planning.shift.write"),
        )

        rows = self.service.list_board_shifts(
            "tenant-1",
            PlanningBoardFilter(
                date_from=datetime(2026, 4, 3, 0, 0, tzinfo=UTC),
                date_to=datetime(2026, 4, 4, 0, 0, tzinfo=UTC),
                release_state="release_ready",
            ),
            _context("planning.shift.read"),
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].workforce_scope_code, "mixed")
        self.assertEqual(rows[0].release_state, "release_ready")
