from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.modules.customers.collaboration_service import CustomerCollaborationService
from app.modules.customers.schemas import (
    CustomerContactCreate,
    CustomerCreate,
    CustomerEmployeeBlockCreate,
    CustomerEmployeeBlockUpdate,
    CustomerHistoryAttachmentLinkCreate,
    CustomerPortalPrivacyUpdate,
)
from app.modules.customers.service import CustomerService
from app.modules.iam.audit_schemas import LoginEventRead
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.customers.test_customer_backbone import FakeCustomerRepository
from tests.modules.customers.test_customer_portal_context import _internal_actor


@dataclass
class FakeDocumentType:
    key: str


@dataclass
class FakeDocumentVersion:
    file_name: str
    content_type: str


@dataclass
class FakeDocument:
    id: str
    title: str
    document_type: FakeDocumentType | None
    versions: list[FakeDocumentVersion]
    current_version_no: int


class FakeDocumentRepository:
    def __init__(self) -> None:
        self.documents_by_owner: dict[tuple[str, str, str], list[FakeDocument]] = {}

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str):
        return self.documents_by_owner.get((tenant_id, owner_type, owner_id), [])


class FakeDocumentService:
    def __init__(self) -> None:
        self.links: list[tuple[str, str, str, str | None]] = []

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.links.append((tenant_id, document_id, payload.owner_id, payload.label))
        return None


class FakeLoginAuditRepository:
    def __init__(self) -> None:
        self.events: list[LoginEventRead] = []

    def list_login_events_for_users(self, tenant_id: str, user_ids: list[str]):
        return [row for row in self.events if row.tenant_id == tenant_id and row.user_account_id in user_ids]


