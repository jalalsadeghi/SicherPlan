from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.finance.models import EmployeePayProfile, PayrollExportBatch, PayrollExportItem, PayrollPayslipArchive, PayrollSurchargeRule, PayrollTariffRate, PayrollTariffTable
from app.modules.finance.payroll_schemas import (
    EmployeePayProfileCreate,
    PayrollExportBatchGenerate,
    PayrollPayslipArchiveCreate,
    PayrollReconciliationFilter,
    PayrollSurchargeRuleCreate,
    PayrollTariffRateCreate,
    PayrollTariffTableCreate,
)
from app.modules.finance.payroll_service import PayrollService
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.field_execution.test_watchbook_flows import _FakeAuditRepository


def _actor(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-payroll",
        user_id="finance-user",
        tenant_id="tenant-1",
        role_keys=frozenset({"accounting"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="accounting", scope_type="tenant"),),
        request_id="req-payroll",
    )


@dataclass
class _FakeDocumentService:
    documents: list[dict[str, object]] = field(default_factory=list)
    versions: list[dict[str, object]] = field(default_factory=list)
    links: list[dict[str, object]] = field(default_factory=list)

    def create_document(self, tenant_id: str, payload, actor):  # noqa: ANN001
        row = {"id": f"doc-{len(self.documents) + 1}", "tenant_id": tenant_id, "payload": payload}
        self.documents.append(row)
        return SimpleNamespace(**row)

    def add_document_version(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.versions.append({"tenant_id": tenant_id, "document_id": document_id, "payload": payload})
        return SimpleNamespace(document_id=document_id, version_no=len(self.versions))

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.links.append({"tenant_id": tenant_id, "document_id": document_id, "payload": payload})
        return SimpleNamespace(document_id=document_id, owner_id=payload.owner_id)


@dataclass
class _FakeIntegrationRepo:
    jobs: list[object] = field(default_factory=list)
    outbox: list[object] = field(default_factory=list)

    def create_job_and_outbox(self, job, outbox_event):  # noqa: ANN001
        job.id = f"job-{len(self.jobs) + 1}"
        self.jobs.append(job)
        self.outbox.append(outbox_event)
        return job

    def save_job(self, row):  # noqa: ANN001
        return row


@dataclass
class _FakeRepo:
    tariff_tables: dict[str, PayrollTariffTable] = field(default_factory=dict)
    pay_profiles: dict[str, EmployeePayProfile] = field(default_factory=dict)
    export_batches: dict[str, PayrollExportBatch] = field(default_factory=dict)
    export_items: list[PayrollExportItem] = field(default_factory=list)
    archives: dict[str, PayrollPayslipArchive] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.employee = SimpleNamespace(id="employee-1")
        demand_group = SimpleNamespace(function_type_id="function-1", qualification_type_id="qualification-1")
        assignment = SimpleNamespace(id="assignment-1", demand_group=demand_group)
        self.actual = SimpleNamespace(
            id="actual-1",
            tenant_id="tenant-1",
            employee_id="employee-1",
            assignment_id="assignment-1",
            shift_id="shift-1",
            assignment=assignment,
            shift=SimpleNamespace(id="shift-1"),
            planned_start_at=datetime(2026, 3, 1, 8, 0, tzinfo=UTC),
            actual_start_at=datetime(2026, 3, 1, 22, 30, tzinfo=UTC),
            derived_at=datetime(2026, 3, 1, 23, 0, tzinfo=UTC),
            payable_minutes=480,
            approval_stage_code="finance_signed_off",
            allowances=[],
            reconciliations=[],
        )

    def list_tariff_tables(self, tenant_id: str, filters=None):
        rows = [row for row in self.tariff_tables.values() if row.tenant_id == tenant_id]
        if filters and filters.status:
            rows = [row for row in rows if row.tariff_status_code == filters.status]
        return rows

    def get_tariff_table(self, tenant_id: str, tariff_table_id: str):
        row = self.tariff_tables.get(tariff_table_id)
        return row if row and row.tenant_id == tenant_id else None

    def create_tariff_table(self, row: PayrollTariffTable):
        row.id = row.id or str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        row.version_no = row.version_no or 1
        row.status = row.status or "active"
        row.rates = []
        row.surcharge_rules = []
        self.tariff_tables[row.id] = row
        return row

    def save_tariff_table(self, row: PayrollTariffTable):
        self.tariff_tables[row.id] = row
        return row

    def create_tariff_rate(self, row: PayrollTariffRate):
        row.id = row.id or str(uuid4())
        row.version_no = row.version_no or 1
        table = self.tariff_tables[row.tariff_table_id]
        table.rates.append(row)
        return row

    def create_surcharge_rule(self, row: PayrollSurchargeRule):
        row.id = row.id or str(uuid4())
        row.version_no = row.version_no or 1
        table = self.tariff_tables[row.tariff_table_id]
        table.surcharge_rules.append(row)
        return row

    def find_overlapping_tariff_tables(self, tenant_id: str, region_code: str, effective_from: date, effective_until: date | None, *, exclude_id: str | None = None):
        rows = []
        for row in self.tariff_tables.values():
            if row.tenant_id != tenant_id or row.region_code != region_code or row.id == exclude_id:
                continue
            if row.effective_until is not None and row.effective_until < effective_from:
                continue
            if effective_until is not None and row.effective_from > effective_until:
                continue
            rows.append(row)
        return rows

    def list_active_tariff_tables(self, tenant_id: str, region_code: str, on_date: date):
        return [
            row
            for row in self.tariff_tables.values()
            if row.tenant_id == tenant_id
            and row.region_code == region_code
            and row.tariff_status_code == "active"
            and row.effective_from <= on_date
            and (row.effective_until is None or row.effective_until >= on_date)
        ]

    def list_employee_pay_profiles(self, tenant_id: str, filters=None):
        rows = [row for row in self.pay_profiles.values() if row.tenant_id == tenant_id]
        if filters and filters.employee_id:
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        return rows

    def get_employee_pay_profile(self, tenant_id: str, profile_id: str):
        row = self.pay_profiles.get(profile_id)
        return row if row and row.tenant_id == tenant_id else None

    def create_employee_pay_profile(self, row: EmployeePayProfile):
        row.id = row.id or str(uuid4())
        row.version_no = row.version_no or 1
        row.status = row.status or "active"
        self.pay_profiles[row.id] = row
        return row

    def save_employee_pay_profile(self, row: EmployeePayProfile):
        self.pay_profiles[row.id] = row
        return row

    def find_overlapping_employee_pay_profiles(self, tenant_id: str, employee_id: str, effective_from: date, effective_until: date | None, *, exclude_id: str | None = None):
        rows = []
        for row in self.pay_profiles.values():
            if row.tenant_id != tenant_id or row.employee_id != employee_id or row.id == exclude_id:
                continue
            if row.effective_until is not None and row.effective_until < effective_from:
                continue
            if effective_until is not None and row.effective_from > effective_until:
                continue
            rows.append(row)
        return rows

    def get_effective_employee_pay_profile(self, tenant_id: str, employee_id: str, on_date: date):
        rows = [
            row
            for row in self.pay_profiles.values()
            if row.tenant_id == tenant_id
            and row.employee_id == employee_id
            and row.effective_from <= on_date
            and (row.effective_until is None or row.effective_until >= on_date)
        ]
        rows.sort(key=lambda row: row.effective_from, reverse=True)
        return rows[0] if rows else None

    def get_employee(self, tenant_id: str, employee_id: str):
        return self.employee if tenant_id == "tenant-1" and employee_id == "employee-1" else None

    def get_actual_record(self, tenant_id: str, actual_record_id: str):
        return self.actual if tenant_id == "tenant-1" and actual_record_id == "actual-1" else None

    def list_approved_actual_records_for_period(self, tenant_id: str, period_start: date, period_end: date):
        if tenant_id != "tenant-1":
            return []
        actual_date = self.actual.planned_start_at.date()
        return [self.actual] if period_start <= actual_date <= period_end else []

    def list_employee_allowances(self, tenant_id: str, employee_id: str, on_date: date):
        return [
            SimpleNamespace(id="allow-1", basis_code="meal", amount=12.5, currency_code="EUR"),
        ]

    def list_employee_advances(self, tenant_id: str, employee_id: str):
        return [
            SimpleNamespace(advance_no="ADV-1", outstanding_amount=50, currency_code="EUR", status="disbursed"),
        ]

    def list_employee_time_accounts(self, tenant_id: str, employee_id: str):
        return [
            SimpleNamespace(
                account_type="overtime",
                unit_code="minutes",
                transactions=[
                    SimpleNamespace(txn_type="credit", amount_minutes=120),
                    SimpleNamespace(txn_type="debit", amount_minutes=30),
                ],
            ),
        ]

    def get_integration_endpoint(self, tenant_id: str, endpoint_id: str):
        return SimpleNamespace(id=endpoint_id, tenant_id=tenant_id)

    def find_integration_endpoint(self, tenant_id: str, provider_key: str, endpoint_type: str):
        return SimpleNamespace(id="endpoint-1", tenant_id=tenant_id)

    def list_export_batches(self, tenant_id: str, filters=None):
        return list(self.export_batches.values())

    def get_export_batch(self, tenant_id: str, batch_id: str):
        return self.export_batches.get(batch_id)

    def find_export_batch_by_source_hash(self, tenant_id: str, source_hash: str):
        for row in self.export_batches.values():
            if row.source_hash == source_hash:
                return row
        return None

    def create_export_batch(self, row: PayrollExportBatch):
        row.id = row.id or str(uuid4())
        row.version_no = row.version_no or 1
        row.status = row.status or "active"
        row.items = []
        self.export_batches[row.id] = row
        return row

    def save_export_batch(self, row: PayrollExportBatch):
        self.export_batches[row.id] = row
        return row

    def create_export_item(self, row: PayrollExportItem):
        row.id = row.id or str(uuid4())
        self.export_items.append(row)
        self.export_batches[row.batch_id].items.append(row)
        return row

    def list_document_links_for_export_batch(self, tenant_id: str, batch_id: str):
        return []

    def list_payslip_archives(self, tenant_id: str, filters=None):
        rows = list(self.archives.values())
        if filters and filters.employee_id:
            rows = [row for row in rows if row.employee_id == filters.employee_id]
        return rows

    def get_payslip_archive(self, tenant_id: str, archive_id: str):
        return self.archives.get(archive_id)

    def find_active_payslip_archive(self, tenant_id: str, employee_id: str, provider_key: str, period_start: date, period_end: date):
        for row in self.archives.values():
            if (
                row.employee_id == employee_id
                and row.provider_key == provider_key
                and row.period_start == period_start
                and row.period_end == period_end
                and row.archive_status_code == "active"
            ):
                return row
        return None

    def create_payslip_archive(self, row: PayrollPayslipArchive):
        row.id = row.id or str(uuid4())
        row.version_no = row.version_no or 1
        row.status = row.status or "active"
        self.archives[row.id] = row
        return row

    def save_payslip_archive(self, row: PayrollPayslipArchive):
        self.archives[row.id] = row
        return row


class PayrollServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _FakeRepo()
        self.docs = _FakeDocumentService()
        self.integration = _FakeIntegrationRepo()
        self.service = PayrollService(
            repository=self.repo,
            integration_repository=self.integration,
            document_service=self.docs,
            audit_service=AuditService(_FakeAuditRepository()),
        )
        self.actor = _actor("finance.payroll.read", "finance.payroll.write", "finance.payroll.export")

    def test_tariff_table_overlap_is_rejected(self) -> None:
        self.service.create_tariff_table(
            "tenant-1",
            PayrollTariffTableCreate(code="TV-1", title="NRW 2026", region_code="NRW", status="active", effective_from=date(2026, 1, 1)),
            self.actor,
        )
        with self.assertRaises(ApiException) as ctx:
            self.service.create_tariff_table(
                "tenant-1",
                PayrollTariffTableCreate(code="TV-2", title="NRW overlap", region_code="NRW", status="active", effective_from=date(2026, 6, 1)),
                self.actor,
            )
        self.assertEqual(ctx.exception.status_code, 409)

    def test_resolution_prefers_employee_profile_override_and_matching_rate(self) -> None:
        table = self.service.create_tariff_table(
            "tenant-1",
            PayrollTariffTableCreate(code="TV-1", title="NRW 2026", region_code="NRW", status="active", effective_from=date(2026, 1, 1)),
            self.actor,
        )
        self.service.add_tariff_rate(
            "tenant-1",
            table.id,
            PayrollTariffRateCreate(function_type_id="function-1", qualification_type_id="qualification-1", employment_type_code="full_time", base_amount=25, payroll_code="BASE25"),
            self.actor,
        )
        self.service.add_surcharge_rule(
            "tenant-1",
            table.id,
            PayrollSurchargeRuleCreate(surcharge_type_code="night", start_minute_local=1320, end_minute_local=1440, fixed_amount=5, payroll_code="NIGHT"),
            self.actor,
        )
        self.service.create_employee_pay_profile(
            "tenant-1",
            EmployeePayProfileCreate(
                employee_id="employee-1",
                tariff_table_id=table.id,
                payroll_region_code="NRW",
                employment_type_code="full_time",
                base_rate_override=30,
                export_employee_code="EMP-001",
                effective_from=date(2026, 1, 1),
            ),
            self.actor,
        )
        resolution = self.service.resolve_actual("tenant-1", "actual-1", self.actor)
        self.assertEqual(resolution.pay_code, "EMP-001")
        self.assertEqual(resolution.base_amount, 240.0)
        self.assertEqual(len(resolution.allowances), 1)
        self.assertEqual(len(resolution.surcharges), 1)

    def test_percent_surcharge_uses_resolved_base_amount(self) -> None:
        table = self.service.create_tariff_table(
            "tenant-1",
            PayrollTariffTableCreate(code="TV-1", title="NRW 2026", region_code="NRW", status="active", effective_from=date(2026, 1, 1)),
            self.actor,
        )
        self.service.add_tariff_rate(
            "tenant-1",
            table.id,
            PayrollTariffRateCreate(function_type_id="function-1", qualification_type_id="qualification-1", employment_type_code="full_time", base_amount=25, payroll_code="BASE25"),
            self.actor,
        )
        self.service.add_surcharge_rule(
            "tenant-1",
            table.id,
            PayrollSurchargeRuleCreate(surcharge_type_code="night", start_minute_local=1320, end_minute_local=1440, percent_value=25, payroll_code="NIGHT25"),
            self.actor,
        )
        self.service.create_employee_pay_profile(
            "tenant-1",
            EmployeePayProfileCreate(
                employee_id="employee-1",
                tariff_table_id=table.id,
                payroll_region_code="NRW",
                employment_type_code="full_time",
                base_rate_override=30,
                effective_from=date(2026, 1, 1),
            ),
            self.actor,
        )

        resolution = self.service.resolve_actual("tenant-1", "actual-1", self.actor)

        self.assertEqual(len(resolution.surcharges), 1)
        self.assertEqual(resolution.surcharges[0].pay_code, "NIGHT25")
        self.assertEqual(resolution.surcharges[0].amount_total, 60.0)

    def test_export_generation_is_idempotent_and_queues_job(self) -> None:
        table = self.service.create_tariff_table(
            "tenant-1",
            PayrollTariffTableCreate(code="TV-1", title="NRW 2026", region_code="NRW", status="active", effective_from=date(2026, 1, 1)),
            self.actor,
        )
        self.service.add_tariff_rate(
            "tenant-1",
            table.id,
            PayrollTariffRateCreate(function_type_id="function-1", qualification_type_id="qualification-1", employment_type_code="full_time", base_amount=25, payroll_code="BASE25"),
            self.actor,
        )
        self.service.create_employee_pay_profile(
            "tenant-1",
            EmployeePayProfileCreate(
                employee_id="employee-1",
                tariff_table_id=table.id,
                payroll_region_code="NRW",
                employment_type_code="full_time",
                export_employee_code="EMP-001",
                effective_from=date(2026, 1, 1),
            ),
            self.actor,
        )
        batch = self.service.generate_export_batch(
            "tenant-1",
            PayrollExportBatchGenerate(provider_key="generic_csv", period_start=date(2026, 3, 1), period_end=date(2026, 3, 31)),
            self.actor,
        )
        rerun = self.service.generate_export_batch(
            "tenant-1",
            PayrollExportBatchGenerate(provider_key="generic_csv", period_start=date(2026, 3, 1), period_end=date(2026, 3, 31)),
            self.actor,
        )
        self.assertEqual(batch.id, rerun.id)
        self.assertEqual(batch.status, "queued")
        self.assertEqual(len(self.integration.jobs), 1)
        self.assertEqual(len(self.docs.documents), 1)

    def test_payslip_archive_supersedes_previous_archive(self) -> None:
        first = self.service.archive_payslip(
            "tenant-1",
            PayrollPayslipArchiveCreate(
                employee_id="employee-1",
                provider_key="generic_csv",
                period_start=date(2026, 3, 1),
                period_end=date(2026, 3, 31),
                source_document_id="doc-1",
            ),
            self.actor,
        )
        second = self.service.archive_payslip(
            "tenant-1",
            PayrollPayslipArchiveCreate(
                employee_id="employee-1",
                provider_key="generic_csv",
                period_start=date(2026, 3, 1),
                period_end=date(2026, 3, 31),
                source_document_id="doc-2",
            ),
            self.actor,
        )
        self.assertEqual(second.archive_status_code, "active")
        self.assertEqual(self.repo.archives[first.id].archive_status_code, "superseded")

    def test_reconciliation_reports_missing_export_and_payslip(self) -> None:
        table = self.service.create_tariff_table(
            "tenant-1",
            PayrollTariffTableCreate(code="TV-1", title="NRW 2026", region_code="NRW", status="active", effective_from=date(2026, 1, 1)),
            self.actor,
        )
        self.service.add_tariff_rate(
            "tenant-1",
            table.id,
            PayrollTariffRateCreate(function_type_id="function-1", qualification_type_id="qualification-1", employment_type_code="full_time", base_amount=25),
            self.actor,
        )
        self.service.create_employee_pay_profile(
            "tenant-1",
            EmployeePayProfileCreate(
                employee_id="employee-1",
                tariff_table_id=table.id,
                payroll_region_code="NRW",
                employment_type_code="full_time",
                effective_from=date(2026, 1, 1),
            ),
            self.actor,
        )
        rows = self.service.list_reconciliation_rows(
            "tenant-1",
            PayrollReconciliationFilter(period_start=date(2026, 3, 1), period_end=date(2026, 3, 31)),
            self.actor,
        )
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].missing_export)
        self.assertTrue(rows[0].missing_payslip)
        self.assertIn("missing_export_batch", rows[0].mismatch_codes)


if __name__ == "__main__":
    unittest.main()
