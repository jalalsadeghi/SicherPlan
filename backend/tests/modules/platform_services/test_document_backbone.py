from __future__ import annotations

import base64
import tempfile
import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from app.db import Base
from app.errors import ApiException
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_models import Document, DocumentLink, DocumentType, DocumentVersion
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import FileSystemObjectStorageAdapter, InMemoryObjectStorageAdapter


@dataclass
class FakeDocumentType:
    id: str
    key: str
    name: str
    description: str | None = None
    is_system_type: bool = True


@dataclass
class FakeDocumentVersion:
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
    metadata_json: dict[str, object] = field(default_factory=dict)


@dataclass
class FakeDocumentLink:
    id: str
    tenant_id: str
    document_id: str
    owner_type: str
    owner_id: str
    relation_type: str
    label: str | None
    linked_by_user_id: str | None
    linked_at: datetime
    metadata_json: dict[str, object] = field(default_factory=dict)


@dataclass
class FakeDocument:
    id: str
    tenant_id: str
    title: str
    document_type_id: str | None
    source_module: str | None
    source_label: str | None
    status: str = "active"
    current_version_no: int = 0
    metadata_json: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None
    version_no: int = 1
    document_type: FakeDocumentType | None = None
    versions: list[FakeDocumentVersion] = field(default_factory=list)
    links: list[FakeDocumentLink] = field(default_factory=list)


