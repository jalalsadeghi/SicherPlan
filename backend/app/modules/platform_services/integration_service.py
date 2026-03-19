"""Integration endpoint management, job lifecycle, and outbox worker services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_schemas import DocumentLinkCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.integration_models import ImportExportJob, IntegrationEndpoint, OutboxEvent
from app.modules.platform_services.integration_schemas import (
    ImportExportJobCreate,
    ImportExportJobRead,
    IntegrationEndpointCreate,
    IntegrationEndpointRead,
    OutboxEventRead,
)
from app.modules.platform_services.integration_security import IntegrationSecretBox


class IntegrationRepository(Protocol):
    def create_endpoint(self, row: IntegrationEndpoint) -> IntegrationEndpoint: ...
    def list_endpoints(self, tenant_id: str) -> list[IntegrationEndpoint]: ...
    def get_endpoint(self, tenant_id: str, endpoint_id: str) -> IntegrationEndpoint | None: ...
    def create_job_and_outbox(self, job: ImportExportJob, outbox_event: OutboxEvent) -> ImportExportJob: ...
    def save_job(self, row: ImportExportJob) -> ImportExportJob: ...
    def get_job(self, tenant_id: str, job_id: str) -> ImportExportJob | None: ...
    def list_document_links_for_job(self, tenant_id: str, job_id: str): ...  # noqa: ANN001
    def create_outbox_event(self, row: OutboxEvent) -> OutboxEvent: ...
    def list_pending_outbox_events(self, tenant_id: str | None, limit: int, now: datetime) -> list[OutboxEvent]: ...
    def save_outbox_event(self, row: OutboxEvent) -> OutboxEvent: ...


@dataclass(frozen=True, slots=True)
class PublicationResult:
    provider_ref: str | None
    status: str


class OutboxPublisherAdapter(Protocol):
    def publish(self, event: OutboxEvent, endpoint: IntegrationEndpoint | None) -> PublicationResult: ...


class DevOutboxPublisher:
    def publish(self, event: OutboxEvent, endpoint: IntegrationEndpoint | None) -> PublicationResult:
        if event.payload_json.get("simulate_failure"):
            raise RuntimeError("simulated failure")
        provider_ref = None
        if endpoint is not None:
            provider_ref = f"{endpoint.provider_key}:{event.id}"
        return PublicationResult(provider_ref=provider_ref, status="published")


class IntegrationService:
    def __init__(
        self,
        repository: IntegrationRepository,
        *,
        document_service: DocumentService,
        secret_box: IntegrationSecretBox,
        outbox_publisher: OutboxPublisherAdapter | None = None,
        retry_delay_seconds: int = 60,
        max_attempts: int = 3,
    ) -> None:
        self.repository = repository
        self.document_service = document_service
        self.secret_box = secret_box
        self.outbox_publisher = outbox_publisher or DevOutboxPublisher()
        self.retry_delay_seconds = retry_delay_seconds
        self.max_attempts = max_attempts

    def register_endpoint(
        self,
        tenant_id: str,
        payload: IntegrationEndpointCreate,
        actor: RequestAuthorizationContext,
    ) -> IntegrationEndpointRead:
        self._ensure_tenant_scope(actor, tenant_id)
        try:
            row = self.repository.create_endpoint(
                IntegrationEndpoint(
                    tenant_id=tenant_id,
                    provider_key=payload.provider_key,
                    endpoint_type=payload.endpoint_type,
                    base_url=payload.base_url,
                    auth_mode=payload.auth_mode,
                    config_public_json=payload.config_public_json,
                    secret_ciphertext=self.secret_box.seal(payload.secret_config_json),
                    created_by_user_id=actor.user_id,
                    updated_by_user_id=actor.user_id,
                )
            )
        except IntegrityError as exc:
            raise ApiException(
                409,
                "integration.endpoint.duplicate_provider",
                "errors.integration.endpoint.duplicate_provider",
            ) from exc
        return IntegrationEndpointRead.model_validate(row)

    def list_endpoints(self, tenant_id: str, actor: RequestAuthorizationContext) -> list[IntegrationEndpointRead]:
        self._ensure_tenant_scope(actor, tenant_id)
        return [IntegrationEndpointRead.model_validate(row) for row in self.repository.list_endpoints(tenant_id)]

    def request_job(
        self,
        tenant_id: str,
        payload: ImportExportJobCreate,
        actor: RequestAuthorizationContext,
    ) -> ImportExportJobRead:
        self._ensure_tenant_scope(actor, tenant_id)
        endpoint_id = payload.endpoint_id
        if endpoint_id is not None and self.repository.get_endpoint(tenant_id, endpoint_id) is None:
            raise ApiException(404, "integration.endpoint.not_found", "errors.integration.endpoint.not_found")
        job = self.repository.create_job_and_outbox(
            ImportExportJob(
                tenant_id=tenant_id,
                endpoint_id=endpoint_id,
                job_direction=payload.job_direction,
                job_type=payload.job_type,
                request_payload_json=payload.request_payload_json,
                requested_by_user_id=actor.user_id,
                status="requested",
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            ),
            OutboxEvent(
                tenant_id=tenant_id,
                endpoint_id=endpoint_id,
                aggregate_type="integration.import_export_job",
                aggregate_id="pending",
                event_type=f"integration.job.{payload.job_direction}_requested",
                topic="integration.jobs",
                payload_json={
                    "job_type": payload.job_type,
                    "job_direction": payload.job_direction,
                    "request_payload_json": payload.request_payload_json,
                },
                dedupe_key=f"job:{tenant_id}:{payload.job_direction}:{payload.job_type}:{actor.user_id}:{datetime.now(UTC).timestamp()}",
                status="pending",
            ),
        )
        if payload.result_document_id:
            self.attach_result_document(tenant_id, job.id, payload.result_document_id, actor)
        return self._to_job_read(job)

    def get_job(self, tenant_id: str, job_id: str, actor: RequestAuthorizationContext) -> ImportExportJobRead:
        self._ensure_tenant_scope(actor, tenant_id)
        job = self.repository.get_job(tenant_id, job_id)
        if job is None:
            raise ApiException(404, "integration.job.not_found", "errors.integration.job.not_found")
        return self._to_job_read(job)

    def attach_result_document(self, tenant_id: str, job_id: str, document_id: str, actor: RequestAuthorizationContext) -> None:
        self.document_service.get_document(tenant_id, document_id, actor)
        self.document_service.add_document_link(
            tenant_id,
            document_id,
            DocumentLinkCreate(
                owner_type="integration.import_export_job",
                owner_id=job_id,
                relation_type="result",
            ),
            actor,
        )

    def process_outbox(self, *, tenant_id: str | None, worker_name: str, limit: int) -> list[OutboxEventRead]:
        if not settings.integration_outbox_enabled:
            return []
        now = datetime.now(UTC)
        processed: list[OutboxEventRead] = []
        for event in self.repository.list_pending_outbox_events(tenant_id, limit, now):
            endpoint = None
            if event.tenant_id and event.endpoint_id:
                endpoint = self.repository.get_endpoint(event.tenant_id, event.endpoint_id)
            try:
                if event.aggregate_type == "integration.import_export_job" and event.tenant_id is not None:
                    self._start_job(event.tenant_id, event.aggregate_id)
                result = self.outbox_publisher.publish(event, endpoint)
                event.status = result.status
                event.published_at = now
                event.processed_by = worker_name
                event.attempt_count += 1
                event.last_error_code = None
                event.last_error_summary = None
                event.updated_at = now
                self.repository.save_outbox_event(event)
                if event.aggregate_type == "integration.import_export_job" and event.tenant_id is not None:
                    self._complete_job(event.tenant_id, event.aggregate_id, provider_ref=result.provider_ref)
            except Exception as exc:  # noqa: BLE001
                event.attempt_count += 1
                exhausted = event.attempt_count >= self.max_attempts
                event.status = "failed" if exhausted else "retry"
                event.last_error_code = exc.__class__.__name__
                event.last_error_summary = str(exc)
                event.next_attempt_at = None if exhausted else now + timedelta(seconds=self.retry_delay_seconds)
                event.processed_by = worker_name
                event.updated_at = now
                self.repository.save_outbox_event(event)
                if event.aggregate_type == "integration.import_export_job" and event.tenant_id is not None and exhausted:
                    self._fail_job(event.tenant_id, event.aggregate_id, error_summary=str(exc))
            processed.append(OutboxEventRead.model_validate(event))
        return processed

    def _start_job(self, tenant_id: str, job_id: str) -> None:
        job = self.repository.get_job(tenant_id, job_id)
        if job is None or job.status not in {"requested", "retry"}:
            return
        now = datetime.now(UTC)
        job.status = "started"
        job.started_at = job.started_at or now
        job.version_no += 1
        self.repository.save_job(job)

    def _complete_job(self, tenant_id: str, job_id: str, *, provider_ref: str | None) -> None:
        job = self.repository.get_job(tenant_id, job_id)
        if job is None or job.status == "completed":
            return
        now = datetime.now(UTC)
        if job.started_at is None:
            job.started_at = now
        job.completed_at = now
        job.status = "completed"
        job.result_summary_json = {"provider_ref": provider_ref} if provider_ref else {}
        job.version_no += 1
        self.repository.save_job(job)

    def _fail_job(self, tenant_id: str, job_id: str, *, error_summary: str) -> None:
        job = self.repository.get_job(tenant_id, job_id)
        if job is None:
            return
        now = datetime.now(UTC)
        job.status = "failed"
        job.error_summary = error_summary
        job.completed_at = now
        job.version_no += 1
        self.repository.save_job(job)

    def _to_job_read(self, job: ImportExportJob) -> ImportExportJobRead:
        result_document_ids = [link.document_id for link in self.repository.list_document_links_for_job(job.tenant_id, job.id)]
        schema = ImportExportJobRead.model_validate(job)
        return schema.model_copy(update={"result_document_ids": result_document_ids})

    @staticmethod
    def _ensure_tenant_scope(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.is_platform_admin or actor.tenant_id == tenant_id:
            return
        raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")
