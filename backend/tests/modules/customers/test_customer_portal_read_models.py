from __future__ import annotations

import unittest

from app.modules.customers.portal_read_service import CustomerPortalReadService
from app.modules.customers.portal_service import CustomerPortalService
from app.modules.customers.schemas import CustomerContactCreate, CustomerCreate
from app.modules.customers.service import CustomerService
from tests.modules.customers.test_customer_backbone import PORTAL_USER_ID, FakeCustomerRepository
from tests.modules.customers.test_customer_portal_context import _internal_actor, _portal_actor


class TestCustomerPortalReadModels(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeCustomerRepository()
        self.customer_service = CustomerService(self.repository)
        self.portal_service = CustomerPortalService(self.repository)
        self.read_service = CustomerPortalReadService()
        self.customer = self.customer_service.create_customer(
            "tenant-1",
            CustomerCreate(tenant_id="tenant-1", customer_number="K-2000", name="Portal Kunde GmbH"),
            _internal_actor(),
        )
        self.customer_service.create_contact(
            "tenant-1",
            self.customer.id,
            CustomerContactCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                full_name="Riley Portal",
                email="portal@example.invalid",
                user_id=PORTAL_USER_ID,
                is_primary_contact=True,
            ),
            _internal_actor(),
        )
        self.context = self.portal_service.get_context(_portal_actor(customer_id=self.customer.id))

    def test_orders_contract_is_customer_scoped_and_released_only(self) -> None:
        response = self.read_service.list_orders(self.context)

        self.assertEqual(response.customer_id, self.customer.id)
        self.assertEqual(response.items, [])
        self.assertEqual(response.source.domain_key, "orders")
        self.assertEqual(response.source.source_module_key, "planning")
        self.assertEqual(response.source.availability_status, "pending_source_module")
        self.assertTrue(response.source.customer_scoped)
        self.assertTrue(response.source.released_only)
        self.assertFalse(response.source.docs_backed_outputs)

    def test_timesheets_and_reports_stay_docs_backed_even_when_empty(self) -> None:
        timesheets = self.read_service.list_timesheets(self.context)
        reports = self.read_service.list_report_packages(self.context)

        self.assertEqual(timesheets.items, [])
        self.assertEqual(reports.items, [])
        self.assertTrue(timesheets.source.docs_backed_outputs)
        self.assertTrue(reports.source.docs_backed_outputs)
        self.assertEqual(timesheets.source.source_module_key, "finance")
        self.assertEqual(reports.source.source_module_key, "reporting")

    def test_all_collections_share_stable_pending_contracts(self) -> None:
        collections = (
            self.read_service.list_orders(self.context),
            self.read_service.list_schedules(self.context),
            self.read_service.list_watchbook_entries(self.context),
            self.read_service.list_timesheets(self.context),
            self.read_service.list_report_packages(self.context),
        )

        for collection in collections:
            self.assertEqual(collection.customer_id, self.customer.id)
            self.assertEqual(collection.source.availability_status, "pending_source_module")
            self.assertTrue(collection.source.customer_scoped)
            self.assertTrue(collection.source.released_only)
            self.assertTrue(collection.source.message_key.startswith("portalCustomer.datasets."))


if __name__ == "__main__":
    unittest.main()
