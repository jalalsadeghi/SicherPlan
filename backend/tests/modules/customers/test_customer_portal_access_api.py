from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import UTC, datetime

from app.errors import ApiException
from app.modules.customers.portal_access_service import CustomerPortalAccessService
from app.modules.customers.portal_service import CustomerPortalService
from app.modules.customers.schemas import (
    CustomerPortalAccessCreate,
    CustomerPortalAccessPasswordResetRequest,
    CustomerPortalAccessStatusUpdate,
)
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext


@dataclass
class FakeCustomer:
    id: str
    tenant_id: str
    customer_number: str
    name: str
    status: str = "active"
    archived_at: datetime | None = None


@dataclass
class FakeContact:
    id: str
    tenant_id: str
    customer_id: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    function_label: str | None = None
    status: str = "active"
    archived_at: datetime | None = None
    user_id: str | None = None
    updated_by_user_id: str | None = None
    version_no: int = 1


@dataclass
class FakeUser:
    id: str
    tenant_id: str
    username: str
    email: str
    full_name: str
    locale: str
    timezone: str
    status: str
    password_hash: str
    is_password_login_enabled: bool = True
    last_login_at: datetime | None = None
    created_at: datetime = datetime(2026, 1, 1, tzinfo=UTC)
    updated_at: datetime = datetime(2026, 1, 1, tzinfo=UTC)
    archived_at: datetime | None = None
    version_no: int = 1
    revoked_sessions: int = 0
    used_reset_tokens: int = 0


@dataclass
class FakeAssignment:
    id: str
    tenant_id: str
    user_id: str
    role_key: str
    scope_type: str
    customer_id: str
    status: str
    archived_at: datetime | None = None
    version_no: int = 1