class TestCustomerCollaborationService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeCustomerRepository()
        self.document_repository = FakeDocumentRepository()
        self.document_service = FakeDocumentService()
        self.login_audit_repository = FakeLoginAuditRepository()
        self.customer_service = CustomerService(self.repository)
        self.service = CustomerCollaborationService(
            self.repository,
            login_audit_repository=self.login_audit_repository,
            document_repository=self.document_repository,
            document_service=self.document_service,
            audit_service=None,
        )
        self.customer = self.customer_service.create_customer(
            "tenant-1",
            CustomerCreate(tenant_id="tenant-1", customer_number="K-3000", name="Collab Kunde GmbH"),
            _internal_actor(),
        )
        self.contact = self.customer_service.create_contact(
            "tenant-1",
            self.customer.id,
            CustomerContactCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                full_name="Jamie Admin",
                email="jamie@example.invalid",
                user_id="user-portal",
                is_primary_contact=True,
            ),
            _internal_actor(),
        )

    def test_history_entries_include_docs_backed_attachments(self) -> None:
        history_entry = self.repository.list_history_entries("tenant-1", self.customer.id)[0]
        self.document_repository.documents_by_owner[("tenant-1", "crm.customer_history_entry", history_entry.id)] = [
            FakeDocument(
                id="doc-1",
                title="Freigabevermerk",
                document_type=FakeDocumentType(key="attachment"),
                versions=[FakeDocumentVersion(file_name="freigabe.pdf", content_type="application/pdf")],
                current_version_no=1,
            )
        ]

        history = self.service.list_history("tenant-1", self.customer.id, _internal_actor())

        self.assertEqual(history[0].attachments[0].document_id, "doc-1")
        self.assertEqual(history[0].attachments[0].file_name, "freigabe.pdf")

    def test_portal_history_is_customer_scoped_and_reduced(self) -> None:
        history_entry = self.repository.list_history_entries("tenant-1", self.customer.id)[0]
        context = type(
            "PortalContext",
            (),
            {"tenant_id": "tenant-1", "customer_id": self.customer.id},
        )()

        history = self.service.list_portal_history(context)  # type: ignore[arg-type]

        self.assertEqual(history.customer_id, self.customer.id)
        self.assertEqual(history.items[0].id, history_entry.id)
        self.assertFalse(hasattr(history.items[0], "before_json"))
        self.assertNotIn("Jamie", history.items[0].summary)

    def test_portal_history_masks_attachment_titles_until_explicit_release(self) -> None:
        history_entry = self.repository.list_history_entries("tenant-1", self.customer.id)[0]
        self.document_repository.documents_by_owner[("tenant-1", "crm.customer_history_entry", history_entry.id)] = [
            FakeDocument(
                id="doc-privacy",
                title="Jamie Einsatzbericht",
                document_type=FakeDocumentType(key="report"),
                versions=[FakeDocumentVersion(file_name="jamie-einsatzbericht.pdf", content_type="application/pdf")],
                current_version_no=1,
            )
        ]
        context = type("PortalContext", (), {"tenant_id": "tenant-1", "customer_id": self.customer.id})()

        masked = self.service.list_portal_history(context)  # type: ignore[arg-type]
        self.assertEqual(masked.items[0].attachments[0].title, "Report 1")
        self.assertEqual(masked.items[0].attachments[0].file_name, "attachment-1.pdf")

        self.service.update_portal_privacy(
            "tenant-1",
            self.customer.id,
            CustomerPortalPrivacyUpdate(person_names_released=True),
            _internal_actor(),
        )
        released = self.service.list_portal_history(context)  # type: ignore[arg-type]
        self.assertEqual(released.items[0].attachments[0].title, "Jamie Einsatzbericht")

    def test_login_history_masks_identifier_and_contact_name(self) -> None:
        self.login_audit_repository.events = [
            LoginEventRead(
                id="login-privacy",
                tenant_id="tenant-1",
                user_account_id="user-portal",
                session_id="session-1",
                tenant_code="tenant-1",
                identifier="jamie.admin@example.invalid",
                outcome="success",
                failure_reason=None,
                auth_method="password",
                ip_address=None,
                user_agent=None,
                request_id="req-1",
                created_at=datetime.now(UTC),
                metadata_json={},
            )
        ]

        history = self.service.list_login_history("tenant-1", self.customer.id, _internal_actor())

        self.assertEqual(history[0].identifier, "j***@example.invalid")
        self.assertIsNone(history[0].contact_name)

    def test_link_history_attachment_uses_docs_owner_type(self) -> None:
        history_entry = self.repository.list_history_entries("tenant-1", self.customer.id)[0]

        self.service.link_history_attachment(
            "tenant-1",
            self.customer.id,
            history_entry.id,
            CustomerHistoryAttachmentLinkCreate(document_id="doc-2", label="Kundenanlage"),
            _internal_actor(),
        )

        self.assertEqual(
            self.document_service.links[0],
            ("tenant-1", "doc-2", history_entry.id, "Kundenanlage"),
        )

    def test_login_history_is_filtered_to_customer_portal_users(self) -> None:
        self.login_audit_repository.events = [
            LoginEventRead(
                id="login-1",
                tenant_id="tenant-1",
                user_account_id="user-portal",
                session_id="session-1",
                tenant_code="tenant-1",
                identifier="jamie@example.invalid",
                outcome="success",
                failure_reason=None,
                auth_method="password",
                ip_address=None,
                user_agent=None,
                request_id="req-1",
                created_at=datetime.now(UTC),
                metadata_json={},
            ),
            LoginEventRead(
                id="login-2",
                tenant_id="tenant-1",
                user_account_id="user-other",
                session_id="session-2",
                tenant_code="tenant-1",
                identifier="other@example.invalid",
                outcome="success",
                failure_reason=None,
                auth_method="password",
                ip_address=None,
                user_agent=None,
                request_id="req-2",
                created_at=datetime.now(UTC),
                metadata_json={},
            ),
        ]

        history = self.service.list_login_history("tenant-1", self.customer.id, _internal_actor())

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].contact_id, self.contact.id)

    def test_employee_block_capability_and_create_update_flow(self) -> None:
        created = self.service.create_employee_block(
            "tenant-1",
            self.customer.id,
            CustomerEmployeeBlockCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                employee_id="11111111-1111-1111-1111-111111111111",
                reason="Kundenwunsch",
                effective_from=date(2026, 3, 1),
                effective_to=None,
            ),
            _internal_actor(),
        )
        collection = self.service.list_employee_blocks("tenant-1", self.customer.id, _internal_actor())

        self.assertFalse(collection.capability.directory_available)
        self.assertEqual(collection.capability.employee_reference_mode, "employee_id_only")
        self.assertEqual(collection.items[0].id, created.id)

        updated = self.service.update_employee_block(
            "tenant-1",
            self.customer.id,
            created.id,
            CustomerEmployeeBlockUpdate(reason="Aktualisierter Kundenwunsch", version_no=created.version_no),
            _internal_actor(),
        )
        self.assertEqual(updated.reason, "Aktualisierter Kundenwunsch")

    def test_portal_privacy_release_is_explicit_and_auditable_state(self) -> None:
        before = self.service.get_portal_privacy("tenant-1", self.customer.id, _internal_actor())
        self.assertFalse(before.person_names_released)

        after = self.service.update_portal_privacy(
            "tenant-1",
            self.customer.id,
            CustomerPortalPrivacyUpdate(person_names_released=True),
            _internal_actor(),
        )

        self.assertTrue(after.person_names_released)
        self.assertIsNotNone(after.person_names_released_at)
        self.assertEqual(after.person_names_released_by_user_id, "user-admin")


if __name__ == "__main__":
    unittest.main()
