from __future__ import annotations

import base64
import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from app.errors import ApiException
from app.modules.iam.audit_service import AuditService
from app.modules.planning.ops_service import PlanningOpsService
from app.modules.planning.schemas import PlanningOpsImportDryRunRequest, PlanningOpsImportExecuteRequest
from app.modules.planning.service import PlanningService
from tests.modules.planning.test_ops_master_foundation import FakePlanningRepository, RecordingAuditRepository, _context


def _csv_base64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


@dataclass
class FakeImportJob:
    tenant_id: str
    endpoint_id: str | None
    job_direction: str
    job_type: str
    request_payload_json: dict[str, object]
    requested_by_user_id: str | None
    status: str
    started_at: datetime | None
    created_by_user_id: str | None
    updated_by_user_id: str | None
    id: str = field(default_factory=lambda: str(uuid4()))
    version_no: int = 1
    completed_at: datetime | None = None
    result_summary_json: dict[str, object] | None = None


class FakeImportPlanningRepository(FakePlanningRepository):
    def __post_init__(self) -> None:
        super().__post_init__()
        self.jobs: dict[str, FakeImportJob] = {}

    def create_job(self, row):  # noqa: ANN001
        job = FakeImportJob(
            tenant_id=row.tenant_id,
            endpoint_id=row.endpoint_id,
            job_direction=row.job_direction,
            job_type=row.job_type,
            request_payload_json=row.request_payload_json,
            requested_by_user_id=row.requested_by_user_id,
            status=row.status,
            started_at=row.started_at,
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
        )
        self.jobs[job.id] = job
        return job

    def save_job(self, row):  # noqa: ANN001
        self.jobs[row.id] = row
        return row


class FakeDocumentService:
    def __init__(self) -> None:
        self.documents: dict[str, dict[str, object]] = {}
        self.links: list[dict[str, object]] = []

    def create_document(self, tenant_id: str, payload, actor):  # noqa: ANN001
        document_id = str(uuid4())
        self.documents[document_id] = {
            "tenant_id": tenant_id,
            "title": payload.title,
            "versions": [],
        }
        return type("DocumentReadStub", (), {"id": document_id})()

    def add_document_version(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.documents[document_id]["versions"].append(
            {
                "tenant_id": tenant_id,
                "file_name": payload.file_name,
                "content_base64": payload.content_base64,
            }
        )
        return type("DocumentVersionReadStub", (), {"document_id": document_id, "version_no": len(self.documents[document_id]["versions"])})()

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.links.append(
            {
                "tenant_id": tenant_id,
                "document_id": document_id,
                "owner_type": payload.owner_type,
                "owner_id": payload.owner_id,
                "relation_type": payload.relation_type,
            }
        )
        return type("DocumentLinkReadStub", (), {"document_id": document_id, "owner_id": payload.owner_id})()


class TestPlanningOpsImportService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeImportPlanningRepository()
        self.audit_repository = RecordingAuditRepository()
        self.audit_service = AuditService(self.audit_repository)
        self.document_service = FakeDocumentService()
        self.planning_service = PlanningService(self.repository, audit_service=self.audit_service)
        self.service = PlanningOpsService(
            planning_service=self.planning_service,
            repository=self.repository,
            document_service=self.document_service,
            audit_service=self.audit_service,
        )
        self.actor = _context("planning.ops.write")

    def test_dry_run_reports_invalid_rows(self) -> None:
        payload = PlanningOpsImportDryRunRequest(
            tenant_id="tenant-1",
            entity_key="site",
            csv_content_base64=_csv_base64(
                "customer_id,site_no,name,address_id,timezone,latitude,longitude,watchbook_enabled,notes,status\n"
                "customer-1,S-100,Valid Site,address-1,Europe/Berlin,52.5,13.4,true,ok,active\n"
                "customer-1,,Missing Number,address-1,Europe/Berlin,52.5,13.4,false,,active\n"
            ),
        )

        result = self.service.import_dry_run("tenant-1", payload, self.actor)

        self.assertEqual(result.total_rows, 2)
        self.assertEqual(result.invalid_rows, 1)
        self.assertEqual(result.rows[0].status, "valid")
        self.assertEqual(result.rows[1].status, "invalid")
        self.assertIn("errors.planning.import.missing_value", result.rows[1].messages)

    def test_execute_creates_job_document_and_upserts_records(self) -> None:
        payload = PlanningOpsImportExecuteRequest(
            tenant_id="tenant-1",
            entity_key="requirement_type",
            continue_on_error=True,
            csv_content_base64=_csv_base64(
                "code,label,default_planning_mode_code,notes,status\n"
                "REQ-01,Objektschutz,site,Alpha,active\n"
            ),
        )

        first = self.service.import_execute("tenant-1", payload, self.actor)
        second = self.service.import_execute("tenant-1", payload, self.actor)

        self.assertEqual(first.created_rows, 1)
        self.assertEqual(second.updated_rows, 1)
        self.assertEqual(len(self.repository.requirement_types), 1)
        self.assertEqual(len(self.repository.jobs), 2)
        self.assertEqual(len(self.document_service.documents), 2)
        self.assertEqual(len(self.document_service.links), 2)
        self.assertEqual(self.document_service.links[0]["owner_type"], "integration.import_export_job")
        self.assertEqual(first.job_status, "completed")
        self.assertEqual(second.job_status, "completed")
        stored = next(iter(self.repository.requirement_types.values()))
        self.assertEqual(stored.description, "Alpha")

    def test_execute_accepts_legacy_requirement_type_description_header_alias(self) -> None:
        payload = PlanningOpsImportExecuteRequest(
            tenant_id="tenant-1",
            entity_key="requirement_type",
            continue_on_error=True,
            csv_content_base64=_csv_base64(
                "code,label,default_planning_mode_code,description,status\n"
                "REQ-LEG,Objektschutz,event,Legacy note,active\n"
            ),
        )

        result = self.service.import_execute("tenant-1", payload, self.actor)

        self.assertEqual(result.created_rows, 1)
        stored = next(iter(self.repository.requirement_types.values()))
        self.assertEqual(stored.description, "Legacy note")

    def test_invalid_headers_raise_api_error(self) -> None:
        payload = PlanningOpsImportDryRunRequest(
            tenant_id="tenant-1",
            entity_key="equipment_item",
            csv_content_base64=_csv_base64("wrong,headers\nx,y\n"),
        )

        with self.assertRaises(ApiException) as captured:
            self.service.import_dry_run("tenant-1", payload, self.actor)

        self.assertEqual(captured.exception.message_key, "errors.planning.import.invalid_headers")
