from __future__ import annotations

import json
import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.errors import ApiException
from app.modules.iam.audit_service import AuditService
from app.modules.planning.planning_record_service import PlanningRecordService
from app.modules.planning.schemas import (
    EventPlanDetailCreate,
    EventPlanDetailUpdate,
    PatrolPlanDetailCreate,
    PatrolPlanDetailUpdate,
    PlanningRecordAttachmentCreate,
    PlanningRecordAttachmentLinkCreate,
    PlanningRecordCreate,
    PlanningRecordFilter,
    PlanningRecordReleaseStateUpdate,
    PlanningRecordUpdate,
    SitePlanDetailCreate,
    SitePlanDetailUpdate,
    TradeFairPlanDetailCreate,
    TradeFairPlanDetailUpdate,
)
from tests.modules.planning.test_customer_orders import FakeCustomerOrderRepository, FakeDocumentRecord, FakeOrderDocumentRepository, FakeOrderDocumentService
from tests.modules.planning.test_ops_master_foundation import RecordingAuditRepository, _context


@dataclass
class FakePlanningRecordRepository(FakeCustomerOrderRepository):
    planning_records: dict[str, object] = field(default_factory=dict)
    event_plan_details: dict[str, object] = field(default_factory=dict)
    site_plan_details: dict[str, object] = field(default_factory=dict)
    trade_fair_plan_details: dict[str, object] = field(default_factory=dict)
    patrol_plan_details: dict[str, object] = field(default_factory=dict)
    user_accounts: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        now = datetime.now(UTC)
        self.user_accounts["dispatcher-1"] = SimpleNamespace(
            id="dispatcher-1",
            tenant_id=self.tenant_id,
            username="dispatcher.one",
            email="dispatcher.one@example.invalid",
            full_name="Dispatcher One",
            status="active",
            archived_at=None,
            created_at=now,
            updated_at=now,
        )

    def get_user_account(self, tenant_id: str, user_id: str):
        row = self.user_accounts.get(user_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def list_dispatcher_candidates(self, tenant_id: str):
        rows = []
        for user in sorted(self.user_accounts.values(), key=lambda row: row.id):
            if user.tenant_id != tenant_id:
                continue
            if getattr(user, "status", "active") != "active":
                continue
            if getattr(user, "archived_at", None) is not None:
                continue
            rows.append(
                SimpleNamespace(
                    id=user.id,
                    tenant_id=user.tenant_id,
                    username=getattr(user, "username", user.id),
                    email=getattr(user, "email", None),
                    full_name=getattr(user, "full_name", user.id),
                    status=user.status,
                    role_keys=["dispatcher"],
                    archived_at=getattr(user, "archived_at", None),
                )
            )
        return rows

    def list_planning_records(self, tenant_id: str, filters: PlanningRecordFilter):
        rows = [row for row in self.planning_records.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.order_id is not None:
            rows = [row for row in rows if row.order_id == filters.order_id]
        if filters.customer_id is not None:
            rows = [row for row in rows if self.orders[row.order_id].customer_id == filters.customer_id]
        if filters.planning_mode_code is not None:
            rows = [row for row in rows if row.planning_mode_code == filters.planning_mode_code]
        if filters.planning_entity_type is not None and filters.planning_entity_id is not None:
            if filters.planning_entity_type == "site":
                rows = [
                    row for row in rows
                    if getattr(self.site_plan_details.get(row.id), "site_id", None) == filters.planning_entity_id
                ]
            elif filters.planning_entity_type == "event_venue":
                rows = [
                    row for row in rows
                    if getattr(self.event_plan_details.get(row.id), "event_venue_id", None) == filters.planning_entity_id
                ]
            elif filters.planning_entity_type == "trade_fair":
                rows = [
                    row for row in rows
                    if getattr(self.trade_fair_plan_details.get(row.id), "trade_fair_id", None) == filters.planning_entity_id
                ]
            elif filters.planning_entity_type == "patrol_route":
                rows = [
                    row for row in rows
                    if getattr(self.patrol_plan_details.get(row.id), "patrol_route_id", None) == filters.planning_entity_id
                ]
        if filters.release_state is not None:
            rows = [row for row in rows if row.release_state == filters.release_state]
        if filters.dispatcher_user_id is not None:
            rows = [row for row in rows if row.dispatcher_user_id == filters.dispatcher_user_id]
        return sorted(rows, key=lambda row: (row.planning_from, row.name))

    def get_planning_record(self, tenant_id: str, planning_record_id: str):
        row = self.planning_records.get(planning_record_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        row.event_detail = self.event_plan_details.get(planning_record_id)
        row.site_detail = self.site_plan_details.get(planning_record_id)
        row.trade_fair_detail = self.trade_fair_plan_details.get(planning_record_id)
        row.patrol_detail = self.patrol_plan_details.get(planning_record_id)
        row.order = self.orders[row.order_id]
        row.parent_planning_record = self.planning_records.get(row.parent_planning_record_id)
        row.child_planning_records = [candidate for candidate in self.planning_records.values() if candidate.parent_planning_record_id == row.id]
        row.dispatcher_user = self.user_accounts.get(row.dispatcher_user_id)
        return row

    def find_planning_record_by_name(self, tenant_id: str, order_id: str, name: str, *, exclude_id: str | None = None):
        for row in self.planning_records.values():
            if row.tenant_id == tenant_id and row.order_id == order_id and row.name == name and row.id != exclude_id:
                return row
        return None

    def create_planning_record(self, tenant_id: str, payload, actor_user_id: str | None):
        row = SimpleNamespace(
            id=str(uuid4()),
            tenant_id=tenant_id,
            order_id=payload.order_id,
            parent_planning_record_id=payload.parent_planning_record_id,
            dispatcher_user_id=payload.dispatcher_user_id,
            planning_mode_code=payload.planning_mode_code,
            name=payload.name,
            planning_from=payload.planning_from,
            planning_to=payload.planning_to,
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
            event_detail=None,
            site_detail=None,
            trade_fair_detail=None,
            patrol_detail=None,
            child_planning_records=[],
        )
        self.planning_records[row.id] = row
        self.orders[row.order_id].planning_records.append(row)
        return row

    def update_planning_record(self, tenant_id: str, planning_record_id: str, payload, actor_user_id: str | None):
        row = self.get_planning_record(tenant_id, planning_record_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.planning_record.stale_version", "errors.planning.planning_record.stale_version")
        if any(
            key in payload.model_dump(exclude_unset=True)
            for key in ("event_detail", "site_detail", "trade_fair_detail", "patrol_detail")
        ):
            raise AttributeError("'dict' object has no attribute '_sa_instance_state'")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_at = datetime.now(UTC)
        row.updated_by_user_id = actor_user_id
        return row

    def save_planning_record(self, row):
        self.planning_records[row.id] = row
        return row

    def create_event_plan_detail(self, tenant_id: str, planning_record_id: str, payload):
        row = SimpleNamespace(
            planning_record_id=planning_record_id,
            tenant_id=tenant_id,
            event_venue_id=payload.event_venue_id,
            setup_note=payload.setup_note,
        )
        self.event_plan_details[planning_record_id] = row
        return row

    def update_event_plan_detail(self, tenant_id: str, planning_record_id: str, payload):
        row = self.get_event_plan_detail(tenant_id, planning_record_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        return row

    def get_event_plan_detail(self, tenant_id: str, planning_record_id: str):
        row = self.event_plan_details.get(planning_record_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_site_plan_detail(self, tenant_id: str, planning_record_id: str, payload):
        row = SimpleNamespace(
            planning_record_id=planning_record_id,
            tenant_id=tenant_id,
            site_id=payload.site_id,
            watchbook_scope_note=payload.watchbook_scope_note,
        )
        self.site_plan_details[planning_record_id] = row
        return row

    def update_site_plan_detail(self, tenant_id: str, planning_record_id: str, payload):
        row = self.get_site_plan_detail(tenant_id, planning_record_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        return row

    def get_site_plan_detail(self, tenant_id: str, planning_record_id: str):
        row = self.site_plan_details.get(planning_record_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_trade_fair_plan_detail(self, tenant_id: str, planning_record_id: str, payload):
        row = SimpleNamespace(
            planning_record_id=planning_record_id,
            tenant_id=tenant_id,
            trade_fair_id=payload.trade_fair_id,
            trade_fair_zone_id=payload.trade_fair_zone_id,
            stand_note=payload.stand_note,
        )
        self.trade_fair_plan_details[planning_record_id] = row
        return row

    def update_trade_fair_plan_detail(self, tenant_id: str, planning_record_id: str, payload):
        row = self.get_trade_fair_plan_detail(tenant_id, planning_record_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        return row

    def get_trade_fair_plan_detail(self, tenant_id: str, planning_record_id: str):
        row = self.trade_fair_plan_details.get(planning_record_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_patrol_plan_detail(self, tenant_id: str, planning_record_id: str, payload):
        row = SimpleNamespace(
            planning_record_id=planning_record_id,
            tenant_id=tenant_id,
            patrol_route_id=payload.patrol_route_id,
            execution_note=payload.execution_note,
        )
        self.patrol_plan_details[planning_record_id] = row
        return row

    def update_patrol_plan_detail(self, tenant_id: str, planning_record_id: str, payload):
        row = self.get_patrol_plan_detail(tenant_id, planning_record_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        return row

    def get_patrol_plan_detail(self, tenant_id: str, planning_record_id: str):
        row = self.patrol_plan_details.get(planning_record_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row


class PlanningRecordServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakePlanningRecordRepository()
        self.audit_repository = RecordingAuditRepository()
        self.document_repository = FakeOrderDocumentRepository()
        self.document_service = FakeOrderDocumentService(self.document_repository)
        self.service = PlanningRecordService(
            self.repository,
            document_repository=self.document_repository,
            document_service=self.document_service,
            audit_service=AuditService(self.audit_repository),
        )
        requirement = self.repository.create_requirement_type(
            "tenant-1",
            type("RequirementPayload", (), {"customer_id": "customer-1", "code": "REQ-1", "label": "Event", "default_planning_mode_code": "event", "description": None})(),
            "user-1",
        )
        event_venue = SimpleNamespace(id="venue-1", tenant_id="tenant-1", customer_id="customer-1")
        site = SimpleNamespace(id="site-1", tenant_id="tenant-1", customer_id="customer-1")
        trade_fair = SimpleNamespace(id="fair-1", tenant_id="tenant-1", customer_id="customer-1")
        trade_fair_zone = SimpleNamespace(id="zone-1", tenant_id="tenant-1", trade_fair_id="fair-1")
        patrol_route = SimpleNamespace(id="route-1", tenant_id="tenant-1", customer_id="customer-1")
        self.repository.event_venues[event_venue.id] = event_venue
        self.repository.sites[site.id] = site
        self.repository.trade_fairs[trade_fair.id] = trade_fair
        self.repository.trade_fair_zones[trade_fair_zone.id] = trade_fair_zone
        self.repository.patrol_routes[patrol_route.id] = patrol_route
        order = self.repository.create_customer_order(
            "tenant-1",
            type(
                "OrderPayload",
                (),
                {
                    "customer_id": "customer-1",
                    "requirement_type_id": requirement.id,
                    "patrol_route_id": None,
                    "order_no": "ORD-17-1",
                    "title": "Messe Berlin",
                    "service_category_code": "event_security",
                    "security_concept_text": None,
                    "service_from": date(2026, 9, 1),
                    "service_to": date(2026, 9, 5),
                    "release_state": "draft",
                    "notes": None,
                },
            )(),
            "user-1",
        )
        self.order_id = order.id
        self.event_venue_id = event_venue.id
        self.site_id = site.id
        self.trade_fair_id = trade_fair.id
        self.trade_fair_zone_id = trade_fair_zone.id
        self.patrol_route_id = patrol_route.id
        self.actor = _context("planning.record.read", "planning.record.write")

    def test_create_event_record_with_matching_detail(self) -> None:
        row = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                dispatcher_user_id="dispatcher-1",
                planning_mode_code="event",
                name="Event-Hauptplan",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 3),
                event_detail=EventPlanDetailCreate(event_venue_id=self.event_venue_id, setup_note="Buehne"),
            ),
            self.actor,
        )
        self.assertEqual(row.planning_mode_code, "event")
        self.assertEqual(row.event_detail.event_venue_id, self.event_venue_id)
        self.assertEqual(len(self.audit_repository.audit_events), 1)
        event = self.audit_repository.audit_events[-1]
        self.assertIsInstance(event.after_json["planning_from"], str)
        self.assertIsInstance(event.after_json["planning_to"], str)
        self.assertIsInstance(event.after_json["created_at"], str)
        self.assertNotIn("event_detail", event.after_json)
        json.dumps(event.after_json)

    def test_unlink_attachment_removes_planning_record_relation_without_deleting_document(self) -> None:
        row = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                dispatcher_user_id="dispatcher-1",
                planning_mode_code="event",
                name="Event-Dokumente",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 3),
                event_detail=EventPlanDetailCreate(event_venue_id=self.event_venue_id, setup_note="Buehne"),
            ),
            self.actor,
        )
        document = self.service.create_planning_record_attachment(
            "tenant-1",
            row.id,
            PlanningRecordAttachmentCreate(
                tenant_id="tenant-1",
                title="Planungsbrief",
                file_name="brief.pdf",
                content_type="application/pdf",
                content_base64="UERG",
            ),
            self.actor,
        )

        self.service.unlink_planning_record_attachment("tenant-1", row.id, document.id, self.actor)

        self.assertEqual(self.service.list_planning_record_attachments("tenant-1", row.id, self.actor), [])
        self.assertIn(document.id, self.document_repository.documents)
        event = self.audit_repository.audit_events[-1]
        self.assertEqual(event.event_type, "planning.planning_record.attachment.unlinked")
        self.assertEqual(event.after_json["document_id"], document.id)

    def test_link_attachment_returns_relation_label_without_overwriting_planning_document_title(self) -> None:
        row = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                dispatcher_user_id="dispatcher-1",
                planning_mode_code="event",
                name="Event-Link-Dokumente",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 3),
                event_detail=EventPlanDetailCreate(event_venue_id=self.event_venue_id, setup_note="Buehne"),
            ),
            self.actor,
        )
        self.document_repository.documents["document-existing"] = FakeDocumentRecord(
            id="document-existing",
            tenant_id="tenant-1",
            title="1663202370369.jpg",
            source_label="camera-upload",
        )

        document = self.service.link_planning_record_attachment(
            "tenant-1",
            row.id,
            PlanningRecordAttachmentLinkCreate(
                tenant_id="tenant-1",
                document_id="document-existing",
                label="Image for test",
            ),
            self.actor,
        )

        self.assertEqual(document.id, "document-existing")
        self.assertEqual(document.title, "1663202370369.jpg")
        self.assertEqual(document.relation_label, "Image for test")
        attachments = self.service.list_planning_record_attachments("tenant-1", row.id, self.actor)
        self.assertEqual(attachments[0].title, "1663202370369.jpg")
        self.assertEqual(attachments[0].relation_label, "Image for test")

    def test_rejects_mismatched_detail_payload(self) -> None:
        with self.assertRaises(ApiException) as captured:
            self.service.create_planning_record(
                "tenant-1",
                PlanningRecordCreate(
                    tenant_id="tenant-1",
                    order_id=self.order_id,
                    planning_mode_code="event",
                    name="Falscher Detailmodus",
                    planning_from=date(2026, 9, 1),
                    planning_to=date(2026, 9, 1),
                    site_detail=SitePlanDetailCreate(site_id=self.site_id),
                ),
                self.actor,
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.planning_record.detail_mismatch")

    def test_rejects_duplicate_name_per_order(self) -> None:
        payload = PlanningRecordCreate(
            tenant_id="tenant-1",
            order_id=self.order_id,
            planning_mode_code="event",
            name="Plan A",
            planning_from=date(2026, 9, 1),
            planning_to=date(2026, 9, 2),
            event_detail=EventPlanDetailCreate(event_venue_id=self.event_venue_id),
        )
        self.service.create_planning_record("tenant-1", payload, self.actor)
        with self.assertRaises(ApiException) as captured:
            self.service.create_planning_record("tenant-1", payload, self.actor)
        self.assertEqual(captured.exception.message_key, "errors.planning.planning_record.duplicate_name")

    def test_rejects_non_event_parent_relationship(self) -> None:
        parent = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                planning_mode_code="event",
                name="Event Parent",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 5),
                event_detail=EventPlanDetailCreate(event_venue_id=self.event_venue_id),
            ),
            self.actor,
        )
        with self.assertRaises(ApiException) as captured:
            self.service.create_planning_record(
                "tenant-1",
                PlanningRecordCreate(
                    tenant_id="tenant-1",
                    order_id=self.order_id,
                    parent_planning_record_id=parent.id,
                    planning_mode_code="site",
                    name="Site Child",
                    planning_from=date(2026, 9, 2),
                    planning_to=date(2026, 9, 3),
                    site_detail=SitePlanDetailCreate(site_id=self.site_id),
                ),
                self.actor,
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.planning_record.parent_not_allowed")

    def test_rejects_parent_window_outside_parent_plan(self) -> None:
        parent = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                planning_mode_code="event",
                name="Event Parent",
                planning_from=date(2026, 9, 2),
                planning_to=date(2026, 9, 3),
                event_detail=EventPlanDetailCreate(event_venue_id=self.event_venue_id),
            ),
            self.actor,
        )
        with self.assertRaises(ApiException) as captured:
            self.service.create_planning_record(
                "tenant-1",
                PlanningRecordCreate(
                    tenant_id="tenant-1",
                    order_id=self.order_id,
                    parent_planning_record_id=parent.id,
                    planning_mode_code="event",
                    name="Event Child",
                    planning_from=date(2026, 9, 1),
                    planning_to=date(2026, 9, 4),
                    event_detail=EventPlanDetailCreate(event_venue_id=self.event_venue_id),
                ),
                self.actor,
            )
        self.assertEqual(captured.exception.message_key, "errors.planning.planning_record.parent_window_mismatch")

    def test_release_state_changes_and_filters_by_dispatcher(self) -> None:
        row = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                dispatcher_user_id="dispatcher-1",
                planning_mode_code="event",
                name="Freigabeplan",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 3),
                event_detail=EventPlanDetailCreate(event_venue_id=self.event_venue_id),
            ),
            self.actor,
        )
        row = self.service.set_planning_record_release_state(
            "tenant-1",
            row.id,
            PlanningRecordReleaseStateUpdate(release_state="release_ready", version_no=row.version_no),
            self.actor,
        )
        filtered = self.service.list_planning_records(
            "tenant-1",
            PlanningRecordFilter(dispatcher_user_id="dispatcher-1", release_state="release_ready"),
            self.actor,
        )
        self.assertEqual(row.release_state, "release_ready")
        self.assertEqual(len(filtered), 1)
        self.assertIsNotNone(filtered[0].created_at)

    def test_filters_planning_records_by_planning_entity(self) -> None:
        matching = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                planning_mode_code="site",
                name="Werk Nord Juli",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 3),
                site_detail=SitePlanDetailCreate(site_id=self.site_id),
            ),
            self.actor,
        )
        self.repository.sites["site-2"] = SimpleNamespace(id="site-2", tenant_id="tenant-1", customer_id="customer-1")
        self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                planning_mode_code="site",
                name="Werk Sued Juli",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 3),
                site_detail=SitePlanDetailCreate(site_id="site-2"),
            ),
            self.actor,
        )

        filtered = self.service.list_planning_records(
            "tenant-1",
            PlanningRecordFilter(
                order_id=self.order_id,
                planning_mode_code="site",
                planning_entity_type="site",
                planning_entity_id=self.site_id,
            ),
            self.actor,
        )

        self.assertEqual([row.id for row in filtered], [matching.id])

    def test_planning_record_filter_ignores_incomplete_planning_entity_filter(self) -> None:
        self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                planning_mode_code="site",
                name="Werk Nord Juli",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 3),
                site_detail=SitePlanDetailCreate(site_id=self.site_id),
            ),
            self.actor,
        )

        with_type_only = self.service.list_planning_records(
            "tenant-1",
            PlanningRecordFilter(order_id=self.order_id, planning_entity_type="site"),
            self.actor,
        )
        with_id_only = self.service.list_planning_records(
            "tenant-1",
            PlanningRecordFilter(order_id=self.order_id, planning_entity_id=self.site_id),
            self.actor,
        )

        self.assertEqual(len(with_type_only), 1)
        self.assertEqual(len(with_id_only), 1)

    def test_update_site_record_persists_scalar_and_site_detail_without_relationship_crash(self) -> None:
        created = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                planning_mode_code="site",
                name="Site Plan",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 2),
                site_detail=SitePlanDetailCreate(site_id=self.site_id, watchbook_scope_note="Alt"),
            ),
            self.actor,
        )
        self.repository.sites["site-2"] = SimpleNamespace(id="site-2", tenant_id="tenant-1", customer_id="customer-1")

        updated = self.service.update_planning_record(
            "tenant-1",
            created.id,
            PlanningRecordUpdate(
                dispatcher_user_id="dispatcher-1",
                name="Site Plan Updated",
                planning_from=date(2026, 9, 2),
                planning_to=date(2026, 9, 3),
                notes="Neue Notiz",
                status="inactive",
                version_no=created.version_no,
                site_detail=SitePlanDetailUpdate(site_id="site-2", watchbook_scope_note="Neu"),
            ),
            self.actor,
        )

        self.assertEqual(updated.name, "Site Plan Updated")
        self.assertEqual(updated.dispatcher_user_id, "dispatcher-1")
        self.assertEqual(updated.status, "inactive")
        self.assertEqual(updated.site_detail.site_id, "site-2")
        self.assertEqual(updated.site_detail.watchbook_scope_note, "Neu")

    def test_update_planning_record_supports_lifecycle_changes(self) -> None:
        created = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                planning_mode_code="event",
                name="Lifecycle Plan",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 2),
                event_detail=EventPlanDetailCreate(event_venue_id=self.event_venue_id),
            ),
            self.actor,
        )

        archived = self.service.update_planning_record(
            "tenant-1",
            created.id,
            PlanningRecordUpdate(
                archived_at=datetime.now(UTC),
                version_no=created.version_no,
            ),
            self.actor,
        )
        archived_row = self.repository.get_planning_record("tenant-1", created.id)
        self.assertIsNotNone(archived_row)
        self.assertIsNotNone(archived_row.archived_at)

        reactivated = self.service.update_planning_record(
            "tenant-1",
            created.id,
            PlanningRecordUpdate(
                status="active",
                archived_at=None,
                version_no=archived.version_no,
            ),
            self.actor,
        )
        self.assertEqual(reactivated.status, "active")
        restored_row = self.repository.get_planning_record("tenant-1", created.id)
        self.assertIsNotNone(restored_row)
        self.assertIsNone(restored_row.archived_at)

    def test_update_event_record_persists_event_detail_without_relationship_crash(self) -> None:
        created = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                planning_mode_code="event",
                name="Event Plan",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 2),
                event_detail=EventPlanDetailCreate(event_venue_id=self.event_venue_id, setup_note="Alt"),
            ),
            self.actor,
        )
        self.repository.event_venues["venue-2"] = SimpleNamespace(id="venue-2", tenant_id="tenant-1", customer_id="customer-1")

        updated = self.service.update_planning_record(
            "tenant-1",
            created.id,
            PlanningRecordUpdate(
                name="Event Plan Updated",
                version_no=created.version_no,
                event_detail=EventPlanDetailUpdate(event_venue_id="venue-2", setup_note="Neu"),
            ),
            self.actor,
        )

        self.assertEqual(updated.name, "Event Plan Updated")
        self.assertEqual(updated.event_detail.event_venue_id, "venue-2")
        self.assertEqual(updated.event_detail.setup_note, "Neu")

    def test_update_trade_fair_record_persists_trade_fair_detail_without_relationship_crash(self) -> None:
        created = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                planning_mode_code="trade_fair",
                name="Fair Plan",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 2),
                trade_fair_detail=TradeFairPlanDetailCreate(
                    trade_fair_id=self.trade_fair_id,
                    trade_fair_zone_id=self.trade_fair_zone_id,
                    stand_note="Alt",
                ),
            ),
            self.actor,
        )
        self.repository.trade_fairs["fair-2"] = SimpleNamespace(id="fair-2", tenant_id="tenant-1", customer_id="customer-1")
        self.repository.trade_fair_zones["zone-2"] = SimpleNamespace(id="zone-2", tenant_id="tenant-1", trade_fair_id="fair-2")

        updated = self.service.update_planning_record(
            "tenant-1",
            created.id,
            PlanningRecordUpdate(
                name="Fair Plan Updated",
                version_no=created.version_no,
                trade_fair_detail=TradeFairPlanDetailUpdate(
                    trade_fair_id="fair-2",
                    trade_fair_zone_id="zone-2",
                    stand_note="Neu",
                ),
            ),
            self.actor,
        )

        self.assertEqual(updated.name, "Fair Plan Updated")
        self.assertEqual(updated.trade_fair_detail.trade_fair_id, "fair-2")
        self.assertEqual(updated.trade_fair_detail.trade_fair_zone_id, "zone-2")
        self.assertEqual(updated.trade_fair_detail.stand_note, "Neu")

    def test_update_patrol_record_persists_patrol_detail_without_relationship_crash(self) -> None:
        created = self.service.create_planning_record(
            "tenant-1",
            PlanningRecordCreate(
                tenant_id="tenant-1",
                order_id=self.order_id,
                planning_mode_code="patrol",
                name="Patrol Plan",
                planning_from=date(2026, 9, 1),
                planning_to=date(2026, 9, 2),
                patrol_detail=PatrolPlanDetailCreate(patrol_route_id=self.patrol_route_id, execution_note="Alt"),
            ),
            self.actor,
        )
        self.repository.patrol_routes["route-2"] = SimpleNamespace(id="route-2", tenant_id="tenant-1", customer_id="customer-1")

        updated = self.service.update_planning_record(
            "tenant-1",
            created.id,
            PlanningRecordUpdate(
                notes="Patrol note",
                version_no=created.version_no,
                patrol_detail=PatrolPlanDetailUpdate(patrol_route_id="route-2", execution_note="Neu"),
            ),
            self.actor,
        )

        self.assertEqual(updated.notes, "Patrol note")
        self.assertEqual(updated.patrol_detail.patrol_route_id, "route-2")
        self.assertEqual(updated.patrol_detail.execution_note, "Neu")

    def test_lists_dispatcher_candidates_with_readable_labels(self) -> None:
        self.repository.user_accounts["dispatcher-2"] = SimpleNamespace(
            id="dispatcher-2",
            tenant_id="tenant-1",
            username="dispatch.two",
            email="dispatch.two@example.com",
            full_name="Dispatch Two",
            status="active",
            archived_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        rows = self.service.list_dispatcher_candidates("tenant-1", self.actor)

        self.assertEqual([row.id for row in rows], ["dispatcher-1", "dispatcher-2"])
        self.assertEqual(rows[1].full_name, "Dispatch Two")
        self.assertEqual(rows[1].email, "dispatch.two@example.com")
        self.assertEqual(rows[1].role_keys, ["dispatcher"])

    def test_dispatcher_candidates_exclude_other_tenant_inactive_and_archived_users(self) -> None:
        now = datetime.now(UTC)
        self.repository.user_accounts["other-tenant"] = SimpleNamespace(
            id="other-tenant",
            tenant_id="tenant-2",
            username="other.tenant",
            email="other@example.com",
            full_name="Other Tenant",
            status="active",
            archived_at=None,
            created_at=now,
            updated_at=now,
        )
        self.repository.user_accounts["inactive-user"] = SimpleNamespace(
            id="inactive-user",
            tenant_id="tenant-1",
            username="inactive.user",
            email="inactive@example.com",
            full_name="Inactive User",
            status="inactive",
            archived_at=None,
            created_at=now,
            updated_at=now,
        )
        self.repository.user_accounts["archived-user"] = SimpleNamespace(
            id="archived-user",
            tenant_id="tenant-1",
            username="archived.user",
            email="archived@example.com",
            full_name="Archived User",
            status="active",
            archived_at=now,
            created_at=now,
            updated_at=now,
        )

        rows = self.service.list_dispatcher_candidates("tenant-1", self.actor)

        self.assertEqual([row.id for row in rows], ["dispatcher-1"])

    def test_current_tenant_admin_is_added_as_dispatcher_candidate_when_valid(self) -> None:
        now = datetime.now(UTC)
        self.repository.user_accounts["user-1"] = SimpleNamespace(
            id="user-1",
            tenant_id="tenant-1",
            username="tenant.admin",
            email="tenant.admin@example.com",
            full_name="Tenant Admin",
            status="active",
            archived_at=None,
            created_at=now,
            updated_at=now,
        )
        original_list_dispatchers = self.repository.list_dispatcher_candidates

        def list_without_actor(tenant_id: str):
            return [row for row in original_list_dispatchers(tenant_id) if row.id != "user-1"]

        self.repository.list_dispatcher_candidates = list_without_actor  # type: ignore[method-assign]

        rows = self.service.list_dispatcher_candidates("tenant-1", self.actor)

        actor_row = next(row for row in rows if row.id == "user-1")
        self.assertEqual(actor_row.full_name, "Tenant Admin")
        self.assertIn("tenant_admin", actor_row.role_keys)

    def test_current_tenant_admin_fallback_skips_inactive_user(self) -> None:
        now = datetime.now(UTC)
        self.repository.user_accounts["user-1"] = SimpleNamespace(
            id="user-1",
            tenant_id="tenant-1",
            username="tenant.admin",
            email="tenant.admin@example.com",
            full_name="Tenant Admin",
            status="inactive",
            archived_at=None,
            created_at=now,
            updated_at=now,
        )

        rows = self.service.list_dispatcher_candidates("tenant-1", self.actor)

        self.assertFalse(any(row.id == "user-1" for row in rows))


if __name__ == "__main__":
    unittest.main()
