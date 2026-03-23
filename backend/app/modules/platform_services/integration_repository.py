"""SQLAlchemy repository for integration endpoints, jobs, and outbox persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.platform_services.docs_models import DocumentLink
from app.modules.platform_services.integration_models import ImportExportJob, IntegrationEndpoint, OutboxEvent


class SqlAlchemyIntegrationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_endpoint(self, row: IntegrationEndpoint) -> IntegrationEndpoint:
        self.session.add(row)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(row)
        return row

    def list_endpoints(self, tenant_id: str) -> list[IntegrationEndpoint]:
        statement = select(IntegrationEndpoint).where(IntegrationEndpoint.tenant_id == tenant_id).order_by(IntegrationEndpoint.created_at.desc())
        return list(self.session.scalars(statement).all())

    def get_endpoint(self, tenant_id: str, endpoint_id: str) -> IntegrationEndpoint | None:
        statement = select(IntegrationEndpoint).where(
            IntegrationEndpoint.tenant_id == tenant_id,
            IntegrationEndpoint.id == endpoint_id,
        )
        return self.session.scalars(statement).one_or_none()

    def create_job_and_outbox(
        self,
        job: ImportExportJob,
        outbox_event: OutboxEvent,
    ) -> ImportExportJob:
        self.session.add(job)
        self.session.flush()
        if not outbox_event.aggregate_id:
            outbox_event.aggregate_id = job.id
        self.session.add(outbox_event)
        self.session.commit()
        return self.get_job(job.tenant_id, job.id) or job

    def create_job(self, row: ImportExportJob) -> ImportExportJob:
        self.session.add(row)
        self.session.commit()
        return self.get_job(row.tenant_id, row.id) or row

    def save_job(self, row: ImportExportJob) -> ImportExportJob:
        self.session.add(row)
        self.session.commit()
        return self.get_job(row.tenant_id, row.id) or row

    def get_job(self, tenant_id: str, job_id: str) -> ImportExportJob | None:
        statement = select(ImportExportJob).where(
            ImportExportJob.tenant_id == tenant_id,
            ImportExportJob.id == job_id,
        )
        return self.session.scalars(statement).one_or_none()

    def list_document_links_for_job(self, tenant_id: str, job_id: str) -> list[DocumentLink]:
        statement = select(DocumentLink).where(
            DocumentLink.tenant_id == tenant_id,
            DocumentLink.owner_type == "integration.import_export_job",
            DocumentLink.owner_id == job_id,
        )
        return list(self.session.scalars(statement).all())

    def create_outbox_event(self, row: OutboxEvent) -> OutboxEvent:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_pending_outbox_events(self, tenant_id: str | None, limit: int, now: datetime) -> list[OutboxEvent]:
        statement: Select[tuple[OutboxEvent]] = (
            select(OutboxEvent)
            .where(
                OutboxEvent.status.in_(("pending", "retry")),
                (OutboxEvent.next_attempt_at.is_(None)) | (OutboxEvent.next_attempt_at <= now),
            )
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        if tenant_id is not None:
            statement = statement.where(OutboxEvent.tenant_id == tenant_id)
        return list(self.session.scalars(statement).all())

    def save_outbox_event(self, row: OutboxEvent) -> OutboxEvent:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row
