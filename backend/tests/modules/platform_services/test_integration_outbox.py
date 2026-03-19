from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import Index, UniqueConstraint

from app.db import Base
from app.errors import ApiException
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.integration_models import ImportExportJob, IntegrationEndpoint, OutboxEvent
from app.modules.platform_services.integration_schemas import ImportExportJobCreate, IntegrationEndpointCreate
from app.modules.platform_services.integration_security import IntegrationSecretBox
from app.modules.platform_services.integration_service import IntegrationService, PublicationResult


@dataclass
class FakeEndpoint:
    id: str
    tenant_id: str
    provider_key: str
    endpoint_type: str
    base_url: str
    auth_mode: str
    config_public_json: dict[str, object]
    secret_ciphertext: str | None
    last_tested_at: datetime | None = None
    status: str = "active"
    version_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeJob:
    id: str
    tenant_id: str
    endpoint_id: str | None
    job_direction: str
    job_type: str
    request_payload_json: dict[str, object]
    error_summary: str | None
    requested_by_user_id: str | None
    result_summary_json: dict[str, object] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "requested"
    version_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeOutbox:
    id: str
    tenant_id: str | None
    endpoint_id: str | None
    aggregate_type: str
    aggregate_id: str
    event_type: str
    topic: str
    payload_json: dict[str, object]
    dedupe_key: str
    status: str = "pending"
    published_at: datetime | None = None
    next_attempt_at: datetime | None = None
    attempt_count: int = 0
    last_error_code: str | None = None
    last_error_summary: str | None = None
    processed_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class FakeDocumentService:
    def __init__(self) -> None:
        self.links: list[tuple[str, str, str]] = []

    def get_document(self, tenant_id: str, document_id: str, actor):  # noqa: ANN001
        return {"id": document_id, "tenant_id": tenant_id}

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.links.append((tenant_id, document_id, payload.owner_id))
        return payload


class FakePublisher:
    def publish(self, event, endpoint):  # noqa: ANN001
        if event.payload_json.get("simulate_failure"):
            raise RuntimeError("boom")
        return PublicationResult(provider_ref=f"ref:{event.id}", status="published")


class FakeIntegrationRepository:
    def __init__(self) -> None:
        self.endpoints: dict[str, FakeEndpoint] = {}
        self.jobs: dict[str, FakeJob] = {}
        self.outbox: dict[str, FakeOutbox] = {}
        self.result_links: dict[str, list[object]] = {}

    def create_endpoint(self, row):
        for endpoint in self.endpoints.values():
            if endpoint.tenant_id == row.tenant_id and endpoint.provider_key == row.provider_key and endpoint.endpoint_type == row.endpoint_type:
                from sqlalchemy.exc import IntegrityError

                raise IntegrityError("duplicate", None, None)
        stored = FakeEndpoint(
            id=str(uuid4()),
            tenant_id=row.tenant_id,
            provider_key=row.provider_key,
            endpoint_type=row.endpoint_type,
            base_url=row.base_url,
            auth_mode=row.auth_mode,
            config_public_json=row.config_public_json,
            secret_ciphertext=row.secret_ciphertext,
        )
        self.endpoints[stored.id] = stored
        return stored

    def list_endpoints(self, tenant_id: str):
        return [endpoint for endpoint in self.endpoints.values() if endpoint.tenant_id == tenant_id]

    def get_endpoint(self, tenant_id: str, endpoint_id: str):
        endpoint = self.endpoints.get(endpoint_id)
        if endpoint is None or endpoint.tenant_id != tenant_id:
            return None
        return endpoint

    def create_job_and_outbox(self, job, outbox_event):
        stored_job = FakeJob(
            id=str(uuid4()),
            tenant_id=job.tenant_id,
            endpoint_id=job.endpoint_id,
            job_direction=job.job_direction,
            job_type=job.job_type,
            request_payload_json=job.request_payload_json,
            result_summary_json=job.result_summary_json or {},
            error_summary=job.error_summary,
            requested_by_user_id=job.requested_by_user_id,
            status=job.status,
        )
        stored_event = FakeOutbox(
            id=str(uuid4()),
            tenant_id=outbox_event.tenant_id,
            endpoint_id=outbox_event.endpoint_id,
            aggregate_type=outbox_event.aggregate_type,
            aggregate_id=stored_job.id,
            event_type=outbox_event.event_type,
            topic=outbox_event.topic,
            payload_json=outbox_event.payload_json,
            dedupe_key=outbox_event.dedupe_key,
            status=outbox_event.status,
        )
        self.jobs[stored_job.id] = stored_job
        self.outbox[stored_event.id] = stored_event
        self.result_links[stored_job.id] = []
        return stored_job

    def save_job(self, row):
        row.updated_at = datetime.now(UTC)
        self.jobs[row.id] = row
        return row

    def get_job(self, tenant_id: str, job_id: str):
        job = self.jobs.get(job_id)
        if job is None or job.tenant_id != tenant_id:
            return None
        return job

    def list_document_links_for_job(self, tenant_id: str, job_id: str):
        return self.result_links.get(job_id, [])

    def create_outbox_event(self, row):
        stored = FakeOutbox(
            id=str(uuid4()),
            tenant_id=row.tenant_id,
            endpoint_id=row.endpoint_id,
            aggregate_type=row.aggregate_type,
            aggregate_id=row.aggregate_id,
            event_type=row.event_type,
            topic=row.topic,
            payload_json=row.payload_json,
            dedupe_key=row.dedupe_key,
            status=row.status,
        )
        self.outbox[stored.id] = stored
        return stored

    def list_pending_outbox_events(self, tenant_id: str | None, limit: int, now: datetime):
        rows = [
            event
            for event in self.outbox.values()
            if event.status in {"pending", "retry"}
            and (tenant_id is None or event.tenant_id == tenant_id)
            and (event.next_attempt_at is None or event.next_attempt_at <= now)
        ]
        rows.sort(key=lambda row: row.created_at)
        return rows[:limit]

    def save_outbox_event(self, row):
        row.updated_at = datetime.now(UTC)
        self.outbox[row.id] = row
        return row


