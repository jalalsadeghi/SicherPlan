"""Repository helpers for time-capture configuration and raw event ingest."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.employees.models import Employee, EmployeeIdCredential
from app.modules.field_execution.models import TimeCaptureDevice, TimeCapturePolicy, TimeEvent
from app.modules.planning.models import Assignment, CustomerOrder, PatrolRoute, PlanningRecord, Shift, ShiftPlan, Site
from app.modules.subcontractors.models import SubcontractorWorker, SubcontractorWorkerCredential


class SqlAlchemyTimeCaptureRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_devices(self, tenant_id: str, filters) -> list[TimeCaptureDevice]:  # noqa: ANN001
        statement = select(TimeCaptureDevice).where(TimeCaptureDevice.tenant_id == tenant_id)
        if not filters.include_archived:
            statement = statement.where(TimeCaptureDevice.archived_at.is_(None))
        if filters.site_id is not None:
            statement = statement.where(TimeCaptureDevice.site_id == filters.site_id)
        if filters.device_type_code is not None:
            statement = statement.where(TimeCaptureDevice.device_type_code == filters.device_type_code)
        if filters.status is not None:
            statement = statement.where(TimeCaptureDevice.status == filters.status)
        statement = statement.order_by(TimeCaptureDevice.device_code)
        return list(self.session.scalars(statement).all())

    def get_device(self, tenant_id: str, device_id: str) -> TimeCaptureDevice | None:
        statement = (
            select(TimeCaptureDevice)
            .options(joinedload(TimeCaptureDevice.site))
            .where(TimeCaptureDevice.tenant_id == tenant_id, TimeCaptureDevice.id == device_id)
        )
        return self.session.scalars(statement).one_or_none()

    def get_device_by_code(self, tenant_id: str, device_code: str) -> TimeCaptureDevice | None:
        statement = (
            select(TimeCaptureDevice)
            .options(joinedload(TimeCaptureDevice.site))
            .where(TimeCaptureDevice.tenant_id == tenant_id, TimeCaptureDevice.device_code == device_code)
        )
        return self.session.scalars(statement).one_or_none()

    def find_device_by_code(self, tenant_id: str, device_code: str, *, exclude_id: str | None = None) -> TimeCaptureDevice | None:
        statement = select(TimeCaptureDevice).where(
            TimeCaptureDevice.tenant_id == tenant_id,
            TimeCaptureDevice.device_code == device_code,
        )
        if exclude_id is not None:
            statement = statement.where(TimeCaptureDevice.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_device(self, row: TimeCaptureDevice) -> TimeCaptureDevice:
        self.session.add(row)
        self.session.commit()
        return self.get_device(row.tenant_id, row.id) or row

    def update_device(self, row: TimeCaptureDevice) -> TimeCaptureDevice:
        self.session.add(row)
        self.session.commit()
        return self.get_device(row.tenant_id, row.id) or row

    def list_policies(self, tenant_id: str, filters) -> list[TimeCapturePolicy]:  # noqa: ANN001
        statement = self._policy_query().where(TimeCapturePolicy.tenant_id == tenant_id)
        if not filters.include_archived:
            statement = statement.where(TimeCapturePolicy.archived_at.is_(None))
        if filters.context_type_code is not None:
            statement = statement.where(TimeCapturePolicy.context_type_code == filters.context_type_code)
        if filters.site_id is not None:
            statement = statement.where(TimeCapturePolicy.site_id == filters.site_id)
        if filters.shift_id is not None:
            statement = statement.where(TimeCapturePolicy.shift_id == filters.shift_id)
        if filters.planning_record_id is not None:
            statement = statement.where(TimeCapturePolicy.planning_record_id == filters.planning_record_id)
        if filters.patrol_route_id is not None:
            statement = statement.where(TimeCapturePolicy.patrol_route_id == filters.patrol_route_id)
        if filters.status is not None:
            statement = statement.where(TimeCapturePolicy.status == filters.status)
        statement = statement.order_by(TimeCapturePolicy.policy_code)
        return list(self.session.scalars(statement).unique().all())

    def get_policy(self, tenant_id: str, policy_id: str) -> TimeCapturePolicy | None:
        statement = self._policy_query().where(TimeCapturePolicy.tenant_id == tenant_id, TimeCapturePolicy.id == policy_id)
        return self.session.scalars(statement).unique().one_or_none()

    def find_policy_by_code(self, tenant_id: str, policy_code: str, *, exclude_id: str | None = None) -> TimeCapturePolicy | None:
        statement = select(TimeCapturePolicy).where(
            TimeCapturePolicy.tenant_id == tenant_id,
            TimeCapturePolicy.policy_code == policy_code,
        )
        if exclude_id is not None:
            statement = statement.where(TimeCapturePolicy.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def find_active_policy_for_context(
        self,
        tenant_id: str,
        *,
        shift_id: str | None,
        planning_record_id: str | None,
        patrol_route_id: str | None,
        site_id: str | None,
    ) -> TimeCapturePolicy | None:
        candidates = [
            ("shift", TimeCapturePolicy.shift_id, shift_id),
            ("planning_record", TimeCapturePolicy.planning_record_id, planning_record_id),
            ("patrol_route", TimeCapturePolicy.patrol_route_id, patrol_route_id),
            ("site", TimeCapturePolicy.site_id, site_id),
        ]
        for context_type, column, value in candidates:
            if value is None:
                continue
            statement = self._policy_query().where(
                TimeCapturePolicy.tenant_id == tenant_id,
                TimeCapturePolicy.context_type_code == context_type,
                column == value,
                TimeCapturePolicy.archived_at.is_(None),
                TimeCapturePolicy.status == "active",
            )
            row = self.session.scalars(statement).unique().one_or_none()
            if row is not None:
                return row
        return None

    def create_policy(self, row: TimeCapturePolicy) -> TimeCapturePolicy:
        self.session.add(row)
        self.session.commit()
        return self.get_policy(row.tenant_id, row.id) or row

    def update_policy(self, row: TimeCapturePolicy) -> TimeCapturePolicy:
        self.session.add(row)
        self.session.commit()
        return self.get_policy(row.tenant_id, row.id) or row

    def list_time_events(self, tenant_id: str, filters) -> list[TimeEvent]:  # noqa: ANN001
        statement = self._time_event_query().where(TimeEvent.tenant_id == tenant_id)
        if not filters.include_archived:
            statement = statement.where(TimeEvent.archived_at.is_(None))
        if filters.shift_id is not None:
            statement = statement.where(TimeEvent.shift_id == filters.shift_id)
        if filters.employee_id is not None:
            statement = statement.where(TimeEvent.employee_id == filters.employee_id)
        if filters.subcontractor_worker_id is not None:
            statement = statement.where(TimeEvent.subcontractor_worker_id == filters.subcontractor_worker_id)
        if filters.source_channel_code is not None:
            statement = statement.where(TimeEvent.source_channel_code == filters.source_channel_code)
        if filters.validation_status_code is not None:
            statement = statement.where(TimeEvent.validation_status_code == filters.validation_status_code)
        if filters.device_id is not None:
            statement = statement.where(TimeEvent.device_id == filters.device_id)
        if filters.occurred_from is not None:
            statement = statement.where(TimeEvent.occurred_at >= filters.occurred_from)
        if filters.occurred_to is not None:
            statement = statement.where(TimeEvent.occurred_at <= filters.occurred_to)
        statement = statement.order_by(TimeEvent.occurred_at.desc(), TimeEvent.created_at.desc())
        return list(self.session.scalars(statement).unique().all())

    def list_employee_time_events(self, tenant_id: str, employee_id: str, *, limit: int = 30) -> list[TimeEvent]:
        statement = (
            self._time_event_query()
            .where(TimeEvent.tenant_id == tenant_id, TimeEvent.employee_id == employee_id, TimeEvent.archived_at.is_(None))
            .order_by(TimeEvent.occurred_at.desc(), TimeEvent.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(statement).unique().all())

    def get_time_event(self, tenant_id: str, event_id: str) -> TimeEvent | None:
        statement = self._time_event_query().where(TimeEvent.tenant_id == tenant_id, TimeEvent.id == event_id)
        return self.session.scalars(statement).unique().one_or_none()

    def get_time_event_by_client_id(self, tenant_id: str, client_event_id: str) -> TimeEvent | None:
        statement = self._time_event_query().where(
            TimeEvent.tenant_id == tenant_id,
            TimeEvent.client_event_id == client_event_id,
        )
        return self.session.scalars(statement).unique().one_or_none()

    def create_time_event(self, row: TimeEvent) -> TimeEvent:
        self.session.add(row)
        self.session.commit()
        return self.get_time_event(row.tenant_id, row.id) or row

    def save_time_event(self, row: TimeEvent) -> TimeEvent:
        self.session.add(row)
        self.session.commit()
        return self.get_time_event(row.tenant_id, row.id) or row

    def get_site(self, tenant_id: str, site_id: str) -> Site | None:
        return self.session.scalars(select(Site).where(Site.tenant_id == tenant_id, Site.id == site_id)).one_or_none()

    def get_shift(self, tenant_id: str, shift_id: str) -> Shift | None:
        statement = (
            select(Shift)
            .options(joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record).joinedload(PlanningRecord.order))
            .options(joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record).joinedload(PlanningRecord.patrol_detail))
            .where(Shift.tenant_id == tenant_id, Shift.id == shift_id)
        )
        return self.session.scalars(statement).unique().one_or_none()

    def get_assignment(self, tenant_id: str, assignment_id: str) -> Assignment | None:
        statement = (
            select(Assignment)
            .options(joinedload(Assignment.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record))
            .options(joinedload(Assignment.employee))
            .options(joinedload(Assignment.subcontractor_worker))
            .where(Assignment.tenant_id == tenant_id, Assignment.id == assignment_id)
        )
        return self.session.scalars(statement).unique().one_or_none()

    def find_assignment_for_employee(self, tenant_id: str, shift_id: str, employee_id: str) -> Assignment | None:
        statement = (
            select(Assignment)
            .options(joinedload(Assignment.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record))
            .where(
                Assignment.tenant_id == tenant_id,
                Assignment.shift_id == shift_id,
                Assignment.employee_id == employee_id,
                Assignment.archived_at.is_(None),
                Assignment.assignment_status_code.in_(("assigned", "confirmed")),
            )
        )
        return self.session.scalars(statement).unique().one_or_none()

    def find_assignment_for_worker(self, tenant_id: str, shift_id: str, worker_id: str) -> Assignment | None:
        statement = (
            select(Assignment)
            .options(joinedload(Assignment.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record))
            .where(
                Assignment.tenant_id == tenant_id,
                Assignment.shift_id == shift_id,
                Assignment.subcontractor_worker_id == worker_id,
                Assignment.archived_at.is_(None),
                Assignment.assignment_status_code.in_(("assigned", "confirmed")),
            )
        )
        return self.session.scalars(statement).unique().one_or_none()

    def find_employee_by_user_id(self, tenant_id: str, user_id: str) -> Employee | None:
        return self.session.scalars(
            select(Employee).where(
                Employee.tenant_id == tenant_id,
                Employee.user_id == user_id,
                Employee.archived_at.is_(None),
            )
        ).one_or_none()

    def find_employee_credential_by_encoded_value(self, tenant_id: str, encoded_value: str) -> EmployeeIdCredential | None:
        statement = (
            select(EmployeeIdCredential)
            .options(joinedload(EmployeeIdCredential.employee))
            .where(
                EmployeeIdCredential.tenant_id == tenant_id,
                EmployeeIdCredential.encoded_value == encoded_value,
                EmployeeIdCredential.archived_at.is_(None),
            )
        )
        return self.session.scalars(statement).unique().one_or_none()

    def find_worker_credential_by_encoded_value(self, tenant_id: str, encoded_value: str) -> SubcontractorWorkerCredential | None:
        statement = (
            select(SubcontractorWorkerCredential)
            .options(joinedload(SubcontractorWorkerCredential.worker))
            .where(
                SubcontractorWorkerCredential.tenant_id == tenant_id,
                SubcontractorWorkerCredential.encoded_value == encoded_value,
                SubcontractorWorkerCredential.archived_at.is_(None),
            )
        )
        return self.session.scalars(statement).unique().one_or_none()

    def get_planning_record(self, tenant_id: str, planning_record_id: str) -> PlanningRecord | None:
        return self.session.scalars(
            select(PlanningRecord).where(PlanningRecord.tenant_id == tenant_id, PlanningRecord.id == planning_record_id)
        ).one_or_none()

    def get_patrol_route(self, tenant_id: str, patrol_route_id: str) -> PatrolRoute | None:
        return self.session.scalars(
            select(PatrolRoute).where(PatrolRoute.tenant_id == tenant_id, PatrolRoute.id == patrol_route_id)
        ).one_or_none()

    @staticmethod
    def _policy_query() -> Select[tuple[TimeCapturePolicy]]:
        return (
            select(TimeCapturePolicy)
            .options(joinedload(TimeCapturePolicy.site))
            .options(joinedload(TimeCapturePolicy.shift))
            .options(joinedload(TimeCapturePolicy.planning_record).joinedload(PlanningRecord.order))
            .options(joinedload(TimeCapturePolicy.patrol_route))
            .options(joinedload(TimeCapturePolicy.allowed_device))
        )

    @staticmethod
    def _time_event_query() -> Select[tuple[TimeEvent]]:
        return (
            select(TimeEvent)
            .options(joinedload(TimeEvent.employee))
            .options(joinedload(TimeEvent.subcontractor_worker))
            .options(joinedload(TimeEvent.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record).joinedload(PlanningRecord.order))
            .options(joinedload(TimeEvent.assignment))
            .options(joinedload(TimeEvent.site))
            .options(joinedload(TimeEvent.planning_record))
            .options(joinedload(TimeEvent.patrol_route))
            .options(joinedload(TimeEvent.device))
            .options(joinedload(TimeEvent.policy))
        )
