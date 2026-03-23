from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.finance.billing_schemas import (
    InvoiceDispatchRequest,
    InvoiceGenerateRequest,
    InvoiceIssueRequest,
    InvoiceReleaseRequest,
    TimesheetGenerateRequest,
    TimesheetListFilter,
    TimesheetReleaseRequest,
)
from app.modules.finance.billing_service import FinanceBillingService
from app.modules.finance.models import CustomerInvoice, Timesheet
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


def _actor(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-billing",
        user_id="finance-user",
        tenant_id="tenant-1",
        role_keys=frozenset({"accounting"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="accounting", scope_type="tenant"),),
        request_id="req-billing",
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
        document = next((row for row in self.documents if row["id"] == document_id), None)
        link = SimpleNamespace(
            tenant_id=tenant_id,
            document_id=document_id,
            owner_type=payload.owner_type,
            owner_id=payload.owner_id,
            label=payload.label,
            document=SimpleNamespace(
                id=document_id,
                title=document["payload"].title if document else document_id,
                document_type=None,
                current_version_no=len(self.versions),
                versions=[SimpleNamespace(version_no=len(self.versions), file_name=payload.label or "file.pdf", content_type="application/pdf")],
            ),
        )
        self.links.append({"tenant_id": tenant_id, "document_id": document_id, "payload": payload, "link": link})
        return link

    def download_document_version(self, tenant_id: str, document_id: str, version_no: int, actor):  # noqa: ANN001
        return SimpleNamespace(file_name="document.pdf", content_type="application/pdf", content=b"pdf")


@dataclass
class _FakeIntegrationRepo:
    jobs: list[object] = field(default_factory=list)
    outbox: list[object] = field(default_factory=list)

    def create_job_and_outbox(self, job, outbox_event):  # noqa: ANN001
        job.id = f"job-{len(self.jobs) + 1}"
        self.jobs.append(job)
        self.outbox.append(outbox_event)
        return job


@dataclass
class _FakeBillingRepo:
    timesheets: dict[str, Timesheet] = field(default_factory=dict)
    invoices: dict[str, CustomerInvoice] = field(default_factory=dict)
    timesheet_links: dict[str, list[object]] = field(default_factory=dict)
    invoice_links: dict[str, list[object]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        customer = SimpleNamespace(id="customer-1", customer_number="C-100")
        order = SimpleNamespace(id="order-1", order_no="ORD-1", customer_id="customer-1", customer=customer)
        planning_record = SimpleNamespace(
            id="record-1",
            name="Objekt Nord",
            planning_mode_code="site",
            order=order,
            site_detail=SimpleNamespace(site=SimpleNamespace(name="Nordtor")),
            event_detail=None,
            trade_fair_detail=None,
            patrol_detail=None,
        )
        shift_plan = SimpleNamespace(planning_record=planning_record)
        shift = SimpleNamespace(id="shift-1", location_text="Nordtor", meeting_point=None, shift_plan=shift_plan)
        assignment = SimpleNamespace(id="assignment-1", shift=shift, demand_group=SimpleNamespace(function_type_id="fn-1", qualification_type_id=None))
        self.actual = SimpleNamespace(
            id="actual-1",
            tenant_id="tenant-1",
            shift_id="shift-1",
            assignment_id="assignment-1",
            assignment=assignment,
            shift=shift,
            planned_start_at=datetime(2026, 4, 2, 8, 0, tzinfo=UTC),
            planned_end_at=datetime(2026, 4, 2, 16, 0, tzinfo=UTC),
            actual_start_at=datetime(2026, 4, 2, 8, 15, tzinfo=UTC),
            actual_end_at=datetime(2026, 4, 2, 16, 15, tzinfo=UTC),
            planned_break_minutes=30,
            actual_break_minutes=30,
            billable_minutes=450,
            customer_adjustment_minutes=0,
            derived_at=datetime(2026, 4, 2, 16, 30, tzinfo=UTC),
        )
        self.billing_profile = SimpleNamespace(
            id="billing-1",
            invoice_email="billing@example.com",
            payment_terms_days=14,
            invoice_layout_code="classic",
            shipping_method_code="email_pdf",
            e_invoice_enabled=False,
            leitweg_id=None,
        )
        self.invoice_party = SimpleNamespace(
            id="party-1",
            is_default=True,
            name="Rechnungsempfaenger",
            contact_name="Frau Zahlbar",
            invoice_email="invoice@example.com",
            invoice_layout_lookup=SimpleNamespace(key="classic"),
            address=SimpleNamespace(street_line_1="Hauptstrasse 1", postal_code="12345", city="Berlin", country_code="DE"),
        )
        self.rate_card = SimpleNamespace(
            id="rate-card-1",
            currency_code="EUR",
            rate_lines=[SimpleNamespace(id="rate-line-1", planning_mode_code="site", billing_unit="hour", unit_price=Decimal("40.00"), minimum_quantity=None, sort_order=100)],
            surcharge_rules=[SimpleNamespace(id="surcharge-1", weekday_mask=None, percent_value=Decimal("10.00"), fixed_amount=None, surcharge_type="night", sort_order=100)],
        )
        self.endpoint = SimpleNamespace(id="endpoint-1")

    def list_approved_actuals_for_scope(self, tenant_id: str, *, customer_id: str, order_id: str | None, planning_record_id: str | None, period_start: date, period_end: date):
        if tenant_id != "tenant-1" or customer_id != "customer-1":
            return []
        return [self.actual]

    def list_timesheets(self, tenant_id: str, filters: TimesheetListFilter):
        rows = [row for row in self.timesheets.values() if row.tenant_id == tenant_id]
        if filters.customer_id:
            rows = [row for row in rows if row.customer_id == filters.customer_id]
        if filters.release_state_code:
            rows = [row for row in rows if row.release_state_code == filters.release_state_code]
        if filters.customer_visible_only:
            rows = [row for row in rows if row.customer_visible_flag]
        return rows

    def get_timesheet(self, tenant_id: str, timesheet_id: str):
        row = self.timesheets.get(timesheet_id)
        return row if row and row.tenant_id == tenant_id else None

    def find_timesheet_by_scope_key(self, tenant_id: str, scope_key: str):
        return next((row for row in self.timesheets.values() if row.tenant_id == tenant_id and row.scope_key == scope_key), None)

    def create_timesheet(self, row: Timesheet):
        row.id = row.id or str(uuid4())
        row.version_no = row.version_no or 1
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        for line in row.lines:
            line.id = line.id or str(uuid4())
            line.timesheet_id = row.id
            line.tenant_id = row.tenant_id
            line.created_at = line.created_at or row.created_at
            line.updated_at = line.updated_at or row.updated_at
        self.timesheets[row.id] = row
        return row

    def save_timesheet(self, row: Timesheet):
        row.updated_at = datetime.now(UTC)
        for line in row.lines:
            line.id = line.id or str(uuid4())
            line.timesheet_id = row.id
            line.tenant_id = row.tenant_id
            line.updated_at = row.updated_at
        self.timesheets[row.id] = row
        return row

    def list_invoices(self, tenant_id: str, filters):
        rows = [row for row in self.invoices.values() if row.tenant_id == tenant_id]
        if filters.customer_id:
            rows = [row for row in rows if row.customer_id == filters.customer_id]
        if filters.invoice_status_code:
            rows = [row for row in rows if row.invoice_status_code == filters.invoice_status_code]
        if filters.customer_visible_only:
            rows = [row for row in rows if row.customer_visible_flag]
        return rows

    def get_invoice(self, tenant_id: str, invoice_id: str):
        row = self.invoices.get(invoice_id)
        return row if row and row.tenant_id == tenant_id else None

    def find_invoice_by_timesheet(self, tenant_id: str, timesheet_id: str):
        return next((row for row in self.invoices.values() if row.tenant_id == tenant_id and row.timesheet_id == timesheet_id), None)

    def create_invoice(self, row: CustomerInvoice):
        row.id = row.id or str(uuid4())
        row.version_no = row.version_no or 1
        row.created_at = row.created_at or datetime.now(UTC)
        row.updated_at = row.updated_at or row.created_at
        for line in row.lines:
            line.id = line.id or str(uuid4())
            line.invoice_id = row.id
            line.tenant_id = row.tenant_id
            line.created_at = line.created_at or row.created_at
            line.updated_at = line.updated_at or row.updated_at
        self.invoices[row.id] = row
        return row

    def save_invoice(self, row: CustomerInvoice):
        row.updated_at = datetime.now(UTC)
        for line in row.lines:
            line.id = line.id or str(uuid4())
            line.invoice_id = row.id
            line.tenant_id = row.tenant_id
            line.updated_at = row.updated_at
        self.invoices[row.id] = row
        return row

    def get_customer_billing_profile(self, tenant_id: str, customer_id: str):
        return self.billing_profile if tenant_id == "tenant-1" and customer_id == "customer-1" else None

    def list_customer_invoice_parties(self, tenant_id: str, customer_id: str):
        return [self.invoice_party] if tenant_id == "tenant-1" and customer_id == "customer-1" else []

    def list_active_customer_rate_cards(self, tenant_id: str, customer_id: str, on_date: date):
        return [self.rate_card] if tenant_id == "tenant-1" and customer_id == "customer-1" else []

    def find_integration_endpoint(self, tenant_id: str, provider_key: str, endpoint_type: str):
        return self.endpoint

    def get_integration_endpoint(self, tenant_id: str, endpoint_id: str):
        return self.endpoint if endpoint_id == self.endpoint.id else None

    def list_document_links_for_timesheet(self, tenant_id: str, timesheet_id: str):
        return self.timesheet_links.get(timesheet_id, [])

    def list_document_links_for_invoice(self, tenant_id: str, invoice_id: str):
        return self.invoice_links.get(invoice_id, [])

    def get_document_link_for_timesheet(self, tenant_id: str, timesheet_id: str, document_id: str):
        return next((row for row in self.timesheet_links.get(timesheet_id, []) if row.document_id == document_id), None)

    def get_document_link_for_invoice(self, tenant_id: str, invoice_id: str, document_id: str):
        return next((row for row in self.invoice_links.get(invoice_id, []) if row.document_id == document_id), None)


class FinanceBillingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _FakeBillingRepo()
        self.docs = _FakeDocumentService()
        self.integration = _FakeIntegrationRepo()
        self.service = FinanceBillingService(
            repository=self.repo,
            integration_repository=self.integration,
            document_service=self.docs,
            audit_service=None,
        )
        self.actor = _actor("finance.billing.read", "finance.billing.write", "finance.billing.delivery")

    def test_timesheet_generation_is_deterministic_for_scope(self) -> None:
        payload = TimesheetGenerateRequest(
            customer_id="customer-1",
            order_id="order-1",
            planning_record_id="record-1",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 4, 30),
            billing_granularity_code="shift",
        )
        first = self.service.generate_timesheet("tenant-1", payload, self.actor)
        second = self.service.generate_timesheet("tenant-1", payload, self.actor)

        self.assertEqual(first.id, second.id)
        self.assertEqual(len(first.lines), 1)
        self.assertIn("Nordtor", first.lines[0].line_description)
        self.assertFalse(first.lines[0].personal_names_released)

    def test_releasing_timesheet_creates_docs_backed_output(self) -> None:
        generated = self.service.generate_timesheet(
            "tenant-1",
            TimesheetGenerateRequest(
                customer_id="customer-1",
                order_id="order-1",
                planning_record_id="record-1",
                period_start=date(2026, 4, 1),
                period_end=date(2026, 4, 30),
            ),
            self.actor,
        )
        released = self.service.release_timesheet("tenant-1", generated.id, TimesheetReleaseRequest(customer_visible_flag=True, version_no=generated.version_no), self.actor)
        self.repo.timesheet_links[generated.id] = [entry["link"] for entry in self.docs.links if entry["payload"].owner_id == generated.id]

        self.assertEqual(released.release_state_code, "released")
        self.assertTrue(released.customer_visible_flag)
        self.assertIsNotNone(released.source_document_id)

    def test_invoice_generation_persists_totals_and_source_links(self) -> None:
        generated = self.service.generate_timesheet(
            "tenant-1",
            TimesheetGenerateRequest(
                customer_id="customer-1",
                order_id="order-1",
                planning_record_id="record-1",
                period_start=date(2026, 4, 1),
                period_end=date(2026, 4, 30),
            ),
            self.actor,
        )
        released = self.service.release_timesheet("tenant-1", generated.id, TimesheetReleaseRequest(customer_visible_flag=True, version_no=generated.version_no), self.actor)
        invoice = self.service.generate_invoice(
            "tenant-1",
            InvoiceGenerateRequest(customer_id="customer-1", timesheet_id=released.id, issue_date=date(2026, 5, 1)),
            self.actor,
        )

        self.assertTrue(invoice.invoice_no.startswith("INV-20260501-"))
        self.assertGreater(invoice.total_amount, 0)
        self.assertEqual(invoice.lines[0].timesheet_line_id, released.lines[0].id)
        self.assertEqual(invoice.due_date, date(2026, 5, 15))

    def test_queue_invoice_dispatch_requires_email_context(self) -> None:
        generated = self.service.generate_timesheet(
            "tenant-1",
            TimesheetGenerateRequest(
                customer_id="customer-1",
                order_id="order-1",
                planning_record_id="record-1",
                period_start=date(2026, 4, 1),
                period_end=date(2026, 4, 30),
            ),
            self.actor,
        )
        released_timesheet = self.service.release_timesheet("tenant-1", generated.id, TimesheetReleaseRequest(customer_visible_flag=True, version_no=generated.version_no), self.actor)
        invoice = self.service.generate_invoice(
            "tenant-1",
            InvoiceGenerateRequest(customer_id="customer-1", timesheet_id=released_timesheet.id, issue_date=date(2026, 5, 1)),
            self.actor,
        )
        issued = self.service.issue_invoice("tenant-1", invoice.id, InvoiceIssueRequest(version_no=invoice.version_no), self.actor)
        released_invoice = self.service.release_invoice("tenant-1", issued.id, InvoiceReleaseRequest(customer_visible_flag=True, version_no=issued.version_no), self.actor)
        self.repo.invoice_links[released_invoice.id] = [entry["link"] for entry in self.docs.links if entry["payload"].owner_id == released_invoice.id]
        queued = self.service.queue_invoice_dispatch("tenant-1", released_invoice.id, InvoiceDispatchRequest(version_no=released_invoice.version_no), self.actor)

        self.assertEqual(queued.delivery_status_code, "queued")
        self.assertEqual(len(self.integration.jobs), 1)

    def test_queue_invoice_dispatch_requires_leitweg_for_e_invoice(self) -> None:
        self.repo.billing_profile.e_invoice_enabled = True
        self.repo.billing_profile.shipping_method_code = "e_invoice"
        self.repo.billing_profile.leitweg_id = None
        generated = self.service.generate_timesheet(
            "tenant-1",
            TimesheetGenerateRequest(
                customer_id="customer-1",
                order_id="order-1",
                planning_record_id="record-1",
                period_start=date(2026, 4, 1),
                period_end=date(2026, 4, 30),
            ),
            self.actor,
        )
        released_timesheet = self.service.release_timesheet("tenant-1", generated.id, TimesheetReleaseRequest(customer_visible_flag=True, version_no=generated.version_no), self.actor)
        invoice = self.service.generate_invoice(
            "tenant-1",
            InvoiceGenerateRequest(customer_id="customer-1", timesheet_id=released_timesheet.id, issue_date=date(2026, 5, 1)),
            self.actor,
        )
        issued = self.service.issue_invoice("tenant-1", invoice.id, InvoiceIssueRequest(version_no=invoice.version_no), self.actor)
        released_invoice = self.service.release_invoice("tenant-1", issued.id, InvoiceReleaseRequest(customer_visible_flag=True, version_no=issued.version_no), self.actor)

        with self.assertRaises(ApiException) as ctx:
            self.service.queue_invoice_dispatch("tenant-1", released_invoice.id, InvoiceDispatchRequest(version_no=released_invoice.version_no), self.actor)

        self.assertEqual(ctx.exception.code, "finance.invoice.delivery.leitweg_required")

    def test_customer_portal_lists_only_released_visible_finance_outputs(self) -> None:
        generated = self.service.generate_timesheet(
            "tenant-1",
            TimesheetGenerateRequest(
                customer_id="customer-1",
                order_id="order-1",
                planning_record_id="record-1",
                period_start=date(2026, 4, 1),
                period_end=date(2026, 4, 30),
            ),
            self.actor,
        )
        released_timesheet = self.service.release_timesheet("tenant-1", generated.id, TimesheetReleaseRequest(customer_visible_flag=True, version_no=generated.version_no), self.actor)
        self.repo.timesheet_links[released_timesheet.id] = [entry["link"] for entry in self.docs.links if entry["payload"].owner_id == released_timesheet.id]
        invoice = self.service.generate_invoice(
            "tenant-1",
            InvoiceGenerateRequest(customer_id="customer-1", timesheet_id=released_timesheet.id, issue_date=date(2026, 5, 1)),
            self.actor,
        )
        issued = self.service.issue_invoice("tenant-1", invoice.id, InvoiceIssueRequest(version_no=invoice.version_no), self.actor)
        released_invoice = self.service.release_invoice("tenant-1", issued.id, InvoiceReleaseRequest(customer_visible_flag=True, version_no=issued.version_no), self.actor)
        self.repo.invoice_links[released_invoice.id] = [entry["link"] for entry in self.docs.links if entry["payload"].owner_id == released_invoice.id]

        context = SimpleNamespace(tenant_id="tenant-1", customer_id="customer-1")
        timesheets = self.service.list_customer_portal_timesheets(context)
        invoices = self.service.list_customer_portal_invoices(context)

        self.assertEqual(len(timesheets.items), 1)
        self.assertEqual(len(invoices.items), 1)
        self.assertEqual(timesheets.items[0].documents[0].document_id, released_timesheet.source_document_id)
        self.assertEqual(invoices.items[0].documents[0].document_id, released_invoice.source_document_id)
        self.assertEqual(invoices.items[0].invoice_no, released_invoice.invoice_no)

    def test_customer_portal_download_requires_matching_customer_scope(self) -> None:
        generated = self.service.generate_timesheet(
            "tenant-1",
            TimesheetGenerateRequest(
                customer_id="customer-1",
                order_id="order-1",
                planning_record_id="record-1",
                period_start=date(2026, 4, 1),
                period_end=date(2026, 4, 30),
            ),
            self.actor,
        )
        released = self.service.release_timesheet("tenant-1", generated.id, TimesheetReleaseRequest(customer_visible_flag=True, version_no=generated.version_no), self.actor)
        self.repo.timesheet_links[released.id] = [entry["link"] for entry in self.docs.links if entry["payload"].owner_id == released.id]

        denied_context = SimpleNamespace(tenant_id="tenant-1", customer_id="customer-2")
        with self.assertRaises(ApiException) as ctx:
            self.service.download_customer_portal_timesheet_document(
                denied_context,
                released.id,
                released.source_document_id,
                1,
            )

        self.assertEqual(ctx.exception.code, "finance.timesheet.not_found")

    def test_invoice_generation_requires_released_timesheet(self) -> None:
        generated = self.service.generate_timesheet(
            "tenant-1",
            TimesheetGenerateRequest(
                customer_id="customer-1",
                order_id="order-1",
                planning_record_id="record-1",
                period_start=date(2026, 4, 1),
                period_end=date(2026, 4, 30),
            ),
            self.actor,
        )
        with self.assertRaises(ApiException):
            self.service.generate_invoice(
                "tenant-1",
                InvoiceGenerateRequest(customer_id="customer-1", timesheet_id=generated.id, issue_date=date(2026, 5, 1)),
                self.actor,
            )
