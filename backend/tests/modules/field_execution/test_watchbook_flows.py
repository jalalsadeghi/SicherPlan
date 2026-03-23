from __future__ import annotations

import base64
import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.customers.schemas import CustomerPortalContextRead
from app.modules.field_execution.models import Watchbook, WatchbookEntry
from app.modules.field_execution.schemas import WatchbookEntryCreate, WatchbookOpenRequest, WatchbookReviewRequest, WatchbookVisibilityUpdate
from app.modules.field_execution.watchbook_service import WatchbookService
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_schemas import DocumentRead, DocumentVersionRead


def _actor(*roles: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id="tenant-1",
        role_keys=frozenset(roles),
        permission_keys=frozenset({"field.watchbook.read", "field.watchbook.write", "field.watchbook.review"}),
        scopes=tuple(AuthenticatedRoleScope(role_key=role, scope_type="tenant") for role in roles),
        request_id="req-1",
    )


def _customer_context() -> CustomerPortalContextRead:
    return CustomerPortalContextRead(
        tenant_id="tenant-1",
        user_id="customer-user",
        customer_id="customer-1",
        contact_id="contact-1",
        customer={"id": "customer-1", "tenant_id": "tenant-1", "customer_number": "C1", "name": "Customer", "status": "active"},
        contact={"id": "contact-1", "tenant_id": "tenant-1", "customer_id": "customer-1", "full_name": "Customer Contact", "function_label": None, "email": None, "phone": None, "mobile": None, "status": "active"},
        scopes=[{"role_key": "customer_user", "scope_type": "customer", "customer_id": "customer-1"}],
    )


