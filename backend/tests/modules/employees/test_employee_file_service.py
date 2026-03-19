from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.modules.employees.file_service import EmployeeFileService
from app.modules.employees.models import Employee
from app.modules.employees.schemas import EmployeePhotoUpload
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_models import Document, DocumentLink, DocumentVersion
from app.modules.platform_services.docs_schemas import (
    DocumentCreate,
    DocumentLinkCreate,
    DocumentRead,
    DocumentVersionCreate,
    DocumentVersionRead,
)


def _context() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"employees.employee.read", "employees.employee.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-1",
    )


@dataclass
class FakeEmployeeRepo:
    employee: Employee = field(
        default_factory=lambda: Employee(
            id="employee-1",
            tenant_id="tenant-1",
            personnel_no="EMP-1001",
            first_name="Anna",
            last_name="Wagner",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
    )

    def get_employee(self, tenant_id: str, employee_id: str) -> Employee | None:
        if tenant_id == self.employee.tenant_id and employee_id == self.employee.id:
            return self.employee
        return None


@dataclass
class FakeDocumentRepo:
    documents: list[Document] = field(default_factory=list)

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]:
        return [
            document
            for document in self.documents
            if document.tenant_id == tenant_id
            and any(link.owner_type == owner_type and link.owner_id == owner_id for link in document.links)
        ]


class FakeDocumentService:
    def __init__(self, repository: FakeDocumentRepo) -> None:
        self.repository = repository

    def create_document(self, tenant_id: str, payload: DocumentCreate, actor) -> DocumentRead:  # noqa: ANN001
        now = datetime.now(UTC)
        document = Document(
            id=f"document-{len(self.repository.documents) + 1}",
            tenant_id=tenant_id,
            title=payload.title,
            source_module=payload.source_module,
            source_label=payload.source_label,
            metadata_json=payload.metadata_json,
            current_version_no=0,
            status="active",
            created_at=now,
            updated_at=now,
            created_by_user_id=actor.user_id,
            updated_by_user_id=actor.user_id,
            version_no=1,
            versions=[],
            links=[],
        )
        self.repository.documents.append(document)
        return DocumentRead.model_validate(document)

    def add_document_version(
        self,
        tenant_id: str,
        document_id: str,
        payload: DocumentVersionCreate,
        actor,  # noqa: ANN001
    ) -> DocumentVersionRead:
        document = next(document for document in self.repository.documents if document.id == document_id and document.tenant_id == tenant_id)
        version_no = document.current_version_no + 1
        version = DocumentVersion(
            id=f"version-{document_id}-{version_no}",
            tenant_id=tenant_id,
            document_id=document_id,
            version_no=version_no,
            file_name=payload.file_name,
            content_type=payload.content_type,
            object_bucket="bucket",
            object_key=f"{document_id}/{version_no}",
            checksum_sha256="checksum",
            file_size_bytes=10,
            uploaded_by_user_id=actor.user_id,
            uploaded_at=datetime.now(UTC),
            is_revision_safe_pdf=False,
            metadata_json=payload.metadata_json,
        )
        document.versions.append(version)
        document.current_version_no = version_no
        document.updated_at = datetime.now(UTC)
        return DocumentVersionRead.model_validate(version)

    def add_document_link(self, tenant_id: str, document_id: str, payload: DocumentLinkCreate, actor):  # noqa: ANN001
        document = next(document for document in self.repository.documents if document.id == document_id and document.tenant_id == tenant_id)
        link = DocumentLink(
            id=f"link-{document_id}",
            tenant_id=tenant_id,
            document_id=document_id,
            owner_type=payload.owner_type,
            owner_id=payload.owner_id,
            relation_type=payload.relation_type,
            label=payload.label,
            linked_by_user_id=actor.user_id,
            linked_at=datetime.now(UTC),
            metadata_json=payload.metadata_json,
        )
        document.links.append(link)
        return link


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.audit_events: list[object] = []

    def create_login_event(self, payload):  # noqa: ANN001
        return payload

    def create_audit_event(self, payload):  # noqa: ANN001
        self.audit_events.append(payload)
        return payload


class EmployeeFileServiceTest(unittest.TestCase):
    def test_profile_photo_uses_docs_backbone_and_reuses_document_on_replace(self) -> None:
        repository = FakeDocumentRepo()
        audit_repo = RecordingAuditRepository()
        service = EmployeeFileService(
            employee_repository=FakeEmployeeRepo(),
            document_repository=repository,
            document_service=FakeDocumentService(repository),
            audit_service=AuditService(audit_repo),
        )

        first = service.upsert_profile_photo(
            "tenant-1",
            "employee-1",
            EmployeePhotoUpload(
                title="Profilfoto",
                file_name="anna.png",
                content_type="image/png",
                content_base64="YQ==",
            ),
            _context(),
        )
        second = service.upsert_profile_photo(
            "tenant-1",
            "employee-1",
            EmployeePhotoUpload(
                title="Profilfoto",
                file_name="anna-new.png",
                content_type="image/png",
                content_base64="Yg==",
            ),
            _context(),
        )

        self.assertEqual(len(repository.documents), 1)
        self.assertEqual(first.document_id, second.document_id)
        self.assertEqual(repository.documents[0].current_version_no, 2)
        self.assertEqual(second.file_name, "anna-new.png")
        self.assertIn("employees.photo.updated", [event.event_type for event in audit_repo.audit_events])


if __name__ == "__main__":
    unittest.main()
