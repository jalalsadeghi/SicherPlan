from __future__ import annotations

import base64
import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from app.errors import ApiException
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.migration_document_service import MigrationDocumentPilotService
from app.modules.platform_services.migration_schemas import (
    BarcodeOutputRequest,
    HistoricalDocumentImportRequest,
    HistoricalDocumentManifestEntry,
)


@dataclass
class _Doc:
    id: str
    tenant_id: str
    title: str
    document_type_id: str | None
    source_module: str | None
    source_label: str | None
    metadata_json: dict[str, object]
    status: str = "active"
    current_version_no: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None
    version_no: int = 1
    document_type: object | None = None
    versions: list[object] = field(default_factory=list)
    links: list[object] = field(default_factory=list)


@dataclass
class _DocumentType:
    id: str
    key: str
    name: str
    description: str | None = None
    is_system_type: bool = True


@dataclass
class _Version:
    id: str
    tenant_id: str
    document_id: str
    version_no: int
    file_name: str
    content_type: str
    object_bucket: str
    object_key: str
    checksum_sha256: str
    file_size_bytes: int
    uploaded_by_user_id: str | None
    uploaded_at: datetime
    is_revision_safe_pdf: bool
    metadata_json: dict[str, object]


@dataclass
class _Link:
    id: str
    tenant_id: str
    document_id: str
    owner_type: str
    owner_id: str
    relation_type: str
    label: str | None
    linked_by_user_id: str | None
    linked_at: datetime
    metadata_json: dict[str, object]


class _FakeDocumentRepository:
    SUPPORTED_OWNER_TYPES = frozenset({"crm.customer", "hr.employee", "partner.subcontractor", "ops.customer_order"})

    def __init__(self) -> None:
        self.documents: dict[str, _Doc] = {}
        self.owners = {
            ("tenant-1", "crm.customer", "customer-1"),
            ("tenant-1", "hr.employee", "employee-1"),
            ("tenant-1", "ops.customer_order", "order-1"),
        }

    def get_document_type_by_key(self, key: str):  # noqa: ANN001
        if key is None:
            return None
        if key in {"customer_contract", "generated_badge_output"}:
            return _DocumentType(id=f"type-{key}", key=key, name=key.replace("_", " ").title())
        return None

    def create_document(self, row):  # noqa: ANN001
        document_type = None
        for key in ("customer_contract", "generated_badge_output"):
            if row.document_type_id == f"type-{key}":
                document_type = _DocumentType(id=row.document_type_id, key=key, name=key.replace("_", " ").title())
                break
        document = _Doc(
            id=str(uuid4()),
            tenant_id=row.tenant_id,
            title=row.title,
            document_type_id=row.document_type_id,
            source_module=row.source_module,
            source_label=row.source_label,
            metadata_json=row.metadata_json,
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            document_type=document_type,
        )
        self.documents[document.id] = document
        return document

    def get_document(self, tenant_id: str, document_id: str):  # noqa: ANN001
        document = self.documents.get(document_id)
        return document if document is not None and document.tenant_id == tenant_id else None

    def list_document_versions(self, tenant_id: str, document_id: str):  # noqa: ANN001
        document = self.get_document(tenant_id, document_id)
        return list(document.versions if document is not None else [])

    def create_document_version(self, document, row):  # noqa: ANN001
        version = _Version(
            id=str(uuid4()),
            tenant_id=row.tenant_id,
            document_id=row.document_id,
            version_no=row.version_no,
            file_name=row.file_name,
            content_type=row.content_type,
            object_bucket=row.object_bucket,
            object_key=row.object_key,
            checksum_sha256=row.checksum_sha256,
            file_size_bytes=row.file_size_bytes,
            uploaded_by_user_id=row.uploaded_by_user_id,
            uploaded_at=datetime.now(UTC),
            is_revision_safe_pdf=row.is_revision_safe_pdf,
            metadata_json=row.metadata_json,
        )
        document.current_version_no = row.version_no
        document.version_no += 1
        document.versions.append(version)
        return version

    def get_document_version(self, tenant_id: str, document_id: str, version_no: int):  # noqa: ANN001
        document = self.get_document(tenant_id, document_id)
        if document is None:
            return None
        for version in document.versions:
            if version.version_no == version_no:
                return version
        return None

    def create_document_link(self, row):  # noqa: ANN001
        if not self.owner_exists(row.tenant_id, row.owner_type, row.owner_id):
            from sqlalchemy.exc import IntegrityError

            raise IntegrityError("owner", None, None)
        link = _Link(
            id=str(uuid4()),
            tenant_id=row.tenant_id,
            document_id=row.document_id,
            owner_type=row.owner_type,
            owner_id=row.owner_id,
            relation_type=row.relation_type,
            label=row.label,
            linked_by_user_id=row.linked_by_user_id,
            linked_at=datetime.now(UTC),
            metadata_json=row.metadata_json,
        )
        self.documents[row.document_id].links.append(link)
        return link

    def owner_exists(self, tenant_id: str, owner_type: str, owner_id: str) -> bool:
        return (tenant_id, owner_type, owner_id) in self.owners

    def find_document_by_source_reference(self, tenant_id: str, *, source_module: str, source_label: str):
        for document in self.documents.values():
            if document.tenant_id == tenant_id and document.source_module == source_module and document.source_label == source_label:
                return document
        return None