class FakeCustomerPortalAccessRepository:
    def __init__(self) -> None:
        self.tenants = {"tenant-1", "tenant-2"}
        self.customers = {
            "customer-1": FakeCustomer("customer-1", "tenant-1", "K-1000", "Nord Security GmbH"),
            "customer-2": FakeCustomer("customer-2", "tenant-1", "K-1001", "Atlas Objekt GmbH"),
            "customer-3": FakeCustomer("customer-3", "tenant-1", "K-1002", "Inactive GmbH", status="inactive"),
            "customer-4": FakeCustomer("customer-4", "tenant-2", "K-2000", "Tenant Two"),
        }
        self.contacts = {
            "contact-1": FakeContact("contact-1", "tenant-1", "customer-1", "Alex Kunde", email="alex@example.invalid"),
            "contact-2": FakeContact("contact-2", "tenant-1", "customer-2", "Other Kunde", email="other@example.invalid"),
            "contact-3": FakeContact(
                "contact-3",
                "tenant-1",
                "customer-1",
                "Inactive Contact",
                email="inactive@example.invalid",
                status="inactive",
            ),
            "contact-5": FakeContact("contact-5", "tenant-1", "customer-3", "Inactive Customer Contact", email="inactive-customer@example.invalid"),
            "contact-4": FakeContact("contact-4", "tenant-2", "customer-4", "Tenant Two Contact", email="t2@example.invalid"),
        }
        self.users: dict[str, FakeUser] = {}
        self.assignments: dict[str, FakeAssignment] = {}
        self._user_seq = 0
        self._assignment_seq = 0

    def tenant_exists(self, tenant_id: str) -> bool:
        return tenant_id in self.tenants

    def get_customer(self, tenant_id: str, customer_id: str) -> FakeCustomer | None:
        customer = self.customers.get(customer_id)
        if customer is None or customer.tenant_id != tenant_id:
            return None
        return customer

    def get_contact(self, tenant_id: str, contact_id: str) -> FakeContact | None:
        contact = self.contacts.get(contact_id)
        if contact is None or contact.tenant_id != tenant_id:
            return None
        return contact

    def list_portal_access(self, tenant_id: str, customer_id: str):
        return [
            self._item_for(contact, self.users[contact.user_id], self._assignment_for(contact.user_id, customer_id))
            for contact in self.contacts.values()
            if contact.tenant_id == tenant_id and contact.customer_id == customer_id and contact.user_id
            and self._assignment_for(contact.user_id, customer_id) is not None
        ]

    def get_portal_access_user(self, tenant_id: str, customer_id: str, user_id: str):
        user = self.users.get(user_id)
        if user is None or user.tenant_id != tenant_id:
            return None
        contact = next(
            (
                row for row in self.contacts.values()
                if row.tenant_id == tenant_id and row.customer_id == customer_id and row.user_id == user_id
            ),
            None,
        )
        assignment = self._assignment_for(user_id, customer_id)
        if contact is None or assignment is None:
            return None
        return self._item_for(contact, user, assignment)

    def create_portal_access_user(self, payload: CustomerPortalAccessCreate, password_hash: str, actor_user_id: str | None):
        if any(user.tenant_id == payload.tenant_id and user.username == payload.username for user in self.users.values()):
            raise ApiException(409, "customers.portal_access.duplicate_username", "errors.iam.user.duplicate_username")
        if any(user.tenant_id == payload.tenant_id and user.email == payload.email for user in self.users.values()):
            raise ApiException(409, "customers.portal_access.duplicate_email", "errors.iam.user.duplicate_email")
        contact = self.contacts[payload.contact_id]
        if contact.user_id:
            raise ApiException(409, "customers.portal_access.contact_already_linked", "errors.customers.portal_access.contact_already_linked")
        self._user_seq += 1
        user_id = f"user-{self._user_seq}"
        self._assignment_seq += 1
        assignment_id = f"assignment-{self._assignment_seq}"
        user = FakeUser(
            id=user_id,
            tenant_id=payload.tenant_id,
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            locale=payload.locale,
            timezone=payload.timezone,
            status=payload.status,
            password_hash=password_hash,
            updated_at=datetime.now(UTC),
        )
        assignment = FakeAssignment(
            id=assignment_id,
            tenant_id=payload.tenant_id,
            user_id=user_id,
            role_key="customer_user",
            scope_type="customer",
            customer_id=payload.customer_id,
            status=payload.status,
        )
        self.users[user_id] = user
        self.assignments[assignment_id] = assignment
        contact.user_id = user_id
        contact.updated_by_user_id = actor_user_id
        contact.version_no += 1
        return self._item_for(contact, user, assignment)

    def update_portal_access_status(self, tenant_id: str, customer_id: str, user_id: str, status: str, actor_user_id: str | None):
        item = self.get_portal_access_user(tenant_id, customer_id, user_id)
        if item is None:
            return None
        user = self.users[user_id]
        assignment = self._assignment_for(user_id, customer_id)
        assert assignment is not None
        user.status = status
        user.updated_at = datetime.now(UTC)
        user.version_no += 1
        assignment.status = status
        assignment.archived_at = None
        assignment.version_no += 1
        if status == "inactive":
            user.revoked_sessions += 1
            user.used_reset_tokens += 1
        return self._item_for(self.contacts[item.contact_id], user, assignment)

    def reset_portal_access_password(self, tenant_id: str, customer_id: str, user_id: str, password_hash: str, actor_user_id: str | None, at_time: datetime):
        item = self.get_portal_access_user(tenant_id, customer_id, user_id)
        if item is None:
            return None
        user = self.users[user_id]
        user.password_hash = password_hash
        user.updated_at = at_time
        user.version_no += 1
        user.revoked_sessions += 1
        user.used_reset_tokens += 1
        assignment = self._assignment_for(user_id, customer_id)
        assert assignment is not None
        return self._item_for(self.contacts[item.contact_id], user, assignment)

    def unlink_portal_access(self, tenant_id: str, customer_id: str, user_id: str, actor_user_id: str | None, at_time: datetime | None = None):
        item = self.get_portal_access_user(tenant_id, customer_id, user_id)
        if item is None:
            return False
        event_time = at_time or datetime.now(UTC)
        user = self.users[user_id]
        assignment = self._assignment_for(user_id, customer_id)
        contact = self.contacts[item.contact_id]
        assert assignment is not None
        contact.user_id = None
        contact.updated_by_user_id = actor_user_id
        contact.version_no += 1
        user.status = "inactive"
        user.updated_at = event_time
        user.version_no += 1
        user.revoked_sessions += 1
        user.used_reset_tokens += 1
        assignment.status = "inactive"
        assignment.archived_at = event_time
        assignment.version_no += 1
        return True

    def get_portal_contact_for_user(self, tenant_id: str, user_id: str):
        contact = next(
            (row for row in self.contacts.values() if row.tenant_id == tenant_id and row.user_id == user_id),
            None,
        )
        if contact is None:
            return None
        customer = self.customers.get(contact.customer_id)
        if customer is None:
            return None
        return customer, contact

    def get_portal_customer_scope_match(self, tenant_id: str, user_id: str, allowed_customer_ids: list[str]):
        contact = next(
            (
                row for row in self.contacts.values()
                if row.tenant_id == tenant_id and row.user_id == user_id and row.customer_id in allowed_customer_ids
            ),
            None,
        )
        if contact is None:
            return None
        assignment = self._assignment_for(user_id, contact.customer_id)
        if assignment is None or assignment.status != "active":
            return None
        customer = self.customers.get(contact.customer_id)
        if customer is None:
            return None
        return customer, contact

    def _assignment_for(self, user_id: str, customer_id: str) -> FakeAssignment | None:
        return next(
            (
                row for row in self.assignments.values()
                if row.user_id == user_id
                and row.customer_id == customer_id
                and row.role_key == "customer_user"
                and row.scope_type == "customer"
            ),
            None,
        )

    @staticmethod
    def _item_for(contact: FakeContact, user: FakeUser, assignment: FakeAssignment):
        from app.modules.customers.schemas import CustomerPortalAccessListItemRead

        return CustomerPortalAccessListItemRead(
            user_id=user.id,
            contact_id=contact.id,
            contact_name=contact.full_name,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            locale=user.locale,
            role_key=assignment.role_key,
            status=user.status,
            role_assignment_status=assignment.status,
            is_password_login_enabled=user.is_password_login_enabled,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


def _tenant_admin_actor(
    *,
    tenant_id: str = "tenant-1",
    permissions: tuple[str, ...] = (
        "customers.portal_access.read",
        "customers.portal_access.write",
        "customers.customer.read",
        "customers.customer.write",
    ),
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-admin",
        user_id="user-admin",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-admin",
    )


def _portal_actor(user_id: str, customer_id: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-customer",
        user_id=user_id,
        tenant_id="tenant-1",
        role_keys=frozenset({"customer_user"}),
        permission_keys=frozenset({"portal.customer.access"}),
        scopes=(AuthenticatedRoleScope(role_key="customer_user", scope_type="customer", customer_id=customer_id),),
        request_id="req-customer",
    )


class TestCustomerPortalAccessService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeCustomerPortalAccessRepository()
        self.service = CustomerPortalAccessService(self.repository)
        self.portal_service = CustomerPortalService(self.repository)
        self.actor = _tenant_admin_actor()

    def test_create_portal_user_success(self) -> None:
        result = self.service.create_portal_access(
            "tenant-1",
            "customer-1",
            CustomerPortalAccessCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                contact_id="contact-1",
                username="alex.portal",
                email="alex.portal@example.invalid",
                full_name="Alex Portal",
                locale="de",
            ),
            self.actor,
        )

        self.assertTrue(result.temporary_password)
        linked_contact = self.repository.contacts["contact-1"]
        self.assertIsNotNone(linked_contact.user_id)
        user = self.repository.users[linked_contact.user_id]
        assignment = self.repository._assignment_for(user.id, "customer-1")
        self.assertEqual(user.username, "alex.portal")
        self.assertEqual(assignment.role_key if assignment else None, "customer_user")
        self.assertEqual(assignment.scope_type if assignment else None, "customer")

    def test_duplicate_username_is_rejected(self) -> None:
        self.service.create_portal_access(
            "tenant-1",
            "customer-1",
            CustomerPortalAccessCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                contact_id="contact-1",
                username="duplicate-user",
                email="first@example.invalid",
                full_name="First User",
            ),
            self.actor,
        )
        self.repository.contacts["contact-1"].user_id = None

        with self.assertRaises(ApiException) as raised:
            self.service.create_portal_access(
                "tenant-1",
                "customer-1",
                CustomerPortalAccessCreate(
                    tenant_id="tenant-1",
                    customer_id="customer-1",
                    contact_id="contact-1",
                    username="duplicate-user",
                    email="second@example.invalid",
                    full_name="Second User",
                ),
                self.actor,
            )

        self.assertEqual(raised.exception.message_key, "errors.iam.user.duplicate_username")

    def test_duplicate_email_is_rejected(self) -> None:
        self.service.create_portal_access(
            "tenant-1",
            "customer-1",
            CustomerPortalAccessCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                contact_id="contact-1",
                username="first-user",
                email="duplicate@example.invalid",
                full_name="First User",
            ),
            self.actor,
        )
        self.repository.contacts["contact-1"].user_id = None

        with self.assertRaises(ApiException) as raised:
            self.service.create_portal_access(
                "tenant-1",
                "customer-1",
                CustomerPortalAccessCreate(
                    tenant_id="tenant-1",
                    customer_id="customer-1",
                    contact_id="contact-1",
                    username="second-user",
                    email="duplicate@example.invalid",
                    full_name="Second User",
                ),
                self.actor,
            )

        self.assertEqual(raised.exception.message_key, "errors.iam.user.duplicate_email")

    def test_customer_tenant_mismatch_is_rejected(self) -> None:
        with self.assertRaises(ApiException) as raised:
            self.service.create_portal_access(
                "tenant-1",
                "customer-1",
                CustomerPortalAccessCreate(
                    tenant_id="tenant-2",
                    customer_id="customer-1",
                    contact_id="contact-1",
                    username="alex.portal",
                    email="alex.portal@example.invalid",
                    full_name="Alex Portal",
                ),
                self.actor,
            )

        self.assertEqual(raised.exception.message_key, "errors.customers.contact.tenant_mismatch")

    def test_contact_not_under_selected_customer_is_rejected(self) -> None:
        with self.assertRaises(ApiException) as raised:
            self.service.create_portal_access(
                "tenant-1",
                "customer-1",
                CustomerPortalAccessCreate(
                    tenant_id="tenant-1",
                    customer_id="customer-1",
                    contact_id="contact-2",
                    username="alex.portal",
                    email="alex.portal@example.invalid",
                    full_name="Alex Portal",
                ),
                self.actor,
            )

        self.assertEqual(raised.exception.message_key, "errors.customers.portal_access.contact_customer_mismatch")

    def test_inactive_customer_is_rejected(self) -> None:
        with self.assertRaises(ApiException) as raised:
            self.service.create_portal_access(
                "tenant-1",
                "customer-3",
                CustomerPortalAccessCreate(
                    tenant_id="tenant-1",
                    customer_id="customer-3",
                    contact_id="contact-5",
                    username="alex.portal",
                    email="alex.portal@example.invalid",
                    full_name="Alex Portal",
                ),
                self.actor,
            )

        self.assertEqual(raised.exception.message_key, "errors.customers.portal.customer_inactive")

    def test_inactive_contact_is_rejected(self) -> None:
        with self.assertRaises(ApiException) as raised:
            self.service.create_portal_access(
                "tenant-1",
                "customer-1",
                CustomerPortalAccessCreate(
                    tenant_id="tenant-1",
                    customer_id="customer-1",
                    contact_id="contact-3",
                    username="alex.portal",
                    email="alex.portal@example.invalid",
                    full_name="Alex Portal",
                ),
                self.actor,
            )

        self.assertEqual(raised.exception.message_key, "errors.customers.portal.contact_inactive")

    def test_password_reset_revokes_sessions(self) -> None:
        self.service.create_portal_access(
            "tenant-1",
            "customer-1",
            CustomerPortalAccessCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                contact_id="contact-1",
                username="alex.portal",
                email="alex.portal@example.invalid",
                full_name="Alex Portal",
            ),
            self.actor,
        )
        user_id = self.repository.contacts["contact-1"].user_id
        assert user_id is not None

        result = self.service.reset_portal_access_password(
            "tenant-1",
            "customer-1",
            user_id,
            CustomerPortalAccessPasswordResetRequest(),
            self.actor,
        )

        self.assertTrue(result.temporary_password)
        self.assertEqual(self.repository.users[user_id].revoked_sessions, 1)
        self.assertEqual(self.repository.users[user_id].used_reset_tokens, 1)

    def test_status_update_deactivates_account_and_assignment(self) -> None:
        self.service.create_portal_access(
            "tenant-1",
            "customer-1",
            CustomerPortalAccessCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                contact_id="contact-1",
                username="alex.portal",
                email="alex.portal@example.invalid",
                full_name="Alex Portal",
            ),
            self.actor,
        )
        user_id = self.repository.contacts["contact-1"].user_id
        assert user_id is not None

        updated = self.service.update_portal_access_status(
            "tenant-1",
            "customer-1",
            user_id,
            CustomerPortalAccessStatusUpdate(status="inactive"),
            self.actor,
        )

        self.assertEqual(updated.status, "inactive")
        self.assertEqual(updated.role_assignment_status, "inactive")
        self.assertEqual(self.repository.users[user_id].revoked_sessions, 1)

    def test_unlink_removes_contact_link_and_deactivates_access(self) -> None:
        self.service.create_portal_access(
            "tenant-1",
            "customer-1",
            CustomerPortalAccessCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                contact_id="contact-1",
                username="alex.portal",
                email="alex.portal@example.invalid",
                full_name="Alex Portal",
            ),
            self.actor,
        )
        user_id = self.repository.contacts["contact-1"].user_id
        assert user_id is not None

        result = self.service.unlink_portal_access("tenant-1", "customer-1", user_id, self.actor)

        self.assertEqual(result.message_key, "messages.customers.portal_access.unlinked")
        self.assertIsNone(self.repository.contacts["contact-1"].user_id)
        self.assertEqual(self.repository.users[user_id].status, "inactive")
        assignment = self.repository._assignment_for(user_id, "customer-1")
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.status if assignment else None, "inactive")

    def test_portal_access_resolution_works_after_provisioning(self) -> None:
        self.service.create_portal_access(
            "tenant-1",
            "customer-1",
            CustomerPortalAccessCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                contact_id="contact-1",
                username="alex.portal",
                email="alex.portal@example.invalid",
                full_name="Alex Portal",
            ),
            self.actor,
        )
        user_id = self.repository.contacts["contact-1"].user_id
        assert user_id is not None

        context = self.portal_service.get_context(_portal_actor(user_id, "customer-1"))

        self.assertEqual(context.customer_id, "customer-1")
        self.assertEqual(context.contact_id, "contact-1")


if __name__ == "__main__":
    unittest.main()