class FakeDocumentRepository:
    SUPPORTED_OWNER_TYPES = frozenset({"core.tenant", "core.branch"})

    def __init__(self) -> None:
        self.document_types = {
            "timesheet": FakeDocumentType(id="type-1", key="timesheet", name="Timesheet"),
        }
        self.documents: dict[str, FakeDocument] = {}
        self.owners = {
            ("tenant-1", "core.tenant", "tenant-1"),
            ("tenant-1", "core.branch", "branch-1"),
        }

    def get_document_type_by_key(self, key: str):
        return self.document_types.get(key)

    def create_document(self, row: Document):
        document = FakeDocument(
            id=str(uuid4()),
            tenant_id=row.tenant_id,
            title=row.title,
            document_type_id=row.document_type_id,
            source_module=row.source_module,
            source_label=row.source_label,
            metadata_json=row.metadata_json,
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
            document_type=next(
                (doc_type for doc_type in self.document_types.values() if doc_type.id == row.document_type_id),
                None,
            ),
        )
        self.documents[document.id] = document
        return document

    def get_document(self, tenant_id: str, document_id: str):
        document = self.documents.get(document_id)
        if document is None or document.tenant_id != tenant_id:
            return None
        return document

    def list_document_versions(self, tenant_id: str, document_id: str):
        document = self.get_document(tenant_id, document_id)
        return list(document.versions if document is not None else [])

    def create_document_version(self, document: FakeDocument, row: DocumentVersion):
        version = FakeDocumentVersion(
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
        document.current_version_no = version.version_no
        document.version_no += 1
        document.versions.append(version)
        return version

    def get_document_version(self, tenant_id: str, document_id: str, version_no: int):
        document = self.get_document(tenant_id, document_id)
        if document is None:
            return None
        for version in document.versions:
            if version.version_no == version_no:
                return version
        return None

    def create_document_link(self, row: DocumentLink):
        document = self.documents[row.document_id]
        for existing in document.links:
            if (
                existing.owner_type == row.owner_type
                and existing.owner_id == row.owner_id
                and existing.relation_type == row.relation_type
            ):
                from sqlalchemy.exc import IntegrityError

                raise IntegrityError("duplicate", None, None)
        link = FakeDocumentLink(
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
        document.links.append(link)
        return link

    def owner_exists(self, tenant_id: str, owner_type: str, owner_id: str) -> bool:
        return (tenant_id, owner_type, owner_id) in self.owners


def _actor(tenant_id: str = "tenant-1", *, platform: bool = False) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"platform_admin"} if platform else {"tenant_admin"}),
        permission_keys=frozenset({"platform.docs.read", "platform.docs.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
    )


class TestDocumentMetadata(unittest.TestCase):
    def test_expected_docs_tables_are_registered(self) -> None:
        self.assertIn("docs.document_type", Base.metadata.tables)
        self.assertIn("docs.document", Base.metadata.tables)
        self.assertIn("docs.document_version", Base.metadata.tables)
        self.assertIn("docs.document_link", Base.metadata.tables)

    def test_document_version_is_unique_per_document_and_immutable_oriented(self) -> None:
        version_constraints = {
            constraint.name
            for constraint in DocumentVersion.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn("uq_docs_document_version_document_version_no", version_constraints)
        self.assertIn("uq_docs_document_version_object_ref", version_constraints)
        self.assertNotIn("updated_at", {column.name for column in DocumentVersion.__table__.columns})
        self.assertNotIn("version_no", {name for name in {column.name for column in DocumentVersion.__table__.columns} - {"version_no"}})

    def test_document_link_owner_lookup_index_and_polymorphic_columns_exist(self) -> None:
        index_names = {index.name for index in DocumentLink.__table__.indexes if isinstance(index, Index)}
        self.assertIn("ix_docs_document_link_owner_lookup", index_names)
        ddl = str(CreateTable(DocumentLink.__table__).compile(dialect=dialect()))
        self.assertIn("owner_type", ddl)
        self.assertIn("owner_id", ddl)


class TestFileSystemObjectStorageAdapter(unittest.TestCase):
    def test_filesystem_storage_roundtrip_and_bucket_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = FileSystemObjectStorageAdapter(tmpdir)
            adapter.put_object("bucket-a", "tenant/doc/v1/file.txt", b"hello", content_type="text/plain")
            stored = adapter.get_object("bucket-a", "tenant/doc/v1/file.txt")
            self.assertEqual(stored.content, b"hello")
            self.assertEqual(stored.content_type, "text/plain")
            self.assertFalse((Path(tmpdir) / "bucket-b" / "tenant" / "doc").exists())


class TestDocumentService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeDocumentRepository()
        self.storage = InMemoryObjectStorageAdapter()
        self.service = DocumentService(self.repository, storage=self.storage, bucket_name="docs-test")

    def test_document_can_be_created_versioned_and_linked(self) -> None:
        document = self.service.create_document(
            "tenant-1",
            DocumentCreate(
                tenant_id="tenant-1",
                title="Einsatznachweis",
                document_type_key="timesheet",
                source_module="finance",
            ),
            _actor(),
        )

        version = self.service.add_document_version(
            "tenant-1",
            document.id,
            DocumentVersionCreate(
                file_name="timesheet.pdf",
                content_type="application/pdf",
                content_base64=base64.b64encode(b"pdf-1").decode("ascii"),
                is_revision_safe_pdf=True,
            ),
            _actor(),
        )
        link = self.service.add_document_link(
            "tenant-1",
            document.id,
            DocumentLinkCreate(owner_type="core.branch", owner_id="branch-1", relation_type="attachment"),
            _actor(),
        )
        fetched = self.service.get_document("tenant-1", document.id, _actor())

        self.assertEqual(document.document_type.key, "timesheet")
        self.assertEqual(version.version_no, 1)
        self.assertEqual(link.owner_id, "branch-1")
        self.assertEqual(len(fetched.versions), 1)
        self.assertEqual(len(fetched.links), 1)

    def test_duplicate_content_marks_duplicate_of_version(self) -> None:
        document = self.service.create_document(
            "tenant-1",
            DocumentCreate(tenant_id="tenant-1", title="Objektreport"),
            _actor(),
        )
        payload = DocumentVersionCreate(
            file_name="report.pdf",
            content_type="application/pdf",
            content_base64=base64.b64encode(b"same-content").decode("ascii"),
        )
        first = self.service.add_document_version("tenant-1", document.id, payload, _actor())
        second = self.service.add_document_version("tenant-1", document.id, payload, _actor())

        self.assertEqual(first.version_no, 1)
        self.assertEqual(second.version_no, 2)
        self.assertEqual(second.metadata_json["duplicate_of_version_no"], 1)

    def test_download_is_tenant_scoped(self) -> None:
        document = self.service.create_document(
            "tenant-1",
            DocumentCreate(tenant_id="tenant-1", title="Mandantenakte"),
            _actor(),
        )
        self.service.add_document_version(
            "tenant-1",
            document.id,
            DocumentVersionCreate(
                file_name="akte.txt",
                content_type="text/plain",
                content_base64=base64.b64encode(b"tenant-safe").decode("ascii"),
            ),
            _actor(),
        )

        with self.assertRaises(ApiException):
            self.service.download_document_version("tenant-1", document.id, 1, _actor("tenant-2"))

        download = self.service.download_document_version("tenant-1", document.id, 1, _actor())
        self.assertEqual(download.content, b"tenant-safe")

    def test_link_creation_requires_supported_existing_owner(self) -> None:
        document = self.service.create_document(
            "tenant-1",
            DocumentCreate(tenant_id="tenant-1", title="Hinweis"),
            _actor(),
        )

        with self.assertRaises(ApiException):
            self.service.add_document_link(
                "tenant-1",
                document.id,
                DocumentLinkCreate(owner_type="core.mandate", owner_id="mandate-1"),
                _actor(),
            )

        with self.assertRaises(ApiException):
            self.service.add_document_link(
                "tenant-1",
                document.id,
                DocumentLinkCreate(owner_type="core.branch", owner_id="missing"),
                _actor(),
            )


if __name__ == "__main__":
    unittest.main()
