from __future__ import annotations

import base64
import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.customers.ops_service import CustomerOpsService
from app.modules.customers.schemas import (
    CustomerContactCreate,
    CustomerCreate,
    CustomerExportRequest,
    CustomerImportDryRunRequest,
    CustomerImportExecuteRequest,
    CustomerUpdate,
)
from app.modules.customers.service import CustomerService
from app.modules.platform_services.integration_models import ImportExportJob
from tests.modules.customers.test_customer_backbone import FakeCustomerRepository, _actor


@dataclass
class FakeStoredVersion:
    version_no: int
    file_name: str
    content_type: str
    content: bytes


@dataclass
class FakeStoredDocument:
    id: str
    tenant_id: str
    title: str
    source_module: str | None
    source_label: str | None
    versions: list[FakeStoredVersion] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)

    @property
    def current_version_no(self) -> int:
        return self.versions[-1].version_no if self.versions else 0


class FakeDocumentService:
    def __init__(self) -> None:
        self.documents: dict[str, FakeStoredDocument] = {}

    def create_document(self, tenant_id: str, payload, actor):  # noqa: ANN001
        document = FakeStoredDocument(
            id=str(uuid4()),
            tenant_id=tenant_id,
            title=payload.title,
            source_module=payload.source_module,
            source_label=payload.source_label,
        )
        self.documents[document.id] = document
        return SimpleNamespace(id=document.id)

    def add_document_version(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        document = self.documents[document_id]
        version = FakeStoredVersion(
            version_no=len(document.versions) + 1,
            file_name=payload.file_name,
            content_type=payload.content_type,
            content=base64.b64decode(payload.content_base64),
        )
        document.versions.append(version)
        return SimpleNamespace(
            version_no=version.version_no,
            file_name=version.file_name,
            content_type=version.content_type,
        )

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.documents[document_id].links.append(
            {
                "owner_type": payload.owner_type,
                "owner_id": payload.owner_id,
                "relation_type": payload.relation_type,
            }
        )
        return SimpleNamespace(document_id=document_id)

    def get_document(self, tenant_id: str, document_id: str, actor):  # noqa: ANN001
        document = self.documents[document_id]
        return SimpleNamespace(
            id=document.id,
            versions=[
                SimpleNamespace(
                    version_no=version.version_no,
                    file_name=version.file_name,
                    content_type=version.content_type,
                )
                for version in document.versions
            ],
        )


class FakeIntegrationRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, ImportExportJob] = {}

    def create_job(self, row: ImportExportJob) -> ImportExportJob:
        if not getattr(row, "id", None):
            row.id = str(uuid4())
        if getattr(row, "version_no", None) is None:
            row.version_no = 1
        self.jobs[row.id] = row
        return row

    def save_job(self, row: ImportExportJob) -> ImportExportJob:
        if getattr(row, "version_no", None) is None:
            row.version_no = 1
        self.jobs[row.id] = row
        return row


def _csv_base64(rows: list[list[str]]) -> str:
    lines = [",".join(row) for row in rows]
    return base64.b64encode(("\n".join(lines) + "\n").encode("utf-8")).decode("ascii")


