from __future__ import annotations

import base64
import csv
import io
import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from app.errors import ApiException
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.integration_models import ImportExportJob
from app.modules.subcontractors.models import Subcontractor, SubcontractorWorker
from app.modules.subcontractors.ops_service import IMPORT_HEADERS, SubcontractorWorkforceOpsService
from app.modules.subcontractors.schemas import (
    SubcontractorWorkerCreate,
    SubcontractorWorkerExportRequest,
    SubcontractorWorkerImportDryRunRequest,
    SubcontractorWorkerImportExecuteRequest,
    SubcontractorWorkerRead,
    SubcontractorWorkerUpdate,
)


def _context(*permissions: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-1",
    )


def _csv_base64(rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=IMPORT_HEADERS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return base64.b64encode(buffer.getvalue().encode("utf-8")).decode("ascii")


class FakeWorkforceService:
    def __init__(self, repository: "FakeSubcontractorOpsRepository") -> None:
        self.repository = repository

    def create_worker(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorWorkerCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerRead:
        row = SubcontractorWorker(
            id=f"worker-{len(self.repository.workers) + 1}",
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            worker_no=payload.worker_no,
            first_name=payload.first_name,
            last_name=payload.last_name,
            preferred_name=payload.preferred_name,
            birth_date=payload.birth_date,
            email=payload.email,
            phone=payload.phone,
            mobile=payload.mobile,
            notes=payload.notes,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by_user_id=actor.user_id,
            updated_by_user_id=actor.user_id,
            version_no=1,
        )
        self.repository.workers.append(row)
        return SubcontractorWorkerRead.model_validate(row)

    def update_worker(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        payload: SubcontractorWorkerUpdate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorWorkerRead:
        row = self.repository.find_worker_by_id(tenant_id, subcontractor_id, worker_id)
        if row is None:
            raise ApiException(404, "subcontractors.worker.not_found", "errors.subcontractors.worker.not_found")
        if payload.version_no != row.version_no:
            raise ApiException(409, "subcontractors.conflict.worker.stale_version", "errors.subcontractors.worker.stale_version")
        row.worker_no = payload.worker_no or row.worker_no
        row.first_name = payload.first_name or row.first_name
        row.last_name = payload.last_name or row.last_name
        row.preferred_name = payload.preferred_name
        row.birth_date = payload.birth_date
        row.email = payload.email
        row.phone = payload.phone
        row.mobile = payload.mobile
        row.notes = payload.notes
        row.status = payload.status or row.status
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        return SubcontractorWorkerRead.model_validate(row)


class FakeDocumentService:
    def __init__(self) -> None:
        self.documents: list[dict[str, object]] = []

    def create_document(self, tenant_id: str, payload, actor):  # noqa: ANN001
        document = {"id": f"document-{len(self.documents) + 1}", "tenant_id": tenant_id, "versions": [], "links": [], "payload": payload}
        self.documents.append(document)
        return type("DocumentRead", (), {"id": document["id"]})()

    def add_document_version(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        document = next(row for row in self.documents if row["tenant_id"] == tenant_id and row["id"] == document_id)
        document["versions"].append(payload)
        return payload

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        document = next(row for row in self.documents if row["tenant_id"] == tenant_id and row["id"] == document_id)
        document["links"].append(payload)
        return payload


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.events: list[object] = []

    def create_login_event(self, payload):  # noqa: ANN001
        return payload

    def create_audit_event(self, payload):  # noqa: ANN001
        self.events.append(payload)
        return payload


@dataclass
class FakeSubcontractorOpsRepository:
    subcontractors: list[Subcontractor] = field(default_factory=list)
    workers: list[SubcontractorWorker] = field(default_factory=list)
    jobs: list[ImportExportJob] = field(default_factory=list)

    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None:
        return next((row for row in self.subcontractors if row.tenant_id == tenant_id and row.id == subcontractor_id), None)

    def list_workers(self, tenant_id: str, subcontractor_id: str, filters) -> list[SubcontractorWorker]:  # noqa: ANN001
        rows = [row for row in self.workers if row.tenant_id == tenant_id and row.subcontractor_id == subcontractor_id]
        if filters.search:
            needle = filters.search.lower()
            rows = [row for row in rows if needle in row.worker_no.lower() or needle in row.first_name.lower() or needle in row.last_name.lower()]
        if filters.status:
            rows = [row for row in rows if row.status == filters.status]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        return rows

    def find_worker_by_number(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_no: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorWorker | None:
        return next(
            (
                row
                for row in self.workers
                if row.tenant_id == tenant_id
                and row.subcontractor_id == subcontractor_id
                and row.worker_no == worker_no
                and row.id != exclude_id
            ),
            None,
        )

    def find_worker_by_id(self, tenant_id: str, subcontractor_id: str, worker_id: str) -> SubcontractorWorker | None:
        return next(
            (
                row
                for row in self.workers
                if row.tenant_id == tenant_id and row.subcontractor_id == subcontractor_id and row.id == worker_id
            ),
            None,
        )

    def create_job(self, row: ImportExportJob) -> ImportExportJob:
        row.id = f"job-{len(self.jobs) + 1}"
        row.created_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        row.version_no = 1
        self.jobs.append(row)
        return row

    def save_job(self, row: ImportExportJob) -> ImportExportJob:
        row.updated_at = datetime.now(UTC)
        return row


class SubcontractorWorkforceOpsServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeSubcontractorOpsRepository(
            subcontractors=[
                Subcontractor(
                    id="subcontractor-1",
                    tenant_id="tenant-1",
                    subcontractor_number="SUB-001",
                    legal_name="Partner GmbH",
                    status="active",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    version_no=1,
                )
            ],
            workers=[
                SubcontractorWorker(
                    id="worker-existing",
                    tenant_id="tenant-1",
                    subcontractor_id="subcontractor-1",
                    worker_no="WK-100",
                    first_name="Erika",
                    last_name="Partner",
                    preferred_name=None,
                    birth_date=None,
                    email="erika@example.com",
                    phone=None,
                    mobile=None,
                    notes=None,
                    status="active",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    version_no=2,
                )
            ],
        )
        self.document_service = FakeDocumentService()
        self.audit_repository = RecordingAuditRepository()
        self.service = SubcontractorWorkforceOpsService(
            repository=self.repository,
            workforce_service=FakeWorkforceService(self.repository),
            document_service=self.document_service,
            audit_service=AuditService(self.audit_repository),
        )
        self.write_context = _context("subcontractors.company.write")
        self.read_context = _context("subcontractors.company.read")

    def test_import_dry_run_reports_row_errors(self) -> None:
        result = self.service.import_dry_run(
            "tenant-1",
            "subcontractor-1",
            SubcontractorWorkerImportDryRunRequest(
                tenant_id="tenant-1",
                subcontractor_id="subcontractor-1",
                csv_content_base64=_csv_base64(
                    [
                        {
                            "worker_no": "",
                            "first_name": "",
                            "last_name": "Partner",
                            "preferred_name": "",
                            "birth_date": "bad-date",
                            "email": "",
                            "phone": "",
                            "mobile": "",
                            "status": "unknown",
                            "notes": "",
                        }
                    ]
                ),
            ),
            self.write_context,
        )

        self.assertEqual(result.total_rows, 1)
        self.assertEqual(result.invalid_rows, 1)
        self.assertIn("subcontractors.worker_import.missing_worker_no", result.rows[0].messages)
        self.assertIn("subcontractors.worker_import.invalid_birth_date", result.rows[0].messages)

    def test_execute_import_creates_and_updates_workers(self) -> None:
        result = self.service.execute_import(
            "tenant-1",
            "subcontractor-1",
            SubcontractorWorkerImportExecuteRequest(
                tenant_id="tenant-1",
                subcontractor_id="subcontractor-1",
                continue_on_error=True,
                csv_content_base64=_csv_base64(
                    [
                        {
                            "worker_no": "WK-100",
                            "first_name": "Erika",
                            "last_name": "Updated",
                            "preferred_name": "",
                            "birth_date": "",
                            "email": "erika@example.com",
                            "phone": "",
                            "mobile": "",
                            "status": "inactive",
                            "notes": "changed",
                        },
                        {
                            "worker_no": "WK-200",
                            "first_name": "Nora",
                            "last_name": "Neu",
                            "preferred_name": "",
                            "birth_date": "1994-05-10",
                            "email": "nora@example.com",
                            "phone": "",
                            "mobile": "",
                            "status": "active",
                            "notes": "",
                        },
                    ]
                ),
            ),
            self.write_context,
        )

        self.assertEqual(result.created_workers, 1)
        self.assertEqual(result.updated_workers, 1)
        self.assertEqual(result.invalid_rows, 0)
        self.assertEqual(len(self.repository.jobs), 1)
        self.assertEqual(len(self.document_service.documents), 1)
        updated = self.repository.find_worker_by_number("tenant-1", "subcontractor-1", "WK-100")
        created = self.repository.find_worker_by_number("tenant-1", "subcontractor-1", "WK-200")
        self.assertIsNotNone(updated)
        self.assertEqual(updated.last_name, "Updated")
        self.assertEqual(updated.status, "inactive")
        self.assertIsNotNone(created)
        self.assertEqual(created.birth_date, date(1994, 5, 10))

    def test_export_creates_job_and_result_document(self) -> None:
        result = self.service.export_workers(
            "tenant-1",
            "subcontractor-1",
            SubcontractorWorkerExportRequest(
                tenant_id="tenant-1",
                subcontractor_id="subcontractor-1",
                include_archived=False,
            ),
            self.read_context,
        )

        self.assertEqual(result.row_count, 1)
        self.assertEqual(len(self.repository.jobs), 1)
        self.assertEqual(self.repository.jobs[0].job_direction, "export")
        self.assertEqual(len(self.document_service.documents), 1)
        self.assertTrue(result.document_id.startswith("document-"))

    def test_invalid_headers_raise_api_error(self) -> None:
        invalid_csv = base64.b64encode("bad,header\nx,y\n".encode("utf-8")).decode("ascii")

        with self.assertRaises(ApiException) as context:
            self.service.import_dry_run(
                "tenant-1",
                "subcontractor-1",
                SubcontractorWorkerImportDryRunRequest(
                    tenant_id="tenant-1",
                    subcontractor_id="subcontractor-1",
                    csv_content_base64=invalid_csv,
                ),
                self.write_context,
            )

        self.assertEqual(context.exception.code, "subcontractors.worker_import.invalid_headers")


if __name__ == "__main__":
    unittest.main()
