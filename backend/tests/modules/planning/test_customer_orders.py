from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.iam.audit_service import AuditService
from app.modules.planning.order_service import CustomerOrderService
from app.modules.planning.schemas import (
    CustomerOrderAttachmentCreate,
    CustomerOrderCreate,
    CustomerOrderFilter,
    CustomerOrderReleaseStateUpdate,
    CustomerOrderUpdate,
    OrderEquipmentLineCreate,
    OrderRequirementLineCreate,
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
        return SimpleNamespace(document_id=document_id, owner_id=payload.owner_id)


@dataclass
class FakeCustomerOrderRepository(FakePlanningRepository):
    orders: dict[str, object] = field(default_factory=dict)
    order_equipment_lines: dict[str, object] = field(default_factory=dict)
    order_requirement_lines: dict[str, object] = field(default_factory=dict)
    function_types: dict[str, object] = field(default_factory=dict)
    qualification_types: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        now = datetime.now(UTC)
        self.function_types["function-1"] = SimpleNamespace(id="function-1", tenant_id=self.tenant_id, code="OBJ", created_at=now, updated_at=now)
        self.qualification_types["qualification-1"] = SimpleNamespace(id="qualification-1", tenant_id=self.tenant_id, code="34a", created_at=now, updated_at=now)

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
        if filters.release_state:
            rows = [row for row in rows if row.release_state == filters.release_state]
        return sorted(rows, key=lambda row: row.order_no)

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
        equipment = self.repository.create_equipment_item(
            "tenant-1",
            type("EquipmentPayload", (), {"customer_id": "customer-1", "code": "EQ-1", "label": "Funkgeraet", "unit_of_measure_code": "piece", "description": None})(),
            "user-1",
        )
        self.equipment_item_id = equipment.id
        requirement = self.repository.create_requirement_type(
            "tenant-1",
            type("RequirementPayload", (), {"customer_id": "customer-1", "code": "REQ-1", "label": "Objektschutz", "default_planning_mode_code": "site", "description": None})(),
            "user-1",
        )
        self.requirement_type_id = requirement.id
        self.actor = _context("planning.order.read", "planning.order.write")

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
                    service_category_code="site_security",
                    service_from=date(2026, 6, 2),
                    service_to=date(2026, 6, 1),
                ),
                self.actor,
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.customer_order.invalid_window")

    def test_equipment_line_rejects_duplicate_item(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-2",
                title="Objekt Nord",
                service_category_code="site_security",
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

    def test_create_attachment_links_document_to_order(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-4",
                title="Route",
                service_category_code="patrol",
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

    def test_release_transition_and_archived_listing_behavior(self) -> None:
        order = self.service.create_order(
            "tenant-1",
            CustomerOrderCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                requirement_type_id=self.requirement_type_id,
                order_no="ORD-5",
                title="Objekt Sued",
                service_category_code="site_security",
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
