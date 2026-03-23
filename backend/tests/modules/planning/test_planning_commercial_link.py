from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace

from app.errors import ApiException
from app.modules.iam.audit_service import AuditService
from app.modules.planning.commercial_link_service import PlanningCommercialLinkService
from app.modules.planning.models import CustomerOrder, PlanningRecord
from app.modules.planning.order_service import CustomerOrderService
from app.modules.planning.planning_record_service import PlanningRecordService
from app.modules.planning.schemas import (
    CustomerOrderCreate,
    CustomerOrderReleaseStateUpdate,
    EventPlanDetailCreate,
    PlanningRecordCreate,
    PlanningRecordReleaseStateUpdate,
)
from tests.modules.planning.test_customer_orders import (
    FakeCustomerOrderRepository,
    FakeOrderDocumentRepository,
    FakeOrderDocumentService,
)
from tests.modules.planning.test_ops_master_foundation import RecordingAuditRepository, _context
from tests.modules.planning.test_planning_records import FakePlanningRecordRepository


@dataclass
class FakePlanningCommercialRepository(FakePlanningRecordRepository):
    billing_profiles: dict[str, object] = field(default_factory=dict)
    invoice_parties: dict[str, list[object]] = field(default_factory=dict)
    rate_cards: dict[str, list[object]] = field(default_factory=dict)

    def get_customer_billing_profile(self, tenant_id: str, customer_id: str):
        row = self.billing_profiles.get(customer_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def list_customer_invoice_parties(self, tenant_id: str, customer_id: str):
        return [
            row
            for row in self.invoice_parties.get(customer_id, [])
            if row.tenant_id == tenant_id
        ]

    def list_customer_rate_cards(self, tenant_id: str, customer_id: str):
        return [
            row
            for row in self.rate_cards.get(customer_id, [])
            if row.tenant_id == tenant_id
        ]


class PlanningCommercialLinkServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakePlanningCommercialRepository()
        self.commercial_link_service = PlanningCommercialLinkService(self.repository)
        self.audit_repository = RecordingAuditRepository()
        self.document_repository = FakeOrderDocumentRepository()
        self.document_service = FakeOrderDocumentService(self.document_repository)
        self.order_service = CustomerOrderService(
            self.repository,
            document_repository=self.document_repository,
            document_service=self.document_service,
            commercial_link_service=self.commercial_link_service,
            audit_service=AuditService(self.audit_repository),
        )
        self.planning_record_service = PlanningRecordService(
            self.repository,
            document_repository=self.document_repository,
            commercial_link_service=self.commercial_link_service,
            audit_service=AuditService(self.audit_repository),
        )
        self.actor = _context("planning.order.read", "planning.order.write", "planning.record.read", "planning.record.write")
        requirement = self.repository.create_requirement_type(
            "tenant-1",
            type("RequirementPayload", (), {"customer_id": "customer-1", "code": "REQ-COM", "label": "Objekt", "default_planning_mode_code": "event", "description": None})(),
            "user-1",
        )
        self.repository.event_venues["venue-1"] = SimpleNamespace(id="venue-1", tenant_id="tenant-1", customer_id="customer-1")
        self.order = self.order_service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=requirement.id,
                order_no="ORD-COM-1",
                title="Commercial linkage order",
                service_category_code="site_security",
                service_from=date(2026, 10, 1),
                service_to=date(2026, 10, 3),
            ),
            self.actor,
        )
        self.planning_record = self.planning_record_service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order.id,
                planning_mode_code="event",
                name="Commercial plan",
                planning_from=date(2026, 10, 1),
                planning_to=date(2026, 10, 2),
                event_detail=EventPlanDetailCreate(event_venue_id="venue-1"),
            ),
            self.actor,
        )

    def seed_commercial_truth(self) -> None:
        now = datetime.now(UTC)
        self.repository.billing_profiles["customer-1"] = SimpleNamespace(
            id="billing-1",
            tenant_id="tenant-1",
            customer_id="customer-1",
            shipping_method_code="email_pdf",
            invoice_layout_code="standard_pdf",
            dunning_policy_code="standard",
            e_invoice_enabled=False,
            archived_at=None,
            status="active",
            created_at=now,
            updated_at=now,
        )
        self.repository.invoice_parties["customer-1"] = [
            SimpleNamespace(
                id="party-1",
                tenant_id="tenant-1",
                customer_id="customer-1",
                is_default=True,
                archived_at=None,
                status="active",
            )
        ]
        self.repository.rate_cards["customer-1"] = [
            SimpleNamespace(
                id="rate-1",
                tenant_id="tenant-1",
                customer_id="customer-1",
                effective_from=date(2026, 1, 1),
                effective_to=None,
                archived_at=None,
                status="active",
            )
        ]

    def test_commercial_link_reads_crm_truth_without_copying_fields(self) -> None:
        self.seed_commercial_truth()
        link = self.commercial_link_service.get_order_commercial_link("tenant-1", self.order.id, self.actor)
        self.assertTrue(link.is_release_ready)
        self.assertEqual(link.billing_profile_id, "billing-1")
        self.assertEqual(link.default_invoice_party_id, "party-1")
        self.assertEqual(link.rate_card_ids, ["rate-1"])

    def test_order_release_blocks_when_billing_profile_missing(self) -> None:
        ready = self.order_service.set_order_release_state(
            "tenant-1",
            self.order.id,
            CustomerOrderReleaseStateUpdate(release_state="release_ready", version_no=self.order.version_no),
            self.actor,
        )
        with self.assertRaises(ApiException) as captured:
            self.order_service.set_order_release_state(
                "tenant-1",
                self.order.id,
                CustomerOrderReleaseStateUpdate(release_state="released", version_no=ready.version_no),
                self.actor,
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.commercial_link.prerequisites_missing")
        self.assertIn("missing_billing_profile", captured.exception.details["blocking_codes"])

    def test_planning_release_blocks_when_default_invoice_party_missing(self) -> None:
        now = datetime.now(UTC)
        self.repository.billing_profiles["customer-1"] = SimpleNamespace(
            id="billing-1",
            tenant_id="tenant-1",
            customer_id="customer-1",
            shipping_method_code="email_pdf",
            invoice_layout_code="standard_pdf",
            dunning_policy_code="standard",
            e_invoice_enabled=False,
            archived_at=None,
            status="active",
            created_at=now,
            updated_at=now,
        )
        ready = self.planning_record_service.set_planning_record_release_state(
            "tenant-1",
            self.planning_record.id,
            PlanningRecordReleaseStateUpdate(release_state="release_ready", version_no=self.planning_record.version_no),
            self.actor,
        )
        with self.assertRaises(ApiException) as captured:
            self.planning_record_service.set_planning_record_release_state(
                "tenant-1",
                self.planning_record.id,
                PlanningRecordReleaseStateUpdate(release_state="released", version_no=ready.version_no),
                self.actor,
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.commercial_link.prerequisites_missing")
        self.assertIn("missing_default_invoice_party", captured.exception.details["blocking_codes"])

    def test_planning_tables_do_not_duplicate_commercial_truth_columns(self) -> None:
        order_columns = set(CustomerOrder.__table__.columns.keys())
        planning_columns = set(PlanningRecord.__table__.columns.keys())
        self.assertNotIn("invoice_layout_code", order_columns)
        self.assertNotIn("shipping_method_code", order_columns)
        self.assertNotIn("billing_profile_id", order_columns)
        self.assertNotIn("invoice_layout_code", planning_columns)
        self.assertNotIn("shipping_method_code", planning_columns)
        self.assertNotIn("billing_profile_id", planning_columns)


if __name__ == "__main__":
    unittest.main()
