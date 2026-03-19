from __future__ import annotations

import unittest

from app.errors import ApiException
from app.modules.customers.portal_service import CustomerPortalService
from app.modules.customers.schemas import CustomerContactCreate, CustomerCreate, CustomerUpdate
from app.modules.customers.service import CustomerService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from tests.modules.customers.test_customer_backbone import FakeCustomerRepository


def _internal_actor() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-admin",
        user_id="user-admin",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"customers.customer.read", "customers.customer.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-admin",
    )


def _portal_actor(
    *,
    user_id: str = "user-portal",
    customer_id: str,
    permission_keys: tuple[str, ...] = ("portal.customer.access",),
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-customer",
        user_id=user_id,
        tenant_id="tenant-1",
        role_keys=frozenset({"customer_user"}),
        permission_keys=frozenset(permission_keys),
        scopes=(AuthenticatedRoleScope(role_key="customer_user", scope_type="customer", customer_id=customer_id),),
        request_id="req-customer",
    )


class TestCustomerPortalContext(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeCustomerRepository()
        self.customer_service = CustomerService(self.repository)
        self.portal_service = CustomerPortalService(self.repository)
        self.customer = self.customer_service.create_customer(
            "tenant-1",
            CustomerCreate(tenant_id="tenant-1", customer_number="K-1000", name="Nord Security GmbH"),
            _internal_actor(),
        )
        self.contact = self.customer_service.create_contact(
            "tenant-1",
            self.customer.id,
            CustomerContactCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                full_name="Alex Kunde",
                email="alex@example.invalid",
                user_id="user-portal",
                is_primary_contact=True,
            ),
            _internal_actor(),
        )

    def test_portal_context_resolves_customer_from_scope_and_linkage(self) -> None:
        context = self.portal_service.get_context(_portal_actor(customer_id=self.customer.id))

        self.assertEqual(context.customer_id, self.customer.id)
        self.assertEqual(context.contact_id, self.contact.id)
        self.assertEqual(context.customer.customer_number, "K-1000")
        self.assertEqual(context.contact.full_name, "Alex Kunde")
        self.assertEqual(context.scopes[0].customer_id, self.customer.id)

    def test_missing_customer_scope_is_rejected(self) -> None:
        actor = RequestAuthorizationContext(
            session_id="session-customer",
            user_id="user-portal",
            tenant_id="tenant-1",
            role_keys=frozenset({"customer_user"}),
            permission_keys=frozenset({"portal.customer.access"}),
            scopes=(AuthenticatedRoleScope(role_key="customer_user", scope_type="tenant"),),
            request_id="req-customer",
        )

        with self.assertRaises(ApiException) as raised:
            self.portal_service.get_context(actor)

        self.assertEqual(raised.exception.code, "customers.portal.scope_not_resolved")

    def test_missing_contact_link_is_rejected(self) -> None:
        with self.assertRaises(ApiException) as raised:
            self.portal_service.get_context(_portal_actor(user_id="user-unlinked", customer_id=self.customer.id))

        self.assertEqual(raised.exception.code, "customers.portal.contact_not_linked")

    def test_cross_customer_scope_mismatch_is_rejected(self) -> None:
        with self.assertRaises(ApiException) as raised:
            self.portal_service.get_context(_portal_actor(customer_id="customer-2"))

        self.assertEqual(raised.exception.code, "customers.portal.scope_not_resolved")

    def test_inactive_customer_is_rejected(self) -> None:
        self.customer_service.update_customer(
            "tenant-1",
            self.customer.id,
            CustomerUpdate(status="inactive", version_no=self.customer.version_no),
            _internal_actor(),
        )

        with self.assertRaises(ApiException) as raised:
            self.portal_service.get_context(_portal_actor(customer_id=self.customer.id))

        self.assertEqual(raised.exception.code, "customers.portal.customer_inactive")


if __name__ == "__main__":
    unittest.main()
