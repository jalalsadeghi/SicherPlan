"""Service layer for finance customer timesheets and invoices."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Protocol

from app.errors import ApiException
from app.modules.customers.schemas import (
    CustomerPortalCollectionSourceRead,
    CustomerPortalDocumentRefRead,
    CustomerPortalInvoiceCollectionRead,
    CustomerPortalInvoiceRead,
    CustomerPortalTimesheetCollectionRead,
    CustomerPortalTimesheetRead,
)
from app.modules.finance.billing_schemas import (
    CustomerInvoiceListItem,
    CustomerInvoiceRead,
    InvoiceDispatchRequest,
    InvoiceGenerateRequest,
    InvoiceIssueRequest,
    InvoiceListFilter,
    InvoiceReleaseRequest,
    TimesheetGenerateRequest,
    TimesheetListFilter,
    TimesheetListItem,
    TimesheetRead,
    TimesheetReleaseRequest,
)
from app.modules.finance.models import CustomerInvoice, CustomerInvoiceLine, Timesheet, TimesheetLine
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentDownload, DocumentService
from app.modules.platform_services.integration_models import ImportExportJob, OutboxEvent


class FinanceBillingRepository(Protocol):
    def list_approved_actuals_for_scope(
        self,
        tenant_id: str,
        *,
        customer_id: str,
        order_id: str | None,
        planning_record_id: str | None,
        period_start: date,
        period_end: date,
    ): ...  # noqa: ANN001
    def list_timesheets(self, tenant_id: str, filters: TimesheetListFilter): ...  # noqa: ANN001
    def get_timesheet(self, tenant_id: str, timesheet_id: str): ...  # noqa: ANN001
    def find_timesheet_by_scope_key(self, tenant_id: str, scope_key: str): ...  # noqa: ANN001
    def create_timesheet(self, row: Timesheet) -> Timesheet: ...
    def save_timesheet(self, row: Timesheet) -> Timesheet: ...
    def list_invoices(self, tenant_id: str, filters: InvoiceListFilter): ...  # noqa: ANN001
    def get_invoice(self, tenant_id: str, invoice_id: str): ...  # noqa: ANN001
    def find_invoice_by_timesheet(self, tenant_id: str, timesheet_id: str): ...  # noqa: ANN001
    def create_invoice(self, row: CustomerInvoice) -> CustomerInvoice: ...
    def save_invoice(self, row: CustomerInvoice) -> CustomerInvoice: ...
    def get_customer_billing_profile(self, tenant_id: str, customer_id: str): ...  # noqa: ANN001
    def list_customer_invoice_parties(self, tenant_id: str, customer_id: str): ...  # noqa: ANN001
    def list_active_customer_rate_cards(self, tenant_id: str, customer_id: str, on_date: date): ...  # noqa: ANN001
    def find_integration_endpoint(self, tenant_id: str, provider_key: str, endpoint_type: str): ...  # noqa: ANN001
    def get_integration_endpoint(self, tenant_id: str, endpoint_id: str): ...  # noqa: ANN001
    def list_document_links_for_timesheet(self, tenant_id: str, timesheet_id: str): ...  # noqa: ANN001
    def list_document_links_for_invoice(self, tenant_id: str, invoice_id: str): ...  # noqa: ANN001
    def get_document_link_for_timesheet(self, tenant_id: str, timesheet_id: str, document_id: str): ...  # noqa: ANN001
    def get_document_link_for_invoice(self, tenant_id: str, invoice_id: str, document_id: str): ...  # noqa: ANN001


class BillingIntegrationRepository(Protocol):
    def create_job_and_outbox(self, job: ImportExportJob, outbox_event: OutboxEvent) -> ImportExportJob: ...


@dataclass(slots=True)
class RenderedDocumentArtifact:
    file_name: str
    content_type: str
    content: bytes
    metadata_json: dict[str, object]


class FinanceBillingService:
    def __init__(
        self,
        *,
        repository: FinanceBillingRepository,
        integration_repository: BillingIntegrationRepository,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.integration_repository = integration_repository
        self.document_service = document_service
        self.audit_service = audit_service

    def list_timesheets(
        self,
        tenant_id: str,
        filters: TimesheetListFilter,
        actor: RequestAuthorizationContext,
    ) -> list[TimesheetListItem]:
        self._require_billing_read(actor, tenant_id)
        return [self._map_timesheet_list_item(row) for row in self.repository.list_timesheets(tenant_id, filters)]

    def get_timesheet(self, tenant_id: str, timesheet_id: str, actor: RequestAuthorizationContext) -> TimesheetRead:
        self._require_billing_read(actor, tenant_id)
        return self._map_timesheet_read(self._require_timesheet(tenant_id, timesheet_id))

    def generate_timesheet(
        self,
        tenant_id: str,
        payload: TimesheetGenerateRequest,
        actor: RequestAuthorizationContext,
    ) -> TimesheetRead:
        self._require_billing_write(actor, tenant_id)
        scope_key = self._build_timesheet_scope_key(payload)
        actuals = self.repository.list_approved_actuals_for_scope(
            tenant_id,
            customer_id=payload.customer_id,
            order_id=payload.order_id,
            planning_record_id=payload.planning_record_id,
            period_start=payload.period_start,
            period_end=payload.period_end,
        )
        if not actuals:
            raise ApiException(409, "finance.timesheet.no_eligible_actuals", "errors.finance.timesheet.no_eligible_actuals")
        source_hash = self._build_timesheet_source_hash(actuals)
        current = self.repository.find_timesheet_by_scope_key(tenant_id, scope_key)
        if current is not None and current.source_hash == source_hash:
            return self._map_timesheet_read(current)
        line_rows = [self._build_timesheet_line(tenant_id, index, row, payload.billing_granularity_code) for index, row in enumerate(actuals, start=1)]
        headline = self._build_timesheet_headline(payload, actuals[0])
        summary = f"{len(line_rows)} line(s) from approved actuals"
        totals = self._summarize_timesheet_lines(line_rows)

        if current is None:
            row = self.repository.create_timesheet(
                Timesheet(
                    tenant_id=tenant_id,
                    customer_id=payload.customer_id,
                    order_id=payload.order_id or line_rows[0].order_id,
                    planning_record_id=payload.planning_record_id,
                    scope_key=scope_key,
                    source_hash=source_hash,
                    billing_granularity_code=payload.billing_granularity_code,
                    period_start=payload.period_start,
                    period_end=payload.period_end,
                    headline=headline,
                    summary=summary,
                    total_planned_minutes=totals["planned"],
                    total_actual_minutes=totals["actual"],
                    total_billable_minutes=totals["billable"],
                    release_state_code="draft",
                    customer_visible_flag=False,
                    metadata_json={"generated_from_actual_ids": [row.id for row in actuals]},
                    created_by_user_id=actor.user_id,
                    updated_by_user_id=actor.user_id,
                    lines=line_rows,
                )
            )
        else:
            if current.release_state_code == "released":
                return self._map_timesheet_read(current)
            current.source_hash = source_hash
            current.order_id = payload.order_id or current.order_id
            current.planning_record_id = payload.planning_record_id
            current.billing_granularity_code = payload.billing_granularity_code
            current.period_start = payload.period_start
            current.period_end = payload.period_end
            current.headline = headline
            current.summary = summary
            current.total_planned_minutes = totals["planned"]
            current.total_actual_minutes = totals["actual"]
            current.total_billable_minutes = totals["billable"]
            current.metadata_json = {"generated_from_actual_ids": [row.id for row in actuals]}
            current.updated_by_user_id = actor.user_id
            current.version_no += 1
            current.lines.clear()
            current.lines.extend(line_rows)
            row = self.repository.save_timesheet(current)
        self._record_audit(actor, tenant_id, "finance.timesheet.generated", "finance.timesheet", row.id)
        return self._map_timesheet_read(row)

    def release_timesheet(
        self,
        tenant_id: str,
        timesheet_id: str,
        payload: TimesheetReleaseRequest,
        actor: RequestAuthorizationContext,
    ) -> TimesheetRead:
        self._require_billing_write(actor, tenant_id)
        row = self._require_timesheet(tenant_id, timesheet_id)
        self._require_version(row.version_no, payload.version_no, "timesheet")
        if row.release_state_code == "released" and row.customer_visible_flag == payload.customer_visible_flag:
            return self._map_timesheet_read(row)
        artifact = self._render_timesheet_pdf(row)
        document_id = self._persist_owner_document(
            tenant_id=tenant_id,
            owner_type="finance.timesheet",
            owner_id=row.id,
            title=f"Timesheet {row.headline}",
            artifact=artifact,
            actor=actor,
        )
        row.release_state_code = "released"
        row.customer_visible_flag = payload.customer_visible_flag
        row.released_at = datetime.now(UTC)
        row.released_by_user_id = actor.user_id
        row.source_document_id = document_id
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        row = self.repository.save_timesheet(row)
        self._record_audit(actor, tenant_id, "finance.timesheet.released", "finance.timesheet", row.id)
        return self._map_timesheet_read(row)

    def list_invoices(
        self,
        tenant_id: str,
        filters: InvoiceListFilter,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerInvoiceListItem]:
        self._require_billing_read(actor, tenant_id)
        return [self._map_invoice_list_item(row) for row in self.repository.list_invoices(tenant_id, filters)]

    def get_invoice(self, tenant_id: str, invoice_id: str, actor: RequestAuthorizationContext) -> CustomerInvoiceRead:
        self._require_billing_read(actor, tenant_id)
        return self._map_invoice_read(self._require_invoice(tenant_id, invoice_id))

    def generate_invoice(
        self,
        tenant_id: str,
        payload: InvoiceGenerateRequest,
        actor: RequestAuthorizationContext,
    ) -> CustomerInvoiceRead:
        self._require_billing_write(actor, tenant_id)
        timesheet = self._resolve_invoice_timesheet(tenant_id, payload)
        if timesheet.release_state_code != "released":
            raise ApiException(409, "finance.invoice.timesheet.not_released", "errors.finance.invoice.timesheet.not_released")
        existing = self.repository.find_invoice_by_timesheet(tenant_id, timesheet.id)
        if existing is not None:
            return self._map_invoice_read(existing)

        billing_profile = self.repository.get_customer_billing_profile(tenant_id, timesheet.customer_id)
        invoice_parties = self.repository.list_customer_invoice_parties(tenant_id, timesheet.customer_id)
        default_party = next((row for row in invoice_parties if row.is_default), None)
        rate_cards = self.repository.list_active_customer_rate_cards(tenant_id, timesheet.customer_id, payload.issue_date)
        if not rate_cards:
            raise ApiException(404, "finance.invoice.rate_card.not_found", "errors.finance.invoice.rate_card.not_found")
        rate_card = rate_cards[0]
        line_rows = self._build_invoice_lines(timesheet, rate_card)
        if not line_rows:
            raise ApiException(409, "finance.invoice.no_billable_lines", "errors.finance.invoice.no_billable_lines")
        totals = self._summarize_invoice_lines(line_rows)
        invoice_no = self._build_invoice_number(payload.issue_date, timesheet)
        payment_terms_days = billing_profile.payment_terms_days if billing_profile is not None else 0
        due_date = payload.issue_date + timedelta(days=payment_terms_days or 0)
        row = self.repository.create_invoice(
            CustomerInvoice(
                tenant_id=tenant_id,
                customer_id=timesheet.customer_id,
                timesheet_id=timesheet.id,
                billing_profile_id=billing_profile.id if billing_profile is not None else None,
                invoice_party_id=default_party.id if default_party is not None else None,
                invoice_no=invoice_no,
                period_start=timesheet.period_start,
                period_end=timesheet.period_end,
                issue_date=payload.issue_date,
                due_date=due_date,
                currency_code=rate_card.currency_code,
                layout_code=(
                    default_party.invoice_layout_lookup.key
                    if default_party is not None and getattr(default_party, "invoice_layout_lookup", None) is not None
                    else (billing_profile.invoice_layout_code if billing_profile is not None else None)
                ),
                invoice_status_code="draft",
                subtotal_amount=float(totals["subtotal"]),
                tax_amount=float(totals["tax"]),
                total_amount=float(totals["total"]),
                customer_visible_flag=False,
                source_hash=self._build_invoice_source_hash(timesheet, line_rows),
                invoice_email=self._resolve_invoice_email(billing_profile, default_party),
                dispatch_method_code=billing_profile.shipping_method_code if billing_profile is not None else None,
                e_invoice_enabled=bool(billing_profile.e_invoice_enabled) if billing_profile is not None else False,
                leitweg_id=billing_profile.leitweg_id if billing_profile is not None else None,
                payment_terms_days=payment_terms_days,
                billing_profile_snapshot_json=self._snapshot_billing_profile(billing_profile),
                invoice_party_snapshot_json=self._snapshot_invoice_party(default_party),
                delivery_context_json={},
                delivery_status_code="not_queued",
                notes=payload.notes,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
                lines=line_rows,
            )
        )
        self._record_audit(actor, tenant_id, "finance.customer_invoice.generated", "finance.customer_invoice", row.id)
        return self._map_invoice_read(row)

    def issue_invoice(
        self,
        tenant_id: str,
        invoice_id: str,
        payload: InvoiceIssueRequest,
        actor: RequestAuthorizationContext,
    ) -> CustomerInvoiceRead:
        self._require_billing_write(actor, tenant_id)
        row = self._require_invoice(tenant_id, invoice_id)
        self._require_version(row.version_no, payload.version_no, "invoice")
        if row.invoice_status_code not in {"draft", "issued"}:
            raise ApiException(409, "finance.invoice.invalid_stage", "errors.finance.invoice.invalid_stage")
        artifact = self._render_invoice_pdf(row)
        document_id = self._persist_owner_document(
            tenant_id=tenant_id,
            owner_type="finance.customer_invoice",
            owner_id=row.id,
            title=f"Invoice {row.invoice_no}",
            artifact=artifact,
            actor=actor,
        )
        row.invoice_status_code = "issued"
        row.issued_at = datetime.now(UTC)
        row.source_document_id = document_id
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        row = self.repository.save_invoice(row)
        self._record_audit(actor, tenant_id, "finance.customer_invoice.issued", "finance.customer_invoice", row.id)
        return self._map_invoice_read(row)

    def release_invoice(
        self,
        tenant_id: str,
        invoice_id: str,
        payload: InvoiceReleaseRequest,
        actor: RequestAuthorizationContext,
    ) -> CustomerInvoiceRead:
        self._require_billing_write(actor, tenant_id)
        row = self._require_invoice(tenant_id, invoice_id)
        self._require_version(row.version_no, payload.version_no, "invoice")
        if row.invoice_status_code not in {"issued", "released", "queued", "sent"}:
            raise ApiException(409, "finance.invoice.invalid_stage", "errors.finance.invoice.invalid_stage")
        row.invoice_status_code = "released"
        row.customer_visible_flag = payload.customer_visible_flag
        row.released_at = datetime.now(UTC)
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        row = self.repository.save_invoice(row)
        self._record_audit(actor, tenant_id, "finance.customer_invoice.released", "finance.customer_invoice", row.id)
        return self._map_invoice_read(row)

    def queue_invoice_dispatch(
        self,
        tenant_id: str,
        invoice_id: str,
        payload: InvoiceDispatchRequest,
        actor: RequestAuthorizationContext,
    ) -> CustomerInvoiceRead:
        self._require_billing_delivery(actor, tenant_id)
        row = self._require_invoice(tenant_id, invoice_id)
        self._require_version(row.version_no, payload.version_no, "invoice")
        self._validate_dispatch_context(row)
        endpoint = None
        if payload.endpoint_id is not None:
            endpoint = self.repository.get_integration_endpoint(tenant_id, payload.endpoint_id)
        if endpoint is None:
            provider_key = "e_invoice" if row.e_invoice_enabled else "customer_invoice_dispatch"
            endpoint = self.repository.find_integration_endpoint(tenant_id, provider_key, "finance_invoice_delivery")
        job = self.integration_repository.create_job_and_outbox(
            ImportExportJob(
                tenant_id=tenant_id,
                endpoint_id=None if endpoint is None else endpoint.id,
                job_direction="outbound",
                job_type="finance.customer_invoice_delivery",
                request_payload_json={"invoice_id": row.id, "invoice_no": row.invoice_no},
                result_summary_json={},
                requested_by_user_id=actor.user_id,
                started_at=datetime.now(UTC),
            ),
            OutboxEvent(
                tenant_id=tenant_id,
                endpoint_id=None if endpoint is None else endpoint.id,
                aggregate_type="finance.customer_invoice",
                aggregate_id=row.id,
                event_type="finance.customer_invoice.delivery_queued",
                topic="finance.customer_invoice.dispatch",
                payload_json={
                    "invoice_id": row.id,
                    "invoice_no": row.invoice_no,
                    "dispatch_method_code": row.dispatch_method_code,
                    "e_invoice_enabled": row.e_invoice_enabled,
                    "leitweg_id": row.leitweg_id,
                    "invoice_email": row.invoice_email,
                },
                dedupe_key=f"finance.customer_invoice.dispatch:{row.id}:{row.version_no}",
            ),
        )
        row.job_id = job.id
        row.invoice_status_code = "queued"
        row.delivery_status_code = "queued"
        row.delivery_context_json = {
            "endpoint_id": None if endpoint is None else endpoint.id,
            "queued_job_id": job.id,
            "dispatch_method_code": row.dispatch_method_code,
            "e_invoice_enabled": row.e_invoice_enabled,
        }
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        row = self.repository.save_invoice(row)
        self._record_audit(actor, tenant_id, "finance.customer_invoice.delivery_queued", "finance.customer_invoice", row.id)
        return self._map_invoice_read(row)

    def list_customer_portal_timesheets(self, context) -> CustomerPortalTimesheetCollectionRead:  # noqa: ANN001
        filters = TimesheetListFilter(customer_id=context.customer_id, release_state_code="released", customer_visible_only=True)
        rows = self.repository.list_timesheets(context.tenant_id, filters)
        return CustomerPortalTimesheetCollectionRead(
            customer_id=context.customer_id,
            source=CustomerPortalCollectionSourceRead(
                domain_key="timesheets",
                source_module_key="finance",
                availability_status="ready",
                released_only=True,
                customer_scoped=True,
                docs_backed_outputs=True,
                message_key="portalCustomer.datasets.timesheets.pending",
            ),
            items=[
                CustomerPortalTimesheetRead(
                    id=row.id,
                    customer_id=row.customer_id,
                    period_start=row.period_start,
                    period_end=row.period_end,
                    released_at=row.released_at or row.updated_at,
                    status=row.release_state_code,
                    total_minutes=row.total_billable_minutes,
                    documents=self._map_portal_documents(self.repository.list_document_links_for_timesheet(context.tenant_id, row.id)),
                )
                for row in rows
            ],
        )

    def list_customer_portal_invoices(self, context):  # noqa: ANN001
        rows = self.repository.list_invoices(
            context.tenant_id,
            InvoiceListFilter(customer_id=context.customer_id, invoice_status_code="released", customer_visible_only=True),
        )
        return CustomerPortalInvoiceCollectionRead(
            customer_id=context.customer_id,
            source=CustomerPortalCollectionSourceRead(
                domain_key="invoices",
                source_module_key="finance",
                availability_status="ready",
                released_only=True,
                customer_scoped=True,
                docs_backed_outputs=True,
                message_key="portalCustomer.datasets.invoices.pending",
            ),
            items=[
                CustomerPortalInvoiceRead(
                    id=row.id,
                    customer_id=row.customer_id,
                    invoice_no=row.invoice_no,
                    issue_date=row.issue_date,
                    due_date=row.due_date,
                    released_at=row.released_at,
                    status=row.invoice_status_code,
                    currency_code=row.currency_code,
                    total_amount=Decimal(str(row.total_amount)),
                    documents=self._map_portal_documents(self.repository.list_document_links_for_invoice(context.tenant_id, row.id)),
                )
                for row in rows
            ],
        )

    def download_customer_portal_timesheet_document(
        self,
        context,  # noqa: ANN001
        timesheet_id: str,
        document_id: str,
        version_no: int,
    ) -> DocumentDownload:
        row = self._require_timesheet(context.tenant_id, timesheet_id)
        if row.customer_id != context.customer_id or row.release_state_code != "released" or not row.customer_visible_flag:
            raise ApiException(404, "finance.timesheet.not_found", "errors.finance.timesheet.not_found")
        if self.repository.get_document_link_for_timesheet(context.tenant_id, timesheet_id, document_id) is None:
            raise ApiException(404, "docs.document.not_found", "errors.docs.document.not_found")
        return self.document_service.download_document_version(context.tenant_id, document_id, version_no, context)

    def download_customer_portal_invoice_document(
        self,
        context,  # noqa: ANN001
        invoice_id: str,
        document_id: str,
        version_no: int,
    ) -> DocumentDownload:
        row = self._require_invoice(context.tenant_id, invoice_id)
        if row.customer_id != context.customer_id or row.invoice_status_code not in {"released", "queued", "sent"} or not row.customer_visible_flag:
            raise ApiException(404, "finance.invoice.not_found", "errors.finance.invoice.not_found")
        if self.repository.get_document_link_for_invoice(context.tenant_id, invoice_id, document_id) is None:
            raise ApiException(404, "docs.document.not_found", "errors.docs.document.not_found")
        return self.document_service.download_document_version(context.tenant_id, document_id, version_no, context)

    def _require_timesheet(self, tenant_id: str, timesheet_id: str) -> Timesheet:
        row = self.repository.get_timesheet(tenant_id, timesheet_id)
        if row is None:
            raise ApiException(404, "finance.timesheet.not_found", "errors.finance.timesheet.not_found")
        return row

    def _require_invoice(self, tenant_id: str, invoice_id: str) -> CustomerInvoice:
        row = self.repository.get_invoice(tenant_id, invoice_id)
        if row is None:
            raise ApiException(404, "finance.invoice.not_found", "errors.finance.invoice.not_found")
        return row

    def _resolve_invoice_timesheet(self, tenant_id: str, payload: InvoiceGenerateRequest) -> Timesheet:
        if payload.timesheet_id is not None:
            row = self._require_timesheet(tenant_id, payload.timesheet_id)
            if row.customer_id != payload.customer_id:
                raise ApiException(404, "finance.timesheet.not_found", "errors.finance.timesheet.not_found")
            return row
        rows = self.repository.list_timesheets(
            tenant_id,
            TimesheetListFilter(customer_id=payload.customer_id, release_state_code="released", customer_visible_only=False),
        )
        if not rows:
            raise ApiException(404, "finance.timesheet.not_found", "errors.finance.timesheet.not_found")
        return rows[0]

    def _build_timesheet_scope_key(self, payload: TimesheetGenerateRequest) -> str:
        return "|".join(
            [
                payload.customer_id,
                payload.order_id or "-",
                payload.planning_record_id or "-",
                payload.period_start.isoformat(),
                payload.period_end.isoformat(),
                payload.billing_granularity_code,
            ]
        )

    def _build_timesheet_source_hash(self, actuals: list) -> str:  # noqa: ANN401
        joined = "|".join(f"{row.id}:{row.billable_minutes}:{row.customer_adjustment_minutes}" for row in actuals)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def _build_timesheet_line(self, tenant_id: str, index: int, actual, granularity_code: str) -> TimesheetLine:  # noqa: ANN001
        planning_record = actual.shift.shift_plan.planning_record
        order = planning_record.order
        planned_minutes = self._minutes_between(actual.planned_start_at, actual.planned_end_at) - actual.planned_break_minutes
        actual_minutes = self._minutes_between(actual.actual_start_at, actual.actual_end_at) - actual.actual_break_minutes
        billable_minutes = actual.billable_minutes
        return TimesheetLine(
            tenant_id=tenant_id,
            actual_record_id=actual.id,
            shift_id=actual.shift_id,
            order_id=order.id,
            planning_record_id=planning_record.id,
            sort_order=index * 100,
            service_date=(actual.planned_start_at or actual.derived_at).date(),
            planning_mode_code=planning_record.planning_mode_code,
            line_label=self._build_operational_label(planning_record),
            line_description=self._build_customer_safe_description(planning_record, actual.shift),
            planned_minutes=max(planned_minutes, 0),
            actual_minutes=max(actual_minutes, 0),
            billable_minutes=billable_minutes,
            quantity=float(self._derive_quantity(billable_minutes, "hour")),
            unit_code="hour",
            source_ref_json={
                "granularity_code": granularity_code,
                "customer_id": order.customer_id,
                "order_id": order.id,
                "planning_record_id": planning_record.id,
                "shift_id": actual.shift_id,
            },
            customer_safe_flag=True,
            personal_names_released=False,
        )

    def _build_timesheet_headline(self, payload: TimesheetGenerateRequest, actual) -> str:  # noqa: ANN001
        planning_record = actual.shift.shift_plan.planning_record
        order = planning_record.order
        if payload.planning_record_id is not None:
            return f"{order.order_no} · {planning_record.name}"
        if payload.order_id is not None:
            return f"{order.order_no} · {payload.period_start:%d.%m.%Y}-{payload.period_end:%d.%m.%Y}"
        return f"{order.customer.customer_number if getattr(order, 'customer', None) is not None else 'CUSTOMER'} · {payload.period_start:%d.%m.%Y}-{payload.period_end:%d.%m.%Y}"

    def _build_operational_label(self, planning_record) -> str:  # noqa: ANN001
        order = planning_record.order
        return f"{order.order_no} · {planning_record.name}"

    def _build_customer_safe_description(self, planning_record, shift) -> str:  # noqa: ANN001
        base = planning_record.name
        if planning_record.planning_mode_code == "event" and planning_record.event_detail is not None:
            venue = planning_record.event_detail.event_venue
            return f"{base} · {venue.name}"
        if planning_record.planning_mode_code == "site" and planning_record.site_detail is not None:
            return f"{base} · {planning_record.site_detail.site.name}"
        if planning_record.planning_mode_code == "trade_fair" and planning_record.trade_fair_detail is not None:
            fair = planning_record.trade_fair_detail.trade_fair.name
            zone = planning_record.trade_fair_detail.trade_fair_zone.name if planning_record.trade_fair_detail.trade_fair_zone is not None else None
            return f"{base} · {fair}" if zone is None else f"{base} · {fair} · {zone}"
        if planning_record.planning_mode_code == "patrol" and planning_record.patrol_detail is not None:
            return f"{base} · {planning_record.patrol_detail.patrol_route.name}"
        return f"{base} · {shift.location_text or shift.meeting_point or 'service'}"

    @staticmethod
    def _summarize_timesheet_lines(lines: list[TimesheetLine]) -> dict[str, int]:
        return {
            "planned": sum(row.planned_minutes for row in lines),
            "actual": sum(row.actual_minutes for row in lines),
            "billable": sum(row.billable_minutes for row in lines),
        }

    def _render_timesheet_pdf(self, row: Timesheet) -> RenderedDocumentArtifact:
        body = [
            f"Timesheet: {row.headline}",
            f"Period: {row.period_start} - {row.period_end}",
            "",
        ]
        for line in row.lines:
            body.append(f"{line.service_date} | {line.line_label} | {line.billable_minutes} min | {line.line_description}")
        return self._render_pseudo_pdf(f"timesheet-{row.id}.pdf", "\n".join(body), {"timesheet_id": row.id})

    def _build_invoice_lines(self, timesheet: Timesheet, rate_card) -> list[CustomerInvoiceLine]:  # noqa: ANN001
        lines: list[CustomerInvoiceLine] = []
        sort_order = 100
        for ts_line in timesheet.lines:
            rate_line = self._resolve_rate_line(rate_card, ts_line)
            if rate_line is None:
                continue
            quantity = self._derive_quantity(ts_line.billable_minutes, rate_line.billing_unit)
            if rate_line.minimum_quantity is not None:
                quantity = max(quantity, Decimal(str(rate_line.minimum_quantity)))
            unit_price = Decimal(str(rate_line.unit_price))
            tax_rate = Decimal("19.00")
            net_amount = (quantity * unit_price).quantize(Decimal("0.01"))
            tax_amount = (net_amount * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
            lines.append(
                CustomerInvoiceLine(
                    tenant_id=timesheet.tenant_id,
                    timesheet_line_id=ts_line.id,
                    source_actual_id=ts_line.actual_record_id,
                    rate_card_id=rate_card.id,
                    rate_line_id=rate_line.id,
                    sort_order=sort_order,
                    line_kind_code="base",
                    description=ts_line.line_description,
                    quantity=float(quantity),
                    unit_code=rate_line.billing_unit,
                    unit_price=float(unit_price),
                    tax_rate=float(tax_rate),
                    net_amount=float(net_amount),
                    tax_amount=float(tax_amount),
                    gross_amount=float((net_amount + tax_amount).quantize(Decimal("0.01"))),
                    source_ref_json={"timesheet_line_id": ts_line.id},
                )
            )
            sort_order += 100
            surcharge = self._resolve_customer_surcharge(rate_card, ts_line, net_amount)
            if surcharge is not None:
                surcharge["sort_order"] = sort_order
                lines.append(
                    CustomerInvoiceLine(
                        tenant_id=timesheet.tenant_id,
                        timesheet_line_id=ts_line.id,
                        source_actual_id=ts_line.actual_record_id,
                        rate_card_id=rate_card.id,
                        rate_line_id=None,
                        surcharge_rule_id=surcharge["rule_id"],
                        sort_order=sort_order,
                        line_kind_code="surcharge",
                        description=surcharge["description"],
                        quantity=1.0,
                        unit_code="flat",
                        unit_price=float(surcharge["net_amount"]),
                        tax_rate=float(tax_rate),
                        net_amount=float(surcharge["net_amount"]),
                        tax_amount=float(surcharge["tax_amount"]),
                        gross_amount=float(surcharge["gross_amount"]),
                        source_ref_json={"timesheet_line_id": ts_line.id, "surcharge_rule_id": surcharge["rule_id"]},
                    )
                )
                sort_order += 100
        return lines

    def _resolve_rate_line(self, rate_card, ts_line):  # noqa: ANN001
        for row in sorted(rate_card.rate_lines, key=lambda item: item.sort_order):
            if row.planning_mode_code not in (None, ts_line.planning_mode_code):
                continue
            return row
        return None

    def _resolve_customer_surcharge(self, rate_card, ts_line: TimesheetLine, base_net_amount: Decimal):  # noqa: ANN001
        weekday = datetime.combine(ts_line.service_date, datetime.min.time()).weekday()
        weekday_mask = ["1" if index == weekday else "0" for index in range(7)]
        for row in sorted(rate_card.surcharge_rules, key=lambda item: item.sort_order):
            if row.weekday_mask is not None and row.weekday_mask != "".join(weekday_mask):
                continue
            if row.percent_value is None and row.fixed_amount is None:
                continue
            net_amount = Decimal(str(row.fixed_amount or 0))
            if row.percent_value is not None:
                net_amount += (base_net_amount * Decimal(str(row.percent_value)) / Decimal("100")).quantize(Decimal("0.01"))
            tax_amount = (net_amount * Decimal("19.00") / Decimal("100")).quantize(Decimal("0.01"))
            return {
                "rule_id": row.id,
                "description": f"Surcharge {row.surcharge_type}",
                "net_amount": net_amount.quantize(Decimal("0.01")),
                "tax_amount": tax_amount,
                "gross_amount": (net_amount + tax_amount).quantize(Decimal("0.01")),
            }
        return None

    @staticmethod
    def _summarize_invoice_lines(lines: list[CustomerInvoiceLine]) -> dict[str, Decimal]:
        subtotal = sum((Decimal(str(line.net_amount)) for line in lines), Decimal("0.00"))
        tax = sum((Decimal(str(line.tax_amount)) for line in lines), Decimal("0.00"))
        return {"subtotal": subtotal.quantize(Decimal("0.01")), "tax": tax.quantize(Decimal("0.01")), "total": (subtotal + tax).quantize(Decimal("0.01"))}

    def _build_invoice_source_hash(self, timesheet: Timesheet, lines: list[CustomerInvoiceLine]) -> str:
        joined = "|".join(f"{timesheet.id}:{line.source_actual_id}:{line.description}:{line.net_amount}" for line in lines)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def _build_invoice_number(self, issue_date: date, timesheet: Timesheet) -> str:
        customer_number = timesheet.customer.customer_number if getattr(timesheet, "customer", None) is not None else "CUSTOMER"
        return f"INV-{issue_date:%Y%m%d}-{customer_number}-{timesheet.id[:8].upper()}"

    def _render_invoice_pdf(self, row: CustomerInvoice) -> RenderedDocumentArtifact:
        body = [
            f"Invoice: {row.invoice_no}",
            f"Issue date: {row.issue_date}",
            f"Due date: {row.due_date}",
            f"Total: {row.total_amount} {row.currency_code}",
            "",
        ]
        for line in row.lines:
            body.append(f"{line.description} | {line.quantity} {line.unit_code} | {line.net_amount}")
        return self._render_pseudo_pdf(f"invoice-{row.invoice_no}.pdf", "\n".join(body), {"invoice_id": row.id})

    def _persist_owner_document(
        self,
        *,
        tenant_id: str,
        owner_type: str,
        owner_id: str,
        title: str,
        artifact: RenderedDocumentArtifact,
        actor: RequestAuthorizationContext,
    ) -> str:
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=title,
                document_type_key=None,
                source_module="finance",
                source_label=owner_type,
                metadata_json=artifact.metadata_json,
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
                is_revision_safe_pdf=True,
                metadata_json=artifact.metadata_json,
            ),
            actor,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(owner_type=owner_type, owner_id=owner_id, relation_type="generated_output", label=title),
            actor,
        )
        return document.id

    @staticmethod
    def _render_pseudo_pdf(file_name: str, text_body: str, metadata_json: dict[str, object]) -> RenderedDocumentArtifact:
        buffer = BytesIO()
        buffer.write(b"%PDF-1.4\n")
        buffer.write(text_body.encode("utf-8"))
        buffer.write(b"\n%%EOF")
        return RenderedDocumentArtifact(
            file_name=file_name,
            content_type="application/pdf",
            content=buffer.getvalue(),
            metadata_json=metadata_json,
        )

    @staticmethod
    def _snapshot_billing_profile(profile) -> dict[str, object]:  # noqa: ANN001
        if profile is None:
            return {}
        return {
            "invoice_email": profile.invoice_email,
            "payment_terms_days": profile.payment_terms_days,
            "invoice_layout_code": profile.invoice_layout_code,
            "shipping_method_code": profile.shipping_method_code,
            "e_invoice_enabled": profile.e_invoice_enabled,
            "leitweg_id": profile.leitweg_id,
        }

    @staticmethod
    def _snapshot_invoice_party(party) -> dict[str, object]:  # noqa: ANN001
        if party is None:
            return {}
        address = party.address
        return {
            "name": party.name,
            "contact_name": party.contact_name,
            "invoice_email": party.invoice_email,
            "street_line_1": None if address is None else address.street_line_1,
            "postal_code": None if address is None else address.postal_code,
            "city": None if address is None else address.city,
            "country_code": None if address is None else address.country_code,
        }

    @staticmethod
    def _resolve_invoice_email(profile, party) -> str | None:  # noqa: ANN001
        if party is not None and party.invoice_email:
            return party.invoice_email
        if profile is not None:
            return profile.invoice_email
        return None

    def _validate_dispatch_context(self, row: CustomerInvoice) -> None:
        method = row.dispatch_method_code or "email_pdf"
        if method == "e_invoice":
            if not row.e_invoice_enabled:
                raise ApiException(409, "finance.invoice.delivery.e_invoice_required", "errors.finance.invoice.delivery.e_invoice_required")
            if not row.leitweg_id:
                raise ApiException(409, "finance.invoice.delivery.leitweg_required", "errors.finance.invoice.delivery.leitweg_required")
        if method == "email_pdf" and not row.invoice_email:
            raise ApiException(409, "finance.invoice.delivery.email_required", "errors.finance.invoice.delivery.email_required")

    @staticmethod
    def _derive_quantity(minutes: int, unit_code: str) -> Decimal:
        if unit_code == "minute":
            return Decimal(minutes)
        if unit_code == "hour":
            return (Decimal(minutes) / Decimal("60")).quantize(Decimal("0.01"))
        return Decimal("1.00")

    @staticmethod
    def _minutes_between(start: datetime | None, end: datetime | None) -> int:
        if start is None or end is None:
            return 0
        return max(int((end - start).total_seconds() // 60), 0)

    @staticmethod
    def _map_portal_documents(links) -> list[CustomerPortalDocumentRefRead]:  # noqa: ANN001
        rows = []
        for link in links:
            document = link.document
            current_version = None if document is None else next((row for row in document.versions if row.version_no == document.current_version_no), None)
            rows.append(
                CustomerPortalDocumentRefRead(
                    document_id=link.document_id,
                    title=document.title if document is not None else (link.label or link.document_id),
                    document_type_key=None if document is None or document.document_type is None else document.document_type.key,
                    file_name=None if current_version is None else current_version.file_name,
                    content_type=None if current_version is None else current_version.content_type,
                    current_version_no=None if current_version is None else current_version.version_no,
                    is_name_masked=True,
                )
            )
        return rows

    def _map_timesheet_list_item(self, row: Timesheet) -> TimesheetListItem:
        return TimesheetListItem.model_validate(row)

    def _map_timesheet_read(self, row: Timesheet) -> TimesheetRead:
        return TimesheetRead.model_validate(row)

    def _map_invoice_list_item(self, row: CustomerInvoice) -> CustomerInvoiceListItem:
        return CustomerInvoiceListItem.model_validate(row)

    def _map_invoice_read(self, row: CustomerInvoice) -> CustomerInvoiceRead:
        return CustomerInvoiceRead.model_validate(row)

    def _record_audit(self, actor: RequestAuthorizationContext, tenant_id: str, event_type: str, entity_type: str, entity_id: str) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(tenant_id=tenant_id, user_id=actor.user_id, request_id=actor.request_id),
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            after_json={},
        )

    @staticmethod
    def _require_version(current_version: int, requested_version: int, entity_key: str) -> None:
        if current_version != requested_version:
            raise ApiException(409, f"finance.{entity_key}.stale_version", f"errors.finance.{entity_key}.stale_version")

    @staticmethod
    def _require_billing_read(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.tenant_id == tenant_id and "finance.billing.read" in actor.permission_keys:
            return
        raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")

    @staticmethod
    def _require_billing_write(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.tenant_id == tenant_id and "finance.billing.write" in actor.permission_keys:
            return
        raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")

    @staticmethod
    def _require_billing_delivery(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.tenant_id == tenant_id and "finance.billing.delivery" in actor.permission_keys:
            return
        raise ApiException(403, "iam.authorization.permission_denied", "errors.iam.authorization.permission_denied")