class _FakeStorage:
    def put_object(self, bucket_name, object_key, content, *, content_type, metadata=None):  # noqa: ANN001
        return None

    def get_object(self, bucket_name, object_key):  # noqa: ANN001
        raise AssertionError("downloads not expected in this test")


def _actor() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"platform.docs.read", "platform.docs.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
    )


class TestMigrationDocumentPilot(unittest.TestCase):
    def setUp(self) -> None:
        from app.modules.platform_services.docs_service import DocumentService

        self.repository = _FakeDocumentRepository()
        self.document_service = DocumentService(self.repository, storage=_FakeStorage(), bucket_name="docs-test")
        self.service = MigrationDocumentPilotService(document_service=self.document_service, repository=self.repository)

    def test_import_historical_document_preserves_provenance(self) -> None:
        entry = HistoricalDocumentManifestEntry(
            manifest_row_key="DOC-1",
            source_system="legacy_dms",
            legacy_document_id="4711",
            source_file_name="contract.pdf",
            title="Contract",
            owner_type="crm.customer",
            owner_id="customer-1",
            relation_type="attachment",
            document_type_key="customer_contract",
            checksum_sha256="d" * 64,
            content_base64=base64.b64encode(b"contract").decode("ascii"),
            metadata_json={"legacy_folder": "/kunden/vertrag"},
        )
        entry.checksum_sha256 = __import__("hashlib").sha256(b"contract").hexdigest()
        result = self.service.import_historical_documents("tenant-1", HistoricalDocumentImportRequest(tenant_id="tenant-1", entries=[entry]), _actor())
        self.assertEqual(result.imported_count, 1)
        document = next(iter(self.repository.documents.values()))
        self.assertEqual(document.metadata_json["migration"]["legacy_document_id"], "4711")
        self.assertEqual(document.source_label, "historical:legacy_dms:4711")

    def test_import_flags_missing_file_and_orphan_link(self) -> None:
        result = self.service.import_historical_documents(
            "tenant-1",
            HistoricalDocumentImportRequest(
                tenant_id="tenant-1",
                entries=[
                    HistoricalDocumentManifestEntry(
                        manifest_row_key="DOC-1",
                        source_system="legacy_dms",
                        legacy_document_id="1",
                        source_file_name="missing.pdf",
                        title="Missing",
                        owner_type="crm.customer",
                        owner_id="customer-404",
                        relation_type="attachment",
                        checksum_sha256="a" * 64,
                        content_base64=None,
                    )
                ],
            ),
            _actor(),
        )
        self.assertEqual(result.invalid_count, 1)
        issue_codes = {issue.code for issue in result.rows[0].issues}
        self.assertIn("missing_file_content", issue_codes)

    def test_import_blocks_duplicate_manifest_reference(self) -> None:
        raw = base64.b64encode(b"x").decode("ascii")
        checksum = __import__("hashlib").sha256(b"x").hexdigest()
        entry = HistoricalDocumentManifestEntry(
            manifest_row_key="DOC-1",
            source_system="legacy",
            legacy_document_id="42",
            source_file_name="x.pdf",
            title="X",
            owner_type="crm.customer",
            owner_id="customer-1",
            relation_type="attachment",
            checksum_sha256=checksum,
            content_base64=raw,
        )
        self.service.import_historical_documents("tenant-1", HistoricalDocumentImportRequest(tenant_id="tenant-1", entries=[entry]), _actor())
        second = self.service.import_historical_documents("tenant-1", HistoricalDocumentImportRequest(tenant_id="tenant-1", entries=[entry]), _actor())
        self.assertEqual(second.invalid_count, 1)
        self.assertEqual(second.rows[0].issues[0].code, "duplicate_manifest_reference")

    def test_generate_barcode_output_is_deterministic_and_linked(self) -> None:
        result = self.service.generate_barcode_output(
            "tenant-1",
            BarcodeOutputRequest(
                tenant_id="tenant-1",
                owner_type="ops.customer_order",
                owner_id="order-1",
                output_kind="order_badge",
                title="Order Badge",
                document_type_key="generated_badge_output",
                payload_fields={"order_no": "A-1001", "customer_number": "K-1001"},
            ),
            _actor(),
        )
        self.assertEqual(result.payload_text, "SP|1|order_badge|ops.customer_order|order-1|customer_number=K-1001|order_no=A-1001")
        document = self.repository.documents[result.document_id]
        self.assertEqual(document.links[0].owner_id, "order-1")

    def test_generate_barcode_output_rejects_unsupported_owner(self) -> None:
        with self.assertRaises(ApiException):
            self.service.generate_barcode_output(
                "tenant-1",
                BarcodeOutputRequest(
                    tenant_id="tenant-1",
                    owner_type="unsupported.owner",
                    owner_id="1",
                    output_kind="employee_badge",
                    title="Bad",
                ),
                _actor(),
            )
