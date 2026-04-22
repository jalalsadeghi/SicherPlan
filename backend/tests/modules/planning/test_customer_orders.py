from __future__ import annotations

import json
import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.core.models import LookupValue
from app.modules.customers.models import Customer
from app.modules.iam.audit_service import AuditService
from app.modules.planning.order_service import CustomerOrderService
from app.modules.planning.schemas import (
    CustomerOrderAttachmentCreate,
    CustomerOrderAttachmentLinkCreate,
    CustomerOrderCreate,
    CustomerOrderFilter,
    CustomerOrderReleaseStateUpdate,
    CustomerOrderUpdate,
    OrderEquipmentLineCreate,
    OrderRequirementLineCreate,
    OrderRequirementLineUpdate,
)
from tests.modules.planning.test_ops_master_foundation import FakePlanningRepository, RecordingAuditRepository, _context


@dataclass
class FakeDocumentRecord:
    id: str
    tenant_id: str
    title: str
    document_type_id: str | None = None
    source_module: str | None = None
    source_label: str | None = None
    status: str = "active"
    current_version_no: int = 1
    metadata_json: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None
    version_no: int = 1
    document_type: object | None = None
    versions: list[object] = field(default_factory=list)
    links: list[object] = field(default_factory=list)


class FakeOrderDocumentRepository:
    def __init__(self) -> None:
        self.documents: dict[str, FakeDocumentRecord] = {}
        self.by_owner: dict[tuple[str, str, str], list[str]] = {}

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str):
        return [self.documents[doc_id] for doc_id in self.by_owner.get((tenant_id, owner_type, owner_id), [])]


