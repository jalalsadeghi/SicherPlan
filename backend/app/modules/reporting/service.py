"""Reporting query service, CSV export shaping, and delivery hooks."""

from __future__ import annotations

import csv
from base64 import b64encode
from datetime import UTC, datetime
from io import StringIO
from typing import Any, Protocol

from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.integration_models import ImportExportJob, OutboxEvent
from app.modules.reporting.repository import ReportingRepository, serialize_rows_for_csv
from app.modules.reporting.schemas import (
    ReportExportEnvelope,
    ReportingDeliveryJobRead,
    ReportingDeliveryRequest,
    ReportingFilterBase,
)


class ReportingIntegrationRepository(Protocol):
    def get_endpoint(self, tenant_id: str, endpoint_id: str): ...  # noqa: ANN001
    def create_job_and_outbox(self, job: ImportExportJob, outbox_event: OutboxEvent) -> ImportExportJob: ...  # noqa: ANN001


DELIVERABLE_REPORT_KEYS = frozenset(
    {
        "compliance-status",
        "notice-read-stats",
        "free-sundays",
        "absence-visibility",
        "inactivity-signals",
        "security-activity",
    }
)


class ReportingService:
    def __init__(
        self,
        repository: ReportingRepository,
        *,
        document_service: DocumentService | None = None,
        integration_repository: ReportingIntegrationRepository | None = None,
    ) -> None:
        self._repository = repository
        self._document_service = document_service
        self._integration_repository = integration_repository

    def list_employee_activity(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        self._require_tenant_or_platform_scope(actor)
        return self._repository.list_employee_activity(
            tenant_id,
            filters,
        )

    def list_customer_revenue(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        return self._repository.list_customer_revenue(
            tenant_id,
            filters,
            allowed_customer_ids=self._allowed_customer_ids(actor),
        )

    def list_subcontractor_control(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        return self._repository.list_subcontractor_control(
            tenant_id,
            filters,
            allowed_subcontractor_ids=self._allowed_subcontractor_ids(actor),
        )

    def list_planning_performance(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        return self._repository.list_planning_performance(
            tenant_id,
            filters,
            allowed_customer_ids=self._allowed_customer_ids(actor),
        )

    def list_payroll_basis(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        self._require_tenant_or_platform_scope(actor)
        return self._repository.list_payroll_basis(tenant_id, filters)

    def list_customer_profitability(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        return self._repository.list_customer_profitability(
            tenant_id,
            filters,
            allowed_customer_ids=self._allowed_customer_ids(actor),
        )

    def list_compliance_status(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        self._require_tenant_or_platform_scope(actor)
        return self._repository.list_compliance_status(tenant_id, filters)

    def list_notice_read_stats(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        self._require_tenant_or_platform_scope(actor)
        return self._repository.list_notice_read_stats(tenant_id, filters)

    def list_free_sundays(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        self._require_tenant_or_platform_scope(actor)
        rows = self._repository.list_free_sundays(tenant_id, filters)
        if filters.free_sunday_threshold is None:
            return rows
        threshold = filters.free_sunday_threshold
        return [
            row.model_copy(
                update={
                    "threshold_days_or_count": threshold,
                    "status_code": "compliant" if row.free_sunday_count >= threshold else "non_compliant",
                    "severity_code": "info" if row.free_sunday_count >= threshold else "warning",
                }
            )
            for row in rows
        ]

    def list_absence_visibility(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        self._require_tenant_or_platform_scope(actor)
        return self._repository.list_absence_visibility(tenant_id, filters)

    def list_inactivity_signals(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        self._require_tenant_or_platform_scope(actor)
        rows = self._repository.list_inactivity_signals(tenant_id, filters)
        if filters.inactivity_threshold_days is None:
            return rows
        threshold = filters.inactivity_threshold_days
        return [
            row.model_copy(
                update={
                    "inactivity_threshold_days": threshold,
                    "status_code": (
                        row.status_code
                        if row.account_status != "active"
                        else ("never_logged_in" if row.last_login_at is None else ("inactive" if (row.days_since_last_login or 0) >= threshold else "active"))
                    ),
                    "severity_code": (
                        row.severity_code
                        if row.account_status != "active"
                        else ("warning" if row.last_login_at is None or (row.days_since_last_login or 0) >= threshold else "info")
                    ),
                }
            )
            for row in rows
        ]

    def list_security_activity(
        self,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        self._enforce_same_tenant(actor, tenant_id)
        self._require_tenant_or_platform_scope(actor)
        return self._repository.list_security_activity(tenant_id, filters)

    def export_csv(
        self,
        report_key: str,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ) -> tuple[ReportExportEnvelope, str]:
        rows = self._resolve_report(report_key, tenant_id, filters, actor)
        columns, data = serialize_rows_for_csv(rows)
        buffer = StringIO()
        writer = csv.writer(buffer)
        if columns:
            writer.writerow(columns)
            writer.writerows(data)
        return (
            ReportExportEnvelope(
                report_key=report_key,
                generated_at=datetime.now(UTC),
                row_count=len(rows),
                applied_filters=filters.model_dump(exclude_none=True),
            ),
            buffer.getvalue(),
        )

    def queue_export_delivery(
        self,
        report_key: str,
        tenant_id: str,
        filters: ReportingFilterBase,
        payload: ReportingDeliveryRequest,
        actor: RequestAuthorizationContext,
    ) -> ReportingDeliveryJobRead:
        self._enforce_same_tenant(actor, tenant_id)
        if report_key not in DELIVERABLE_REPORT_KEYS:
            raise ApiException(409, "reporting.delivery.report_not_supported", "errors.reporting.delivery.report_not_supported")
        if self._document_service is None or self._integration_repository is None:
            raise ApiException(503, "reporting.delivery.unavailable", "errors.reporting.delivery.unavailable")
        endpoint = None
        if payload.endpoint_id is not None:
            endpoint = self._integration_repository.get_endpoint(tenant_id, payload.endpoint_id)
            if endpoint is None:
                raise ApiException(404, "integration.endpoint.not_found", "errors.integration.endpoint.not_found")
        envelope, csv_payload = self.export_csv(report_key, tenant_id, filters, actor)
        document = self._document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=f"Reporting export {report_key} {envelope.generated_at.date().isoformat()}",
                source_module="reporting",
                source_label="reporting_export",
                metadata_json={
                    "report_key": report_key,
                    "applied_filters": envelope.applied_filters,
                    "row_count": envelope.row_count,
                },
            ),
            actor,
        )
        self._document_service.add_document_version(
            tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=f"{report_key}.csv",
                content_type="text/csv",
                content_base64=b64encode(csv_payload.encode("utf-8")).decode("ascii"),
                metadata_json={"report_key": report_key},
            ),
            actor,
        )
        scheduled_for = payload.scheduled_for
        job = self._integration_repository.create_job_and_outbox(
            ImportExportJob(
                tenant_id=tenant_id,
                endpoint_id=None if endpoint is None else endpoint.id,
                job_direction="outbound",
                job_type="reporting_export",
                request_payload_json={
                    "report_key": report_key,
                    "applied_filters": envelope.applied_filters,
                    "scheduled_for": None if scheduled_for is None else scheduled_for.isoformat(),
                    "target_label": payload.target_label,
                    "target_address": payload.target_address,
                    "note_text": payload.note_text,
                    "document_id": document.id,
                },
                result_summary_json={"row_count": envelope.row_count},
                requested_by_user_id=actor.user_id,
                status="requested",
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            ),
            OutboxEvent(
                tenant_id=tenant_id,
                endpoint_id=None if endpoint is None else endpoint.id,
                aggregate_type="integration.import_export_job",
                aggregate_id="",
                event_type="reporting.export.delivery_requested",
                topic="reporting.export.delivery",
                payload_json={
                    "report_key": report_key,
                    "document_id": document.id,
                    "row_count": envelope.row_count,
                    "target_label": payload.target_label,
                    "target_address": payload.target_address,
                },
                dedupe_key=f"reporting.export:{tenant_id}:{report_key}:{actor.user_id}:{envelope.generated_at.isoformat()}",
                status="retry" if scheduled_for is not None else "pending",
                next_attempt_at=scheduled_for,
            ),
        )
        self._document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type="integration.import_export_job",
                owner_id=job.id,
                relation_type="generated_output",
                label=report_key,
                metadata_json={"report_key": report_key},
            ),
            actor,
        )
        history = self._repository.list_reporting_delivery_jobs(tenant_id, report_key=report_key, limit=1)
        return history[0]

    def list_delivery_jobs(
        self,
        tenant_id: str,
        *,
        report_key: str | None,
        actor: RequestAuthorizationContext,
        limit: int = 50,
    ) -> list[ReportingDeliveryJobRead]:
        self._enforce_same_tenant(actor, tenant_id)
        self._require_tenant_or_platform_scope(actor)
        return self._repository.list_reporting_delivery_jobs(tenant_id, report_key=report_key, limit=limit)

    def _resolve_report(
        self,
        report_key: str,
        tenant_id: str,
        filters: ReportingFilterBase,
        actor: RequestAuthorizationContext,
    ):
        report_map = {
            "employee-activity": self.list_employee_activity,
            "customer-revenue": self.list_customer_revenue,
            "subcontractor-control": self.list_subcontractor_control,
            "planning-performance": self.list_planning_performance,
            "payroll-basis": self.list_payroll_basis,
            "customer-profitability": self.list_customer_profitability,
            "compliance-status": self.list_compliance_status,
            "notice-read-stats": self.list_notice_read_stats,
            "free-sundays": self.list_free_sundays,
            "absence-visibility": self.list_absence_visibility,
            "inactivity-signals": self.list_inactivity_signals,
            "security-activity": self.list_security_activity,
        }
        handler = report_map.get(report_key)
        if handler is None:
            raise ApiException(404, "reporting.report.not_found", "errors.reporting.report.not_found", {"report_key": report_key})
        return handler(tenant_id, filters, actor)

    def _enforce_same_tenant(self, actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.is_platform_admin:
            return
        if actor.tenant_id != tenant_id:
            raise ApiException(
                403,
                "iam.authorization.scope_denied",
                "errors.iam.authorization.scope_denied",
                {"scope": "tenant", "tenant_id": tenant_id},
            )

    def _require_tenant_or_platform_scope(self, actor: RequestAuthorizationContext) -> None:
        if actor.is_platform_admin or any(scope.scope_type == "tenant" for scope in actor.scopes):
            return
        raise ApiException(
            403,
            "iam.authorization.scope_denied",
            "errors.iam.authorization.scope_denied",
            {"scope": "tenant"},
        )

    def _allowed_customer_ids(self, actor: RequestAuthorizationContext) -> set[str] | None:
        if actor.is_platform_admin or any(scope.scope_type == "tenant" for scope in actor.scopes):
            return None
        scoped_ids = {scope.customer_id for scope in actor.scopes if scope.scope_type == "customer" and scope.customer_id}
        return scoped_ids or None

    def _allowed_subcontractor_ids(self, actor: RequestAuthorizationContext) -> set[str] | None:
        if actor.is_platform_admin or any(scope.scope_type == "tenant" for scope in actor.scopes):
            return None
        scoped_ids = {
            scope.subcontractor_id
            for scope in actor.scopes
            if scope.scope_type == "subcontractor" and scope.subcontractor_id
        }
        return scoped_ids or None
