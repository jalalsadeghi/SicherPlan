"""SQLAlchemy repository for finance payroll configuration, exports, and archive flows."""

from __future__ import annotations

from datetime import date

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.employees.models import Employee, EmployeeAdvance, EmployeeAllowance, EmployeeTimeAccount, EmployeeTimeAccountTxn
from app.modules.finance.models import (
    ActualRecord,
    EmployeePayProfile,
    PayrollExportBatch,
    PayrollExportItem,
    PayrollPayslipArchive,
    PayrollSurchargeRule,
    PayrollTariffRate,
    PayrollTariffTable,
)
from app.modules.platform_services.docs_models import DocumentLink
from app.modules.platform_services.integration_models import IntegrationEndpoint
from app.modules.planning.models import Assignment, DemandGroup, Shift


class SqlAlchemyPayrollRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_tariff_tables(self, tenant_id: str, filters) -> list[PayrollTariffTable]:  # noqa: ANN001
        statement = (
            select(PayrollTariffTable)
            .where(PayrollTariffTable.tenant_id == tenant_id)
            .options(selectinload(PayrollTariffTable.rates), selectinload(PayrollTariffTable.surcharge_rules))
            .order_by(PayrollTariffTable.effective_from.desc(), PayrollTariffTable.code)
        )
        if filters is not None:
            if filters.region_code is not None:
                statement = statement.where(PayrollTariffTable.region_code == filters.region_code)
            if filters.status is not None:
                statement = statement.where(PayrollTariffTable.tariff_status_code == filters.status)
            if filters.active_on is not None:
                statement = statement.where(
                    PayrollTariffTable.effective_from <= filters.active_on,
                    or_(PayrollTariffTable.effective_until.is_(None), PayrollTariffTable.effective_until >= filters.active_on),
                )
            if not filters.include_archived:
                statement = statement.where(PayrollTariffTable.archived_at.is_(None))
        return list(self.session.scalars(statement).unique().all())

    def get_tariff_table(self, tenant_id: str, tariff_table_id: str) -> PayrollTariffTable | None:
        statement = (
            select(PayrollTariffTable)
            .where(PayrollTariffTable.tenant_id == tenant_id, PayrollTariffTable.id == tariff_table_id)
            .options(selectinload(PayrollTariffTable.rates), selectinload(PayrollTariffTable.surcharge_rules))
        )
        return self.session.scalars(statement).unique().one_or_none()

    def create_tariff_table(self, row: PayrollTariffTable) -> PayrollTariffTable:
        self.session.add(row)
        self.session.commit()
        return self.get_tariff_table(row.tenant_id, row.id) or row

    def save_tariff_table(self, row: PayrollTariffTable) -> PayrollTariffTable:
        self.session.add(row)
        self.session.commit()
        return self.get_tariff_table(row.tenant_id, row.id) or row

    def create_tariff_rate(self, row: PayrollTariffRate) -> PayrollTariffRate:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def create_surcharge_rule(self, row: PayrollSurchargeRule) -> PayrollSurchargeRule:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def find_overlapping_tariff_tables(
        self,
        tenant_id: str,
        region_code: str,
        effective_from: date,
        effective_until: date | None,
        *,
        exclude_id: str | None = None,
    ) -> list[PayrollTariffTable]:
        statement = select(PayrollTariffTable).where(
            PayrollTariffTable.tenant_id == tenant_id,
            PayrollTariffTable.region_code == region_code,
            PayrollTariffTable.archived_at.is_(None),
            or_(PayrollTariffTable.effective_until.is_(None), PayrollTariffTable.effective_until >= effective_from),
        )
        if effective_until is not None:
            statement = statement.where(PayrollTariffTable.effective_from <= effective_until)
        if exclude_id is not None:
            statement = statement.where(PayrollTariffTable.id != exclude_id)
        return list(self.session.scalars(statement).all())

    def list_active_tariff_tables(self, tenant_id: str, region_code: str, on_date: date) -> list[PayrollTariffTable]:
        statement = (
            select(PayrollTariffTable)
            .where(
                PayrollTariffTable.tenant_id == tenant_id,
                PayrollTariffTable.region_code == region_code,
                PayrollTariffTable.tariff_status_code == "active",
                PayrollTariffTable.archived_at.is_(None),
                PayrollTariffTable.effective_from <= on_date,
                or_(PayrollTariffTable.effective_until.is_(None), PayrollTariffTable.effective_until >= on_date),
            )
            .options(selectinload(PayrollTariffTable.rates), selectinload(PayrollTariffTable.surcharge_rules))
            .order_by(PayrollTariffTable.effective_from.desc(), PayrollTariffTable.created_at.desc())
        )
        return list(self.session.scalars(statement).unique().all())

    def list_employee_pay_profiles(self, tenant_id: str, filters) -> list[EmployeePayProfile]:  # noqa: ANN001
        statement = (
            select(EmployeePayProfile)
            .where(EmployeePayProfile.tenant_id == tenant_id)
            .options(joinedload(EmployeePayProfile.employee), joinedload(EmployeePayProfile.tariff_table))
            .order_by(EmployeePayProfile.effective_from.desc(), EmployeePayProfile.created_at.desc())
        )
        if filters is not None:
            if filters.employee_id is not None:
                statement = statement.where(EmployeePayProfile.employee_id == filters.employee_id)
            if filters.active_on is not None:
                statement = statement.where(
                    EmployeePayProfile.effective_from <= filters.active_on,
                    or_(EmployeePayProfile.effective_until.is_(None), EmployeePayProfile.effective_until >= filters.active_on),
                )
            if not filters.include_archived:
                statement = statement.where(EmployeePayProfile.archived_at.is_(None))
        return list(self.session.scalars(statement).unique().all())

    def get_employee_pay_profile(self, tenant_id: str, profile_id: str) -> EmployeePayProfile | None:
        statement = (
            select(EmployeePayProfile)
            .where(EmployeePayProfile.tenant_id == tenant_id, EmployeePayProfile.id == profile_id)
            .options(joinedload(EmployeePayProfile.employee), joinedload(EmployeePayProfile.tariff_table))
        )
        return self.session.scalars(statement).unique().one_or_none()

    def create_employee_pay_profile(self, row: EmployeePayProfile) -> EmployeePayProfile:
        self.session.add(row)
        self.session.commit()
        return self.get_employee_pay_profile(row.tenant_id, row.id) or row

    def save_employee_pay_profile(self, row: EmployeePayProfile) -> EmployeePayProfile:
        self.session.add(row)
        self.session.commit()
        return self.get_employee_pay_profile(row.tenant_id, row.id) or row

    def find_overlapping_employee_pay_profiles(
        self,
        tenant_id: str,
        employee_id: str,
        effective_from: date,
        effective_until: date | None,
        *,
        exclude_id: str | None = None,
    ) -> list[EmployeePayProfile]:
        statement = select(EmployeePayProfile).where(
            EmployeePayProfile.tenant_id == tenant_id,
            EmployeePayProfile.employee_id == employee_id,
            EmployeePayProfile.archived_at.is_(None),
            or_(EmployeePayProfile.effective_until.is_(None), EmployeePayProfile.effective_until >= effective_from),
        )
        if effective_until is not None:
            statement = statement.where(EmployeePayProfile.effective_from <= effective_until)
        if exclude_id is not None:
            statement = statement.where(EmployeePayProfile.id != exclude_id)
        return list(self.session.scalars(statement).all())

    def get_effective_employee_pay_profile(self, tenant_id: str, employee_id: str, on_date: date) -> EmployeePayProfile | None:
        statement = (
            select(EmployeePayProfile)
            .where(
                EmployeePayProfile.tenant_id == tenant_id,
                EmployeePayProfile.employee_id == employee_id,
                EmployeePayProfile.archived_at.is_(None),
                EmployeePayProfile.effective_from <= on_date,
                or_(EmployeePayProfile.effective_until.is_(None), EmployeePayProfile.effective_until >= on_date),
            )
            .options(joinedload(EmployeePayProfile.tariff_table).selectinload(PayrollTariffTable.rates))
            .order_by(EmployeePayProfile.effective_from.desc(), EmployeePayProfile.created_at.desc())
        )
        return self.session.scalars(statement).unique().first()

    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None:
        return self.session.scalars(select(Employee).where(Employee.tenant_id == tenant_id, Employee.id == employee_id)).one_or_none()

    def get_actual_record(self, tenant_id: str, actual_record_id: str) -> ActualRecord | None:
        statement = (
            select(ActualRecord)
            .where(ActualRecord.tenant_id == tenant_id, ActualRecord.id == actual_record_id)
            .options(
                joinedload(ActualRecord.employee),
                joinedload(ActualRecord.assignment).joinedload(Assignment.demand_group).joinedload(DemandGroup.function_type),
                joinedload(ActualRecord.assignment).joinedload(Assignment.demand_group).joinedload(DemandGroup.qualification_type),
                joinedload(ActualRecord.shift),
                selectinload(ActualRecord.allowances),
                selectinload(ActualRecord.reconciliations),
            )
        )
        return self.session.scalars(statement).unique().one_or_none()

    def list_approved_actual_records_for_period(self, tenant_id: str, period_start: date, period_end: date) -> list[ActualRecord]:
        statement = (
            select(ActualRecord)
            .where(
                ActualRecord.tenant_id == tenant_id,
                ActualRecord.is_current.is_(True),
                ActualRecord.archived_at.is_(None),
                ActualRecord.approval_stage_code == "finance_signed_off",
                ActualRecord.employee_id.is_not(None),
                func.date(ActualRecord.planned_start_at) >= period_start,
                func.date(ActualRecord.planned_start_at) <= period_end,
            )
            .options(
                joinedload(ActualRecord.employee),
                joinedload(ActualRecord.assignment).joinedload(Assignment.demand_group),
                joinedload(ActualRecord.shift),
                selectinload(ActualRecord.allowances),
                selectinload(ActualRecord.reconciliations),
            )
            .order_by(ActualRecord.planned_start_at, ActualRecord.created_at)
        )
        return list(self.session.scalars(statement).unique().all())

    def list_employee_allowances(self, tenant_id: str, employee_id: str, on_date: date) -> list[EmployeeAllowance]:
        statement = (
            select(EmployeeAllowance)
            .where(
                EmployeeAllowance.tenant_id == tenant_id,
                EmployeeAllowance.employee_id == employee_id,
                EmployeeAllowance.archived_at.is_(None),
                EmployeeAllowance.effective_from <= on_date,
                or_(EmployeeAllowance.effective_until.is_(None), EmployeeAllowance.effective_until >= on_date),
            )
            .order_by(EmployeeAllowance.effective_from.desc(), EmployeeAllowance.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def list_employee_advances(self, tenant_id: str, employee_id: str) -> list[EmployeeAdvance]:
        statement = (
            select(EmployeeAdvance)
            .where(
                EmployeeAdvance.tenant_id == tenant_id,
                EmployeeAdvance.employee_id == employee_id,
                EmployeeAdvance.archived_at.is_(None),
                EmployeeAdvance.status.in_(("approved", "disbursed")),
            )
            .order_by(EmployeeAdvance.requested_on.desc())
        )
        return list(self.session.scalars(statement).all())

    def list_employee_time_accounts(self, tenant_id: str, employee_id: str) -> list[EmployeeTimeAccount]:
        statement = (
            select(EmployeeTimeAccount)
            .where(
                EmployeeTimeAccount.tenant_id == tenant_id,
                EmployeeTimeAccount.employee_id == employee_id,
                EmployeeTimeAccount.archived_at.is_(None),
            )
            .options(selectinload(EmployeeTimeAccount.transactions))
            .order_by(EmployeeTimeAccount.account_type)
        )
        return list(self.session.scalars(statement).unique().all())

    def get_integration_endpoint(self, tenant_id: str, endpoint_id: str) -> IntegrationEndpoint | None:
        statement = select(IntegrationEndpoint).where(
            IntegrationEndpoint.tenant_id == tenant_id,
            IntegrationEndpoint.id == endpoint_id,
        )
        return self.session.scalars(statement).one_or_none()

    def find_integration_endpoint(self, tenant_id: str, provider_key: str, endpoint_type: str) -> IntegrationEndpoint | None:
        statement = select(IntegrationEndpoint).where(
            IntegrationEndpoint.tenant_id == tenant_id,
            IntegrationEndpoint.provider_key == provider_key,
            IntegrationEndpoint.endpoint_type == endpoint_type,
        )
        return self.session.scalars(statement).one_or_none()

    def list_export_batches(self, tenant_id: str, filters) -> list[PayrollExportBatch]:  # noqa: ANN001
        statement = (
            select(PayrollExportBatch)
            .where(PayrollExportBatch.tenant_id == tenant_id)
            .options(selectinload(PayrollExportBatch.items))
            .order_by(PayrollExportBatch.period_start.desc(), PayrollExportBatch.created_at.desc())
        )
        if filters is not None:
            if filters.provider_key is not None:
                statement = statement.where(PayrollExportBatch.provider_key == filters.provider_key)
            if filters.status is not None:
                statement = statement.where(PayrollExportBatch.batch_status_code == filters.status)
            if filters.period_start is not None:
                statement = statement.where(PayrollExportBatch.period_start >= filters.period_start)
            if filters.period_end is not None:
                statement = statement.where(PayrollExportBatch.period_end <= filters.period_end)
        return list(self.session.scalars(statement).unique().all())

    def get_export_batch(self, tenant_id: str, batch_id: str) -> PayrollExportBatch | None:
        statement = (
            select(PayrollExportBatch)
            .where(PayrollExportBatch.tenant_id == tenant_id, PayrollExportBatch.id == batch_id)
            .options(selectinload(PayrollExportBatch.items))
        )
        return self.session.scalars(statement).unique().one_or_none()

    def find_export_batch_by_source_hash(self, tenant_id: str, source_hash: str) -> PayrollExportBatch | None:
        statement = select(PayrollExportBatch).where(
            PayrollExportBatch.tenant_id == tenant_id,
            PayrollExportBatch.source_hash == source_hash,
            PayrollExportBatch.archived_at.is_(None),
        )
        return self.session.scalars(statement).one_or_none()

    def create_export_batch(self, row: PayrollExportBatch) -> PayrollExportBatch:
        self.session.add(row)
        self.session.commit()
        return self.get_export_batch(row.tenant_id, row.id) or row

    def save_export_batch(self, row: PayrollExportBatch) -> PayrollExportBatch:
        self.session.add(row)
        self.session.commit()
        return self.get_export_batch(row.tenant_id, row.id) or row

    def create_export_item(self, row: PayrollExportItem) -> PayrollExportItem:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_document_links_for_export_batch(self, tenant_id: str, batch_id: str) -> list[DocumentLink]:
        statement = select(DocumentLink).where(
            DocumentLink.tenant_id == tenant_id,
            DocumentLink.owner_type == "finance.payroll_export_batch",
            DocumentLink.owner_id == batch_id,
        )
        return list(self.session.scalars(statement).all())

    def list_payslip_archives(self, tenant_id: str, filters) -> list[PayrollPayslipArchive]:  # noqa: ANN001
        statement = (
            select(PayrollPayslipArchive)
            .where(PayrollPayslipArchive.tenant_id == tenant_id)
            .order_by(PayrollPayslipArchive.period_start.desc(), PayrollPayslipArchive.created_at.desc())
        )
        if filters is not None:
            if filters.employee_id is not None:
                statement = statement.where(PayrollPayslipArchive.employee_id == filters.employee_id)
            if filters.provider_key is not None:
                statement = statement.where(PayrollPayslipArchive.provider_key == filters.provider_key)
            if filters.period_start is not None:
                statement = statement.where(PayrollPayslipArchive.period_start >= filters.period_start)
            if filters.period_end is not None:
                statement = statement.where(PayrollPayslipArchive.period_end <= filters.period_end)
        return list(self.session.scalars(statement).all())

    def get_payslip_archive(self, tenant_id: str, archive_id: str) -> PayrollPayslipArchive | None:
        statement = select(PayrollPayslipArchive).where(
            PayrollPayslipArchive.tenant_id == tenant_id,
            PayrollPayslipArchive.id == archive_id,
        )
        return self.session.scalars(statement).one_or_none()

    def find_active_payslip_archive(
        self,
        tenant_id: str,
        employee_id: str,
        provider_key: str,
        period_start: date,
        period_end: date,
    ) -> PayrollPayslipArchive | None:
        statement = select(PayrollPayslipArchive).where(
            PayrollPayslipArchive.tenant_id == tenant_id,
            PayrollPayslipArchive.employee_id == employee_id,
            PayrollPayslipArchive.provider_key == provider_key,
            PayrollPayslipArchive.period_start == period_start,
            PayrollPayslipArchive.period_end == period_end,
            PayrollPayslipArchive.archive_status_code == "active",
            PayrollPayslipArchive.archived_at.is_(None),
        )
        return self.session.scalars(statement).one_or_none()

    def create_payslip_archive(self, row: PayrollPayslipArchive) -> PayrollPayslipArchive:
        self.session.add(row)
        self.session.commit()
        return self.get_payslip_archive(row.tenant_id, row.id) or row

    def save_payslip_archive(self, row: PayrollPayslipArchive) -> PayrollPayslipArchive:
        self.session.add(row)
        self.session.commit()
        return self.get_payslip_archive(row.tenant_id, row.id) or row
