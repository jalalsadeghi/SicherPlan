"""SQLAlchemy repository for finance actual bridge records and approvals."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.employees.models import Employee
from app.modules.field_execution.models import AttendanceRecord
from app.modules.finance.models import ActualAllowance, ActualApproval, ActualComment, ActualExpense, ActualReconciliation, ActualRecord
from app.modules.iam.audit_models import AuditEvent
from app.modules.iam.audit_schemas import AuditEventRead
from app.modules.planning.models import Assignment, Shift, ShiftPlan
from app.modules.subcontractors.models import SubcontractorWorker


class SqlAlchemyFinanceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_assignment(self, tenant_id: str, assignment_id: str) -> Assignment | None:
        statement = (
            select(Assignment)
            .options(joinedload(Assignment.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record))
            .options(joinedload(Assignment.employee))
            .options(joinedload(Assignment.subcontractor_worker))
            .where(Assignment.tenant_id == tenant_id, Assignment.id == assignment_id)
        )
        return self.session.scalars(statement).unique().one_or_none()

    def get_attendance_record(self, tenant_id: str, attendance_record_id: str) -> AttendanceRecord | None:
        statement = (
            select(AttendanceRecord)
            .options(joinedload(AttendanceRecord.assignment))
            .options(joinedload(AttendanceRecord.shift))
            .options(joinedload(AttendanceRecord.employee))
            .options(joinedload(AttendanceRecord.subcontractor_worker))
            .where(AttendanceRecord.tenant_id == tenant_id, AttendanceRecord.id == attendance_record_id)
        )
        return self.session.scalars(statement).unique().one_or_none()

    def get_current_attendance_for_assignment(self, tenant_id: str, assignment_id: str) -> AttendanceRecord | None:
        statement = (
            select(AttendanceRecord)
            .options(joinedload(AttendanceRecord.assignment))
            .options(joinedload(AttendanceRecord.shift))
            .where(
                AttendanceRecord.tenant_id == tenant_id,
                AttendanceRecord.assignment_id == assignment_id,
                AttendanceRecord.is_current.is_(True),
                AttendanceRecord.archived_at.is_(None),
            )
        )
        return self.session.scalars(statement).unique().one_or_none()

    def get_actual_record(self, tenant_id: str, actual_record_id: str) -> ActualRecord | None:
        statement = self._actual_query().where(ActualRecord.tenant_id == tenant_id, ActualRecord.id == actual_record_id)
        return self.session.scalars(statement).unique().one_or_none()

    def get_current_actual_for_assignment(self, tenant_id: str, assignment_id: str) -> ActualRecord | None:
        statement = self._actual_query().where(
            ActualRecord.tenant_id == tenant_id,
            ActualRecord.assignment_id == assignment_id,
            ActualRecord.is_current.is_(True),
            ActualRecord.archived_at.is_(None),
        )
        return self.session.scalars(statement).unique().one_or_none()

    def list_actual_records(self, tenant_id: str, filters) -> list[ActualRecord]:  # noqa: ANN001
        statement = self._actual_query().where(ActualRecord.tenant_id == tenant_id)
        if not filters.include_archived:
            statement = statement.where(ActualRecord.archived_at.is_(None))
        if filters.current_only:
            statement = statement.where(ActualRecord.is_current.is_(True))
        if filters.shift_id is not None:
            statement = statement.where(ActualRecord.shift_id == filters.shift_id)
        if filters.assignment_id is not None:
            statement = statement.where(ActualRecord.assignment_id == filters.assignment_id)
        if filters.employee_id is not None:
            statement = statement.where(ActualRecord.employee_id == filters.employee_id)
        if filters.subcontractor_worker_id is not None:
            statement = statement.where(ActualRecord.subcontractor_worker_id == filters.subcontractor_worker_id)
        if filters.approval_stage_code is not None:
            statement = statement.where(ActualRecord.approval_stage_code == filters.approval_stage_code)
        if filters.discrepancy_only:
            statement = statement.where(ActualRecord.discrepancy_state_code != "clean")
        statement = statement.order_by(ActualRecord.derived_at.desc(), ActualRecord.created_at.desc())
        return list(self.session.scalars(statement).unique().all())

    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None:
        return self.session.scalars(select(Employee).where(Employee.tenant_id == tenant_id, Employee.id == employee_id)).one_or_none()

    def get_subcontractor_worker(self, tenant_id: str, worker_id: str) -> SubcontractorWorker | None:
        return self.session.scalars(
            select(SubcontractorWorker).where(SubcontractorWorker.tenant_id == tenant_id, SubcontractorWorker.id == worker_id)
        ).one_or_none()

    def create_actual_record(self, row: ActualRecord) -> ActualRecord:
        self.session.add(row)
        self.session.commit()
        return self.get_actual_record(row.tenant_id, row.id) or row

    def save_actual_record(self, row: ActualRecord) -> ActualRecord:
        self.session.add(row)
        self.session.commit()
        return self.get_actual_record(row.tenant_id, row.id) or row

    def create_actual_approval(self, row: ActualApproval) -> ActualApproval:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def create_actual_reconciliation(self, row: ActualReconciliation) -> ActualReconciliation:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def create_actual_allowance(self, row: ActualAllowance) -> ActualAllowance:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def create_actual_expense(self, row: ActualExpense) -> ActualExpense:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def create_actual_comment(self, row: ActualComment) -> ActualComment:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_audit_events_for_actual_record(self, tenant_id: str, actual_record_id: str) -> list[AuditEventRead]:
        statement = (
            select(AuditEvent)
            .where(
                AuditEvent.tenant_id == tenant_id,
                AuditEvent.entity_type == "finance.actual_record",
                AuditEvent.entity_id == actual_record_id,
            )
            .order_by(AuditEvent.created_at.asc())
        )
        rows = self.session.scalars(statement).all()
        return [AuditEventRead.model_validate(row) for row in rows]

    def _actual_query(self):
        return (
            select(ActualRecord)
            .options(joinedload(ActualRecord.assignment).joinedload(Assignment.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record))
            .options(joinedload(ActualRecord.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record))
            .options(joinedload(ActualRecord.attendance_record))
            .options(joinedload(ActualRecord.employee))
            .options(joinedload(ActualRecord.subcontractor_worker))
            .options(selectinload(ActualRecord.approvals))
            .options(selectinload(ActualRecord.reconciliations))
            .options(selectinload(ActualRecord.allowances))
            .options(selectinload(ActualRecord.expenses))
            .options(selectinload(ActualRecord.comments))
        )
