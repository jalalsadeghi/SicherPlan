"""Bulk import/export orchestration for subcontractor workforce records."""

from __future__ import annotations

import base64
import csv
import io
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext, enforce_scope
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.integration_models import ImportExportJob
from app.modules.subcontractors.models import Subcontractor, SubcontractorWorker
from app.modules.subcontractors.policy import (
    enforce_subcontractor_internal_read_access,
    enforce_subcontractor_internal_write_access,
)
from app.modules.subcontractors.schemas import (
    SubcontractorWorkerCreate,
    SubcontractorWorkerExportRequest,
    SubcontractorWorkerExportResult,
    SubcontractorWorkerFilter,
    SubcontractorWorkerImportDryRunRequest,
    SubcontractorWorkerImportDryRunResult,
    SubcontractorWorkerImportExecuteRequest,
    SubcontractorWorkerImportExecuteResult,
    SubcontractorWorkerImportRowResult,
    SubcontractorWorkerUpdate,
)
from app.modules.subcontractors.workforce_service import SubcontractorWorkforceService


IMPORT_HEADERS = (
    "worker_no",
    "first_name",
    "last_name",
    "preferred_name",
    "birth_date",
    "email",
    "phone",
    "mobile",
    "status",
    "notes",
)

ALLOWED_IMPORT_STATUSES = {"active", "inactive", "archived"}


