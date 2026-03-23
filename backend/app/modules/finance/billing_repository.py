"""SQLAlchemy repository for finance customer timesheets and invoices."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.customers.models import CustomerBillingProfile, CustomerInvoiceParty, CustomerRateCard
from app.modules.finance.models import CustomerInvoice, Timesheet
from app.modules.finance.models import CustomerInvoiceLine, TimesheetLine
from app.modules.finance.models import ActualRecord
from app.modules.planning.models import Assignment, Shift, ShiftPlan
from app.modules.platform_services.docs_models import Document, DocumentLink
from app.modules.platform_services.integration_models import IntegrationEndpoint


class SqlAlchemyFinanceBillingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_approved_actuals_for_scope(
        self,
        tenant_id: str,
        *,
        customer_id: str,
        order_id: str | None,
        planning_record_id: str | None,
        period_start: date,
        period_end: date,
    ) -> list[ActualRecord]:
        statement = (
            select(ActualRecord)
            .options(joinedload(ActualRecord.assignment).joinedload(Assignment.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record))
            .options(joinedload(ActualRecord.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record))
            .options(joinedload(ActualRecord.assignment).joinedload(Assignment.demand_group))
            .where(
                ActualRecord.tenant_id == tenant_id,
                ActualRecord.is_current.is_(True),
                ActualRecord.archived_at.is_(None),
                ActualRecord.approval_stage_code == "finance_signed_off",
            )
            .order_by(ActualRecord.planned_start_at.asc(), ActualRecord.created_at.asc())
        )
        rows = list(self.session.scalars(statement).unique().all())
        filtered: list[ActualRecord] = []
        for row in rows:
            shift = row.shift
            plan = getattr(shift, "shift_plan", None)
            planning_record = getattr(plan, "planning_record", None)
            order = getattr(planning_record, "order", None)
            if planning_record is None or order is None:
                continue
            if order.customer_id != customer_id:
                continue
            service_date = (row.planned_start_at or row.derived_at).date()
            if service_date < period_start or service_date > period_end:
                continue
            if order_id is not None and order.id != order_id:
                continue
            if planning_record_id is not None and planning_record.id != planning_record_id:
                continue
            filtered.append(row)
        return filtered

    def list_timesheets(self, tenant_id: str, filters) -> list[Timesheet]:  # noqa: ANN001
        statement = self._timesheet_query().where(Timesheet.tenant_id == tenant_id)
        if not filters.include_archived:
            statement = statement.where(Timesheet.archived_at.is_(None))
        if filters.customer_id is not None:
            statement = statement.where(Timesheet.customer_id == filters.customer_id)
        if filters.order_id is not None:
            statement = statement.where(Timesheet.order_id == filters.order_id)
        if filters.planning_record_id is not None:
            statement = statement.where(Timesheet.planning_record_id == filters.planning_record_id)
        if filters.release_state_code is not None:
            statement = statement.where(Timesheet.release_state_code == filters.release_state_code)
        if filters.customer_visible_only:
            statement = statement.where(Timesheet.customer_visible_flag.is_(True))
        if filters.period_start is not None:
            statement = statement.where(Timesheet.period_end >= filters.period_start)
        if filters.period_end is not None:
            statement = statement.where(Timesheet.period_start <= filters.period_end)
        statement = statement.order_by(Timesheet.period_start.desc(), Timesheet.created_at.desc())
        return list(self.session.scalars(statement).unique().all())

    def get_timesheet(self, tenant_id: str, timesheet_id: str) -> Timesheet | None:
        statement = self._timesheet_query().where(Timesheet.tenant_id == tenant_id, Timesheet.id == timesheet_id)
        return self.session.scalars(statement).unique().one_or_none()

    def find_timesheet_by_scope_key(self, tenant_id: str, scope_key: str) -> Timesheet | None:
        statement = self._timesheet_query().where(Timesheet.tenant_id == tenant_id, Timesheet.scope_key == scope_key)
        return self.session.scalars(statement).unique().one_or_none()

    def create_timesheet(self, row: Timesheet) -> Timesheet:
        self.session.add(row)
        self.session.commit()
        return self.get_timesheet(row.tenant_id, row.id) or row

    def save_timesheet(self, row: Timesheet) -> Timesheet:
        self.session.add(row)
        self.session.commit()
        return self.get_timesheet(row.tenant_id, row.id) or row

    def list_invoices(self, tenant_id: str, filters) -> list[CustomerInvoice]:  # noqa: ANN001
        statement = self._invoice_query().where(CustomerInvoice.tenant_id == tenant_id)
        if not filters.include_archived:
            statement = statement.where(CustomerInvoice.archived_at.is_(None))
        if filters.customer_id is not None:
            statement = statement.where(CustomerInvoice.customer_id == filters.customer_id)
        if filters.timesheet_id is not None:
            statement = statement.where(CustomerInvoice.timesheet_id == filters.timesheet_id)
        if filters.invoice_status_code is not None:
            statement = statement.where(CustomerInvoice.invoice_status_code == filters.invoice_status_code)
        if filters.delivery_status_code is not None:
            statement = statement.where(CustomerInvoice.delivery_status_code == filters.delivery_status_code)
        if filters.customer_visible_only:
            statement = statement.where(CustomerInvoice.customer_visible_flag.is_(True))
        if filters.issue_date_from is not None:
            statement = statement.where(CustomerInvoice.issue_date >= filters.issue_date_from)
        if filters.issue_date_to is not None:
            statement = statement.where(CustomerInvoice.issue_date <= filters.issue_date_to)
        statement = statement.order_by(CustomerInvoice.issue_date.desc(), CustomerInvoice.created_at.desc())
        return list(self.session.scalars(statement).unique().all())

    def get_invoice(self, tenant_id: str, invoice_id: str) -> CustomerInvoice | None:
        statement = self._invoice_query().where(CustomerInvoice.tenant_id == tenant_id, CustomerInvoice.id == invoice_id)
        return self.session.scalars(statement).unique().one_or_none()

    def find_invoice_by_timesheet(self, tenant_id: str, timesheet_id: str) -> CustomerInvoice | None:
        statement = self._invoice_query().where(CustomerInvoice.tenant_id == tenant_id, CustomerInvoice.timesheet_id == timesheet_id)
        return self.session.scalars(statement).unique().one_or_none()

    def create_invoice(self, row: CustomerInvoice) -> CustomerInvoice:
        self.session.add(row)
        self.session.commit()
        return self.get_invoice(row.tenant_id, row.id) or row

    def save_invoice(self, row: CustomerInvoice) -> CustomerInvoice:
        self.session.add(row)
        self.session.commit()
        return self.get_invoice(row.tenant_id, row.id) or row

    def get_customer_billing_profile(self, tenant_id: str, customer_id: str) -> CustomerBillingProfile | None:
        statement = select(CustomerBillingProfile).where(
            CustomerBillingProfile.tenant_id == tenant_id,
            CustomerBillingProfile.customer_id == customer_id,
            CustomerBillingProfile.archived_at.is_(None),
        )
        return self.session.scalars(statement).one_or_none()

    def list_customer_invoice_parties(self, tenant_id: str, customer_id: str) -> list[CustomerInvoiceParty]:
        statement = (
            select(CustomerInvoiceParty)
            .options(joinedload(CustomerInvoiceParty.address))
            .where(
                CustomerInvoiceParty.tenant_id == tenant_id,
                CustomerInvoiceParty.customer_id == customer_id,
                CustomerInvoiceParty.archived_at.is_(None),
            )
            .order_by(CustomerInvoiceParty.is_default.desc(), CustomerInvoiceParty.created_at.asc())
        )
        return list(self.session.scalars(statement).unique().all())

    def list_active_customer_rate_cards(self, tenant_id: str, customer_id: str, on_date: date) -> list[CustomerRateCard]:
        statement = (
            select(CustomerRateCard)
            .options(selectinload(CustomerRateCard.rate_lines))
            .options(selectinload(CustomerRateCard.surcharge_rules))
            .where(
                CustomerRateCard.tenant_id == tenant_id,
                CustomerRateCard.customer_id == customer_id,
                CustomerRateCard.archived_at.is_(None),
                CustomerRateCard.effective_from <= on_date,
                (CustomerRateCard.effective_to.is_(None)) | (CustomerRateCard.effective_to >= on_date),
            )
            .order_by(CustomerRateCard.effective_from.desc(), CustomerRateCard.created_at.asc())
        )
        return list(self.session.scalars(statement).unique().all())

    def find_integration_endpoint(self, tenant_id: str, provider_key: str, endpoint_type: str) -> IntegrationEndpoint | None:
        statement = select(IntegrationEndpoint).where(
            IntegrationEndpoint.tenant_id == tenant_id,
            IntegrationEndpoint.provider_key == provider_key,
            IntegrationEndpoint.endpoint_type == endpoint_type,
            IntegrationEndpoint.archived_at.is_(None),
        )
        return self.session.scalars(statement).one_or_none()

    def get_integration_endpoint(self, tenant_id: str, endpoint_id: str) -> IntegrationEndpoint | None:
        statement = select(IntegrationEndpoint).where(
            IntegrationEndpoint.tenant_id == tenant_id,
            IntegrationEndpoint.id == endpoint_id,
            IntegrationEndpoint.archived_at.is_(None),
        )
        return self.session.scalars(statement).one_or_none()

    def list_document_links_for_timesheet(self, tenant_id: str, timesheet_id: str) -> list[DocumentLink]:
        statement = select(DocumentLink).where(
            DocumentLink.tenant_id == tenant_id,
            DocumentLink.owner_type == "finance.timesheet",
            DocumentLink.owner_id == timesheet_id,
        )
        statement = statement.options(
            joinedload(DocumentLink.document).joinedload(Document.document_type),
            joinedload(DocumentLink.document).joinedload(Document.versions),
        )
        return list(self.session.scalars(statement).unique().all())

    def list_document_links_for_invoice(self, tenant_id: str, invoice_id: str) -> list[DocumentLink]:
        statement = select(DocumentLink).where(
            DocumentLink.tenant_id == tenant_id,
            DocumentLink.owner_type == "finance.customer_invoice",
            DocumentLink.owner_id == invoice_id,
        )
        statement = statement.options(
            joinedload(DocumentLink.document).joinedload(Document.document_type),
            joinedload(DocumentLink.document).joinedload(Document.versions),
        )
        return list(self.session.scalars(statement).unique().all())

    def get_document_link_for_timesheet(self, tenant_id: str, timesheet_id: str, document_id: str) -> DocumentLink | None:
        statement = select(DocumentLink).where(
            DocumentLink.tenant_id == tenant_id,
            DocumentLink.owner_type == "finance.timesheet",
            DocumentLink.owner_id == timesheet_id,
            DocumentLink.document_id == document_id,
        )
        return self.session.scalars(statement).one_or_none()

    def get_document_link_for_invoice(self, tenant_id: str, invoice_id: str, document_id: str) -> DocumentLink | None:
        statement = select(DocumentLink).where(
            DocumentLink.tenant_id == tenant_id,
            DocumentLink.owner_type == "finance.customer_invoice",
            DocumentLink.owner_id == invoice_id,
            DocumentLink.document_id == document_id,
        )
        return self.session.scalars(statement).one_or_none()

    def _timesheet_query(self):
        return (
            select(Timesheet)
            .options(joinedload(Timesheet.customer))
            .options(joinedload(Timesheet.order))
            .options(joinedload(Timesheet.planning_record))
            .options(selectinload(Timesheet.lines).joinedload(TimesheetLine.actual_record))
            .options(selectinload(Timesheet.lines).joinedload(TimesheetLine.shift))
        )

    def _invoice_query(self):
        return (
            select(CustomerInvoice)
            .options(joinedload(CustomerInvoice.customer))
            .options(joinedload(CustomerInvoice.timesheet))
            .options(joinedload(CustomerInvoice.billing_profile))
            .options(joinedload(CustomerInvoice.invoice_party).joinedload(CustomerInvoiceParty.address))
            .options(joinedload(CustomerInvoice.job))
            .options(selectinload(CustomerInvoice.lines).joinedload(CustomerInvoiceLine.timesheet_line))
            .options(selectinload(CustomerInvoice.lines).joinedload(CustomerInvoiceLine.source_actual))
        )