@dataclass
class _FakeDocumentService:
    links: list[tuple[str, str, str, str]] = field(default_factory=list)
    documents: dict[str, DocumentRead] = field(default_factory=dict)
    owner_documents: dict[tuple[str, str, str], list[SimpleNamespace]] = field(default_factory=dict)
    version_counter: int = 0

    def get_document(self, tenant_id: str, document_id: str, actor):  # noqa: ANN001
        if document_id not in self.documents:
            self.documents[document_id] = DocumentRead(
                id=document_id,
                tenant_id=tenant_id,
                title=document_id,
                document_type_id=None,
                source_module=None,
                source_label=None,
                status="active",
                current_version_no=1,
                metadata_json={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                created_by_user_id=None,
                updated_by_user_id=None,
                archived_at=None,
                version_no=1,
                document_type=None,
                versions=[
                    DocumentVersionRead(
                        id=f"{document_id}-v1",
                        tenant_id=tenant_id,
                        document_id=document_id,
                        version_no=1,
                        file_name=f"{document_id}.pdf",
                        content_type="application/pdf",
                        object_bucket="bucket",
                        object_key=f"{document_id}/1",
                        checksum_sha256="abc",
                        file_size_bytes=3,
                        uploaded_by_user_id=None,
                        uploaded_at=datetime.now(UTC),
                        is_revision_safe_pdf=True,
                        metadata_json={},
                    )
                ],
                links=[],
            )
        return self.documents[document_id]

    def create_document(self, tenant_id: str, payload, actor):  # noqa: ANN001
        document_id = str(uuid4())
        document = DocumentRead(
            id=document_id,
            tenant_id=tenant_id,
            title=payload.title,
            document_type_id=None,
            source_module=payload.source_module,
            source_label=payload.source_label,
            status="active",
            current_version_no=0,
            metadata_json=payload.metadata_json,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by_user_id=actor.user_id,
            updated_by_user_id=actor.user_id,
            archived_at=None,
            version_no=1,
            document_type=None,
            versions=[],
            links=[],
        )
        self.documents[document_id] = document
        return document

    def add_document_version(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.version_counter += 1
        decoded = base64.b64decode(payload.content_base64)
        doc = self.documents[document_id]
        version = DocumentVersionRead(
            id=f"{document_id}-v{self.version_counter}",
            tenant_id=tenant_id,
            document_id=document_id,
            version_no=self.version_counter,
            file_name=payload.file_name,
            content_type=payload.content_type,
            object_bucket="bucket",
            object_key=f"{document_id}/{self.version_counter}",
            checksum_sha256="abc",
            file_size_bytes=len(decoded),
            uploaded_by_user_id=actor.user_id,
            uploaded_at=datetime.now(UTC),
            is_revision_safe_pdf=payload.is_revision_safe_pdf,
            metadata_json=payload.metadata_json,
        )
        self.documents[document_id] = doc.model_copy(update={"current_version_no": version.version_no, "versions": [*doc.versions, version]})
        return version

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        if (tenant_id, document_id, payload.owner_type, payload.owner_id) in self.links:
            raise ApiException(409, "docs.document_link.duplicate", "errors.docs.document_link.duplicate")
        self.links.append((tenant_id, document_id, payload.owner_type, payload.owner_id))
        self.owner_documents[(tenant_id, payload.owner_type, payload.owner_id)] = [SimpleNamespace(id=document_id)]
        return payload


@dataclass
class _FakeAuditRepository:
    events: list[dict[str, object]] = field(default_factory=list)

    def create_login_event(self, payload):  # noqa: ANN001
        raise NotImplementedError

    def create_audit_event(self, payload):  # noqa: ANN001
        self.events.append(payload.model_dump())
        return payload


class _FakeRepo:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.watchbooks: dict[str, Watchbook] = {}
        self.entries: dict[str, list[WatchbookEntry]] = {}
        self.documents: dict[tuple[str, str, str], list[SimpleNamespace]] = {}
        self.site = SimpleNamespace(id="site-1", tenant_id="tenant-1", customer_id="customer-1", watchbook_enabled=True)
        self.order = SimpleNamespace(id="order-1", tenant_id="tenant-1", customer_id="customer-1")
        self.planning_record = SimpleNamespace(id="planning-1", tenant_id="tenant-1", order=SimpleNamespace(id="order-1", customer_id="customer-1"))
        self.subcontractor = SimpleNamespace(id="sub-1", tenant_id="tenant-1")
        self.pdf_document = SimpleNamespace(
            id="pdf-1",
            title="Watchbook PDF",
            current_version_no=1,
            document_type=None,
            versions=[SimpleNamespace(version_no=1, file_name="watchbook.pdf", content_type="application/pdf")],
        )

    def list_watchbooks(self, tenant_id: str, filters):  # noqa: ANN001
        return list(self.watchbooks.values())

    def get_watchbook(self, tenant_id: str, watchbook_id: str):
        return self.watchbooks.get(watchbook_id)

    def find_open_watchbook(self, tenant_id: str, *, context_type: str, log_date, site_id: str | None, order_id: str | None, planning_record_id: str | None):
        for row in self.watchbooks.values():
            if row.context_type == context_type and row.log_date == log_date and row.site_id == site_id and row.order_id == order_id and row.planning_record_id == planning_record_id and row.closure_state_code == "open":
                return row
        return None

    def create_watchbook(self, row: Watchbook):
        if row.id is None:
            row.id = str(uuid4())
        now = datetime.now(UTC)
        row.review_status_code = row.review_status_code or "pending"
        row.closure_state_code = row.closure_state_code or "open"
        row.customer_visibility_released = bool(row.customer_visibility_released)
        row.subcontractor_visibility_released = bool(row.subcontractor_visibility_released)
        row.customer_participation_enabled = bool(row.customer_participation_enabled)
        row.subcontractor_participation_enabled = bool(row.subcontractor_participation_enabled)
        row.customer_personal_names_released = bool(row.customer_personal_names_released)
        row.status = row.status or "active"
        row.version_no = row.version_no or 1
        row.created_at = row.created_at or now
        row.updated_at = row.updated_at or now
        self.watchbooks[row.id] = row
        self.entries[row.id] = []
        return row

    def save_watchbook(self, row: Watchbook):
        row.entries = self.entries.get(row.id, [])
        self.watchbooks[row.id] = row
        return row

    def create_entry(self, row: WatchbookEntry):
        if row.id is None:
            row.id = str(uuid4())
        row.created_at = row.created_at or datetime.now(UTC)
        self.entries[row.watchbook_id].append(row)
        self.watchbooks[row.watchbook_id].entries = self.entries[row.watchbook_id]
        return row

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str):
        return self.documents.get((tenant_id, owner_type, owner_id), [])

    def get_document(self, tenant_id: str, document_id: str):
        return self.pdf_document if document_id == "pdf-1" else None

    def get_site(self, tenant_id: str, row_id: str):
        return self.site if row_id == "site-1" else None

    def get_order(self, tenant_id: str, row_id: str):
        return self.order if row_id == "order-1" else None

    def get_planning_record(self, tenant_id: str, row_id: str):
        return self.planning_record if row_id == "planning-1" else None

    def get_shift(self, tenant_id: str, row_id: str):
        return None

    def get_subcontractor(self, tenant_id: str, subcontractor_id: str):
        return self.subcontractor if subcontractor_id == "sub-1" else None

    def list_customer_released_watchbooks(self, tenant_id: str, customer_id: str):
        return [row for row in self.watchbooks.values() if row.customer_id == customer_id and row.customer_visibility_released and row.review_status_code == "reviewed"]

    def list_subcontractor_released_watchbooks(self, tenant_id: str, subcontractor_id: str):
        return [row for row in self.watchbooks.values() if row.subcontractor_id == subcontractor_id and row.subcontractor_visibility_released and row.review_status_code == "reviewed"]


class WatchbookServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = _FakeRepo()
        self.docs = _FakeDocumentService()
        self.repo.documents = self.docs.owner_documents
        self.audit_repo = _FakeAuditRepository()
        self.service = WatchbookService(self.repo, self.docs, AuditService(self.audit_repo))

    def test_open_or_create_keeps_single_open_watchbook_per_context_and_date(self) -> None:
        payload = WatchbookOpenRequest(tenant_id="tenant-1", context_type="site", site_id="site-1", log_date=date(2026, 4, 2))
        created = self.service.open_or_create_watchbook("tenant-1", payload, _actor("dispatcher"))
        duplicate = self.service.open_or_create_watchbook("tenant-1", payload, _actor("dispatcher"))
        self.assertEqual(created.id, duplicate.id)
        self.assertEqual(len(self.repo.watchbooks), 1)

    def test_entry_keeps_author_attribution_and_attachment_links(self) -> None:
        opened = self.service.open_or_create_watchbook(
            "tenant-1",
            WatchbookOpenRequest(tenant_id="tenant-1", context_type="site", site_id="site-1", log_date=date(2026, 4, 2)),
            _actor("employee_user"),
        )
        self.docs.documents["doc-1"] = self.docs.get_document("tenant-1", "doc-1", _actor("employee_user"))
        entry = self.service.create_entry(
            "tenant-1",
            opened.id,
            WatchbookEntryCreate(entry_type_code="employee_note", narrative="All clear", attachment_document_ids=["doc-1"]),
            _actor("employee_user"),
            author_actor_type="employee",
        )
        self.assertEqual(entry.author_actor_type, "employee")
        self.assertEqual(entry.attachment_document_ids, ["doc-1"])

    def test_review_close_and_pdf_generation_are_auditable(self) -> None:
        opened = self.service.open_or_create_watchbook(
            "tenant-1",
            WatchbookOpenRequest(tenant_id="tenant-1", context_type="site", site_id="site-1", log_date=date(2026, 4, 2)),
            _actor("dispatcher"),
        )
        reviewed = self.service.review_watchbook("tenant-1", opened.id, WatchbookReviewRequest(supervisor_note="Checked"), _actor("controller_qm"))
        closed = self.service.close_watchbook("tenant-1", opened.id, _actor("controller_qm"))
        pdf = self.service.generate_pdf("tenant-1", opened.id, _actor("controller_qm"))
        self.assertEqual(reviewed.review_status_code, "reviewed")
        self.assertEqual(closed.closure_state_code, "closed")
        self.assertEqual(pdf.document.current_version_no, 1)
        self.assertTrue(any(item["event_type"] == "field.watchbook.pdf_generated" for item in self.audit_repo.events))

    def test_customer_participation_stays_disabled_until_enabled(self) -> None:
        opened = self.service.open_or_create_watchbook(
            "tenant-1",
            WatchbookOpenRequest(tenant_id="tenant-1", context_type="site", site_id="site-1", log_date=date(2026, 4, 2)),
            _actor("dispatcher"),
        )
        with self.assertRaises(ApiException):
            self.service.add_customer_portal_entry(_customer_context(), opened.id, WatchbookEntryCreate(entry_type_code="customer_note", narrative="Need update"), _actor("customer_user"))
        self.service.update_visibility(
            "tenant-1",
            opened.id,
            WatchbookVisibilityUpdate(customer_visibility_released=True, customer_participation_enabled=True),
            _actor("controller_qm"),
        )
        entry = self.service.add_customer_portal_entry(
            _customer_context(),
            opened.id,
            WatchbookEntryCreate(entry_type_code="customer_note", narrative="Need update"),
            _actor("customer_user"),
        )
        self.assertEqual(entry.author_actor_type, "customer")

    def test_watchbook_metadata_exposes_composite_tenant_unique_key(self) -> None:
        constraints = {constraint.name for constraint in Watchbook.__table__.constraints}
        self.assertIn("uq_field_watchbook_tenant_id_id", constraints)


if __name__ == "__main__":
    unittest.main()
