"""Service layer for finance payroll configuration, export batches, and payslip archive."""

from __future__ import annotations

import base64
import csv
import hashlib
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from io import StringIO
from typing import Protocol

from app.errors import ApiException
from app.modules.finance.models import (
    EmployeePayProfile,
    PayrollExportBatch,
    PayrollExportItem,
    PayrollPayslipArchive,
    PayrollSurchargeRule,
    PayrollTariffRate,
    PayrollTariffTable,
)
from app.modules.finance.payroll_schemas import (
    EmployeePayProfileCreate,
    EmployeePayProfileFilter,
    EmployeePayProfileRead,
    EmployeePayProfileUpdate,
    PayrollActualResolutionRead,
    PayrollExportBatchFilter,
    PayrollExportBatchGenerate,
    PayrollExportBatchListItem,
    PayrollExportBatchRead,
    PayrollExportItemRead,
    PayrollPayslipArchiveCreate,
    PayrollPayslipArchiveFilter,
    PayrollPayslipArchiveRead,
    PayrollReconciliationFilter,
    PayrollReconciliationRowRead,
    PayrollResolvedAdvanceRead,
    PayrollResolvedAllowanceRead,
    PayrollResolvedSurchargeRead,
    PayrollResolvedTimeAccountRead,
    PayrollSurchargeRuleCreate,
    PayrollSurchargeRuleRead,
    PayrollTariffRateCreate,
    PayrollTariffRateRead,
    PayrollTariffTableCreate,
    PayrollTariffTableFilter,
    PayrollTariffTableListItem,
    PayrollTariffTableRead,
    PayrollTariffTableUpdate,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.integration_models import ImportExportJob, OutboxEvent


class PayrollRepository(Protocol):
    def list_tariff_tables(self, tenant_id: str, filters: PayrollTariffTableFilter | None = None) -> list[PayrollTariffTable]: ...
    def get_tariff_table(self, tenant_id: str, tariff_table_id: str) -> PayrollTariffTable | None: ...
    def create_tariff_table(self, row: PayrollTariffTable) -> PayrollTariffTable: ...
    def save_tariff_table(self, row: PayrollTariffTable) -> PayrollTariffTable: ...
    def create_tariff_rate(self, row: PayrollTariffRate) -> PayrollTariffRate: ...
    def create_surcharge_rule(self, row: PayrollSurchargeRule) -> PayrollSurchargeRule: ...
    def find_overlapping_tariff_tables(
        self,
        tenant_id: str,
        region_code: str,
        effective_from: date,
        effective_until: date | None,
        *,
        exclude_id: str | None = None,
    ) -> list[PayrollTariffTable]: ...
    def list_active_tariff_tables(self, tenant_id: str, region_code: str, on_date: date) -> list[PayrollTariffTable]: ...
    def list_employee_pay_profiles(self, tenant_id: str, filters: EmployeePayProfileFilter | None = None) -> list[EmployeePayProfile]: ...
    def get_employee_pay_profile(self, tenant_id: str, profile_id: str) -> EmployeePayProfile | None: ...
    def create_employee_pay_profile(self, row: EmployeePayProfile) -> EmployeePayProfile: ...
    def save_employee_pay_profile(self, row: EmployeePayProfile) -> EmployeePayProfile: ...
    def find_overlapping_employee_pay_profiles(
        self,
        tenant_id: str,
        employee_id: str,
        effective_from: date,
        effective_until: date | None,
        *,
        exclude_id: str | None = None,
    ) -> list[EmployeePayProfile]: ...
    def get_effective_employee_pay_profile(self, tenant_id: str, employee_id: str, on_date: date) -> EmployeePayProfile | None: ...
    def get_employee(self, tenant_id: str, employee_id: str): ...  # noqa: ANN001
    def get_actual_record(self, tenant_id: str, actual_record_id: str): ...  # noqa: ANN001
    def list_approved_actual_records_for_period(self, tenant_id: str, period_start: date, period_end: date): ...  # noqa: ANN001
    def list_employee_allowances(self, tenant_id: str, employee_id: str, on_date: date): ...  # noqa: ANN001
    def list_employee_advances(self, tenant_id: str, employee_id: str): ...  # noqa: ANN001
    def list_employee_time_accounts(self, tenant_id: str, employee_id: str): ...  # noqa: ANN001
    def get_integration_endpoint(self, tenant_id: str, endpoint_id: str): ...  # noqa: ANN001
    def find_integration_endpoint(self, tenant_id: str, provider_key: str, endpoint_type: str): ...  # noqa: ANN001
    def list_export_batches(self, tenant_id: str, filters: PayrollExportBatchFilter | None = None) -> list[PayrollExportBatch]: ...
    def get_export_batch(self, tenant_id: str, batch_id: str) -> PayrollExportBatch | None: ...
    def find_export_batch_by_source_hash(self, tenant_id: str, source_hash: str) -> PayrollExportBatch | None: ...
    def create_export_batch(self, row: PayrollExportBatch) -> PayrollExportBatch: ...
    def save_export_batch(self, row: PayrollExportBatch) -> PayrollExportBatch: ...
    def create_export_item(self, row: PayrollExportItem) -> PayrollExportItem: ...
    def list_document_links_for_export_batch(self, tenant_id: str, batch_id: str): ...  # noqa: ANN001
    def list_payslip_archives(self, tenant_id: str, filters: PayrollPayslipArchiveFilter | None = None) -> list[PayrollPayslipArchive]: ...
    def get_payslip_archive(self, tenant_id: str, archive_id: str) -> PayrollPayslipArchive | None: ...
    def find_active_payslip_archive(
        self,
        tenant_id: str,
        employee_id: str,
        provider_key: str,
        period_start: date,
        period_end: date,
    ) -> PayrollPayslipArchive | None: ...
    def create_payslip_archive(self, row: PayrollPayslipArchive) -> PayrollPayslipArchive: ...
    def save_payslip_archive(self, row: PayrollPayslipArchive) -> PayrollPayslipArchive: ...


class IntegrationJobRepository(Protocol):
    def create_job_and_outbox(self, job: ImportExportJob, outbox_event: OutboxEvent) -> ImportExportJob: ...
    def save_job(self, row: ImportExportJob) -> ImportExportJob: ...


@dataclass(slots=True)
class RenderedPayrollArtifact:
    file_name: str
    content_type: str
    content: bytes
    metadata_json: dict[str, object]


class PayrollExportAdapter(Protocol):
    provider_key: str

    def render_batch(self, batch: PayrollExportBatch, items: list[PayrollExportItemRead]) -> RenderedPayrollArtifact: ...


class CsvPayrollExportAdapter:
    provider_key = "generic_csv"

    def render_batch(self, batch: PayrollExportBatch, items: list[PayrollExportItemRead]) -> RenderedPayrollArtifact:
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "batch_no",
                "provider_key",
                "actual_record_id",
                "employee_id",
                "pay_code",
                "quantity",
                "unit_code",
                "amount_total",
                "currency_code",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "batch_no": batch.batch_no,
                    "provider_key": batch.provider_key,
                    "actual_record_id": item.actual_record_id,
                    "employee_id": item.employee_id or "",
                    "pay_code": item.pay_code,
                    "quantity": item.quantity,
                    "unit_code": item.unit_code,
                    "amount_total": item.amount_total,
                    "currency_code": item.currency_code,
                }
            )
        return RenderedPayrollArtifact(
            file_name=f"{batch.batch_no}.csv",
            content_type="text/csv",
            content=output.getvalue().encode("utf-8"),
            metadata_json={"provider_key": batch.provider_key, "item_count": len(items)},
        )