def _actor(tenant_id: str = "tenant-1") -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"platform.integration.read", "platform.integration.write", "platform.docs.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
    )


class TestIntegrationMetadata(unittest.TestCase):
    def test_expected_integration_tables_are_registered(self) -> None:
        self.assertIn("integration.endpoint", Base.metadata.tables)
        self.assertIn("integration.import_export_job", Base.metadata.tables)
        self.assertIn("integration.outbox_event", Base.metadata.tables)

    def test_endpoint_uniqueness_and_outbox_index_exist(self) -> None:
        endpoint_constraints = {
            constraint.name
            for constraint in IntegrationEndpoint.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        outbox_indexes = {index.name for index in OutboxEvent.__table__.indexes if isinstance(index, Index)}
        self.assertIn("uq_integration_endpoint_tenant_provider_type", endpoint_constraints)
        self.assertIn("ix_integration_outbox_event_status_next_attempt", outbox_indexes)


class TestIntegrationService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeIntegrationRepository()
        self.documents = FakeDocumentService()
        self.secret_box = IntegrationSecretBox("integration-test-secret")
        self.service = IntegrationService(
            self.repository,
            document_service=self.documents,
            secret_box=self.secret_box,
            outbox_publisher=FakePublisher(),
            retry_delay_seconds=30,
            max_attempts=3,
        )

    def test_endpoint_registration_seals_secret_and_redacts_read_model(self) -> None:
        endpoint = self.service.register_endpoint(
            "tenant-1",
            IntegrationEndpointCreate(
                tenant_id="tenant-1",
                provider_key="mailpit",
                endpoint_type="message_delivery",
                base_url="http://mailpit.local",
                secret_config_json={"token": "secret"},
            ),
            _actor(),
        )

        stored = next(iter(self.repository.endpoints.values()))
        self.assertEqual(endpoint.provider_key, "mailpit")
        self.assertTrue(stored.secret_ciphertext)
        self.assertNotIn("secret_ciphertext", endpoint.model_dump())
        self.assertEqual(self.secret_box.open(stored.secret_ciphertext), {"token": "secret"})

    def test_request_job_persists_job_and_outbox_and_can_attach_result_document(self) -> None:
        endpoint = self.service.register_endpoint(
            "tenant-1",
            IntegrationEndpointCreate(
                tenant_id="tenant-1",
                provider_key="payroll",
                endpoint_type="export",
                base_url="http://payroll.local",
            ),
            _actor(),
        )
        job = self.service.request_job(
            "tenant-1",
            ImportExportJobCreate(
                tenant_id="tenant-1",
                endpoint_id=endpoint.id,
                job_direction="export",
                job_type="payroll_csv",
                request_payload_json={"month": "2026-03"},
                result_document_id="doc-1",
            ),
            _actor(),
        )

        self.assertEqual(job.status, "requested")
        self.assertEqual(len(self.repository.outbox), 1)
        self.assertEqual(self.documents.links[0][1], "doc-1")

    def test_outbox_processing_completes_job_idempotently(self) -> None:
        endpoint = self.service.register_endpoint(
            "tenant-1",
            IntegrationEndpointCreate(
                tenant_id="tenant-1",
                provider_key="exports",
                endpoint_type="export",
                base_url="http://exports.local",
            ),
            _actor(),
        )
        job = self.service.request_job(
            "tenant-1",
            ImportExportJobCreate(
                tenant_id="tenant-1",
                endpoint_id=endpoint.id,
                job_direction="export",
                job_type="timesheet_pdf",
                request_payload_json={},
            ),
            _actor(),
        )
        first = self.service.process_outbox(tenant_id="tenant-1", worker_name="worker-1", limit=10)
        second = self.service.process_outbox(tenant_id="tenant-1", worker_name="worker-1", limit=10)

        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].status, "published")
        self.assertEqual(second, [])
        refreshed = self.service.get_job("tenant-1", job.id, _actor())
        self.assertEqual(refreshed.status, "completed")

    def test_outbox_failure_transitions_to_retry_with_backoff(self) -> None:
        job = self.service.request_job(
            "tenant-1",
            ImportExportJobCreate(
                tenant_id="tenant-1",
                endpoint_id=None,
                job_direction="import",
                job_type="scanner_sync",
                request_payload_json={"simulate_failure": True},
            ),
            _actor(),
        )
        event = next(iter(self.repository.outbox.values()))
        event.payload_json["simulate_failure"] = True

        processed = self.service.process_outbox(tenant_id="tenant-1", worker_name="worker-2", limit=10)

        self.assertEqual(processed[0].status, "retry")
        stored = next(iter(self.repository.outbox.values()))
        self.assertEqual(stored.attempt_count, 1)
        self.assertIsNotNone(stored.next_attempt_at)
        self.assertEqual(self.service.get_job("tenant-1", job.id, _actor()).status, "started")


if __name__ == "__main__":
    unittest.main()
