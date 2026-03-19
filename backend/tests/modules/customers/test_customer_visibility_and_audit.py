from __future__ import annotations

import unittest
from dataclasses import dataclass

from app.errors import ApiException
from app.modules.customers.ops_service import CustomerOpsService
from app.modules.customers.schemas import (
    CustomerContactCreate,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerExportRequest,
    CustomerFilter,
    CustomerImportDryRunRequest,
    CustomerUpdate,
)
from app.modules.customers.service import CustomerService
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.integration_models import ImportExportJob
from tests.modules.customers.test_customer_backbone import FakeCustomerRepository
from tests.modules.customers.test_customer_ops import FakeDocumentService, FakeIntegrationRepository, _csv_base64


@dataclass
class RecordingAuditEvent:
    event_type: str
    entity_type: str
    entity_id: str
    tenant_id: str | None
    actor_user_id: str | None
    metadata_json: dict[str, object]
    before_json: dict[str, object]
    after_json: dict[str, object]


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.login_events: list[object] = []
        self.audit_events: list[RecordingAuditEvent] = []

    def create_login_event(self, payload):  # noqa: ANN001
        self.login_events.append(payload)
        return payload

    def create_audit_event(self, payload):  # noqa: ANN001
        event = RecordingAuditEvent(
            event_type=payload.event_type,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            tenant_id=payload.tenant_id,
            actor_user_id=payload.actor_user_id,
            metadata_json=payload.metadata_json,
            before_json=payload.before_json,
            after_json=payload.after_json,
        )
        self.audit_events.append(event)
        return payload


def _internal_actor(
    *,
    role_key: str = "tenant_admin",
    tenant_id: str = "tenant-1",
    permission_keys: tuple[str, ...] = ("customers.customer.read", "customers.customer.write"),
    scope_type: str = "tenant",
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-admin",
        tenant_id=tenant_id,
        role_keys=frozenset({role_key}),
        permission_keys=frozenset(permission_keys),
        scopes=(AuthenticatedRoleScope(role_key=role_key, scope_type=scope_type),),
        request_id="req-customers",
    )


def _portal_actor() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-customer",
        user_id="user-customer",
        tenant_id="tenant-1",
        role_keys=frozenset({"customer_user"}),
        permission_keys=frozenset({"customers.customer.read", "portal.customer.access"}),
        scopes=(AuthenticatedRoleScope(role_key="customer_user", scope_type="customer", customer_id="customer-1"),),
        request_id="req-portal",
    )


class TestCustomerVisibilityAndAudit(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeCustomerRepository()
        self.audit_repo = RecordingAuditRepository()
        self.audit_service = AuditService(self.audit_repo)
        self.service = CustomerService(self.repository, audit_service=self.audit_service)
        self.document_service = FakeDocumentService()
        self.integration_repository = FakeIntegrationRepository()
        self.ops_service = CustomerOpsService(
            customer_service=self.service,
            customer_repository=self.repository,
            integration_repository=self.integration_repository,
            document_service=self.document_service,
            audit_service=self.audit_service,
        )
        self.repository.users["portal-user"] = type(
            "FakeUser",
            (),
            {"id": "portal-user", "tenant_id": "tenant-1", "archived_at": None},
        )()
        self.actor = _internal_actor()
        self.customer = self.service.create_customer(
            "tenant-1",
            CustomerCreate(tenant_id="tenant-1", customer_number="K-1000", name="Nord Security GmbH"),
            self.actor,
        )

    def test_portal_roles_are_rejected_from_internal_customer_api(self) -> None:
        with self.assertRaises(ApiException) as context:
            self.service.get_customer("tenant-1", self.customer.id, _portal_actor())

        self.assertEqual(context.exception.code, "customers.authorization.portal_forbidden")

    def test_branch_scoped_internal_roles_cannot_widen_to_customer_admin_access(self) -> None:
        branch_actor = RequestAuthorizationContext(
            session_id="session-branch",
            user_id="user-branch",
            tenant_id="tenant-1",
            role_keys=frozenset({"dispatcher"}),
            permission_keys=frozenset({"customers.customer.read"}),
            scopes=(AuthenticatedRoleScope(role_key="dispatcher", scope_type="branch", branch_id="branch-1"),),
            request_id="req-branch",
        )

        with self.assertRaises(ApiException) as context:
            self.service.list_customers("tenant-1", CustomerFilter(), branch_actor)

        self.assertEqual(context.exception.code, "customers.authorization.internal_scope_required")

    def test_customer_updates_emit_durable_audit_events(self) -> None:
        contact = self.service.create_contact(
            "tenant-1",
            self.customer.id,
            CustomerContactCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                full_name="Alex Kunde",
                email="alex@example.invalid",
            ),
            self.actor,
        )

        self.service.update_contact(
            "tenant-1",
            self.customer.id,
            contact.id,
            CustomerContactUpdate(user_id="portal-user", version_no=contact.version_no),
            self.actor,
        )

        event_types = [event.event_type for event in self.audit_repo.audit_events]
        self.assertIn("customers.customer.created", event_types)
        self.assertIn("customers.contact.created", event_types)
        self.assertIn("customers.contact.portal_link_changed", event_types)
        portal_event = next(event for event in self.audit_repo.audit_events if event.event_type == "customers.contact.portal_link_changed")
        self.assertEqual(portal_event.entity_type, "crm.customer_contact")
        self.assertEqual(portal_event.metadata_json["customer_id"], self.customer.id)

    def test_archive_visibility_is_predictable(self) -> None:
        self.service.update_customer(
            "tenant-1",
            self.customer.id,
            CustomerUpdate(status="archived", version_no=self.customer.version_no),
            self.actor,
        )

        visible_default = self.service.list_customers("tenant-1", CustomerFilter(), self.actor)
        visible_including_archived = self.service.list_customers(
            "tenant-1",
            CustomerFilter(include_archived=True),
            self.actor,
        )
        detail = self.service.get_customer("tenant-1", self.customer.id, self.actor)

        self.assertEqual(len(visible_default), 0)
        self.assertEqual(len(visible_including_archived), 1)
        self.assertEqual(detail.status, "archived")

    def test_bulk_actions_are_audited(self) -> None:
        dry_run = CustomerImportDryRunRequest(
            tenant_id="tenant-1",
            csv_content_base64=_csv_base64([["customer_number", "name"], ["K-2000", "Atlas Objekt GmbH"]]),
        )
        self.ops_service.import_dry_run("tenant-1", dry_run, self.actor)
        export_result = self.ops_service.export_customers(
            "tenant-1",
            CustomerExportRequest(tenant_id="tenant-1"),
            self.actor,
        )

        event_types = [event.event_type for event in self.audit_repo.audit_events]
        self.assertIn("customers.import.dry_run_requested", event_types)
        self.assertIn("customers.export.executed", event_types)
        export_event = next(event for event in self.audit_repo.audit_events if event.event_type == "customers.export.executed")
        self.assertEqual(export_event.entity_id, export_result.job_id)
        self.assertEqual(export_event.metadata_json["document_id"], export_result.document_id)


if __name__ == "__main__":
    unittest.main()
