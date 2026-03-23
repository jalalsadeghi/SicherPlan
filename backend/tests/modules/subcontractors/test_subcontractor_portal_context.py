from __future__ import annotations

import unittest

from app.errors import ApiException
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.subcontractors.portal_service import SubcontractorPortalService
from app.modules.subcontractors.schemas import (
    SubcontractorContactCreate,
    SubcontractorContactUpdate,
    SubcontractorCreate,
    SubcontractorUpdate,
)
from app.modules.subcontractors.service import SubcontractorService
from tests.modules.subcontractors.test_subcontractor_master import FakeSubcontractorRepository


def _internal_actor() -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-admin",
        user_id="user-admin",
        tenant_id="tenant-1",
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"subcontractors.company.read", "subcontractors.company.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-admin",
    )


def _portal_actor(
    *,
    user_id: str = "user-portal",
    subcontractor_id: str,
    permission_keys: tuple[str, ...] = ("portal.subcontractor.access",),
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-subcontractor",
        user_id=user_id,
        tenant_id="tenant-1",
        role_keys=frozenset({"subcontractor_user"}),
        permission_keys=frozenset(permission_keys),
        scopes=(
            AuthenticatedRoleScope(
                role_key="subcontractor_user",
                scope_type="subcontractor",
                subcontractor_id=subcontractor_id,
            ),
        ),
        request_id="req-subcontractor",
    )


class TestSubcontractorPortalContext(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeSubcontractorRepository()
        self.service = SubcontractorService(self.repository)
        self.portal_service = SubcontractorPortalService(self.repository)
        self.subcontractor = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(
                tenant_id="tenant-1",
                subcontractor_number="SU-1000",
                legal_name="Partnerwache GmbH",
            ),
            _internal_actor(),
        )
        self.contact = self.service.create_contact(
            "tenant-1",
            self.subcontractor.id,
            SubcontractorContactCreate(
                tenant_id="tenant-1",
                subcontractor_id=self.subcontractor.id,
                full_name="Pat Portal",
                email="portal.partner@example.invalid",
                user_id="user-portal",
                portal_enabled=True,
                is_primary_contact=True,
            ),
            _internal_actor(),
        )

    def test_portal_context_resolves_subcontractor_from_scope_and_linkage(self) -> None:
        context = self.portal_service.get_context(_portal_actor(subcontractor_id=self.subcontractor.id))

        self.assertEqual(context.subcontractor_id, self.subcontractor.id)
        self.assertEqual(context.contact_id, self.contact.id)
        self.assertEqual(context.company.subcontractor_number, "SU-1000")
        self.assertEqual(context.contact.full_name, "Pat Portal")
        self.assertEqual(context.scopes[0].subcontractor_id, self.subcontractor.id)

    def test_missing_subcontractor_scope_is_rejected(self) -> None:
        actor = RequestAuthorizationContext(
            session_id="session-subcontractor",
            user_id="user-portal",
            tenant_id="tenant-1",
            role_keys=frozenset({"subcontractor_user"}),
            permission_keys=frozenset({"portal.subcontractor.access"}),
            scopes=(AuthenticatedRoleScope(role_key="subcontractor_user", scope_type="tenant"),),
            request_id="req-subcontractor",
        )

        with self.assertRaises(ApiException) as raised:
            self.portal_service.get_context(actor)

        self.assertEqual(raised.exception.code, "subcontractors.portal.scope_not_resolved")

    def test_missing_contact_link_is_rejected(self) -> None:
        with self.assertRaises(ApiException) as raised:
            self.portal_service.get_context(
                _portal_actor(user_id="user-unlinked", subcontractor_id=self.subcontractor.id)
            )

        self.assertEqual(raised.exception.code, "subcontractors.portal.contact_not_linked")

    def test_portal_disabled_contact_is_rejected(self) -> None:
        self.contact = self.service.update_contact(
            "tenant-1",
            self.subcontractor.id,
            self.contact.id,
            SubcontractorContactUpdate(portal_enabled=False, version_no=self.contact.version_no),
            _internal_actor(),
        )

        with self.assertRaises(ApiException) as raised:
            self.portal_service.get_context(_portal_actor(subcontractor_id=self.subcontractor.id))

        self.assertEqual(raised.exception.code, "subcontractors.portal.contact_portal_disabled")

    def test_inactive_subcontractor_is_rejected(self) -> None:
        self.service.update_subcontractor(
            "tenant-1",
            self.subcontractor.id,
            SubcontractorUpdate(status="inactive", version_no=self.subcontractor.version_no),
            _internal_actor(),
        )

        with self.assertRaises(ApiException) as raised:
            self.portal_service.get_context(_portal_actor(subcontractor_id=self.subcontractor.id))

        self.assertEqual(raised.exception.code, "subcontractors.portal.company_inactive")


if __name__ == "__main__":
    unittest.main()
