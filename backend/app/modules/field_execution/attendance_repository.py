"""Repository helpers for attendance derivation and review reads."""

from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.field_execution.models import AttendanceRecord, TimeEvent
from app.modules.planning.models import Assignment, Shift, ShiftPlan


class SqlAlchemyAttendanceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_shift(self, tenant_id: str, shift_id: str) -> Shift | None:
        statement = (
            select(Shift)
            .options(joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record))
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

    def list_assignments_for_shift(self, tenant_id: str, shift_id: str) -> list[Assignment]:
        statement = (
            select(Assignment)
            .options(joinedload(Assignment.shift))
            .options(joinedload(Assignment.employee))
            .options(joinedload(Assignment.subcontractor_worker))
            .where(
                Assignment.tenant_id == tenant_id,
                Assignment.shift_id == shift_id,
                Assignment.archived_at.is_(None),
                Assignment.assignment_status_code.in_(("assigned", "confirmed")),
            )
            .order_by(Assignment.created_at, Assignment.id)
        )
        return list(self.session.scalars(statement).unique().all())

    def list_events_for_actor_shift(
        self,
        tenant_id: str,
        *,
        shift_id: str,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
    ) -> list[TimeEvent]:
        statement = (
            select(TimeEvent)
            .where(
                TimeEvent.tenant_id == tenant_id,
                TimeEvent.shift_id == shift_id,
                TimeEvent.archived_at.is_(None),
            )
            .order_by(TimeEvent.occurred_at, TimeEvent.created_at, TimeEvent.id)
        )
        if employee_id is not None:
            statement = statement.where(TimeEvent.employee_id == employee_id)
        if subcontractor_worker_id is not None:
            statement = statement.where(TimeEvent.subcontractor_worker_id == subcontractor_worker_id)
        return list(self.session.scalars(statement).all())

    def get_attendance_record(self, tenant_id: str, attendance_record_id: str) -> AttendanceRecord | None:
        statement = self._attendance_query().where(
            AttendanceRecord.tenant_id == tenant_id,
            AttendanceRecord.id == attendance_record_id,
        )
        return self.session.scalars(statement).unique().one_or_none()

    def get_current_attendance_for_actor_shift(
        self,
        tenant_id: str,
        *,
        shift_id: str,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
    ) -> AttendanceRecord | None:
        statement = self._attendance_query().where(
            AttendanceRecord.tenant_id == tenant_id,
            AttendanceRecord.shift_id == shift_id,
            AttendanceRecord.is_current.is_(True),
            AttendanceRecord.archived_at.is_(None),
        )
        if employee_id is not None:
            statement = statement.where(AttendanceRecord.employee_id == employee_id)
        if subcontractor_worker_id is not None:
            statement = statement.where(AttendanceRecord.subcontractor_worker_id == subcontractor_worker_id)
        return self.session.scalars(statement).unique().one_or_none()

    def list_attendance_records(self, tenant_id: str, filters) -> list[AttendanceRecord]:  # noqa: ANN001
        statement = self._attendance_query().where(AttendanceRecord.tenant_id == tenant_id)
        if not filters.include_archived:
            statement = statement.where(AttendanceRecord.archived_at.is_(None))
        if filters.current_only:
            statement = statement.where(AttendanceRecord.is_current.is_(True))
        if filters.shift_id is not None:
            statement = statement.where(AttendanceRecord.shift_id == filters.shift_id)
        if filters.assignment_id is not None:
            statement = statement.where(AttendanceRecord.assignment_id == filters.assignment_id)
        if filters.employee_id is not None:
            statement = statement.where(AttendanceRecord.employee_id == filters.employee_id)
        if filters.subcontractor_worker_id is not None:
            statement = statement.where(AttendanceRecord.subcontractor_worker_id == filters.subcontractor_worker_id)
        if filters.discrepancy_only:
            statement = statement.where(AttendanceRecord.discrepancy_state_code != "clean")
        statement = statement.order_by(AttendanceRecord.derived_at.desc(), AttendanceRecord.created_at.desc())
        return list(self.session.scalars(statement).unique().all())

    def create_attendance_record(self, row: AttendanceRecord) -> AttendanceRecord:
        self.session.add(row)
        self.session.commit()
        return self.get_attendance_record(row.tenant_id, row.id) or row

    def save_attendance_record(self, row: AttendanceRecord) -> AttendanceRecord:
        self.session.add(row)
        self.session.commit()
        return self.get_attendance_record(row.tenant_id, row.id) or row

    def _attendance_query(self):
        return (
            select(AttendanceRecord)
            .options(joinedload(AttendanceRecord.assignment))
            .options(joinedload(AttendanceRecord.shift))
            .options(joinedload(AttendanceRecord.employee))
            .options(joinedload(AttendanceRecord.subcontractor_worker))
            .options(joinedload(AttendanceRecord.first_time_event))
            .options(joinedload(AttendanceRecord.last_time_event))
        )