class FakeOrderDocumentService:
    def __init__(self, repository: FakeOrderDocumentRepository) -> None:
        self.repository = repository

    def create_document(self, tenant_id: str, payload, actor):  # noqa: ANN001
        document_id = str(uuid4())
        record = FakeDocumentRecord(
            id=document_id,
            tenant_id=tenant_id,
            title=payload.title,
            source_module=payload.source_module,
            source_label=payload.source_label,
            metadata_json=payload.metadata_json,
            created_by_user_id=actor.user_id,
            updated_by_user_id=actor.user_id,
        )
        self.repository.documents[document_id] = record
        return SimpleNamespace(id=document_id)

    def add_document_version(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        record = self.repository.documents[document_id]
        record.current_version_no = 1
        record.version_no += 1
        record.updated_at = datetime.now(UTC)
        record.updated_by_user_id = actor.user_id
        record.versions = []
        return SimpleNamespace(document_id=document_id, version_no=record.current_version_no)

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.repository.by_owner.setdefault((tenant_id, payload.owner_type, payload.owner_id), []).append(document_id)
        self.repository.documents[document_id].links.append(
            SimpleNamespace(
                id=str(uuid4()),
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
        )
        return SimpleNamespace(document_id=document_id, owner_id=payload.owner_id)

    def delete_document_link(self, tenant_id: str, document_id: str, owner_type: str, owner_id: str, actor):  # noqa: ANN001
        owner_key = (tenant_id, owner_type, owner_id)
        document_ids = self.repository.by_owner.get(owner_key, [])
        if document_id not in document_ids:
            raise ApiException(404, "docs.document_link.not_found", "errors.docs.document_link.not_found")
        document_ids.remove(document_id)
        self.repository.documents[document_id].links = [
            link
            for link in self.repository.documents[document_id].links
            if not (link.owner_type == owner_type and link.owner_id == owner_id)
        ]


@dataclass
class FakeCustomerOrderRepository(FakePlanningRepository):
    orders: dict[str, object] = field(default_factory=dict)
    order_planning_links: list[dict[str, str]] = field(default_factory=list)
    order_equipment_lines: dict[str, object] = field(default_factory=dict)
    order_requirement_lines: dict[str, object] = field(default_factory=dict)
    function_types: dict[str, object] = field(default_factory=dict)
    qualification_types: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        now = datetime.now(UTC)
        self.function_types["function-1"] = SimpleNamespace(id="function-1", tenant_id=self.tenant_id, code="OBJ", created_at=now, updated_at=now)
        self.function_types["function-2"] = SimpleNamespace(id="function-2", tenant_id=self.tenant_id, code="SUP", created_at=now, updated_at=now)
        self.qualification_types["qualification-1"] = SimpleNamespace(id="qualification-1", tenant_id=self.tenant_id, code="34a", created_at=now, updated_at=now)
        self.qualification_types["qualification-2"] = SimpleNamespace(id="qualification-2", tenant_id=self.tenant_id, code="efa", created_at=now, updated_at=now)

    def get_function_type(self, tenant_id: str, function_type_id: str):
        row = self.function_types.get(function_type_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def get_equipment_item(self, tenant_id: str, row_id: str):
        row = self.equipment_items.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def get_qualification_type(self, tenant_id: str, qualification_type_id: str):
        row = self.qualification_types.get(qualification_type_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def list_customer_orders(self, tenant_id: str, filters: CustomerOrderFilter):
        rows = [row for row in self.orders.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.customer_id:
            rows = [row for row in rows if row.customer_id == filters.customer_id]
        if filters.lifecycle_status:
            rows = [row for row in rows if row.status == filters.lifecycle_status]
        if filters.release_state:
            rows = [row for row in rows if row.release_state == filters.release_state]
        if filters.service_from is not None:
            rows = [row for row in rows if row.service_to >= filters.service_from]
        if filters.service_to is not None:
            rows = [row for row in rows if row.service_from <= filters.service_to]
        if filters.search:
            search_term = filters.search.strip().lower()
            rows = [
                row
                for row in rows
                if search_term in (row.order_no or "").lower() or search_term in (row.title or "").lower()
            ]
        if filters.planning_entity_type and filters.planning_entity_id:
            allowed_order_ids = {
                link["order_id"]
                for link in self.order_planning_links
                if link["tenant_id"] == tenant_id
                and link["planning_entity_type"] == filters.planning_entity_type
                and link["planning_entity_id"] == filters.planning_entity_id
            }
            rows = [row for row in rows if row.id in allowed_order_ids]
        return sorted(rows, key=lambda row: row.order_no)

    def link_order_to_planning_entity(
        self,
        tenant_id: str,
        order_id: str,
        planning_entity_type: str,
        planning_entity_id: str,
    ) -> None:
        self.order_planning_links.append(
            {
                "order_id": order_id,
                "planning_entity_id": planning_entity_id,
                "planning_entity_type": planning_entity_type,
                "tenant_id": tenant_id,
            }
        )

    def get_customer_order(self, tenant_id: str, order_id: str):
        row = self.orders.get(order_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        row.equipment_lines = self.list_order_equipment_lines(tenant_id, order_id)
        row.requirement_lines = self.list_order_requirement_lines(tenant_id, order_id)
        return row

    def find_customer_order_by_no(self, tenant_id: str, order_no: str, *, exclude_id: str | None = None):
        for row in self.orders.values():
            if row.tenant_id == tenant_id and row.order_no == order_no and row.id != exclude_id:
                return row
        return None

    def create_customer_order(self, tenant_id: str, payload, actor_user_id: str | None):
        row = SimpleNamespace(
            id=str(uuid4()),
            tenant_id=tenant_id,
            customer_id=payload.customer_id,
            requirement_type_id=payload.requirement_type_id,
            patrol_route_id=payload.patrol_route_id,
            order_no=payload.order_no,
            title=payload.title,
            service_category_code=payload.service_category_code,
            security_concept_text=payload.security_concept_text,
            service_from=payload.service_from,
            service_to=payload.service_to,
            release_state=payload.release_state,
            released_at=None,
            released_by_user_id=None,
            notes=payload.notes,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
            archived_at=None,
            version_no=1,
            customer=self.customers[payload.customer_id],
            requirement_type=self.requirement_types[payload.requirement_type_id],
            patrol_route=self.patrol_routes.get(payload.patrol_route_id),
            planning_records=[],
        )
        self.orders[row.id] = row
        return row

    def update_customer_order(self, tenant_id: str, order_id: str, payload, actor_user_id: str | None):
        row = self.get_customer_order(tenant_id, order_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.customer_order.stale_version", "errors.planning.customer_order.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        row.version_no += 1
        row.customer = self.customers[row.customer_id]
        row.requirement_type = self.requirement_types[row.requirement_type_id]
        row.patrol_route = self.patrol_routes.get(row.patrol_route_id)
        return row

    def save_customer_order(self, row):
        self.orders[row.id] = row
        return row

    def list_order_equipment_lines(self, tenant_id: str, order_id: str):
        return [row for row in self.order_equipment_lines.values() if row.tenant_id == tenant_id and row.order_id == order_id]

    def get_order_equipment_line(self, tenant_id: str, row_id: str):
        row = self.order_equipment_lines.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_order_equipment_line(self, tenant_id: str, payload, actor_user_id: str | None):
        row = SimpleNamespace(
            id=str(uuid4()),
            tenant_id=tenant_id,
            order_id=payload.order_id,
            equipment_item_id=payload.equipment_item_id,
            required_qty=payload.required_qty,
            notes=payload.notes,
            status="active",
            version_no=1,
            archived_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
            equipment_item=self.equipment_items[payload.equipment_item_id],
        )
        self.order_equipment_lines[row.id] = row
        return row

    def update_order_equipment_line(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_order_equipment_line(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.order_equipment.stale_version", "errors.planning.order_equipment.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def delete_order_equipment_line(self, tenant_id: str, row_id: str) -> bool:
        row = self.get_order_equipment_line(tenant_id, row_id)
        if row is None:
            return False
        del self.order_equipment_lines[row_id]
        return True

    def find_order_equipment_line(self, tenant_id: str, order_id: str, equipment_item_id: str, *, exclude_id: str | None = None):
        for row in self.order_equipment_lines.values():
            if row.tenant_id == tenant_id and row.order_id == order_id and row.equipment_item_id == equipment_item_id and row.id != exclude_id:
                return row
        return None

    def list_order_requirement_lines(self, tenant_id: str, order_id: str):
        return [row for row in self.order_requirement_lines.values() if row.tenant_id == tenant_id and row.order_id == order_id]

    def get_order_requirement_line(self, tenant_id: str, row_id: str):
        row = self.order_requirement_lines.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_order_requirement_line(self, tenant_id: str, payload, actor_user_id: str | None):
        row = SimpleNamespace(
            id=str(uuid4()),
            tenant_id=tenant_id,
            order_id=payload.order_id,
            requirement_type_id=payload.requirement_type_id,
            function_type_id=payload.function_type_id,
            qualification_type_id=payload.qualification_type_id,
            min_qty=payload.min_qty,
            target_qty=payload.target_qty,
            notes=payload.notes,
            status="active",
            version_no=1,
            archived_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
            requirement_type=self.requirement_types[payload.requirement_type_id],
            function_type=self.function_types.get(payload.function_type_id),
            qualification_type=self.qualification_types.get(payload.qualification_type_id),
        )
        self.order_requirement_lines[row.id] = row
        return row

    def update_order_requirement_line(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_order_requirement_line(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.order_requirement_line.stale_version", "errors.planning.order_requirement_line.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        row.requirement_type = self.requirement_types[row.requirement_type_id]
        row.function_type = self.function_types.get(row.function_type_id)
        row.qualification_type = self.qualification_types.get(row.qualification_type_id)
        return row

    def delete_order_requirement_line(self, tenant_id: str, row_id: str) -> bool:
        row = self.get_order_requirement_line(tenant_id, row_id)
        if row is None:
            return False
        del self.order_requirement_lines[row_id]
        return True


class CustomerOrderServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeCustomerOrderRepository()
        self.audit_repository = RecordingAuditRepository()
        self.document_repository = FakeOrderDocumentRepository()
        self.document_service = FakeOrderDocumentService(self.document_repository)
        self.service = CustomerOrderService(
            self.repository,
            document_repository=self.document_repository,
            document_service=self.document_service,
            audit_service=AuditService(self.audit_repository),
        )
        self.repository.lookup_values.extend(
            [
                LookupValue(tenant_id=None, domain="service_category", code="object_security", label="Objektschutz", sort_order=10),
                LookupValue(tenant_id=None, domain="service_category", code="event_security", label="Veranstaltungsschutz", sort_order=20),
                LookupValue(tenant_id=None, domain="service_category", code="trade_fair_security", label="Messebewachung", sort_order=30),
                LookupValue(tenant_id=None, domain="service_category", code="patrol_service", label="Revier- / Patrouillendienst", sort_order=40),
            ]
        )
        equipment = self.repository.create_equipment_item(
            "tenant-1",
            type("EquipmentPayload", (), {"customer_id": None, "code": "EQ-1", "label": "Funkgeraet", "unit_of_measure_code": "piece", "description": None})(),
            "user-1",
        )
        self.equipment_item_id = equipment.id
        requirement = self.repository.create_requirement_type(
            "tenant-1",
            type("RequirementPayload", (), {"customer_id": None, "code": "REQ-1", "label": "Objektschutz", "default_planning_mode_code": "site", "description": None})(),
            "user-1",
        )
        self.requirement_type_id = requirement.id
        self.actor = _context("planning.order.read", "planning.order.write")

    def assert_json_safe(self, value: object) -> None:
        json.dumps(value)

    def test_create_order_rejects_invalid_window(self) -> None:
        with self.assertRaises(ApiException) as captured:
            self.service.create_order(
                "tenant-1",
                CustomerOrderCreate(
                    tenant_id="tenant-1",
                    customer_id="customer-1",
                    requirement_type_id=self.requirement_type_id,
                    order_no="ORD-1",
                    title="Objekt Nord",
                    service_category_code="object_security",
                    service_from=date(2026, 6, 2),
                    service_to=date(2026, 6, 1),
                ),
                self.actor,
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.customer_order.invalid_window")

    def test_create_order_rejects_blank_requirement_type_id(self) -> None:
        with self.assertRaises(ApiException) as captured:
            self.service.create_order(
                "tenant-1",
                CustomerOrderCreate(
                    tenant_id="tenant-1",
                    customer_id="customer-1",
                    requirement_type_id="",
                    order_no="ORD-BLANK-REQ",
                    title="Objekt Nord",
                    service_category_code="object_security",
                    service_from=date(2026, 6, 1),
                    service_to=date(2026, 6, 2),
                ),
                self.actor,
            )
        self.assertEqual(captured.exception.status_code, 400)
        self.assertEqual(captured.exception.message_key, "errors.planning.customer_order.invalid_requirement_type_id")

    def test_create_order_rejects_unknown_service_category_code(self) -> None:
        with self.assertRaises(ApiException) as captured:
            self.service.create_order(
                "tenant-1",
                CustomerOrderCreate(
                    tenant_id="tenant-1",
                    customer_id="customer-1",
                    requirement_type_id=self.requirement_type_id,
                    order_no="ORD-BAD-SERVICE-CATEGORY",
                    title="Objekt Nord",
                    service_category_code="site_security",
                    service_from=date(2026, 6, 1),
                    service_to=date(2026, 6, 2),
                ),
                self.actor,
            )
        self.assertEqual(captured.exception.status_code, 400)
        self.assertEqual(captured.exception.message_key, "errors.planning.customer_order.invalid_service_category_code")

    def test_create_order_allows_blank_optional_patrol_route_id(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                patrol_route_id="",
                order_no="ORD-NO-ROUTE",
                title="Objekt Nord",
                service_category_code="object_security",
                service_from=date(2026, 6, 1),
                service_to=date(2026, 6, 2),
            ),
            self.actor,
        )
        self.assertIsNone(order.patrol_route_id)

    def test_create_order_allows_tenant_scoped_requirement_type_across_customers(self) -> None:
        cross_customer_requirement = self.repository.create_requirement_type(
            "tenant-1",
            type(
                "RequirementPayload",
                (),
                {
                    "customer_id": "customer-2",
                    "code": "REQ-2",
                    "label": "Messeschutz",
                    "default_planning_mode_code": "event",
                    "description": None,
                },
            )(),
            "user-1",
        )

        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=cross_customer_requirement.id,
                order_no="ORD-CROSS-REQ",
                title="Objekt Nord",
                service_category_code="object_security",
                service_from=date(2026, 6, 1),
                service_to=date(2026, 6, 2),
            ),
            self.actor,
        )

        self.assertEqual(order.customer_id, "customer-1")
        self.assertEqual(order.requirement_type_id, cross_customer_requirement.id)

    def test_update_order_allows_unchanged_legacy_service_category_code(self) -> None:
        legacy_order = self.repository.create_customer_order(
            "tenant-1",
            type(
                "OrderPayload",
                (),
                {
                    "customer_id": "customer-1",
                    "requirement_type_id": self.requirement_type_id,
                    "patrol_route_id": None,
                    "order_no": "ORD-LEGACY-SERVICE-CATEGORY",
                    "title": "Objekt Nord",
                    "service_category_code": "site_security",
                    "security_concept_text": None,
                    "service_from": date(2026, 6, 1),
                    "service_to": date(2026, 6, 2),
                    "release_state": "draft",
                    "notes": None,
                },
            )(),
            "user-1",
        )

        updated = self.service.update_order(
            "tenant-1",
            legacy_order.id,
            CustomerOrderUpdate(
                title="Objekt Nord 2",
                version_no=legacy_order.version_no,
            ),
            self.actor,
        )

        self.assertEqual(updated.service_category_code, "site_security")
        self.assertEqual(updated.title, "Objekt Nord 2")

    def test_equipment_line_rejects_duplicate_item(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-2",
                title="Objekt Nord",
                service_category_code="object_security",
                service_from=date(2026, 6, 1),
                service_to=date(2026, 6, 2),
            ),
            self.actor,
        )
        payload = OrderEquipmentLineCreate(
            tenant_id="tenant-1",
            order_id=order.id,
            equipment_item_id=self.equipment_item_id,
            required_qty=2,
        )
        self.service.create_order_equipment_line("tenant-1", order.id, payload, self.actor)
        with self.assertRaises(ApiException) as captured:
            self.service.create_order_equipment_line("tenant-1", order.id, payload, self.actor)
        self.assertEqual(captured.exception.message_key, "errors.planning.order_equipment.duplicate_item")

    def test_create_equipment_line_writes_json_safe_audit_event(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-EQUIP-AUDIT",
                title="Objekt Nord",
                service_category_code="object_security",
                service_from=date(2026, 6, 1),
                service_to=date(2026, 6, 2),
            ),
            self.actor,
        )

        line = self.service.create_order_equipment_line(
            "tenant-1",
            order.id,
            OrderEquipmentLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                equipment_item_id=self.equipment_item_id,
                required_qty=2,
                notes="Funkgeraete",
            ),
            self.actor,
        )

        self.assertEqual(line.required_qty, 2)
        event = self.audit_repository.audit_events[-1]
        self.assertEqual(event.event_type, "planning.order_equipment.created")
        self.assertEqual(event.after_json["equipment_item_id"], self.equipment_item_id)
        self.assertNotIn("equipment_item", event.after_json)
        self.assert_json_safe(event.after_json)

    def test_delete_equipment_line_removes_scope_line_and_audits(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-EQUIP-DELETE",
                title="Objekt Nord",
                service_category_code="object_security",
                service_from=date(2026, 6, 1),
                service_to=date(2026, 6, 2),
            ),
            self.actor,
        )
        line = self.service.create_order_equipment_line(
            "tenant-1",
            order.id,
            OrderEquipmentLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                equipment_item_id=self.equipment_item_id,
                required_qty=2,
            ),
            self.actor,
        )

        self.service.delete_order_equipment_line("tenant-1", order.id, line.id, self.actor)

        self.assertEqual(self.service.list_order_equipment_lines("tenant-1", order.id, self.actor), [])
        event = self.audit_repository.audit_events[-1]
        self.assertEqual(event.event_type, "planning.order_equipment.deleted")
        self.assertEqual(event.before_json["id"], line.id)
        self.assert_json_safe(event.before_json)

    def test_requirement_line_rejects_invalid_qty_window(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-3",
                title="Messe",
                service_category_code="event_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 3),
            ),
            self.actor,
        )
        with self.assertRaises(ApiException) as captured:
            self.service.create_order_requirement_line(
                "tenant-1",
                order.id,
                OrderRequirementLineCreate(
                    tenant_id="tenant-1",
                    order_id=order.id,
                    requirement_type_id=self.requirement_type_id,
                    min_qty=4,
                    target_qty=2,
                ),
                self.actor,
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.order_requirement_line.invalid_qty_window")

    def test_requirement_line_rejects_exact_active_tuple_duplicate(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-REQ-DUP",
                title="Objekt",
                service_category_code="object_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 3),
            ),
            self.actor,
        )

        self.service.create_order_requirement_line(
            "tenant-1",
            order.id,
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                requirement_type_id=self.requirement_type_id,
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=1,
                target_qty=2,
            ),
            self.actor,
        )

        with self.assertRaises(ApiException) as captured:
            self.service.create_order_requirement_line(
                "tenant-1",
                order.id,
                OrderRequirementLineCreate(
                    tenant_id="tenant-1",
                    order_id=order.id,
                    requirement_type_id=self.requirement_type_id,
                    function_type_id="function-1",
                    qualification_type_id="qualification-1",
                    min_qty=2,
                    target_qty=4,
                ),
                self.actor,
            )

        self.assertEqual(captured.exception.status_code, 409)
        self.assertEqual(captured.exception.message_key, "errors.planning.order_requirement_line.duplicate_tuple")

    def test_requirement_line_allows_same_requirement_type_with_different_tuple(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-REQ-TUPLE",
                title="Objekt",
                service_category_code="object_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 3),
            ),
            self.actor,
        )

        self.service.create_order_requirement_line(
            "tenant-1",
            order.id,
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                requirement_type_id=self.requirement_type_id,
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=1,
                target_qty=2,
            ),
            self.actor,
        )

        different_function = self.service.create_order_requirement_line(
            "tenant-1",
            order.id,
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                requirement_type_id=self.requirement_type_id,
                function_type_id="function-2",
                qualification_type_id="qualification-1",
                min_qty=1,
                target_qty=2,
            ),
            self.actor,
        )
        different_qualification = self.service.create_order_requirement_line(
            "tenant-1",
            order.id,
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                requirement_type_id=self.requirement_type_id,
                function_type_id="function-1",
                qualification_type_id="qualification-2",
                min_qty=1,
                target_qty=2,
            ),
            self.actor,
        )

        self.assertEqual(different_function.function_type_id, "function-2")
        self.assertEqual(different_qualification.qualification_type_id, "qualification-2")

    def test_requirement_line_archived_row_does_not_block_same_tuple(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-REQ-ARCHIVE",
                title="Objekt",
                service_category_code="object_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 3),
            ),
            self.actor,
        )

        archived = self.service.create_order_requirement_line(
            "tenant-1",
            order.id,
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                requirement_type_id=self.requirement_type_id,
                function_type_id=None,
                qualification_type_id=None,
                min_qty=1,
                target_qty=2,
            ),
            self.actor,
        )
        self.service.update_order_requirement_line(
            "tenant-1",
            order.id,
            archived.id,
            OrderRequirementLineUpdate(
                status="archived",
                archived_at=datetime.now(UTC),
                version_no=archived.version_no,
            ),
            self.actor,
        )

        created = self.service.create_order_requirement_line(
            "tenant-1",
            order.id,
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                requirement_type_id=self.requirement_type_id,
                function_type_id=None,
                qualification_type_id=None,
                min_qty=2,
                target_qty=3,
            ),
            self.actor,
        )

        self.assertIsNone(created.function_type_id)
        self.assertIsNone(created.qualification_type_id)

    def test_create_requirement_line_writes_json_safe_audit_event(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-REQ-AUDIT",
                title="Messe",
                service_category_code="event_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 3),
            ),
            self.actor,
        )

        line = self.service.create_order_requirement_line(
            "tenant-1",
            order.id,
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                requirement_type_id=self.requirement_type_id,
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=1,
                target_qty=3,
                notes="Objektschutz",
            ),
            self.actor,
        )

        self.assertEqual(line.target_qty, 3)
        event = self.audit_repository.audit_events[-1]
        self.assertEqual(event.event_type, "planning.order_requirement_line.created")
        self.assertEqual(event.after_json["requirement_type_id"], self.requirement_type_id)
        self.assertEqual(event.after_json["function_type_id"], "function-1")
        self.assertEqual(event.after_json["qualification_type_id"], "qualification-1")
        self.assertNotIn("requirement_type", event.after_json)
        self.assertNotIn("function_type", event.after_json)
        self.assertNotIn("qualification_type", event.after_json)
        self.assert_json_safe(event.after_json)

    def test_delete_requirement_line_removes_scope_line_and_audits(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-REQ-DELETE",
                title="Objekt",
                service_category_code="object_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 3),
            ),
            self.actor,
        )
        line = self.service.create_order_requirement_line(
            "tenant-1",
            order.id,
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                requirement_type_id=self.requirement_type_id,
                min_qty=1,
                target_qty=2,
            ),
            self.actor,
        )

        self.service.delete_order_requirement_line("tenant-1", order.id, line.id, self.actor)

        self.assertEqual(self.service.list_order_requirement_lines("tenant-1", order.id, self.actor), [])
        event = self.audit_repository.audit_events[-1]
        self.assertEqual(event.event_type, "planning.order_requirement_line.deleted")
        self.assertEqual(event.before_json["id"], line.id)
        self.assert_json_safe(event.before_json)

    def test_requirement_line_round_trip_supports_optional_function_and_qualification_ids(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-REQ-ROUNDTRIP",
                title="Objekt",
                service_category_code="object_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 3),
            ),
            self.actor,
        )

        created = self.service.create_order_requirement_line(
            "tenant-1",
            order.id,
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                requirement_type_id=self.requirement_type_id,
                function_type_id=None,
                qualification_type_id=None,
                min_qty=1,
                target_qty=2,
                notes="Legacy null compatibility",
            ),
            self.actor,
        )
        self.assertIsNone(created.function_type_id)
        self.assertIsNone(created.qualification_type_id)

        updated = self.service.update_order_requirement_line(
            "tenant-1",
            order.id,
            created.id,
            OrderRequirementLineUpdate(
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=2,
                target_qty=3,
                version_no=created.version_no,
            ),
            self.actor,
        )
        self.assertEqual(updated.function_type_id, "function-1")
        self.assertEqual(updated.qualification_type_id, "qualification-1")

        listed = self.service.list_order_requirement_lines("tenant-1", order.id, self.actor)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].function_type_id, "function-1")
        self.assertEqual(listed[0].qualification_type_id, "qualification-1")

    def test_requirement_line_update_allows_self_same_tuple(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-REQ-SELF",
                title="Objekt",
                service_category_code="object_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 3),
            ),
            self.actor,
        )

        line = self.service.create_order_requirement_line(
            "tenant-1",
            order.id,
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                requirement_type_id=self.requirement_type_id,
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=1,
                target_qty=2,
            ),
            self.actor,
        )

        updated = self.service.update_order_requirement_line(
            "tenant-1",
            order.id,
            line.id,
            OrderRequirementLineUpdate(
                min_qty=2,
                target_qty=3,
                version_no=line.version_no,
            ),
            self.actor,
        )

        self.assertEqual(updated.id, line.id)
        self.assertEqual(updated.function_type_id, "function-1")
        self.assertEqual(updated.qualification_type_id, "qualification-1")

    def test_update_requirement_line_supports_lifecycle_changes(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-REQ-LIFE",
                title="Objekt",
                service_category_code="object_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 3),
            ),
            self.actor,
        )
        line = self.service.create_order_requirement_line(
            "tenant-1",
            order.id,
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id=order.id,
                requirement_type_id=self.requirement_type_id,
                min_qty=1,
                target_qty=2,
            ),
            self.actor,
        )

        archived = self.service.update_order_requirement_line(
            "tenant-1",
            order.id,
            line.id,
            OrderRequirementLineUpdate(
                status="archived",
                archived_at=datetime.now(UTC),
                version_no=line.version_no,
            ),
            self.actor,
        )
        self.assertEqual(archived.status, "archived")
        self.assertIsNotNone(archived.archived_at)

        restored = self.service.update_order_requirement_line(
            "tenant-1",
            order.id,
            line.id,
            OrderRequirementLineUpdate(
                status="active",
                archived_at=None,
                version_no=archived.version_no,
            ),
            self.actor,
        )
        self.assertEqual(restored.status, "active")
        self.assertIsNone(restored.archived_at)

    def test_snapshot_excludes_relationship_objects_and_stays_json_safe(self) -> None:
        requirement_line = self.repository.create_order_requirement_line(
            "tenant-1",
            OrderRequirementLineCreate(
                tenant_id="tenant-1",
                order_id="order-1",
                requirement_type_id=self.requirement_type_id,
                function_type_id="function-1",
                qualification_type_id="qualification-1",
                min_qty=0,
                target_qty=2,
                notes="Snapshot check",
            ),
            "user-1",
        )

        snapshot = self.service._snapshot(requirement_line)

        self.assertEqual(snapshot["requirement_type_id"], self.requirement_type_id)
        self.assertEqual(snapshot["function_type_id"], "function-1")
        self.assertEqual(snapshot["qualification_type_id"], "qualification-1")
        self.assertNotIn("requirement_type", snapshot)
        self.assertNotIn("function_type", snapshot)
        self.assertNotIn("qualification_type", snapshot)
        self.assert_json_safe(snapshot)

    def test_create_attachment_links_document_to_order(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-4",
                title="Route",
                service_category_code="patrol_service",
                service_from=date(2026, 8, 1),
                service_to=date(2026, 8, 1),
            ),
            self.actor,
        )

        document = self.service.create_order_attachment(
            "tenant-1",
            order.id,
            CustomerOrderAttachmentCreate(
                tenant_id="tenant-1",
                title="Sicherheitskonzept",
                file_name="konzept.pdf",
                content_type="application/pdf",
                content_base64="UERG",
            ),
            self.actor,
        )

        attachments = self.service.list_order_attachments("tenant-1", order.id, self.actor)
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].id, document.id)
        self.assertEqual(self.document_repository.by_owner[("tenant-1", "ops.customer_order", order.id)], [document.id])

    def test_link_attachment_returns_relation_label_without_overwriting_document_title(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-DOC-LINK-LABEL",
                title="Route",
                service_category_code="patrol_service",
                service_from=date(2026, 8, 1),
                service_to=date(2026, 8, 1),
            ),
            self.actor,
        )
        self.document_repository.documents["document-existing"] = FakeDocumentRecord(
            id="document-existing",
            tenant_id="tenant-1",
            title="1663202370369.jpg",
        )

        document = self.service.link_order_attachment(
            "tenant-1",
            order.id,
            CustomerOrderAttachmentLinkCreate(
                tenant_id="tenant-1",
                document_id="document-existing",
                label="Bestehendes Dokument",
            ),
            self.actor,
        )

        self.assertEqual(document.id, "document-existing")
        self.assertEqual(document.title, "1663202370369.jpg")
        self.assertEqual(document.relation_label, "Bestehendes Dokument")
        attachments = self.service.list_order_attachments("tenant-1", order.id, self.actor)
        self.assertEqual(attachments[0].title, "1663202370369.jpg")
        self.assertEqual(attachments[0].relation_label, "Bestehendes Dokument")

    def test_unlink_attachment_removes_order_relation_without_deleting_document(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-DOC-UNLINK",
                title="Route",
                service_category_code="patrol_service",
                service_from=date(2026, 8, 1),
                service_to=date(2026, 8, 1),
            ),
            self.actor,
        )
        document = self.service.create_order_attachment(
            "tenant-1",
            order.id,
            CustomerOrderAttachmentCreate(
                tenant_id="tenant-1",
                title="Sicherheitskonzept",
                file_name="konzept.pdf",
                content_type="application/pdf",
                content_base64="UERG",
            ),
            self.actor,
        )

        self.service.unlink_order_attachment("tenant-1", order.id, document.id, self.actor)

        self.assertEqual(self.service.list_order_attachments("tenant-1", order.id, self.actor), [])
        self.assertIn(document.id, self.document_repository.documents)
        event = self.audit_repository.audit_events[-1]
        self.assertEqual(event.event_type, "planning.customer_order.attachment.unlinked")
        self.assertEqual(event.metadata_json["document_id"], document.id)

    def test_release_transition_and_archived_listing_behavior(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-5",
                title="Objekt Sued",
                service_category_code="object_security",
                service_from=date(2026, 9, 1),
                service_to=date(2026, 9, 2),
            ),
            self.actor,
        )

        ready = self.service.set_order_release_state(
            "tenant-1",
            order.id,
            CustomerOrderReleaseStateUpdate(release_state="release_ready", version_no=order.version_no),
            self.actor,
        )
        released = self.service.set_order_release_state(
            "tenant-1",
            order.id,
            CustomerOrderReleaseStateUpdate(release_state="released", version_no=ready.version_no),
            self.actor,
        )
        self.assertEqual(released.release_state, "released")
        self.assertIsNotNone(released.released_at)

        archived = self.service.update_order(
            "tenant-1",
            order.id,
            CustomerOrderUpdate(archived_at=datetime.now(UTC), version_no=released.version_no),
            self.actor,
        )
        active_rows = self.service.list_orders("tenant-1", CustomerOrderFilter(), self.actor)
        archived_rows = self.service.list_orders("tenant-1", CustomerOrderFilter(include_archived=True), self.actor)
        self.assertEqual(active_rows, [])
        self.assertEqual([row.id for row in archived_rows], [archived.id])

    def test_list_orders_with_customer_filter_only_returns_all_customer_orders(self) -> None:
        first = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="A-4002",
                title="Nordtor Juli",
                service_category_code="object_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 31),
            ),
            self.actor,
        )
        second = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="OBJECT_GUARD",
                title="Mai 2026",
                service_category_code="object_security",
                service_from=date(2026, 5, 1),
                service_to=date(2026, 5, 31),
            ),
            self.actor,
        )

        rows = self.service.list_orders("tenant-1", CustomerOrderFilter(customer_id="customer-1"), self.actor)

        self.assertEqual([row.id for row in rows], [first.id, second.id])

    def test_customer_order_filter_rejects_invalid_planning_entity_type(self) -> None:
        with self.assertRaises(ValueError):
            CustomerOrderFilter(planning_entity_type="branch", planning_entity_id="site-1")

    def test_customer_order_filter_ignores_incomplete_planning_entity_filter(self) -> None:
        first = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="A-4100",
                title="Scoped candidate",
                service_category_code="object_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 31),
            ),
            self.actor,
        )
        second = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="A-4101",
                title="Fallback candidate",
                service_category_code="object_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 31),
            ),
            self.actor,
        )
        self.repository.link_order_to_planning_entity("tenant-1", first.id, "site", "site-nord")

        type_only_rows = self.service.list_orders(
            "tenant-1",
            CustomerOrderFilter(customer_id="customer-1", planning_entity_type="site"),
            self.actor,
        )
        id_only_rows = self.service.list_orders(
            "tenant-1",
            CustomerOrderFilter(customer_id="customer-1", planning_entity_id="site-nord"),
            self.actor,
        )

        self.assertEqual([row.id for row in type_only_rows], [first.id, second.id])
        self.assertEqual([row.id for row in id_only_rows], [first.id, second.id])

    def test_list_orders_filters_site_related_orders_only_and_deduplicates(self) -> None:
        related = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="A-4002",
                title="Nordtor Juli",
                service_category_code="object_security",
                service_from=date(2026, 7, 1),
                service_to=date(2026, 7, 31),
            ),
            self.actor,
        )
        unrelated = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="OBJECT_GUARD",
                title="Mai 2026",
                service_category_code="object_security",
                service_from=date(2026, 5, 1),
                service_to=date(2026, 5, 31),
            ),
            self.actor,
        )
        self.repository.link_order_to_planning_entity("tenant-1", related.id, "site", "site-nord")
        self.repository.link_order_to_planning_entity("tenant-1", related.id, "site", "site-nord")
        self.repository.link_order_to_planning_entity("tenant-1", unrelated.id, "site", "site-sued")

        rows = self.service.list_orders(
            "tenant-1",
            CustomerOrderFilter(customer_id="customer-1", planning_entity_type="site", planning_entity_id="site-nord"),
            self.actor,
        )

        self.assertEqual([row.id for row in rows], [related.id])

    def test_list_orders_filters_event_venue_related_orders_only(self) -> None:
        related = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="EV-1",
                title="Arena Sommer",
                service_category_code="event_security",
                service_from=date(2026, 8, 1),
                service_to=date(2026, 8, 2),
            ),
            self.actor,
        )
        self.repository.link_order_to_planning_entity("tenant-1", related.id, "event_venue", "venue-1")

        rows = self.service.list_orders(
            "tenant-1",
            CustomerOrderFilter(customer_id="customer-1", planning_entity_type="event_venue", planning_entity_id="venue-1"),
            self.actor,
        )

        self.assertEqual([row.id for row in rows], [related.id])

    def test_list_orders_filters_trade_fair_related_orders_only(self) -> None:
        related = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="FAIR-1",
                title="Expo Halle 2",
                service_category_code="trade_fair_security",
                service_from=date(2026, 9, 10),
                service_to=date(2026, 9, 12),
            ),
            self.actor,
        )
        self.repository.link_order_to_planning_entity("tenant-1", related.id, "trade_fair", "fair-1")

        rows = self.service.list_orders(
            "tenant-1",
            CustomerOrderFilter(customer_id="customer-1", planning_entity_type="trade_fair", planning_entity_id="fair-1"),
            self.actor,
        )

        self.assertEqual([row.id for row in rows], [related.id])

    def test_list_orders_filters_patrol_route_related_orders_only(self) -> None:
        related = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="PATROL-1",
                title="Innenstadt Nacht",
                service_category_code="patrol_service",
                service_from=date(2026, 10, 1),
                service_to=date(2026, 10, 1),
            ),
            self.actor,
        )
        self.repository.link_order_to_planning_entity("tenant-1", related.id, "patrol_route", "route-1")

        rows = self.service.list_orders(
            "tenant-1",
            CustomerOrderFilter(customer_id="customer-1", planning_entity_type="patrol_route", planning_entity_id="route-1"),
            self.actor,
        )

        self.assertEqual([row.id for row in rows], [related.id])

    def test_list_orders_planning_entity_filter_enforces_tenant_isolation(self) -> None:
        tenant_two_customer = Customer(
            id="customer-tenant-2",
            tenant_id="tenant-2",
            customer_number="K-900",
            name="Other Tenant",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.repository.customers[tenant_two_customer.id] = tenant_two_customer
        tenant_two_requirement = self.repository.create_requirement_type(
            "tenant-2",
            type("RequirementPayload", (), {"customer_id": None, "code": "REQ-T2", "label": "Objektschutz", "default_planning_mode_code": "site", "description": None})(),
            "user-1",
        )
        tenant_two_actor = _context("planning.order.read", "planning.order.write", tenant_id="tenant-2")
        tenant_two_order = self.service.create_order(
            "tenant-2",
            CustomerOrderCreate(
                tenant_id="tenant-2",
                customer_id=tenant_two_customer.id,
                requirement_type_id=tenant_two_requirement.id,
                order_no="T2-1",
                title="Cross tenant",
                service_category_code="object_security",
                service_from=date(2026, 11, 1),
                service_to=date(2026, 11, 2),
            ),
            tenant_two_actor,
        )
        self.repository.link_order_to_planning_entity("tenant-2", tenant_two_order.id, "site", "site-nord")

        rows = self.service.list_orders(
            "tenant-1",
            CustomerOrderFilter(customer_id="customer-1", planning_entity_type="site", planning_entity_id="site-nord"),
            self.actor,
        )

        self.assertEqual(rows, [])

    def test_list_orders_combines_planning_entity_with_search_date_and_release_filters(self) -> None:
        matching = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="A-5001",
                title="Nordtor August",
                service_category_code="object_security",
                service_from=date(2026, 8, 1),
                service_to=date(2026, 8, 31),
                release_state="release_ready",
            ),
            self.actor,
        )
        wrong_state = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="A-5002",
                title="Nordtor Draft",
                service_category_code="object_security",
                service_from=date(2026, 8, 1),
                service_to=date(2026, 8, 31),
                release_state="draft",
            ),
            self.actor,
        )
        wrong_window = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="A-5003",
                title="Nordtor September",
                service_category_code="object_security",
                service_from=date(2026, 9, 1),
                service_to=date(2026, 9, 30),
                release_state="release_ready",
            ),
            self.actor,
        )
        for order in (matching, wrong_state, wrong_window):
            self.repository.link_order_to_planning_entity("tenant-1", order.id, "site", "site-nord")

        rows = self.service.list_orders(
            "tenant-1",
            CustomerOrderFilter(
                customer_id="customer-1",
                planning_entity_type="site",
                planning_entity_id="site-nord",
                release_state="release_ready",
                search="Nordtor",
                service_from=date(2026, 8, 15),
                service_to=date(2026, 8, 20),
            ),
            self.actor,
        )

        self.assertEqual([row.id for row in rows], [matching.id])