class TestCustomerOpsService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeCustomerRepository()
        self.customer_service = CustomerService(self.repository)
        self.document_service = FakeDocumentService()
        self.integration_repository = FakeIntegrationRepository()
        self.ops_service = CustomerOpsService(
            customer_service=self.customer_service,
            customer_repository=self.repository,
            integration_repository=self.integration_repository,
            document_service=self.document_service,
        )
        self.actor = _actor()
        self.customer = self.customer_service.create_customer(
            "tenant-1",
            CustomerCreate(
                tenant_id="tenant-1",
                customer_number="K-1000",
                name="Nord Security GmbH",
            ),
            self.actor,
        )
        self.contact = self.customer_service.create_contact(
            "tenant-1",
            self.customer.id,
            CustomerContactCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                full_name="Alex Kunde",
                email="alex@example.invalid",
                phone="+49 40 1234",
                mobile="+49 171 555",
                function_label="Einsatzleitung",
                is_primary_contact=True,
            ),
            self.actor,
        )

    def test_import_dry_run_rejects_missing_headers(self) -> None:
        payload = CustomerImportDryRunRequest(
            tenant_id="tenant-1",
            csv_content_base64=_csv_base64([["name"], ["Only Name"]]),
        )

        with self.assertRaises(ApiException) as context:
            self.ops_service.import_dry_run("tenant-1", payload, self.actor)

        self.assertEqual(context.exception.code, "customers.import.invalid_headers")

    def test_import_execute_reports_row_failures_and_links_report_document(self) -> None:
        payload = CustomerImportExecuteRequest(
            tenant_id="tenant-1",
            continue_on_error=True,
            csv_content_base64=_csv_base64(
                [
                    ["customer_number", "name", "default_branch_id"],
                    ["K-2000", "Atlas Objekt GmbH", "branch-1"],
                    ["K-2001", "Fehlerkunde", "branch-missing"],
                ]
            ),
        )

        result = self.ops_service.execute_import("tenant-1", payload, self.actor)

        self.assertEqual(result.total_rows, 2)
        self.assertEqual(result.invalid_rows, 1)
        self.assertEqual(result.created_customers, 1)
        self.assertEqual(result.rows[0].status, "processed")
        self.assertEqual(result.rows[1].status, "invalid")
        self.assertIn("customers.validation.branch_scope", result.rows[1].messages)

        job = self.integration_repository.jobs[result.job_id]
        self.assertEqual(job.status, "completed")
        self.assertEqual(job.requested_by_user_id, self.actor.user_id)
        self.assertEqual(len(result.result_document_ids), 1)

        report_document = self.document_service.documents[result.result_document_ids[0]]
        report_content = report_document.versions[-1].content.decode("utf-8")
        self.assertEqual(report_document.links[0]["owner_type"], "integration.import_export_job")
        self.assertIn("K-2000", report_content)
        self.assertIn("customers.validation.branch_scope", report_content)

    def test_export_customers_creates_csv_document_for_job(self) -> None:
        result = self.ops_service.export_customers(
            "tenant-1",
            CustomerExportRequest(tenant_id="tenant-1", search="K-1000"),
            self.actor,
        )

        self.assertEqual(result.row_count, 1)
        self.assertTrue(result.file_name.endswith(".csv"))
        job = self.integration_repository.jobs[result.job_id]
        self.assertEqual(job.job_direction, "export")

        document = self.document_service.documents[result.document_id]
        csv_content = document.versions[-1].content.decode("utf-8")
        self.assertEqual(document.links[0]["owner_type"], "integration.import_export_job")
        self.assertIn("customer_number,name,status", csv_content)
        self.assertIn("K-1000,Nord Security GmbH,active", csv_content)

    def test_vcard_export_uses_current_contact_truth_and_links_document(self) -> None:
        result = self.ops_service.export_vcard("tenant-1", self.customer.id, self.contact.id, self.actor)
        content = base64.b64decode(result.content_base64).decode("utf-8")
        document = self.document_service.documents[result.document_id]

        self.assertEqual(result.file_name, "alex-kunde.vcf")
        self.assertIn("BEGIN:VCARD", content)
        self.assertIn("FN:Alex Kunde", content)
        self.assertIn("ORG:Nord Security GmbH", content)
        self.assertNotIn("notes", content.lower())
        self.assertEqual(document.links[0]["owner_type"], "crm.customer_contact")
        self.assertEqual(document.links[0]["owner_id"], self.contact.id)

    def test_history_listing_is_tenant_scoped(self) -> None:
        self.customer_service.update_customer(
            "tenant-1",
            self.customer.id,
            CustomerUpdate(name="Nord Security AG", version_no=self.customer.version_no),
            self.actor,
        )
        history = self.ops_service.list_history("tenant-1", self.customer.id, self.actor)

        self.assertGreaterEqual(len(history), 2)
        self.assertEqual(history[0].tenant_id, "tenant-1")

        with self.assertRaises(ApiException) as context:
            self.ops_service.list_history("tenant-1", self.customer.id, _actor("tenant-2"))

        self.assertEqual(context.exception.code, "iam.authorization.scope_denied")

    def test_payload_tenant_mismatch_is_rejected(self) -> None:
        payload = CustomerExportRequest(tenant_id="tenant-2")

        with self.assertRaises(ApiException) as context:
            self.ops_service.export_customers("tenant-1", payload, self.actor)

        self.assertEqual(context.exception.code, "customers.validation.tenant_mismatch")


if __name__ == "__main__":
    unittest.main()
