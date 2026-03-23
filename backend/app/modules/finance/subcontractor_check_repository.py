from __future__ import annotations

from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.finance.models import ActualRecord, SubcontractorInvoiceCheck, SubcontractorInvoiceCheckLine, SubcontractorInvoiceCheckNote
from app.modules.iam.audit_models import AuditEvent
from app.modules.iam.audit_schemas import AuditEventRead
from app.modules.planning.models import Assignment, Shift, ShiftPlan
from app.modules.subcontractors.models import SubcontractorFinanceProfile, SubcontractorRateCard, SubcontractorWorker


class SqlAlchemySubcontractorInvoiceCheckRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_invoice_checks(self, tenant_id: str, filters) -> list[SubcontractorInvoiceCheck]:  # noqa: ANN001
        statement = self._base_query().where(SubcontractorInvoiceCheck.tenant_id == tenant_id)
        if filters.subcontractor_id is not None:
            statement = statement.where(SubcontractorInvoiceCheck.subcontractor_id == filters.subcontractor_id)
        if filters.status_code is not None:
            statement = statement.where(SubcontractorInvoiceCheck.status_code == filters.status_code)
        if filters.period_start is not None:
            statement = statement.where(SubcontractorInvoiceCheck.period_end >= filters.period_start)
        if filters.period_end is not None:
            statement = statement.where(SubcontractorInvoiceCheck.period_start <= filters.period_end)
        statement = statement.order_by(SubcontractorInvoiceCheck.period_start.desc(), SubcontractorInvoiceCheck.created_at.desc())
        return list(self.session.scalars(statement).unique().all())

    def get_invoice_check(self, tenant_id: str, invoice_check_id: str) -> SubcontractorInvoiceCheck | None:
        statement = self._base_query().where(
            SubcontractorInvoiceCheck.tenant_id == tenant_id,
            SubcontractorInvoiceCheck.id == invoice_check_id,
        )
        return self.session.scalars(statement).unique().one_or_none()

    def find_by_period(self, tenant_id: str, subcontractor_id: str, period_start: date, period_end: date) -> SubcontractorInvoiceCheck | None:
        statement = self._base_query().where(
            SubcontractorInvoiceCheck.tenant_id == tenant_id,
            SubcontractorInvoiceCheck.subcontractor_id == subcontractor_id,
            SubcontractorInvoiceCheck.period_start == period_start,
            SubcontractorInvoiceCheck.period_end == period_end,
        )
        return self.session.scalars(statement).unique().one_or_none()

    def create_invoice_check(self, row: SubcontractorInvoiceCheck) -> SubcontractorInvoiceCheck:
        self.session.add(row)
        self.session.commit()
        return self.get_invoice_check(row.tenant_id, row.id) or row

    def save_invoice_check(self, row: SubcontractorInvoiceCheck) -> SubcontractorInvoiceCheck:
        self.session.add(row)
        self.session.commit()
        return self.get_invoice_check(row.tenant_id, row.id) or row

    def create_note(self, row: SubcontractorInvoiceCheckNote) -> SubcontractorInvoiceCheckNote:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_signed_off_actuals_for_subcontractor(self, tenant_id: str, subcontractor_id: str, period_start: date, period_end: date):
        statement = (
            select(ActualRecord)
            .options(
                joinedload(ActualRecord.assignment).joinedload(Assignment.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record),
                joinedload(ActualRecord.assignment).joinedload(Assignment.demand_group),
                joinedload(ActualRecord.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record),
                joinedload(ActualRecord.subcontractor_worker).joinedload(SubcontractorWorker.subcontractor),
                selectinload(ActualRecord.reconciliations),
            )
            .where(
                ActualRecord.tenant_id == tenant_id,
                ActualRecord.is_current.is_(True),
                ActualRecord.archived_at.is_(None),
                ActualRecord.actor_type_code == "subcontractor_worker",
                ActualRecord.approval_stage_code == "finance_signed_off",
                ActualRecord.subcontractor_worker_id.is_not(None),
                ActualRecord.planned_start_at.is_not(None),
            )
        )
        rows = list(self.session.scalars(statement).unique().all())
        result = []
        for row in rows:
            worker = row.subcontractor_worker
            service_date = row.planned_start_at.date() if row.planned_start_at is not None else None
            if worker is None or worker.subcontractor_id != subcontractor_id or service_date is None:
                continue
            if service_date < period_start or service_date > period_end:
                continue
            result.append(row)
        return result

    def list_active_subcontractor_rate_cards(self, tenant_id: str, subcontractor_id: str, on_date: date) -> list[SubcontractorRateCard]:
        statement = (
            select(SubcontractorRateCard)
            .options(selectinload(SubcontractorRateCard.rate_lines))
            .where(
                SubcontractorRateCard.tenant_id == tenant_id,
                SubcontractorRateCard.subcontractor_id == subcontractor_id,
                SubcontractorRateCard.status_code == "active",
                SubcontractorRateCard.effective_from <= on_date,
                or_(SubcontractorRateCard.effective_until.is_(None), SubcontractorRateCard.effective_until >= on_date),
            )
            .order_by(SubcontractorRateCard.effective_from.desc(), SubcontractorRateCard.created_at.desc())
        )
        return list(self.session.scalars(statement).unique().all())

    def get_subcontractor_finance_profile(self, tenant_id: str, subcontractor_id: str) -> SubcontractorFinanceProfile | None:
        statement = select(SubcontractorFinanceProfile).where(
            SubcontractorFinanceProfile.tenant_id == tenant_id,
            SubcontractorFinanceProfile.subcontractor_id == subcontractor_id,
        )
        return self.session.scalars(statement).one_or_none()

    def list_audit_events_for_invoice_check(self, tenant_id: str, invoice_check_id: str) -> list[AuditEventRead]:
        statement = (
            select(AuditEvent)
            .where(
                AuditEvent.tenant_id == tenant_id,
                AuditEvent.entity_type == "finance.subcontractor_invoice_check",
                AuditEvent.entity_id == invoice_check_id,
            )
            .order_by(AuditEvent.created_at.asc())
        )
        return [AuditEventRead.model_validate(row) for row in self.session.scalars(statement).all()]

    def _base_query(self):
        return (
            select(SubcontractorInvoiceCheck)
            .options(joinedload(SubcontractorInvoiceCheck.subcontractor))
            .options(selectinload(SubcontractorInvoiceCheck.lines))
            .options(selectinload(SubcontractorInvoiceCheck.notes))
        )
