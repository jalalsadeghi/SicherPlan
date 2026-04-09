"""Service layer for planning shift plans, templates, series, exceptions, and concrete shifts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.errors import ApiException
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.models import PlanningRecord, Shift, ShiftPlan, ShiftSeries, ShiftSeriesException, ShiftTemplate
from app.modules.planning.validation_service import PlanningValidationService
from app.modules.planning.schemas import (
    OpsMasterFilter,
    PlanningBoardFilter,
    PlanningBoardShiftListItem,
    ShiftCopyRequest,
    ShiftCopyResult,
    ShiftCreate,
    ShiftListFilter,
    ShiftListItem,
    ShiftPlanCreate,
    ShiftPlanFilter,
    ShiftPlanListItem,
    ShiftPlanRead,
    ShiftPlanUpdate,
    ShiftRead,
    ShiftReleaseDiagnosticsRead,
    ShiftReleaseStateUpdate,
    ShiftSeriesCreate,
    ShiftSeriesExceptionCreate,
    ShiftSeriesExceptionRead,
    ShiftSeriesExceptionUpdate,
    ShiftSeriesGenerationRequest,
    ShiftSeriesListItem,
    ShiftSeriesRead,
    ShiftSeriesUpdate,
    ShiftTemplateCreate,
    ShiftTemplateListItem,
    ShiftTemplateRead,
    ShiftTemplateUpdate,
    ShiftUpdate,
    ShiftVisibilityUpdate,
)


class ShiftPlanningRepository(Protocol):
    def get_planning_record(self, tenant_id: str, planning_record_id: str) -> PlanningRecord | None: ...
    def list_shift_templates(self, tenant_id: str, filters: OpsMasterFilter) -> list[ShiftTemplate]: ...
    def get_shift_template(self, tenant_id: str, row_id: str) -> ShiftTemplate | None: ...
    def find_shift_template_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> ShiftTemplate | None: ...
    def create_shift_template(self, tenant_id: str, payload: ShiftTemplateCreate, actor_user_id: str | None) -> ShiftTemplate: ...
    def update_shift_template(self, tenant_id: str, row_id: str, payload: ShiftTemplateUpdate, actor_user_id: str | None) -> ShiftTemplate | None: ...
    def list_shift_plans(self, tenant_id: str, filters: ShiftPlanFilter) -> list[ShiftPlan]: ...
    def get_shift_plan(self, tenant_id: str, row_id: str) -> ShiftPlan | None: ...
    def find_shift_plan_by_name(self, tenant_id: str, planning_record_id: str, name: str, *, exclude_id: str | None = None) -> ShiftPlan | None: ...
    def create_shift_plan(self, tenant_id: str, payload: ShiftPlanCreate, actor_user_id: str | None) -> ShiftPlan: ...
    def update_shift_plan(self, tenant_id: str, row_id: str, payload: ShiftPlanUpdate, actor_user_id: str | None) -> ShiftPlan | None: ...
    def save_shift_plan(self, row: ShiftPlan) -> ShiftPlan: ...
    def list_shift_series(self, tenant_id: str, shift_plan_id: str) -> list[ShiftSeries]: ...
    def get_shift_series(self, tenant_id: str, row_id: str) -> ShiftSeries | None: ...
    def create_shift_series(self, tenant_id: str, payload: ShiftSeriesCreate, actor_user_id: str | None) -> ShiftSeries: ...
    def update_shift_series(self, tenant_id: str, row_id: str, payload: ShiftSeriesUpdate, actor_user_id: str | None) -> ShiftSeries | None: ...
    def save_shift_series(self, row: ShiftSeries) -> ShiftSeries: ...
    def list_shift_series_exceptions(self, tenant_id: str, shift_series_id: str) -> list[ShiftSeriesException]: ...
    def get_shift_series_exception(self, tenant_id: str, row_id: str) -> ShiftSeriesException | None: ...
    def get_shift_series_exception_by_date(self, tenant_id: str, shift_series_id: str, exception_date: date) -> ShiftSeriesException | None: ...
    def create_shift_series_exception(self, tenant_id: str, shift_series_id: str, payload: ShiftSeriesExceptionCreate, actor_user_id: str | None) -> ShiftSeriesException: ...
    def update_shift_series_exception(self, tenant_id: str, row_id: str, payload: ShiftSeriesExceptionUpdate, actor_user_id: str | None) -> ShiftSeriesException | None: ...
    def list_shifts(self, tenant_id: str, filters: ShiftListFilter) -> list[Shift]: ...
    def get_shift(self, tenant_id: str, row_id: str) -> Shift | None: ...
    def find_shift_duplicate(self, tenant_id: str, shift_plan_id: str, starts_at: datetime, ends_at: datetime, shift_type_code: str, *, exclude_id: str | None = None) -> Shift | None: ...
    def create_shift(self, tenant_id: str, payload: ShiftCreate, actor_user_id: str | None) -> Shift: ...
    def update_shift(self, tenant_id: str, row_id: str, payload: ShiftUpdate, actor_user_id: str | None) -> Shift | None: ...
    def save_shift(self, row: Shift) -> Shift: ...
    def delete_shift(self, tenant_id: str, row_id: str) -> None: ...
    def delete_shift_by_series_occurrence(self, tenant_id: str, shift_series_id: str, occurrence_date: date) -> None: ...
    def list_board_shifts(self, tenant_id: str, filters: PlanningBoardFilter) -> list[dict[str, object]]: ...
    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[object]: ...
    def list_subcontractor_releases_for_shift(self, tenant_id: str, shift_id: str) -> list[object]: ...


@dataclass(frozen=True)
class _OccurrenceValues:
    occurrence_date: date
    starts_at: datetime
    ends_at: datetime
    break_minutes: int
    shift_type_code: str
    meeting_point: str | None
    location_text: str | None
    customer_visible_flag: bool
    subcontractor_visible_flag: bool
    stealth_mode_flag: bool


class ShiftPlanningService:
    WORKFORCE_SCOPES = frozenset({"internal", "subcontractor", "mixed"})
    RELEASE_STATES = frozenset({"draft", "release_ready", "released"})
    SERIES_RECURRENCE_CODES = frozenset({"daily", "weekly"})
    SERIES_EXCEPTION_ACTIONS = frozenset({"skip", "override"})
    COPY_DUPLICATE_MODES = frozenset({"skip_existing", "fail"})
    VISIBILITY_STATES = frozenset({"customer", "subcontractor", "stealth"})

    def __init__(
        self,
        repository: ShiftPlanningRepository,
        *,
        validation_service: PlanningValidationService | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.validation_service = validation_service
        self.audit_service = audit_service

    def list_shift_templates(
        self,
        tenant_id: str,
        filters: OpsMasterFilter,
        _actor: RequestAuthorizationContext,
    ) -> list[ShiftTemplateListItem]:
        return [ShiftTemplateListItem.model_validate(row) for row in self.repository.list_shift_templates(tenant_id, filters)]

    def get_shift_template(self, tenant_id: str, template_id: str, _actor: RequestAuthorizationContext) -> ShiftTemplateRead:
        return ShiftTemplateRead.model_validate(self._require_template(tenant_id, template_id))

    def create_shift_template(self, tenant_id: str, payload: ShiftTemplateCreate, actor: RequestAuthorizationContext) -> ShiftTemplateRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        self._validate_template_times(payload.local_start_time, payload.local_end_time)
        if self.repository.find_shift_template_by_code(tenant_id, payload.code) is not None:
            raise ApiException(409, "planning.shift_template.duplicate_code", "errors.planning.shift_template.duplicate_code")
        row = self.repository.create_shift_template(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.shift_template.created", "ops.shift_template", row.id, tenant_id, after_json=self._snapshot(row))
        return ShiftTemplateRead.model_validate(row)

    def update_shift_template(
        self,
        tenant_id: str,
        template_id: str,
        payload: ShiftTemplateUpdate,
        actor: RequestAuthorizationContext,
    ) -> ShiftTemplateRead:
        current = self._require_template(tenant_id, template_id)
        before_json = self._snapshot(current)
        next_code = self._field_value(payload, "code", current.code)
        next_start = self._field_value(payload, "local_start_time", current.local_start_time)
        next_end = self._field_value(payload, "local_end_time", current.local_end_time)
        self._validate_template_times(next_start, next_end)
        if self.repository.find_shift_template_by_code(tenant_id, next_code, exclude_id=template_id) is not None:
            raise ApiException(409, "planning.shift_template.duplicate_code", "errors.planning.shift_template.duplicate_code")
        row = self.repository.update_shift_template(tenant_id, template_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("shift_template")
        self._record_event(actor, "planning.shift_template.updated", "ops.shift_template", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return ShiftTemplateRead.model_validate(row)

    def list_shift_plans(
        self,
        tenant_id: str,
        filters: ShiftPlanFilter,
        _actor: RequestAuthorizationContext,
    ) -> list[ShiftPlanListItem]:
        return [ShiftPlanListItem.model_validate(row) for row in self.repository.list_shift_plans(tenant_id, filters)]

    def get_shift_plan(self, tenant_id: str, shift_plan_id: str, _actor: RequestAuthorizationContext) -> ShiftPlanRead:
        return self._read_shift_plan(self._require_shift_plan(tenant_id, shift_plan_id))

    def create_shift_plan(self, tenant_id: str, payload: ShiftPlanCreate, actor: RequestAuthorizationContext) -> ShiftPlanRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        planning_record = self._require_planning_record(tenant_id, payload.planning_record_id)
        self._validate_shift_plan_payload(planning_record, payload.workforce_scope_code, payload.planning_from, payload.planning_to)
        if self.repository.find_shift_plan_by_name(tenant_id, payload.planning_record_id, payload.name) is not None:
            raise ApiException(409, "planning.shift_plan.duplicate_name", "errors.planning.shift_plan.duplicate_name")
        row = self.repository.create_shift_plan(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.shift_plan.created", "ops.shift_plan", row.id, tenant_id, after_json=self._snapshot(row))
        return self._read_shift_plan(self._require_shift_plan(tenant_id, row.id))

    def update_shift_plan(self, tenant_id: str, shift_plan_id: str, payload: ShiftPlanUpdate, actor: RequestAuthorizationContext) -> ShiftPlanRead:
        current = self._require_shift_plan(tenant_id, shift_plan_id)
        planning_record = self._require_planning_record(tenant_id, current.planning_record_id)
        before_json = self._snapshot(current)
        next_name = self._field_value(payload, "name", current.name)
        next_scope = self._field_value(payload, "workforce_scope_code", current.workforce_scope_code)
        next_from = self._field_value(payload, "planning_from", current.planning_from)
        next_to = self._field_value(payload, "planning_to", current.planning_to)
        self._validate_shift_plan_payload(planning_record, next_scope, next_from, next_to)
        if self.repository.find_shift_plan_by_name(tenant_id, current.planning_record_id, next_name, exclude_id=shift_plan_id) is not None:
            raise ApiException(409, "planning.shift_plan.duplicate_name", "errors.planning.shift_plan.duplicate_name")
        row = self.repository.update_shift_plan(tenant_id, shift_plan_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("shift_plan")
        self._record_event(actor, "planning.shift_plan.updated", "ops.shift_plan", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return self._read_shift_plan(self._require_shift_plan(tenant_id, shift_plan_id))

    def list_shift_series(self, tenant_id: str, shift_plan_id: str, _actor: RequestAuthorizationContext) -> list[ShiftSeriesListItem]:
        self._require_shift_plan(tenant_id, shift_plan_id)
        return [ShiftSeriesListItem.model_validate(row) for row in self.repository.list_shift_series(tenant_id, shift_plan_id)]

    def get_shift_series(self, tenant_id: str, shift_series_id: str, _actor: RequestAuthorizationContext) -> ShiftSeriesRead:
        return self._read_shift_series(self._require_shift_series(tenant_id, shift_series_id))

    def create_shift_series(self, tenant_id: str, payload: ShiftSeriesCreate, actor: RequestAuthorizationContext) -> ShiftSeriesRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        shift_plan = self._require_shift_plan(tenant_id, payload.shift_plan_id)
        self._require_template(tenant_id, payload.shift_template_id)
        self._validate_shift_series_payload(shift_plan, payload)
        row = self.repository.create_shift_series(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.shift_series.created", "ops.shift_series", row.id, tenant_id, after_json=self._snapshot(row))
        return self._read_shift_series(self._require_shift_series(tenant_id, row.id))

    def update_shift_series(self, tenant_id: str, shift_series_id: str, payload: ShiftSeriesUpdate, actor: RequestAuthorizationContext) -> ShiftSeriesRead:
        current = self._require_shift_series(tenant_id, shift_series_id)
        shift_plan = self._require_shift_plan(tenant_id, current.shift_plan_id)
        if "shift_template_id" in payload.model_dump(exclude_unset=True):
            raise ApiException(400, "planning.shift_series.template_change_not_allowed", "errors.planning.shift_series.template_change_not_allowed")
        before_json = self._snapshot(current)
        candidate = ShiftSeriesCreate(
            tenant_id=tenant_id,
            shift_plan_id=current.shift_plan_id,
            shift_template_id=current.shift_template_id,
            label=self._field_value(payload, "label", current.label),
            recurrence_code=self._field_value(payload, "recurrence_code", current.recurrence_code),
            interval_count=self._field_value(payload, "interval_count", current.interval_count),
            weekday_mask=self._field_value(payload, "weekday_mask", current.weekday_mask),
            timezone=self._field_value(payload, "timezone", current.timezone),
            date_from=self._field_value(payload, "date_from", current.date_from),
            date_to=self._field_value(payload, "date_to", current.date_to),
            default_break_minutes=self._field_value(payload, "default_break_minutes", current.default_break_minutes),
            shift_type_code=self._field_value(payload, "shift_type_code", current.shift_type_code),
            meeting_point=self._field_value(payload, "meeting_point", current.meeting_point),
            location_text=self._field_value(payload, "location_text", current.location_text),
            customer_visible_flag=self._field_value(payload, "customer_visible_flag", current.customer_visible_flag),
            subcontractor_visible_flag=self._field_value(payload, "subcontractor_visible_flag", current.subcontractor_visible_flag),
            stealth_mode_flag=self._field_value(payload, "stealth_mode_flag", current.stealth_mode_flag),
            release_state=self._field_value(payload, "release_state", current.release_state),
            notes=self._field_value(payload, "notes", current.notes),
        )
        self._validate_shift_series_payload(shift_plan, candidate)
        row = self.repository.update_shift_series(tenant_id, shift_series_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("shift_series")
        self._record_event(actor, "planning.shift_series.updated", "ops.shift_series", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return self._read_shift_series(self._require_shift_series(tenant_id, shift_series_id))

    def generate_shift_series(
        self,
        tenant_id: str,
        shift_series_id: str,
        payload: ShiftSeriesGenerationRequest,
        actor: RequestAuthorizationContext,
    ) -> list[ShiftRead]:
        series = self._require_shift_series(tenant_id, shift_series_id)
        shift_plan = self._require_shift_plan(tenant_id, series.shift_plan_id)
        template = self._require_template(tenant_id, series.shift_template_id)
        generation_from = max(payload.from_date or series.date_from, series.date_from)
        generation_to = min(payload.to_date or series.date_to, series.date_to)
        if generation_to < generation_from:
            raise ApiException(400, "planning.shift_series.invalid_generation_window", "errors.planning.shift_series.invalid_generation_window")
        rows: list[ShiftRead] = []
        for occurrence_date in self._occurrence_dates(series, generation_from, generation_to):
            exception = self.repository.get_shift_series_exception_by_date(tenant_id, series.id, occurrence_date)
            if exception is not None and exception.action_code == "skip":
                continue
            occurrence = self._resolve_occurrence(series, template, exception, occurrence_date)
            self.repository.delete_shift_by_series_occurrence(tenant_id, series.id, occurrence_date) if payload.regenerate_existing else None
            duplicate = self.repository.find_shift_duplicate(
                tenant_id,
                shift_plan.id,
                occurrence.starts_at,
                occurrence.ends_at,
                occurrence.shift_type_code,
            )
            if duplicate is not None and duplicate.shift_series_id == series.id and duplicate.occurrence_date == occurrence_date:
                rows.append(ShiftRead.model_validate(duplicate))
                continue
            if duplicate is not None and not payload.regenerate_existing:
                continue
            created = self.repository.create_shift(
                tenant_id,
                ShiftCreate(
                    tenant_id=tenant_id,
                    shift_plan_id=shift_plan.id,
                    shift_series_id=series.id,
                    occurrence_date=occurrence.occurrence_date,
                    starts_at=occurrence.starts_at,
                    ends_at=occurrence.ends_at,
                    break_minutes=occurrence.break_minutes,
                    shift_type_code=occurrence.shift_type_code,
                    location_text=occurrence.location_text,
                    meeting_point=occurrence.meeting_point,
                    release_state=series.release_state,
                    customer_visible_flag=occurrence.customer_visible_flag,
                    subcontractor_visible_flag=occurrence.subcontractor_visible_flag,
                    stealth_mode_flag=occurrence.stealth_mode_flag,
                    source_kind_code="generated",
                ),
                actor.user_id,
            )
            self._record_event(
                actor,
                "planning.shift.generated",
                "ops.shift",
                created.id,
                tenant_id,
                metadata_json={"shift_series_id": series.id, "occurrence_date": occurrence_date.isoformat()},
            )
            rows.append(ShiftRead.model_validate(created))
        return rows

    def list_shift_series_exceptions(self, tenant_id: str, shift_series_id: str, _actor: RequestAuthorizationContext) -> list[ShiftSeriesExceptionRead]:
        self._require_shift_series(tenant_id, shift_series_id)
        return [ShiftSeriesExceptionRead.model_validate(row) for row in self.repository.list_shift_series_exceptions(tenant_id, shift_series_id)]

    def create_shift_series_exception(
        self,
        tenant_id: str,
        shift_series_id: str,
        payload: ShiftSeriesExceptionCreate,
        actor: RequestAuthorizationContext,
    ) -> ShiftSeriesExceptionRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        series = self._require_shift_series(tenant_id, shift_series_id)
        self._validate_exception(series, payload.action_code, payload.exception_date, payload.override_local_start_time, payload.override_local_end_time)
        if self.repository.get_shift_series_exception_by_date(tenant_id, shift_series_id, payload.exception_date) is not None:
            raise ApiException(409, "planning.shift_series_exception.duplicate_date", "errors.planning.shift_series_exception.duplicate_date")
        row = self.repository.create_shift_series_exception(tenant_id, shift_series_id, payload, actor.user_id)
        self._record_event(actor, "planning.shift_series_exception.created", "ops.shift_series_exception", row.id, tenant_id, after_json=self._snapshot(row))
        return ShiftSeriesExceptionRead.model_validate(row)

    def update_shift_series_exception(
        self,
        tenant_id: str,
        row_id: str,
        payload: ShiftSeriesExceptionUpdate,
        actor: RequestAuthorizationContext,
    ) -> ShiftSeriesExceptionRead:
        current = self._require_shift_series_exception(tenant_id, row_id)
        series = self._require_shift_series(tenant_id, current.shift_series_id)
        before_json = self._snapshot(current)
        next_action = self._field_value(payload, "action_code", current.action_code)
        next_start = self._field_value(payload, "override_local_start_time", current.override_local_start_time)
        next_end = self._field_value(payload, "override_local_end_time", current.override_local_end_time)
        self._validate_exception(series, next_action, current.exception_date, next_start, next_end)
        row = self.repository.update_shift_series_exception(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("shift_series_exception")
        self._record_event(actor, "planning.shift_series_exception.updated", "ops.shift_series_exception", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return ShiftSeriesExceptionRead.model_validate(row)

    def list_shifts(self, tenant_id: str, filters: ShiftListFilter, _actor: RequestAuthorizationContext) -> list[ShiftListItem]:
        return [ShiftListItem.model_validate(row) for row in self.repository.list_shifts(tenant_id, filters)]

    def get_shift(self, tenant_id: str, shift_id: str, _actor: RequestAuthorizationContext) -> ShiftRead:
        return ShiftRead.model_validate(self._require_shift(tenant_id, shift_id))

    def get_shift_release_diagnostics(
        self,
        tenant_id: str,
        shift_id: str,
        _actor: RequestAuthorizationContext,
    ) -> ShiftReleaseDiagnosticsRead:
        shift = self._require_shift(tenant_id, shift_id)
        validations = self.validation_service.validate_shift_release(tenant_id, shift_id) if self.validation_service is not None else None
        return ShiftReleaseDiagnosticsRead(
            tenant_id=tenant_id,
            shift_id=shift_id,
            release_state=shift.release_state,
            customer_visible_flag=shift.customer_visible_flag,
            subcontractor_visible_flag=shift.subcontractor_visible_flag,
            employee_visible=shift.release_state == "released",
            blocking_count=validations.blocking_count if validations is not None else 0,
            warning_count=validations.warning_count if validations is not None else 0,
            issues=validations.issues if validations is not None else [],
        )

    def set_shift_release_state(
        self,
        tenant_id: str,
        shift_id: str,
        payload: ShiftReleaseStateUpdate,
        actor: RequestAuthorizationContext,
    ) -> ShiftRead:
        shift = self._require_shift(tenant_id, shift_id)
        before_json = self._snapshot(shift)
        self._require_release_state(payload.release_state, "shift")
        if payload.version_no is not None and payload.version_no != shift.version_no:
            raise ApiException(409, "planning.shift.stale_version", "errors.planning.shift.stale_version")
        self._enforce_release_transition(shift.release_state, payload.release_state)
        if payload.release_state == "released":
            self._assert_release_allowed(tenant_id, shift_id)
        shift.release_state = payload.release_state
        if payload.release_state == "released":
            shift.released_at = datetime.now(UTC)
            shift.released_by_user_id = actor.user_id
        else:
            shift.released_at = None
            shift.released_by_user_id = None
            shift.customer_visible_flag = False
            shift.subcontractor_visible_flag = False
        shift.updated_by_user_id = actor.user_id
        shift.version_no += 1
        row = self.repository.save_shift(shift)
        self._record_event(
            actor,
            "planning.shift.release_state.changed",
            "ops.shift",
            row.id,
            tenant_id,
            before_json=before_json,
            after_json=self._snapshot(row),
        )
        return ShiftRead.model_validate(row)

    def update_shift_visibility(
        self,
        tenant_id: str,
        shift_id: str,
        payload: ShiftVisibilityUpdate,
        actor: RequestAuthorizationContext,
    ) -> ShiftRead:
        shift = self._require_shift(tenant_id, shift_id)
        before_json = self._snapshot(shift)
        if payload.version_no is not None and payload.version_no != shift.version_no:
            raise ApiException(409, "planning.shift.stale_version", "errors.planning.shift.stale_version")
        next_customer_visible = self._field_value(payload, "customer_visible_flag", shift.customer_visible_flag)
        next_subcontractor_visible = self._field_value(payload, "subcontractor_visible_flag", shift.subcontractor_visible_flag)
        if (next_customer_visible or next_subcontractor_visible) and shift.release_state != "released":
            raise ApiException(
                409,
                "planning.shift.visibility_requires_release",
                "errors.planning.shift.visibility_requires_release",
            )
        if next_customer_visible or next_subcontractor_visible:
            self._assert_release_allowed(tenant_id, shift_id)
        shift.customer_visible_flag = next_customer_visible
        shift.subcontractor_visible_flag = next_subcontractor_visible
        shift.updated_by_user_id = actor.user_id
        shift.version_no += 1
        row = self.repository.save_shift(shift)
        self._record_event(
            actor,
            "planning.shift.visibility.changed",
            "ops.shift",
            row.id,
            tenant_id,
            before_json=before_json,
            after_json=self._snapshot(row),
        )
        return ShiftRead.model_validate(row)

    def create_shift(self, tenant_id: str, payload: ShiftCreate, actor: RequestAuthorizationContext) -> ShiftRead:
        self._require_tenant_scope(tenant_id, payload.tenant_id)
        shift_plan = self._require_shift_plan(tenant_id, payload.shift_plan_id)
        planning_record = self._require_planning_record(tenant_id, shift_plan.planning_record_id)
        self._validate_shift_payload(
            payload.starts_at,
            payload.ends_at,
            payload.break_minutes,
            payload.release_state,
            payload.customer_visible_flag,
            payload.subcontractor_visible_flag,
        )
        self._validate_shift_window(shift_plan, planning_record, payload.starts_at, payload.ends_at)
        duplicate = self.repository.find_shift_duplicate(
            tenant_id,
            payload.shift_plan_id,
            payload.starts_at,
            payload.ends_at,
            payload.shift_type_code,
        )
        if duplicate is not None:
            raise ApiException(409, "planning.shift.duplicate_window", "errors.planning.shift.duplicate_window")
        row = self.repository.create_shift(tenant_id, payload, actor.user_id)
        if payload.release_state in {"release_ready", "released"} and self.validation_service is not None:
            validations = self.validation_service.validate_shift_release(tenant_id, row.id)
            if validations.blocking_count:
                self.repository.delete_shift(tenant_id, row.id)
                raise ApiException(
                    409,
                    "planning.shift.blocked_by_validation",
                    "errors.planning.shift.blocked_by_validation",
                    {"issues": [issue.model_dump() for issue in validations.issues]},
                )
        self._record_event(actor, "planning.shift.created", "ops.shift", row.id, tenant_id, after_json=self._snapshot(row))
        return ShiftRead.model_validate(row)

    def update_shift(self, tenant_id: str, shift_id: str, payload: ShiftUpdate, actor: RequestAuthorizationContext) -> ShiftRead:
        current = self._require_shift(tenant_id, shift_id)
        shift_plan = self._require_shift_plan(tenant_id, current.shift_plan_id)
        planning_record = self._require_planning_record(tenant_id, shift_plan.planning_record_id)
        before_json = self._snapshot(current)
        next_starts_at = self._field_value(payload, "starts_at", current.starts_at)
        next_ends_at = self._field_value(payload, "ends_at", current.ends_at)
        next_break = self._field_value(payload, "break_minutes", current.break_minutes)
        next_release = self._field_value(payload, "release_state", current.release_state)
        next_type = self._field_value(payload, "shift_type_code", current.shift_type_code)
        next_customer_visible = self._field_value(payload, "customer_visible_flag", current.customer_visible_flag)
        next_subcontractor_visible = self._field_value(payload, "subcontractor_visible_flag", current.subcontractor_visible_flag)
        self._validate_shift_payload(
            next_starts_at,
            next_ends_at,
            next_break,
            next_release,
            next_customer_visible,
            next_subcontractor_visible,
        )
        self._validate_shift_window(shift_plan, planning_record, next_starts_at, next_ends_at)
        duplicate = self.repository.find_shift_duplicate(
            tenant_id,
            current.shift_plan_id,
            next_starts_at,
            next_ends_at,
            next_type,
            exclude_id=shift_id,
        )
        if duplicate is not None:
            raise ApiException(409, "planning.shift.duplicate_window", "errors.planning.shift.duplicate_window")
        if next_release in {"release_ready", "released"} and self.validation_service is not None:
            validations = self.validation_service.validate_shift_release(tenant_id, shift_id)
            if validations.blocking_count:
                raise ApiException(
                    409,
                    "planning.shift.blocked_by_validation",
                    "errors.planning.shift.blocked_by_validation",
                    {"issues": [issue.model_dump() for issue in validations.issues]},
                )
        row = self.repository.update_shift(tenant_id, shift_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("shift")
        self._record_event(actor, "planning.shift.updated", "ops.shift", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return ShiftRead.model_validate(row)

    def copy_shift_slice(self, tenant_id: str, shift_plan_id: str, payload: ShiftCopyRequest, actor: RequestAuthorizationContext) -> ShiftCopyResult:
        shift_plan = self._require_shift_plan(tenant_id, shift_plan_id)
        planning_record = self._require_planning_record(tenant_id, shift_plan.planning_record_id)
        if payload.duplicate_mode not in self.COPY_DUPLICATE_MODES:
            raise ApiException(400, "planning.shift.copy.invalid_duplicate_mode", "errors.planning.shift.copy.invalid_duplicate_mode")
        if payload.source_to < payload.source_from:
            raise ApiException(400, "planning.shift.copy.invalid_source_window", "errors.planning.shift.copy.invalid_source_window")
        delta_days = (payload.target_from - payload.source_from).days
        source_filters = ShiftListFilter(
            shift_plan_id=shift_plan_id,
            date_from=payload.source_from,
            date_to=payload.source_to + timedelta(days=1),
            include_archived=False,
        )
        source_rows = self.repository.list_shifts(tenant_id, source_filters)
        copied_count = 0
        skipped_count = 0
        for source_row in source_rows:
            if source_row.source_kind_code == "generated" and not payload.include_generated:
                continue
            if source_row.source_kind_code != "generated" and not payload.include_manual:
                continue
            target_start = source_row.starts_at + timedelta(days=delta_days)
            target_end = source_row.ends_at + timedelta(days=delta_days)
            self._validate_shift_window(shift_plan, planning_record, target_start, target_end)
            duplicate = self.repository.find_shift_duplicate(
                tenant_id,
                shift_plan_id,
                target_start,
                target_end,
                source_row.shift_type_code,
            )
            if duplicate is not None:
                if payload.duplicate_mode == "fail":
                    raise ApiException(409, "planning.shift.copy.duplicate_conflict", "errors.planning.shift.copy.duplicate_conflict")
                skipped_count += 1
                continue
            self.repository.create_shift(
                tenant_id,
                ShiftCreate(
                    tenant_id=tenant_id,
                    shift_plan_id=shift_plan_id,
                    shift_series_id=None,
                    occurrence_date=target_start.date(),
                    starts_at=target_start,
                    ends_at=target_end,
                    break_minutes=source_row.break_minutes,
                    shift_type_code=source_row.shift_type_code,
                    location_text=source_row.location_text,
                    meeting_point=source_row.meeting_point,
                    release_state="draft",
                    customer_visible_flag=False,
                    subcontractor_visible_flag=False,
                    stealth_mode_flag=source_row.stealth_mode_flag,
                    source_kind_code="copied",
                    notes=source_row.notes if hasattr(source_row, "notes") else None,
                ),
                actor.user_id,
            )
            copied_count += 1
        self._record_event(
            actor,
            "planning.shift.copy.executed",
            "ops.shift_plan",
            shift_plan_id,
            tenant_id,
            metadata_json={
                "source_from": payload.source_from.isoformat(),
                "source_to": payload.source_to.isoformat(),
                "target_from": payload.target_from.isoformat(),
                "copied_count": copied_count,
                "skipped_count": skipped_count,
            },
        )
        return ShiftCopyResult(
            tenant_id=tenant_id,
            shift_plan_id=shift_plan_id,
            copied_count=copied_count,
            skipped_count=skipped_count,
            target_from=payload.target_from,
        )

    def list_board_shifts(
        self,
        tenant_id: str,
        filters: PlanningBoardFilter,
        _actor: RequestAuthorizationContext,
    ) -> list[PlanningBoardShiftListItem]:
        if filters.date_to <= filters.date_from:
            raise ApiException(400, "planning.shift_board.invalid_window", "errors.planning.shift_board.invalid_window")
        if filters.visibility_state is not None and filters.visibility_state not in self.VISIBILITY_STATES:
            raise ApiException(400, "planning.shift_board.invalid_visibility_state", "errors.planning.shift_board.invalid_visibility_state")
        return [PlanningBoardShiftListItem.model_validate(row) for row in self.repository.list_board_shifts(tenant_id, filters)]

    def _validate_shift_plan_payload(
        self,
        planning_record: PlanningRecord,
        workforce_scope_code: str,
        planning_from: date,
        planning_to: date,
    ) -> None:
        if workforce_scope_code not in self.WORKFORCE_SCOPES:
            raise ApiException(400, "planning.shift_plan.invalid_workforce_scope", "errors.planning.shift_plan.invalid_workforce_scope")
        if planning_to < planning_from:
            raise ApiException(400, "planning.shift_plan.invalid_window", "errors.planning.shift_plan.invalid_window")
        if planning_from < planning_record.planning_from or planning_to > planning_record.planning_to:
            raise ApiException(400, "planning.shift_plan.record_window_mismatch", "errors.planning.shift_plan.record_window_mismatch")

    def _validate_shift_series_payload(self, shift_plan: ShiftPlan, payload: ShiftSeriesCreate) -> None:
        if payload.recurrence_code not in self.SERIES_RECURRENCE_CODES:
            raise ApiException(400, "planning.shift_series.invalid_recurrence_code", "errors.planning.shift_series.invalid_recurrence_code")
        if payload.date_to < payload.date_from:
            raise ApiException(400, "planning.shift_series.invalid_window", "errors.planning.shift_series.invalid_window")
        if payload.date_from < shift_plan.planning_from or payload.date_to > shift_plan.planning_to:
            raise ApiException(400, "planning.shift_series.plan_window_mismatch", "errors.planning.shift_series.plan_window_mismatch")
        self._require_release_state(payload.release_state, "shift_series")
        zone = self._require_timezone(payload.timezone)
        _ = zone
        if payload.recurrence_code == "weekly":
            if payload.weekday_mask is None or len(payload.weekday_mask) != 7 or not set(payload.weekday_mask).issubset({"0", "1"}):
                raise ApiException(400, "planning.shift_series.invalid_weekday_mask", "errors.planning.shift_series.invalid_weekday_mask")

    def _validate_exception(
        self,
        series: ShiftSeries,
        action_code: str,
        exception_date: date,
        override_local_start_time: time | None,
        override_local_end_time: time | None,
    ) -> None:
        if action_code not in self.SERIES_EXCEPTION_ACTIONS:
            raise ApiException(400, "planning.shift_series_exception.invalid_action", "errors.planning.shift_series_exception.invalid_action")
        if exception_date < series.date_from or exception_date > series.date_to:
            raise ApiException(400, "planning.shift_series_exception.outside_window", "errors.planning.shift_series_exception.outside_window")
        if action_code == "override":
            if override_local_start_time is None or override_local_end_time is None:
                raise ApiException(400, "planning.shift_series_exception.override_times_required", "errors.planning.shift_series_exception.override_times_required")
            self._validate_template_times(override_local_start_time, override_local_end_time)

    def _validate_shift_payload(
        self,
        starts_at: datetime,
        ends_at: datetime,
        break_minutes: int,
        release_state: str,
        customer_visible_flag: bool,
        subcontractor_visible_flag: bool,
    ) -> None:
        if ends_at <= starts_at:
            raise ApiException(400, "planning.shift.invalid_window", "errors.planning.shift.invalid_window")
        if break_minutes < 0:
            raise ApiException(400, "planning.shift.invalid_break_minutes", "errors.planning.shift.invalid_break_minutes")
        self._require_release_state(release_state, "shift")
        if (customer_visible_flag or subcontractor_visible_flag) and release_state != "released":
            raise ApiException(409, "planning.shift.visibility_requires_release", "errors.planning.shift.visibility_requires_release")

    @staticmethod
    def _validate_shift_window(
        shift_plan: ShiftPlan,
        planning_record: PlanningRecord,
        starts_at: datetime,
        ends_at: datetime,
    ) -> None:
        start_date = starts_at.date()
        end_date = ends_at.date()
        if start_date < shift_plan.planning_from or end_date > shift_plan.planning_to:
            raise ApiException(400, "planning.shift.plan_window_mismatch", "errors.planning.shift.plan_window_mismatch")
        if start_date < planning_record.planning_from or end_date > planning_record.planning_to:
            raise ApiException(400, "planning.shift.plan_window_mismatch", "errors.planning.shift.plan_window_mismatch")

    @staticmethod
    def _validate_template_times(start: time, end: time) -> None:
        if start == end:
            raise ApiException(400, "planning.shift_template.invalid_time_range", "errors.planning.shift_template.invalid_time_range")

    def _resolve_occurrence(
        self,
        series: ShiftSeries,
        template: ShiftTemplate,
        exception: ShiftSeriesException | None,
        occurrence_date: date,
    ) -> _OccurrenceValues:
        local_start_time = exception.override_local_start_time if exception and exception.override_local_start_time is not None else template.local_start_time
        local_end_time = exception.override_local_end_time if exception and exception.override_local_end_time is not None else template.local_end_time
        break_minutes = (
            exception.override_break_minutes
            if exception and exception.override_break_minutes is not None
            else series.default_break_minutes
            if series.default_break_minutes is not None
            else template.default_break_minutes
        )
        shift_type_code = (
            exception.override_shift_type_code
            if exception and exception.override_shift_type_code is not None
            else series.shift_type_code
            if series.shift_type_code is not None
            else template.shift_type_code
        )
        meeting_point = exception.override_meeting_point if exception and exception.override_meeting_point is not None else (series.meeting_point or template.meeting_point)
        location_text = exception.override_location_text if exception and exception.override_location_text is not None else (series.location_text or template.location_text)
        customer_visible_flag = exception.customer_visible_flag if exception and exception.customer_visible_flag is not None else series.customer_visible_flag
        subcontractor_visible_flag = exception.subcontractor_visible_flag if exception and exception.subcontractor_visible_flag is not None else series.subcontractor_visible_flag
        stealth_mode_flag = exception.stealth_mode_flag if exception and exception.stealth_mode_flag is not None else series.stealth_mode_flag
        starts_at, ends_at = self._build_occurrence_window(series.timezone, occurrence_date, local_start_time, local_end_time)
        return _OccurrenceValues(
            occurrence_date=occurrence_date,
            starts_at=starts_at,
            ends_at=ends_at,
            break_minutes=break_minutes,
            shift_type_code=shift_type_code,
            meeting_point=meeting_point,
            location_text=location_text,
            customer_visible_flag=customer_visible_flag,
            subcontractor_visible_flag=subcontractor_visible_flag,
            stealth_mode_flag=stealth_mode_flag,
        )

    def _occurrence_dates(self, series: ShiftSeries, generation_from: date, generation_to: date) -> list[date]:
        dates: list[date] = []
        cursor = generation_from
        while cursor <= generation_to:
            include = False
            if series.recurrence_code == "daily":
                include = ((cursor - series.date_from).days % series.interval_count) == 0
            else:
                weekday_mask = series.weekday_mask or "1111111"
                week_index = (cursor - series.date_from).days // 7
                include = weekday_mask[cursor.weekday()] == "1" and (week_index % series.interval_count) == 0
            if include:
                dates.append(cursor)
            cursor += timedelta(days=1)
        return dates

    def _build_occurrence_window(self, timezone_name: str, occurrence_date: date, local_start_time: time, local_end_time: time) -> tuple[datetime, datetime]:
        zone = self._require_timezone(timezone_name)
        start_local = datetime.combine(occurrence_date, local_start_time, tzinfo=zone)
        end_date = occurrence_date if local_end_time > local_start_time else occurrence_date + timedelta(days=1)
        end_local = datetime.combine(end_date, local_end_time, tzinfo=zone)
        return start_local.astimezone(UTC), end_local.astimezone(UTC)

    @staticmethod
    def _require_timezone(timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ApiException(400, "planning.shift_series.invalid_timezone", "errors.planning.shift_series.invalid_timezone") from exc

    def _read_shift_plan(self, row: ShiftPlan) -> ShiftPlanRead:
        return ShiftPlanRead.model_validate(
            row,
            from_attributes=True,
        )

    def _read_shift_series(self, row: ShiftSeries) -> ShiftSeriesRead:
        return ShiftSeriesRead.model_validate(row, from_attributes=True)

    def _require_planning_record(self, tenant_id: str, planning_record_id: str) -> PlanningRecord:
        row = self.repository.get_planning_record(tenant_id, planning_record_id)
        if row is None:
            raise self._not_found("planning_record")
        return row

    def _require_shift_plan(self, tenant_id: str, shift_plan_id: str) -> ShiftPlan:
        row = self.repository.get_shift_plan(tenant_id, shift_plan_id)
        if row is None:
            raise self._not_found("shift_plan")
        return row

    def _require_template(self, tenant_id: str, template_id: str) -> ShiftTemplate:
        row = self.repository.get_shift_template(tenant_id, template_id)
        if row is None:
            raise self._not_found("shift_template")
        return row

    def _require_shift_series(self, tenant_id: str, shift_series_id: str) -> ShiftSeries:
        row = self.repository.get_shift_series(tenant_id, shift_series_id)
        if row is None:
            raise self._not_found("shift_series")
        return row

    def _require_shift_series_exception(self, tenant_id: str, row_id: str) -> ShiftSeriesException:
        row = self.repository.get_shift_series_exception(tenant_id, row_id)
        if row is None:
            raise self._not_found("shift_series_exception")
        return row

    def _require_shift(self, tenant_id: str, shift_id: str) -> Shift:
        row = self.repository.get_shift(tenant_id, shift_id)
        if row is None:
            raise self._not_found("shift")
        return row

    @staticmethod
    def _field_value(payload, field_name: str, current_value):
        return payload.model_dump(exclude_unset=True).get(field_name, current_value)

    @classmethod
    def _require_release_state(cls, release_state: str, resource_code: str) -> None:
        if release_state not in cls.RELEASE_STATES:
            raise ApiException(400, f"planning.{resource_code}.invalid_release_state", f"errors.planning.{resource_code}.invalid_release_state")

    @staticmethod
    def _enforce_release_transition(current_state: str, next_state: str) -> None:
        transitions = {
            "draft": {"release_ready", "released"},
            "release_ready": {"draft", "released"},
            "released": {"draft"},
        }
        if next_state not in transitions[current_state]:
            raise ApiException(
                409,
                "planning.shift.invalid_release_transition",
                "errors.planning.shift.invalid_release_transition",
            )

    def _assert_release_allowed(self, tenant_id: str, shift_id: str) -> None:
        if self.validation_service is None:
            return
        validations = self.validation_service.validate_shift_release(tenant_id, shift_id)
        if validations.blocking_count:
            raise ApiException(
                409,
                "planning.shift.blocked_by_validation",
                "errors.planning.shift.blocked_by_validation",
                {"issues": [issue.model_dump() for issue in validations.issues]},
            )

    @staticmethod
    def _require_tenant_scope(tenant_id: str, payload_tenant_id: str) -> None:
        if tenant_id != payload_tenant_id:
            raise ApiException(400, "planning.shift.scope_mismatch", "errors.planning.shift.scope_mismatch")

    def _not_found(self, resource: str) -> ApiException:
        return ApiException(404, f"planning.{resource}.not_found", f"errors.planning.{resource}.not_found")

    @staticmethod
    def _snapshot(row) -> dict[str, object]:
        return {key: value for key, value in row.__dict__.items() if not key.startswith("_")}

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        *,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                user_id=actor.user_id,
                tenant_id=tenant_id,
                request_id=actor.request_id,
                session_id=actor.session_id,
            ),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=after_json,
            metadata_json=metadata_json,
        )