class SubcontractorWorkforceOpsRepository(Protocol):
    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None: ...
    def list_workers(self, tenant_id: str, subcontractor_id: str, filters: SubcontractorWorkerFilter) -> list[SubcontractorWorker]: ...
    def find_worker_by_number(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_no: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorWorker | None: ...
    def create_job(self, row: ImportExportJob) -> ImportExportJob: ...
    def save_job(self, row: ImportExportJob) -> ImportExportJob: ...


@dataclass(slots=True)
class ParsedImportRow:
    row_no: int
    data: dict[str, str]


class SubcontractorWorkforceOpsService:
    def __init__(
        self,
        *,
        repository: SubcontractorWorkforceOpsRepository,
        workforce_service: SubcontractorWorkforceService,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.workforce_service = workforce_service
        self.document_service = document_service
        self.audit_service = audit_service

    def import_dry_run(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorWorkerImportDryRunRequest,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerImportDryRunResult:
        self._require_write_access(actor, tenant_id, subcontractor_id)
        self._ensure_payload_scope(tenant_id, subcontractor_id, payload.tenant_id, payload.subcontractor_id)
        rows = self._parse_import_csv(payload.csv_content_base64)
        results = [self._validate_import_row(tenant_id, subcontractor_id, row) for row in rows]
        invalid_rows = sum(1 for row in results if row.status == "invalid")
        self._record_event(
            actor,
            event_type="subcontractors.worker_import.dry_run_requested",
            entity_type="partner.subcontractor_worker_import",
            entity_id=subcontractor_id,
            tenant_id=tenant_id,
            metadata_json={"subcontractor_id": subcontractor_id, "row_count": len(rows), "invalid_rows": invalid_rows},
        )
        return SubcontractorWorkerImportDryRunResult(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            total_rows=len(results),
            valid_rows=len(results) - invalid_rows,
            invalid_rows=invalid_rows,
            rows=results,
        )

    def execute_import(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorWorkerImportExecuteRequest,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerImportExecuteResult:
        self._require_write_access(actor, tenant_id, subcontractor_id)
        self._ensure_payload_scope(tenant_id, subcontractor_id, payload.tenant_id, payload.subcontractor_id)
        rows = self._parse_import_csv(payload.csv_content_base64)
        job = self.repository.create_job(
            ImportExportJob(
                tenant_id=tenant_id,
                endpoint_id=None,
                job_direction="import",
                job_type="subcontractors.worker_csv",
                request_payload_json={
                    "subcontractor_id": subcontractor_id,
                    "row_count": len(rows),
                    "continue_on_error": payload.continue_on_error,
                },
                requested_by_user_id=actor.user_id,
                status="started",
                started_at=datetime.now(UTC),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        row_results: list[SubcontractorWorkerImportRowResult] = []
        created_workers = 0
        updated_workers = 0
        for row in rows:
            preview = self._validate_import_row(tenant_id, subcontractor_id, row)
            if preview.status == "invalid":
                row_results.append(preview)
                if not payload.continue_on_error:
                    break
                continue
            try:
                result = self._execute_import_row(tenant_id, subcontractor_id, row, actor)
            except ApiException as exc:
                row_results.append(
                    SubcontractorWorkerImportRowResult(
                        row_no=row.row_no,
                        worker_no=row.data.get("worker_no") or None,
                        status="invalid",
                        messages=[exc.code],
                    )
                )
                if not payload.continue_on_error:
                    break
                continue
            row_results.append(result)
            created_workers += int("created_worker" in result.messages)
            updated_workers += int("updated_worker" in result.messages)

        invalid_rows = sum(1 for row in row_results if row.status == "invalid")
        report_document_id = self._create_result_document(
            tenant_id=tenant_id,
            actor=actor,
            owner_id=job.id,
            file_name=f"subcontractor-workers-import-{job.id}.csv",
            title="Subcontractor worker import result",
            source_label="subcontractor-worker-import-result",
            content=self._build_import_result_csv(row_results).encode("utf-8"),
        )
        job.completed_at = datetime.now(UTC)
        job.status = "completed"
        job.error_summary = None if invalid_rows == 0 else f"Import completed with {invalid_rows} invalid rows."
        job.result_summary_json = {
            "subcontractor_id": subcontractor_id,
            "total_rows": len(row_results),
            "invalid_rows": invalid_rows,
            "report_document_id": report_document_id,
        }
        job.version_no += 1
        job.updated_by_user_id = actor.user_id
        self.repository.save_job(job)
        self._record_event(
            actor,
            event_type="subcontractors.worker_import.executed",
            entity_type="integration.import_export_job",
            entity_id=job.id,
            tenant_id=tenant_id,
            metadata_json={
                "subcontractor_id": subcontractor_id,
                "invalid_rows": invalid_rows,
                "report_document_id": report_document_id,
            },
        )
        return SubcontractorWorkerImportExecuteResult(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            job_id=job.id,
            job_status=job.status,
            total_rows=len(row_results),
            invalid_rows=invalid_rows,
            created_workers=created_workers,
            updated_workers=updated_workers,
            result_document_ids=[report_document_id],
            rows=row_results,
        )

    def export_workers(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorWorkerExportRequest,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerExportResult:
        self._require_read_access(actor, tenant_id, subcontractor_id)
        self._ensure_payload_scope(tenant_id, subcontractor_id, payload.tenant_id, payload.subcontractor_id)
        rows = self.repository.list_workers(
            tenant_id,
            subcontractor_id,
            SubcontractorWorkerFilter(
                search=payload.search,
                status=payload.status,
                include_archived=payload.include_archived,
            ),
        )
        job = self.repository.create_job(
            ImportExportJob(
                tenant_id=tenant_id,
                endpoint_id=None,
                job_direction="export",
                job_type="subcontractors.worker_csv",
                request_payload_json={
                    "subcontractor_id": subcontractor_id,
                    "search": payload.search,
                    "status": payload.status,
                    "include_archived": payload.include_archived,
                },
                requested_by_user_id=actor.user_id,
                status="started",
                started_at=datetime.now(UTC),
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        csv_content, row_count = self._build_export_csv(rows)
        document_id = self._create_result_document(
            tenant_id=tenant_id,
            actor=actor,
            owner_id=job.id,
            file_name=f"subcontractor-workers-export-{job.id}.csv",
            title="Subcontractor workforce export",
            source_label="subcontractor-worker-export",
            content=csv_content.encode("utf-8"),
        )
        job.completed_at = datetime.now(UTC)
        job.status = "completed"
        job.result_summary_json = {
            "subcontractor_id": subcontractor_id,
            "row_count": row_count,
            "document_id": document_id,
        }
        job.version_no += 1
        job.updated_by_user_id = actor.user_id
        self.repository.save_job(job)
        self._record_event(
            actor,
            event_type="subcontractors.worker_export.executed",
            entity_type="integration.import_export_job",
            entity_id=job.id,
            tenant_id=tenant_id,
            metadata_json={"subcontractor_id": subcontractor_id, "row_count": row_count, "document_id": document_id},
        )
        return SubcontractorWorkerExportResult(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            job_id=job.id,
            document_id=document_id,
            file_name=f"subcontractor-workers-export-{job.id}.csv",
            row_count=row_count,
        )

    def _validate_import_row(
        self,
        tenant_id: str,
        subcontractor_id: str,
        row: ParsedImportRow,
    ) -> SubcontractorWorkerImportRowResult:
        messages: list[str] = []
        worker_no = row.data.get("worker_no", "").strip() or None
        first_name = row.data.get("first_name", "").strip()
        last_name = row.data.get("last_name", "").strip()
        birth_date_value = row.data.get("birth_date", "").strip()
        status_value = (row.data.get("status", "").strip() or "active").lower()
        if not worker_no:
            messages.append("subcontractors.worker_import.missing_worker_no")
        if not first_name:
            messages.append("subcontractors.worker_import.missing_first_name")
        if not last_name:
            messages.append("subcontractors.worker_import.missing_last_name")
        if birth_date_value:
            try:
                date.fromisoformat(birth_date_value)
            except ValueError:
                messages.append("subcontractors.worker_import.invalid_birth_date")
        if status_value not in ALLOWED_IMPORT_STATUSES:
            messages.append("subcontractors.worker_import.invalid_status")
        return SubcontractorWorkerImportRowResult(
            row_no=row.row_no,
            worker_no=worker_no,
            status="invalid" if messages else "valid",
            messages=messages,
        )

    def _execute_import_row(
        self,
        tenant_id: str,
        subcontractor_id: str,
        row: ParsedImportRow,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerImportRowResult:
        worker_no = row.data["worker_no"].strip()
        birth_date_value = row.data["birth_date"].strip()
        existing = self.repository.find_worker_by_number(tenant_id, subcontractor_id, worker_no)
        if existing is None:
            created = self.workforce_service.create_worker(
                tenant_id,
                subcontractor_id,
                SubcontractorWorkerCreate(
                    tenant_id=tenant_id,
                    subcontractor_id=subcontractor_id,
                    worker_no=worker_no,
                    first_name=row.data["first_name"].strip(),
                    last_name=row.data["last_name"].strip(),
                    preferred_name=self._empty_to_none(row.data["preferred_name"]),
                    birth_date=date.fromisoformat(birth_date_value) if birth_date_value else None,
                    email=self._empty_to_none(row.data["email"]),
                    phone=self._empty_to_none(row.data["phone"]),
                    mobile=self._empty_to_none(row.data["mobile"]),
                    notes=self._empty_to_none(row.data["notes"]),
                ),
                actor,
            )
            return SubcontractorWorkerImportRowResult(
                row_no=row.row_no,
                worker_no=worker_no,
                status="created",
                messages=["created_worker"],
                worker_id=created.id,
            )
        updated = self.workforce_service.update_worker(
            tenant_id,
            subcontractor_id,
            existing.id,
            SubcontractorWorkerUpdate(
                worker_no=worker_no,
                first_name=row.data["first_name"].strip(),
                last_name=row.data["last_name"].strip(),
                preferred_name=self._empty_to_none(row.data["preferred_name"]),
                birth_date=date.fromisoformat(birth_date_value) if birth_date_value else None,
                email=self._empty_to_none(row.data["email"]),
                phone=self._empty_to_none(row.data["phone"]),
                mobile=self._empty_to_none(row.data["mobile"]),
                notes=self._empty_to_none(row.data["notes"]),
                status=(row.data["status"].strip() or "active").lower(),
                version_no=existing.version_no,
            ),
            actor,
        )
        return SubcontractorWorkerImportRowResult(
            row_no=row.row_no,
            worker_no=worker_no,
            status="updated",
            messages=["updated_worker"],
            worker_id=updated.id,
        )

    def _parse_import_csv(self, csv_content_base64: str) -> list[ParsedImportRow]:
        try:
            csv_text = base64.b64decode(csv_content_base64).decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise ApiException(
                400,
                "subcontractors.worker_import.invalid_csv",
                "errors.subcontractors.worker_import.invalid_csv",
            ) from exc
        buffer = io.StringIO(csv_text)
        reader = csv.DictReader(buffer)
        if tuple(reader.fieldnames or ()) != IMPORT_HEADERS:
            raise ApiException(
                400,
                "subcontractors.worker_import.invalid_headers",
                "errors.subcontractors.worker_import.invalid_headers",
                {"expected_headers": list(IMPORT_HEADERS)},
            )
        rows: list[ParsedImportRow] = []
        for index, row in enumerate(reader, start=2):
            rows.append(
                ParsedImportRow(
                    row_no=index,
                    data={header: (row.get(header) or "").strip() for header in IMPORT_HEADERS},
                )
            )
        return rows

    @staticmethod
    def _build_import_result_csv(rows: list[SubcontractorWorkerImportRowResult]) -> str:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=("row_no", "worker_no", "status", "worker_id", "messages"))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "row_no": row.row_no,
                    "worker_no": row.worker_no or "",
                    "status": row.status,
                    "worker_id": row.worker_id or "",
                    "messages": "|".join(row.messages),
                }
            )
        return buffer.getvalue()

    @staticmethod
    def _build_export_csv(rows: list[SubcontractorWorker]) -> tuple[str, int]:
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=(
                "worker_no",
                "first_name",
                "last_name",
                "preferred_name",
                "birth_date",
                "email",
                "phone",
                "mobile",
                "status",
                "qualification_count",
                "expired_qualification_count",
                "credential_count",
                "notes",
            ),
        )
        writer.writeheader()
        row_count = 0
        today = date.today()
        for row in rows:
            expired_qualification_count = sum(
                1
                for qualification in row.qualifications
                if qualification.archived_at is None
                and qualification.valid_until is not None
                and qualification.valid_until < today
            )
            writer.writerow(
                {
                    "worker_no": row.worker_no,
                    "first_name": row.first_name,
                    "last_name": row.last_name,
                    "preferred_name": row.preferred_name or "",
                    "birth_date": row.birth_date.isoformat() if row.birth_date else "",
                    "email": row.email or "",
                    "phone": row.phone or "",
                    "mobile": row.mobile or "",
                    "status": row.status,
                    "qualification_count": sum(1 for qualification in row.qualifications if qualification.archived_at is None),
                    "expired_qualification_count": expired_qualification_count,
                    "credential_count": sum(1 for credential in row.credentials if credential.archived_at is None),
                    "notes": row.notes or "",
                }
            )
            row_count += 1
        return buffer.getvalue(), row_count

    def _create_result_document(
        self,
        *,
        tenant_id: str,
        actor: RequestAuthorizationContext,
        owner_id: str,
        file_name: str,
        title: str,
        source_label: str,
        content: bytes,
    ) -> str:
        document = self.document_service.create_document(
            tenant_id,
            DocumentCreate(
                tenant_id=tenant_id,
                title=title,
                source_module="subcontractors",
                source_label=source_label,
                metadata_json={},
            ),
            actor,
        )
        self.document_service.add_document_version(
            tenant_id,
            document.id,
            DocumentVersionCreate(
                file_name=file_name,
                content_type="text/csv",
                content_base64=base64.b64encode(content).decode("ascii"),
                metadata_json={},
            ),
            actor,
        )
        self.document_service.add_document_link(
            tenant_id,
            document.id,
            DocumentLinkCreate(
                owner_type="integration.import_export_job",
                owner_id=owner_id,
                relation_type="generated_output",
                label=title,
                metadata_json={},
            ),
            actor,
        )
        return document.id

    def _require_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor:
        row = self.repository.get_subcontractor(tenant_id, subcontractor_id)
        if row is None:
            raise ApiException(404, "subcontractors.subcontractor.not_found", "errors.subcontractors.subcontractor.not_found")
        return row

    def _require_read_access(
        self,
        actor: RequestAuthorizationContext,
        tenant_id: str,
        subcontractor_id: str,
    ) -> Subcontractor:
        row = self._require_subcontractor(tenant_id, subcontractor_id)
        enforce_scope(actor, scope="tenant", tenant_id=tenant_id)
        enforce_subcontractor_internal_read_access(actor, tenant_id=tenant_id, subcontractor=row)
        return row

    def _require_write_access(
        self,
        actor: RequestAuthorizationContext,
        tenant_id: str,
        subcontractor_id: str,
    ) -> Subcontractor:
        row = self._require_subcontractor(tenant_id, subcontractor_id)
        enforce_scope(actor, scope="tenant", tenant_id=tenant_id)
        enforce_subcontractor_internal_write_access(actor, tenant_id=tenant_id)
        return row

    @staticmethod
    def _ensure_payload_scope(
        tenant_id: str,
        subcontractor_id: str,
        payload_tenant_id: str,
        payload_subcontractor_id: str,
    ) -> None:
        if payload_tenant_id != tenant_id or payload_subcontractor_id != subcontractor_id:
            raise ApiException(
                400,
                "subcontractors.worker_import.scope_mismatch",
                "errors.subcontractors.worker_import.scope_mismatch",
            )

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
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
            metadata_json=metadata_json,
        )

    @staticmethod
    def _empty_to_none(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