class PayrollService:
    def __init__(
        self,
        *,
        repository: PayrollRepository,
        integration_repository: IntegrationJobRepository,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
        adapters: dict[str, PayrollExportAdapter] | None = None,
    ) -> None:
        self.repository = repository
        self.integration_repository = integration_repository
        self.document_service = document_service
        self.audit_service = audit_service
        self.adapters = adapters or {"generic_csv": CsvPayrollExportAdapter()}

    def list_tariff_tables(
        self,
        tenant_id: str,
        filters: PayrollTariffTableFilter | None,
        actor: RequestAuthorizationContext,
    ) -> list[PayrollTariffTableListItem]:
        self._require_payroll_read(actor, tenant_id)
        return [self._map_tariff_table_list_item(row) for row in self.repository.list_tariff_tables(tenant_id, filters)]

    def create_tariff_table(
        self,
        tenant_id: str,
        payload: PayrollTariffTableCreate,
        actor: RequestAuthorizationContext,
    ) -> PayrollTariffTableRead:
        self._require_payroll_write(actor, tenant_id)
        self._ensure_tariff_table_overlap_free(tenant_id, payload.region_code, payload.effective_from, payload.effective_until)
        row = self.repository.create_tariff_table(
            PayrollTariffTable(
                tenant_id=tenant_id,
                code=payload.code.strip(),
                title=payload.title.strip(),
                region_code=payload.region_code.strip(),
                tariff_status_code=payload.status,
                effective_from=payload.effective_from,
                effective_until=payload.effective_until,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_audit(actor, tenant_id, "finance.payroll.tariff_table.created", "finance.payroll_tariff_table", row.id)
        return self._map_tariff_table_read(row)

    def update_tariff_table(
        self,
        tenant_id: str,
        tariff_table_id: str,
        payload: PayrollTariffTableUpdate,
        actor: RequestAuthorizationContext,
    ) -> PayrollTariffTableRead:
        self._require_payroll_write(actor, tenant_id)
        row = self._require_tariff_table(tenant_id, tariff_table_id)
        self._require_version(row.version_no, payload.version_no, "tariff_table")
        next_region = payload.region_code if payload.region_code is not None else row.region_code
        next_from = payload.effective_from if payload.effective_from is not None else row.effective_from
        next_until = payload.effective_until if payload.effective_until is not None else row.effective_until
        self._ensure_tariff_table_overlap_free(tenant_id, next_region, next_from, next_until, exclude_id=row.id)
        before = row.version_no
        for field_name in ("title", "region_code", "effective_from", "effective_until", "notes"):
            value = getattr(payload, field_name)
            if value is not None:
                setattr(row, field_name, value.strip() if isinstance(value, str) else value)
        if payload.status is not None:
            row.tariff_status_code = payload.status
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        row = self.repository.save_tariff_table(row)
        self._record_audit(
            actor,
            tenant_id,
            "finance.payroll.tariff_table.updated",
            "finance.payroll_tariff_table",
            row.id,
            metadata_json={"previous_version_no": before, "version_no": row.version_no},
        )
        return self._map_tariff_table_read(row)

    def add_tariff_rate(
        self,
        tenant_id: str,
        tariff_table_id: str,
        payload: PayrollTariffRateCreate,
        actor: RequestAuthorizationContext,
    ) -> PayrollTariffTableRead:
        self._require_payroll_write(actor, tenant_id)
        table = self._require_tariff_table(tenant_id, tariff_table_id)
        self._ensure_rate_dimensions_unique(table, payload)
        self.repository.create_tariff_rate(
            PayrollTariffRate(
                tenant_id=tenant_id,
                tariff_table_id=table.id,
                function_type_id=payload.function_type_id,
                qualification_type_id=payload.qualification_type_id,
                employment_type_code=self._normalize_optional(payload.employment_type_code),
                pay_unit_code=payload.pay_unit_code.strip(),
                currency_code=payload.currency_code.upper(),
                base_amount=payload.base_amount,
                payroll_code=self._normalize_optional(payload.payroll_code),
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        return self._map_tariff_table_read(self._require_tariff_table(tenant_id, tariff_table_id))

    def add_surcharge_rule(
        self,
        tenant_id: str,
        tariff_table_id: str,
        payload: PayrollSurchargeRuleCreate,
        actor: RequestAuthorizationContext,
    ) -> PayrollTariffTableRead:
        self._require_payroll_write(actor, tenant_id)
        table = self._require_tariff_table(tenant_id, tariff_table_id)
        self._validate_surcharge_rule(payload)
        self._ensure_surcharge_dimensions_unique(table, payload)
        self.repository.create_surcharge_rule(
            PayrollSurchargeRule(
                tenant_id=tenant_id,
                tariff_table_id=table.id,
                surcharge_type_code=payload.surcharge_type_code.strip(),
                custom_code=self._normalize_optional(payload.custom_code),
                weekday_mask=payload.weekday_mask,
                start_minute_local=payload.start_minute_local,
                end_minute_local=payload.end_minute_local,
                holiday_region_code=self._normalize_optional(payload.holiday_region_code),
                function_type_id=payload.function_type_id,
                qualification_type_id=payload.qualification_type_id,
                employment_type_code=self._normalize_optional(payload.employment_type_code),
                percent_value=payload.percent_value,
                fixed_amount=payload.fixed_amount,
                currency_code=None if payload.currency_code is None else payload.currency_code.upper(),
                payroll_code=self._normalize_optional(payload.payroll_code),
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        return self._map_tariff_table_read(self._require_tariff_table(tenant_id, tariff_table_id))

    def list_employee_pay_profiles(
        self,
        tenant_id: str,
        filters: EmployeePayProfileFilter | None,
        actor: RequestAuthorizationContext,
    ) -> list[EmployeePayProfileRead]:
        self._require_payroll_read(actor, tenant_id)
        return [EmployeePayProfileRead.model_validate(row) for row in self.repository.list_employee_pay_profiles(tenant_id, filters)]

    def create_employee_pay_profile(
        self,
        tenant_id: str,
        payload: EmployeePayProfileCreate,
        actor: RequestAuthorizationContext,
    ) -> EmployeePayProfileRead:
        self._require_payroll_write(actor, tenant_id)
        self._require_employee(tenant_id, payload.employee_id)
        self._ensure_pay_profile_overlap_free(tenant_id, payload.employee_id, payload.effective_from, payload.effective_until)
        if payload.tariff_table_id is not None:
            self._require_tariff_table(tenant_id, payload.tariff_table_id)
        row = self.repository.create_employee_pay_profile(
            EmployeePayProfile(
                tenant_id=tenant_id,
                employee_id=payload.employee_id,
                tariff_table_id=payload.tariff_table_id,
                payroll_region_code=payload.payroll_region_code.strip(),
                employment_type_code=payload.employment_type_code.strip(),
                pay_cycle_code=payload.pay_cycle_code.strip(),
                pay_unit_code=payload.pay_unit_code.strip(),
                currency_code=payload.currency_code.upper(),
                export_employee_code=self._normalize_optional(payload.export_employee_code),
                cost_center_code=self._normalize_optional(payload.cost_center_code),
                base_rate_override=payload.base_rate_override,
                override_reason=self._normalize_optional(payload.override_reason),
                effective_from=payload.effective_from,
                effective_until=payload.effective_until,
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_audit(actor, tenant_id, "finance.payroll.pay_profile.created", "finance.employee_pay_profile", row.id)
        return EmployeePayProfileRead.model_validate(row)

    def update_employee_pay_profile(
        self,
        tenant_id: str,
        profile_id: str,
        payload: EmployeePayProfileUpdate,
        actor: RequestAuthorizationContext,
    ) -> EmployeePayProfileRead:
        self._require_payroll_write(actor, tenant_id)
        row = self._require_pay_profile(tenant_id, profile_id)
        self._require_version(row.version_no, payload.version_no, "employee_pay_profile")
        next_from = payload.effective_from if payload.effective_from is not None else row.effective_from
        next_until = payload.effective_until if payload.effective_until is not None else row.effective_until
        self._ensure_pay_profile_overlap_free(tenant_id, row.employee_id, next_from, next_until, exclude_id=row.id)
        if payload.tariff_table_id is not None:
            self._require_tariff_table(tenant_id, payload.tariff_table_id)
        for field_name in (
            "tariff_table_id",
            "payroll_region_code",
            "employment_type_code",
            "pay_cycle_code",
            "pay_unit_code",
            "currency_code",
            "export_employee_code",
            "cost_center_code",
            "base_rate_override",
            "override_reason",
            "effective_from",
            "effective_until",
            "notes",
        ):
            value = getattr(payload, field_name)
            if value is not None:
                setattr(row, field_name, value.upper() if field_name == "currency_code" else value)
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        row = self.repository.save_employee_pay_profile(row)
        self._record_audit(actor, tenant_id, "finance.payroll.pay_profile.updated", "finance.employee_pay_profile", row.id)
        return EmployeePayProfileRead.model_validate(row)

    def resolve_actual(
        self,
        tenant_id: str,
        actual_record_id: str,
        actor: RequestAuthorizationContext,
    ) -> PayrollActualResolutionRead:
        self._require_payroll_read(actor, tenant_id)
        actual = self._require_actual(tenant_id, actual_record_id)
        if actual.employee_id is None:
            raise ApiException(409, "finance.payroll.actual.employee_required", "errors.finance.payroll.actual.employee_required")
        if actual.approval_stage_code != "finance_signed_off":
            raise ApiException(409, "finance.payroll.actual.not_approved", "errors.finance.payroll.actual.not_approved")
        basis_date = (actual.planned_start_at or actual.derived_at).date()
        profile = self.repository.get_effective_employee_pay_profile(tenant_id, actual.employee_id, basis_date)
        table = None
        if profile is not None and profile.tariff_table_id is not None:
            table = self.repository.get_tariff_table(tenant_id, profile.tariff_table_id)
        if table is None:
            region_code = profile.payroll_region_code if profile is not None else "default"
            active_tables = self.repository.list_active_tariff_tables(tenant_id, region_code, basis_date)
            table = active_tables[0] if active_tables else None
        if table is None:
            raise ApiException(404, "finance.payroll.tariff_table.not_found", "errors.finance.payroll.tariff_table.not_found")

        function_type_id = getattr(actual.assignment.demand_group, "function_type_id", None) if actual.assignment and actual.assignment.demand_group else None
        qualification_type_id = getattr(actual.assignment.demand_group, "qualification_type_id", None) if actual.assignment and actual.assignment.demand_group else None
        employment_type_code = profile.employment_type_code if profile is not None else None
        rate = self._resolve_tariff_rate(table, function_type_id, qualification_type_id, employment_type_code)
        if rate is None and profile is None:
            raise ApiException(404, "finance.payroll.tariff_rate.not_found", "errors.finance.payroll.tariff_rate.not_found")
        base_amount = Decimal(str(profile.base_rate_override)) if profile and profile.base_rate_override is not None else Decimal(str(rate.base_amount if rate is not None else 0))
        unit_code = profile.pay_unit_code if profile is not None else (rate.pay_unit_code if rate is not None else "hour")
        quantity = self._derive_quantity(actual.payable_minutes, unit_code)
        currency_code = profile.currency_code if profile is not None else (rate.currency_code if rate is not None else "EUR")
        allowances = self._resolve_allowances(actual, basis_date)
        advances = self._resolve_advances(tenant_id, actual.employee_id)
        time_accounts = self._resolve_time_accounts(tenant_id, actual.employee_id)
        surcharges = self._resolve_surcharges(
            table,
            actual,
            employment_type_code,
            function_type_id,
            qualification_type_id,
            currency_code,
            unit_code,
            base_rate_amount=base_amount,
        )
        pay_code = None
        if profile is not None and profile.export_employee_code:
            pay_code = profile.export_employee_code
        elif rate is not None and rate.payroll_code:
            pay_code = rate.payroll_code
        else:
            pay_code = "BASE"
        return PayrollActualResolutionRead(
            actual_record_id=actual.id,
            employee_id=actual.employee_id,
            pay_profile_id=None if profile is None else profile.id,
            tariff_table_id=table.id,
            tariff_rate_id=None if rate is None else rate.id,
            pay_code=pay_code,
            quantity=float(quantity),
            unit_code=unit_code,
            base_amount=float((base_amount * quantity).quantize(Decimal("0.01"))),
            currency_code=currency_code,
            minutes_basis=actual.payable_minutes,
            allowances=allowances,
            advances=advances,
            time_accounts=time_accounts,
            surcharges=surcharges,
            source_ref_json={
                "assignment_id": actual.assignment_id,
                "shift_id": actual.shift_id,
                "function_type_id": function_type_id,
                "qualification_type_id": qualification_type_id,
            },
        )

    def list_export_batches(
        self,
        tenant_id: str,
        filters: PayrollExportBatchFilter | None,
        actor: RequestAuthorizationContext,
    ) -> list[PayrollExportBatchListItem]:
        self._require_payroll_read(actor, tenant_id)
        return [self._map_export_batch_list_item(row) for row in self.repository.list_export_batches(tenant_id, filters)]

    def get_export_batch(
        self,
        tenant_id: str,
        batch_id: str,
        actor: RequestAuthorizationContext,
    ) -> PayrollExportBatchRead:
        self._require_payroll_read(actor, tenant_id)
        batch = self._require_export_batch(tenant_id, batch_id)
        return self._map_export_batch_read(batch)

    def generate_export_batch(
        self,
        tenant_id: str,
        payload: PayrollExportBatchGenerate,
        actor: RequestAuthorizationContext,
    ) -> PayrollExportBatchRead:
        self._require_payroll_export(actor, tenant_id)
        actuals = self.repository.list_approved_actual_records_for_period(tenant_id, payload.period_start, payload.period_end)
        eligible_resolutions = [self.resolve_actual(tenant_id, row.id, actor) for row in actuals]
        eligible_resolutions = [row for row in eligible_resolutions if row.quantity > 0]
        if not eligible_resolutions:
            raise ApiException(409, "finance.payroll.export.no_eligible_actuals", "errors.finance.payroll.export.no_eligible_actuals")
        source_hash = self._build_source_hash(payload.provider_key, payload.period_start, payload.period_end, eligible_resolutions)
        existing = self.repository.find_export_batch_by_source_hash(tenant_id, source_hash)
        if existing is not None:
            return self._map_export_batch_read(existing)

        endpoint = None
        if payload.endpoint_id is not None:
            endpoint = self.repository.get_integration_endpoint(tenant_id, payload.endpoint_id)
        if endpoint is None:
            endpoint = self.repository.find_integration_endpoint(tenant_id, payload.provider_key, "payroll_export")
        batch = self.repository.create_export_batch(
            PayrollExportBatch(
                tenant_id=tenant_id,
                batch_no=self._next_batch_no(payload.provider_key, payload.period_start, payload.period_end),
                provider_key=payload.provider_key,
                endpoint_id=None if endpoint is None else endpoint.id,
                batch_status_code="generated",
                period_start=payload.period_start,
                period_end=payload.period_end,
                source_hash=source_hash,
                item_count=0,
                total_amount=0,
                currency_code="EUR",
                generated_at=datetime.now(UTC),
                notes=self._normalize_optional(payload.notes),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        total_amount = Decimal("0.00")
        items: list[PayrollExportItemRead] = []
        for resolution in eligible_resolutions:
            amount_total = Decimal(str(resolution.base_amount))
            for surcharge in resolution.surcharges:
                amount_total += Decimal(str(surcharge.amount_total))
            for allowance in resolution.allowances:
                amount_total += Decimal(str(allowance.amount))
            item = self.repository.create_export_item(
                PayrollExportItem(
                    tenant_id=tenant_id,
                    batch_id=batch.id,
                    actual_record_id=resolution.actual_record_id,
                    employee_id=resolution.employee_id,
                    pay_code=resolution.pay_code,
                    description="Payroll basis export",
                    quantity=resolution.quantity,
                    unit_code=resolution.unit_code,
                    amount_total=float(amount_total),
                    currency_code=resolution.currency_code,
                    payload_json={
                        "allowances": [row.model_dump() for row in resolution.allowances],
                        "advances": [row.model_dump() for row in resolution.advances],
                        "time_accounts": [row.model_dump() for row in resolution.time_accounts],
                        "surcharges": [row.model_dump() for row in resolution.surcharges],
                    },
                    source_ref_json=dict(resolution.source_ref_json),
                    created_by_user_id=actor.user_id,
                    updated_by_user_id=actor.user_id,
                )
            )
            item_read = PayrollExportItemRead.model_validate(item)
            items.append(item_read)
            total_amount += Decimal(str(item.amount_total))
        batch.item_count = len(items)
        batch.total_amount = float(total_amount.quantize(Decimal("0.01")))
        batch.currency_code = items[0].currency_code if items else "EUR"
        batch.updated_by_user_id = actor.user_id
        batch.version_no += 1
        batch = self.repository.save_export_batch(batch)

        artifact = self._render_export_artifact(batch, items)
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=f"Payroll export {batch.batch_no}",
                source_module="finance.payroll",
                source_label="payroll_export_batch",
                metadata_json={"provider_key": batch.provider_key, "batch_id": batch.id},
            ),
            actor,
        )
        self.document_service.add_document_version(
            tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=artifact.file_name,
                content_type=artifact.content_type,
                content_base64=base64.b64encode(artifact.content).decode("ascii"),
                metadata_json=artifact.metadata_json,
                is_revision_safe_pdf=False,
            ),
            actor,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type="finance.payroll_export_batch",
                owner_id=batch.id,
                relation_type="generated_output",
                label=batch.batch_no,
                metadata_json={"provider_key": batch.provider_key},
            ),
            actor,
        )
        job = self.integration_repository.create_job_and_outbox(
            ImportExportJob(
                tenant_id=tenant_id,
                endpoint_id=None if endpoint is None else endpoint.id,
                job_direction="outbound",
                job_type="payroll_export",
                request_payload_json={
                    "batch_id": batch.id,
                    "provider_key": batch.provider_key,
                    "document_id": document.id,
                },
                result_summary_json={"item_count": len(items)},
                requested_by_user_id=actor.user_id,
                started_at=datetime.now(UTC),
            ),
            OutboxEvent(
                tenant_id=tenant_id,
                endpoint_id=None if endpoint is None else endpoint.id,
                aggregate_type="finance.payroll_export_batch",
                aggregate_id=batch.id,
                event_type="finance.payroll.export.queued",
                topic="payroll.export.dispatch",
                payload_json={
                    "batch_id": batch.id,
                    "document_id": document.id,
                    "provider_key": batch.provider_key,
                },
                dedupe_key=f"finance.payroll.export:{batch.source_hash}",
                status="pending",
            ),
        )
        batch.job_id = job.id
        batch.batch_status_code = "queued"
        batch.queued_at = datetime.now(UTC)
        batch.updated_by_user_id = actor.user_id
        batch.version_no += 1
        batch = self.repository.save_export_batch(batch)
        self._record_audit(
            actor,
            tenant_id,
            "finance.payroll.export_batch.generated",
            "finance.payroll_export_batch",
            batch.id,
            metadata_json={"job_id": job.id, "document_id": document.id},
        )
        return self._map_export_batch_read(batch)

    def list_payslip_archives(
        self,
        tenant_id: str,
        filters: PayrollPayslipArchiveFilter | None,
        actor: RequestAuthorizationContext,
    ) -> list[PayrollPayslipArchiveRead]:
        self._require_payroll_read(actor, tenant_id)
        return [PayrollPayslipArchiveRead.model_validate(row) for row in self.repository.list_payslip_archives(tenant_id, filters)]

    def archive_payslip(
        self,
        tenant_id: str,
        payload: PayrollPayslipArchiveCreate,
        actor: RequestAuthorizationContext,
    ) -> PayrollPayslipArchiveRead:
        self._require_payroll_write(actor, tenant_id)
        self._require_employee(tenant_id, payload.employee_id)
        if payload.export_batch_id is not None:
            self._require_export_batch(tenant_id, payload.export_batch_id)
        active = self.repository.find_active_payslip_archive(
            tenant_id,
            payload.employee_id,
            payload.provider_key,
            payload.period_start,
            payload.period_end,
        )
        if active is not None:
            active.archive_status_code = "superseded"
            active.updated_by_user_id = actor.user_id
            active.version_no += 1
            self.repository.save_payslip_archive(active)
        row = self.repository.create_payslip_archive(
            PayrollPayslipArchive(
                tenant_id=tenant_id,
                employee_id=payload.employee_id,
                export_batch_id=payload.export_batch_id,
                provider_key=payload.provider_key,
                period_start=payload.period_start,
                period_end=payload.period_end,
                archive_status_code="active",
                source_document_id=payload.source_document_id,
                notes=self._normalize_optional(payload.notes),
                superseded_by_archive_id=None,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        if active is not None:
            active.superseded_by_archive_id = row.id
            self.repository.save_payslip_archive(active)
        self.document_service.add_document_link(
            tenant_id,
            payload.source_document_id,
            DocumentLinkCreate(
                owner_type="finance.payroll_payslip_archive",
                owner_id=row.id,
                relation_type="archive_source",
                label=f"{payload.provider_key}:{payload.period_start.isoformat()}",
                metadata_json={"employee_id": payload.employee_id},
            ),
            actor,
        )
        self._record_audit(actor, tenant_id, "finance.payroll.payslip_archived", "finance.payroll_payslip_archive", row.id)
        return PayrollPayslipArchiveRead.model_validate(row)

    def list_reconciliation_rows(
        self,
        tenant_id: str,
        filters: PayrollReconciliationFilter,
        actor: RequestAuthorizationContext,
    ) -> list[PayrollReconciliationRowRead]:
        self._require_payroll_read(actor, tenant_id)
        actuals = self.repository.list_approved_actual_records_for_period(tenant_id, filters.period_start, filters.period_end)
        grouped: dict[str, PayrollReconciliationRowRead] = {}
        for actual in actuals:
            if actual.employee_id is None:
                continue
            if filters.employee_id is not None and actual.employee_id != filters.employee_id:
                continue
            resolution = self.resolve_actual(tenant_id, actual.id, actor)
            row = grouped.get(actual.employee_id)
            if row is None:
                profile = self.repository.get_effective_employee_pay_profile(
                    tenant_id,
                    actual.employee_id,
                    (actual.planned_start_at or actual.derived_at).date(),
                )
                row = PayrollReconciliationRowRead(
                    employee_id=actual.employee_id,
                    export_employee_code=None if profile is None else profile.export_employee_code,
                    pay_profile_id=None if profile is None else profile.id,
                    approved_actual_count=0,
                    exported_item_count=0,
                    archived_payslip_count=0,
                    payable_minutes=0,
                    exported_amount_total=0,
                    allowance_amount_total=0,
                    outstanding_advance_total=0,
                    overtime_balance_minutes=0,
                    missing_export=True,
                    missing_payslip=True,
                    mismatch_codes=[],
                )
                grouped[actual.employee_id] = row
            row.approved_actual_count += 1
            row.payable_minutes += actual.payable_minutes
            row.allowance_amount_total += sum(item.amount for item in resolution.allowances)
            row.outstanding_advance_total = sum(item.outstanding_amount for item in resolution.advances)
            overtime_row = next((item for item in resolution.time_accounts if item.account_type == "overtime"), None)
            row.overtime_balance_minutes = 0 if overtime_row is None else overtime_row.balance_minutes

        batches = self.repository.list_export_batches(
            tenant_id,
            PayrollExportBatchFilter(period_start=filters.period_start, period_end=filters.period_end),
        )
        for batch in batches:
            for item in batch.items:
                if item.employee_id is None or item.employee_id not in grouped:
                    continue
                row = grouped[item.employee_id]
                row.exported_item_count += 1
                row.exported_amount_total += item.amount_total
                row.missing_export = False

        archives = self.repository.list_payslip_archives(
            tenant_id,
            PayrollPayslipArchiveFilter(
                employee_id=filters.employee_id,
                period_start=filters.period_start,
                period_end=filters.period_end,
            ),
        )
        for archive in archives:
            if archive.employee_id not in grouped or archive.archive_status_code != "active":
                continue
            row = grouped[archive.employee_id]
            row.archived_payslip_count += 1
            row.missing_payslip = False

        for row in grouped.values():
            if row.missing_export:
                row.mismatch_codes.append("missing_export_batch")
            if row.missing_payslip:
                row.mismatch_codes.append("missing_payslip_archive")
            if row.exported_item_count > 0 and row.approved_actual_count != row.exported_item_count:
                row.mismatch_codes.append("export_item_count_mismatch")
        return sorted(grouped.values(), key=lambda row: row.employee_id)

    def _require_tariff_table(self, tenant_id: str, tariff_table_id: str) -> PayrollTariffTable:
        row = self.repository.get_tariff_table(tenant_id, tariff_table_id)
        if row is None:
            raise ApiException(404, "finance.payroll.tariff_table.not_found", "errors.finance.payroll.tariff_table.not_found")
        return row

    def _require_pay_profile(self, tenant_id: str, profile_id: str) -> EmployeePayProfile:
        row = self.repository.get_employee_pay_profile(tenant_id, profile_id)
        if row is None:
            raise ApiException(404, "finance.payroll.pay_profile.not_found", "errors.finance.payroll.pay_profile.not_found")
        return row

    def _require_actual(self, tenant_id: str, actual_record_id: str):
        row = self.repository.get_actual_record(tenant_id, actual_record_id)
        if row is None:
            raise ApiException(404, "finance.actual.not_found", "errors.finance.actual.not_found")
        return row

    def _require_export_batch(self, tenant_id: str, batch_id: str) -> PayrollExportBatch:
        row = self.repository.get_export_batch(tenant_id, batch_id)
        if row is None:
            raise ApiException(404, "finance.payroll.export_batch.not_found", "errors.finance.payroll.export_batch.not_found")
        return row

    def _require_employee(self, tenant_id: str, employee_id: str) -> None:
        if self.repository.get_employee(tenant_id, employee_id) is None:
            raise ApiException(404, "employees.employee.not_found", "errors.employees.employee.not_found")

    def _ensure_tariff_table_overlap_free(
        self,
        tenant_id: str,
        region_code: str,
        effective_from: date,
        effective_until: date | None,
        *,
        exclude_id: str | None = None,
    ) -> None:
        overlaps = self.repository.find_overlapping_tariff_tables(
            tenant_id,
            region_code,
            effective_from,
            effective_until,
            exclude_id=exclude_id,
        )
        if overlaps:
            raise ApiException(409, "finance.payroll.tariff_table.overlap", "errors.finance.payroll.tariff_table.overlap")

    def _ensure_pay_profile_overlap_free(
        self,
        tenant_id: str,
        employee_id: str,
        effective_from: date,
        effective_until: date | None,
        *,
        exclude_id: str | None = None,
    ) -> None:
        overlaps = self.repository.find_overlapping_employee_pay_profiles(
            tenant_id,
            employee_id,
            effective_from,
            effective_until,
            exclude_id=exclude_id,
        )
        if overlaps:
            raise ApiException(409, "finance.payroll.pay_profile.overlap", "errors.finance.payroll.pay_profile.overlap")

    @staticmethod
    def _ensure_rate_dimensions_unique(table: PayrollTariffTable, payload: PayrollTariffRateCreate) -> None:
        key = (
            payload.function_type_id,
            payload.qualification_type_id,
            payload.employment_type_code,
            payload.pay_unit_code,
        )
        existing = {
            (row.function_type_id, row.qualification_type_id, row.employment_type_code, row.pay_unit_code)
            for row in table.rates
        }
        if key in existing:
            raise ApiException(409, "finance.payroll.tariff_rate.duplicate", "errors.finance.payroll.tariff_rate.duplicate")

    @staticmethod
    def _ensure_surcharge_dimensions_unique(table: PayrollTariffTable, payload: PayrollSurchargeRuleCreate) -> None:
        key = (
            payload.surcharge_type_code,
            payload.custom_code,
            payload.weekday_mask,
            payload.start_minute_local,
            payload.end_minute_local,
            payload.function_type_id,
            payload.qualification_type_id,
            payload.employment_type_code,
            payload.holiday_region_code,
        )
        existing = {
            (
                row.surcharge_type_code,
                row.custom_code,
                row.weekday_mask,
                row.start_minute_local,
                row.end_minute_local,
                row.function_type_id,
                row.qualification_type_id,
                row.employment_type_code,
                row.holiday_region_code,
            )
            for row in table.surcharge_rules
        }
        if key in existing:
            raise ApiException(409, "finance.payroll.surcharge_rule.duplicate", "errors.finance.payroll.surcharge_rule.duplicate")

    @staticmethod
    def _validate_surcharge_rule(payload: PayrollSurchargeRuleCreate) -> None:
        if payload.end_minute_local <= payload.start_minute_local:
            raise ApiException(400, "finance.payroll.surcharge_rule.window_invalid", "errors.finance.payroll.surcharge_rule.window_invalid")
        if payload.percent_value is None and payload.fixed_amount is None:
            raise ApiException(400, "finance.payroll.surcharge_rule.amount_required", "errors.finance.payroll.surcharge_rule.amount_required")

    @staticmethod
    def _derive_quantity(minutes: int, unit_code: str) -> Decimal:
        if unit_code == "hour":
            return (Decimal(minutes) / Decimal(60)).quantize(Decimal("0.01"))
        if unit_code == "day":
            return (Decimal(minutes) / Decimal(480)).quantize(Decimal("0.01"))
        return Decimal(minutes)

    @staticmethod
    def _specificity(value: object | None) -> int:
        return 1 if value is not None else 0

    def _resolve_tariff_rate(
        self,
        table: PayrollTariffTable,
        function_type_id: str | None,
        qualification_type_id: str | None,
        employment_type_code: str | None,
    ) -> PayrollTariffRate | None:
        candidates: list[tuple[int, PayrollTariffRate]] = []
        for row in table.rates:
            if row.function_type_id not in (None, function_type_id):
                continue
            if row.qualification_type_id not in (None, qualification_type_id):
                continue
            if row.employment_type_code not in (None, employment_type_code):
                continue
            score = (
                self._specificity(row.function_type_id) * 100
                + self._specificity(row.qualification_type_id) * 10
                + self._specificity(row.employment_type_code)
            )
            candidates.append((score, row))
        candidates.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
        return None if not candidates else candidates[0][1]

    def _resolve_allowances(self, actual, basis_date: date) -> list[PayrollResolvedAllowanceRead]:  # noqa: ANN001
        rows = []
        hr_rows = self.repository.list_employee_allowances(actual.tenant_id, actual.employee_id, basis_date)
        for item in hr_rows:
            rows.append(
                PayrollResolvedAllowanceRead(
                    source="hr.employee_allowance",
                    code=item.basis_code,
                    amount=float(item.amount),
                    currency_code=item.currency_code,
                    details={"allowance_id": item.id},
                )
            )
        for item in actual.allowances:
            rows.append(
                PayrollResolvedAllowanceRead(
                    source="finance.actual_allowance",
                    code=item.reason_code,
                    amount=float(item.amount_total),
                    currency_code=item.currency_code,
                    details={"actual_allowance_id": item.id, "line_type_code": item.line_type_code},
                )
            )
        return rows

    def _resolve_advances(self, tenant_id: str, employee_id: str) -> list[PayrollResolvedAdvanceRead]:
        return [
            PayrollResolvedAdvanceRead(
                advance_no=row.advance_no,
                outstanding_amount=float(row.outstanding_amount),
                currency_code=row.currency_code,
                status=row.status,
            )
            for row in self.repository.list_employee_advances(tenant_id, employee_id)
        ]

    def _resolve_time_accounts(self, tenant_id: str, employee_id: str) -> list[PayrollResolvedTimeAccountRead]:
        rows = []
        for account in self.repository.list_employee_time_accounts(tenant_id, employee_id):
            balance = 0
            for txn in account.transactions:
                if txn.txn_type in {"opening", "credit", "correction"}:
                    balance += txn.amount_minutes
                else:
                    balance -= txn.amount_minutes
            rows.append(
                PayrollResolvedTimeAccountRead(
                    account_type=account.account_type,
                    balance_minutes=balance,
                    unit_code=account.unit_code,
                )
            )
        return rows

    def _resolve_surcharges(
        self,
        table: PayrollTariffTable,
        actual,
        employment_type_code: str | None,
        function_type_id: str | None,
        qualification_type_id: str | None,
        currency_code: str,
        unit_code: str,
        *,
        base_rate_amount: Decimal,
    ) -> list[PayrollResolvedSurchargeRead]:
        if actual.actual_start_at is None:
            return []
        weekday_bit = 1 << actual.actual_start_at.weekday()
        minute = actual.actual_start_at.hour * 60 + actual.actual_start_at.minute
        quantity = self._derive_quantity(actual.payable_minutes, unit_code)
        base_total = (base_rate_amount * quantity).quantize(Decimal("0.01"))
        result: list[PayrollResolvedSurchargeRead] = []
        for row in table.surcharge_rules:
            if row.weekday_mask & weekday_bit == 0:
                continue
            if minute < row.start_minute_local or minute >= row.end_minute_local:
                continue
            if row.function_type_id not in (None, function_type_id):
                continue
            if row.qualification_type_id not in (None, qualification_type_id):
                continue
            if row.employment_type_code not in (None, employment_type_code):
                continue
            amount_total = Decimal(str(row.fixed_amount or 0))
            if unit_code != "minute":
                amount_total *= quantity
            if row.percent_value is not None:
                amount_total += (base_total * Decimal(str(row.percent_value)) / Decimal("100")).quantize(Decimal("0.01"))
            result.append(
                PayrollResolvedSurchargeRead(
                    rule_id=row.id,
                    surcharge_type_code=row.surcharge_type_code,
                    pay_code=row.payroll_code or row.surcharge_type_code.upper(),
                    percent_value=None if row.percent_value is None else float(row.percent_value),
                    fixed_amount=None if row.fixed_amount is None else float(row.fixed_amount),
                    amount_total=float(amount_total.quantize(Decimal("0.01"))),
                    currency_code=row.currency_code or currency_code,
                )
            )
        return result

    def _render_export_artifact(self, batch: PayrollExportBatch, items: list[PayrollExportItemRead]) -> RenderedPayrollArtifact:
        adapter = self.adapters.get(batch.provider_key) or self.adapters["generic_csv"]
        return adapter.render_batch(batch, items)

    def _build_source_hash(
        self,
        provider_key: str,
        period_start: date,
        period_end: date,
        rows: list[PayrollActualResolutionRead],
    ) -> str:
        joined = "|".join(f"{row.actual_record_id}:{row.pay_code}:{row.quantity}:{row.base_amount}" for row in rows)
        return hashlib.sha256(f"{provider_key}:{period_start}:{period_end}:{joined}".encode("utf-8")).hexdigest()

    @staticmethod
    def _next_batch_no(provider_key: str, period_start: date, period_end: date) -> str:
        return f"PAY-{provider_key.upper()}-{period_start:%Y%m%d}-{period_end:%Y%m%d}"

    def _map_tariff_table_list_item(self, row: PayrollTariffTable) -> PayrollTariffTableListItem:
        return PayrollTariffTableListItem(
            id=row.id,
            code=row.code,
            title=row.title,
            region_code=row.region_code,
            status=row.tariff_status_code,
            effective_from=row.effective_from,
            effective_until=row.effective_until,
            version_no=row.version_no,
            archived_at=row.archived_at,
        )

    def _map_export_batch_list_item(self, row: PayrollExportBatch) -> PayrollExportBatchListItem:
        return PayrollExportBatchListItem(
            id=row.id,
            batch_no=row.batch_no,
            provider_key=row.provider_key,
            status=row.batch_status_code,
            period_start=row.period_start,
            period_end=row.period_end,
            item_count=row.item_count,
            total_amount=float(row.total_amount),
            currency_code=row.currency_code,
            generated_at=row.generated_at,
            queued_at=row.queued_at,
            dispatched_at=row.dispatched_at,
        )

    def _map_tariff_table_read(self, row: PayrollTariffTable) -> PayrollTariffTableRead:
        return PayrollTariffTableRead(
            **PayrollTariffTableListItem.model_validate(row).model_dump(),
            rates=[PayrollTariffRateRead.model_validate(item) for item in row.rates],
            surcharge_rules=[PayrollSurchargeRuleRead.model_validate(item) for item in row.surcharge_rules],
            notes=row.notes,
        )

    def _map_export_batch_read(self, row: PayrollExportBatch) -> PayrollExportBatchRead:
        return PayrollExportBatchRead(
            **self._map_export_batch_list_item(row).model_dump(),
            endpoint_id=row.endpoint_id,
            job_id=row.job_id,
            source_hash=row.source_hash,
            notes=row.notes,
            version_no=row.version_no,
            items=[PayrollExportItemRead.model_validate(item) for item in row.items],
            document_ids=[link.document_id for link in self.repository.list_document_links_for_export_batch(row.tenant_id, row.id)],
        )

    def _record_audit(
        self,
        actor: RequestAuthorizationContext,
        tenant_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        *,
        metadata_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=tenant_id,
                user_id=actor.user_id,
                session_id=actor.session_id,
                request_id=actor.request_id,
            ),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            metadata_json=metadata_json or {},
        )

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @staticmethod
    def _require_version(current_version: int, provided_version: int, entity_label: str) -> None:
        if current_version != provided_version:
            raise ApiException(409, f"finance.payroll.{entity_label}.stale_version", f"errors.finance.payroll.{entity_label}.stale_version")

    @staticmethod
    def _require_payroll_read(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.tenant_id != tenant_id or "finance.payroll.read" not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")

    @staticmethod
    def _require_payroll_write(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.tenant_id != tenant_id or "finance.payroll.write" not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")

    @staticmethod
    def _require_payroll_export(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.tenant_id != tenant_id or "finance.payroll.export" not in actor.permission_keys:
            raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
