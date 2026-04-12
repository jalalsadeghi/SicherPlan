from __future__ import annotations

import json
import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint

from app.db import Base
from app.errors import ApiException
from app.modules.core.models import Address
from app.modules.customers.models import Customer
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.models import EquipmentItem, EventVenue, PatrolCheckpoint, PatrolRoute, RequirementType, Site, TradeFair, TradeFairZone
from app.modules.planning.schemas import (
    EquipmentItemCreate,
    EquipmentItemUpdate,
    OpsMasterFilter,
    PatrolCheckpointCreate,
    PatrolRouteCreate,
    RequirementTypeCreate,
    RequirementTypeUpdate,
    SiteCreate,
    TradeFairCreate,
    TradeFairZoneCreate,
)
from app.modules.planning.service import PlanningService


def _context(*permissions: str, tenant_id: str = "tenant-1") -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset(permissions),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-1",
    )


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.audit_events: list[object] = []

    def create_login_event(self, payload):  # noqa: ANN001
        return payload

    def create_audit_event(self, payload):  # noqa: ANN001
        self.audit_events.append(payload)
        return payload


@dataclass
class FakePlanningRepository:
    tenant_id: str = "tenant-1"
    customers: dict[str, Customer] = field(default_factory=dict)
    addresses: dict[str, Address] = field(default_factory=dict)
    requirement_types: dict[str, RequirementType] = field(default_factory=dict)
    equipment_items: dict[str, EquipmentItem] = field(default_factory=dict)
    sites: dict[str, Site] = field(default_factory=dict)
    event_venues: dict[str, EventVenue] = field(default_factory=dict)
    trade_fairs: dict[str, TradeFair] = field(default_factory=dict)
    patrol_routes: dict[str, PatrolRoute] = field(default_factory=dict)
    trade_fair_zones: dict[str, object] = field(default_factory=dict)
    patrol_checkpoints: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        now = datetime.now(UTC)
        self.customers["customer-1"] = Customer(
            id="customer-1",
            tenant_id=self.tenant_id,
            customer_number="K-001",
            name="ACME",
            created_at=now,
            updated_at=now,
            version_no=1,
            status="active",
        )
        self.customers["customer-2"] = Customer(
            id="customer-2",
            tenant_id=self.tenant_id,
            customer_number="K-002",
            name="Globex",
            created_at=now,
            updated_at=now,
            version_no=1,
            status="active",
        )
        self.addresses["address-1"] = Address(
            id="address-1",
            street_line_1="Testweg 1",
            street_line_2=None,
            postal_code="10115",
            city="Berlin",
            state=None,
            country_code="DE",
        )

    @staticmethod
    def _stamp(row) -> None:  # noqa: ANN001
        now = datetime.now(UTC)
        if getattr(row, "id", None) is None:
            row.id = str(uuid4())
        if getattr(row, "created_at", None) is None:
            row.created_at = now
        row.updated_at = now
        row.version_no = getattr(row, "version_no", 0) or 1
        row.status = getattr(row, "status", None) or "active"

    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None:
        row = self.customers.get(customer_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def get_address(self, address_id: str) -> Address | None:
        return self.addresses.get(address_id)

    def list_requirement_types(self, tenant_id: str, filters: OpsMasterFilter) -> list[RequirementType]:
        rows = [row for row in self.requirement_types.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        return sorted(rows, key=lambda row: row.code)

    def get_requirement_type(self, tenant_id: str, row_id: str) -> RequirementType | None:
        row = self.requirement_types.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_requirement_type(self, tenant_id: str, payload: RequirementTypeCreate, actor_user_id: str | None) -> RequirementType:
        row = RequirementType(
            tenant_id=tenant_id,
            customer_id=payload.customer_id,
            code=payload.code,
            label=payload.label,
            default_planning_mode_code=payload.default_planning_mode_code,
            description=getattr(payload, "notes", getattr(payload, "description", None)),
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.requirement_types[row.id] = row
        return row

    def update_requirement_type(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.get_requirement_type(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.requirement_type.stale_version", "errors.planning.requirement_type.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_by_user_id = actor_user_id
        row.updated_at = datetime.now(UTC)
        return row

    def find_requirement_type_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> RequirementType | None:
        for row in self.requirement_types.values():
            if row.tenant_id == tenant_id and row.code == code and row.id != exclude_id:
                return row
        return None

    def list_equipment_items(self, tenant_id: str, filters: OpsMasterFilter) -> list[EquipmentItem]:
        rows = [row for row in self.equipment_items.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        return sorted(rows, key=lambda row: row.code)

    def get_equipment_item(self, tenant_id: str, row_id: str) -> EquipmentItem | None:
        row = self.equipment_items.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_equipment_item(self, tenant_id: str, payload: EquipmentItemCreate, actor_user_id: str | None) -> EquipmentItem:
        row = EquipmentItem(
            tenant_id=tenant_id,
            customer_id=payload.customer_id,
            code=payload.code,
            label=payload.label,
            unit_of_measure_code=payload.unit_of_measure_code,
            description=payload.description,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.equipment_items[row.id] = row
        return row

    def update_equipment_item(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None) -> EquipmentItem | None:
        row = self.get_equipment_item(tenant_id, row_id)
        if row is None:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.equipment_item.stale_version", "errors.planning.equipment_item.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_by_user_id = actor_user_id
        row.updated_at = datetime.now(UTC)
        return row

    def find_equipment_item_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None):
        for row in self.equipment_items.values():
            if row.tenant_id == tenant_id and row.code == code and row.id != exclude_id:
                return row
        return None

    def list_sites(self, tenant_id: str, filters: OpsMasterFilter) -> list[Site]:
        rows = [row for row in self.sites.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        return sorted(rows, key=lambda row: row.site_no)

    def get_site(self, tenant_id: str, row_id: str) -> Site | None:
        row = self.sites.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_site(self, tenant_id: str, payload: SiteCreate, actor_user_id: str | None) -> Site:
        row = Site(
            tenant_id=tenant_id,
            customer_id=payload.customer_id,
            site_no=payload.site_no,
            name=payload.name,
            address_id=payload.address_id,
            timezone=payload.timezone,
            latitude=payload.latitude,
            longitude=payload.longitude,
            watchbook_enabled=payload.watchbook_enabled,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        row.address = self.addresses.get(row.address_id)
        self.sites[row.id] = row
        return row

    def update_site(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        return None

    def find_site_by_no(self, tenant_id: str, site_no: str, *, exclude_id: str | None = None) -> Site | None:
        for row in self.sites.values():
            if row.tenant_id == tenant_id and row.site_no == site_no and row.id != exclude_id:
                return row
        return None

    def list_event_venues(self, tenant_id: str, filters: OpsMasterFilter) -> list[EventVenue]:
        return list(self.event_venues.values())

    def get_event_venue(self, tenant_id: str, row_id: str) -> EventVenue | None:
        row = self.event_venues.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_event_venue(self, tenant_id: str, payload, actor_user_id: str | None) -> EventVenue:
        row = EventVenue(
            tenant_id=tenant_id,
            customer_id=payload.customer_id,
            venue_no=payload.venue_no,
            name=payload.name,
            address_id=payload.address_id,
            timezone=payload.timezone,
            latitude=payload.latitude,
            longitude=payload.longitude,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.event_venues[row.id] = row
        return row

    def update_event_venue(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        return None

    def find_event_venue_by_no(self, tenant_id: str, venue_no: str, *, exclude_id: str | None = None) -> EventVenue | None:
        for row in self.event_venues.values():
            if row.tenant_id == tenant_id and row.venue_no == venue_no and row.id != exclude_id:
                return row
        return None

    def list_trade_fairs(self, tenant_id: str, filters: OpsMasterFilter) -> list[TradeFair]:
        return list(self.trade_fairs.values())

    def get_trade_fair(self, tenant_id: str, row_id: str) -> TradeFair | None:
        row = self.trade_fairs.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_trade_fair(self, tenant_id: str, payload: TradeFairCreate, actor_user_id: str | None) -> TradeFair:
        row = TradeFair(
            tenant_id=tenant_id,
            customer_id=payload.customer_id,
            venue_id=payload.venue_id,
            fair_no=payload.fair_no,
            name=payload.name,
            address_id=payload.address_id,
            timezone=payload.timezone,
            latitude=payload.latitude,
            longitude=payload.longitude,
            start_date=payload.start_date,
            end_date=payload.end_date,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        row.zones = []
        self.trade_fairs[row.id] = row
        return row

    def update_trade_fair(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        return None

    def find_trade_fair_by_no(self, tenant_id: str, fair_no: str, *, exclude_id: str | None = None) -> TradeFair | None:
        for row in self.trade_fairs.values():
            if row.tenant_id == tenant_id and row.fair_no == fair_no and row.id != exclude_id:
                return row
        return None

    def create_trade_fair_zone(self, tenant_id: str, payload: TradeFairZoneCreate, actor_user_id: str | None):
        row = TradeFairZone(
            tenant_id=tenant_id,
            trade_fair_id=payload.trade_fair_id,
            zone_type_code=payload.zone_type_code,
            zone_code=payload.zone_code,
            label=payload.label,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        row.trade_fair = self.trade_fairs[payload.trade_fair_id]
        self.trade_fair_zones[row.id] = row
        return row

    def update_trade_fair_zone(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.trade_fair_zones.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.trade_fair_zone.stale_version", "errors.planning.trade_fair_zone.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_by_user_id = actor_user_id
        return row

    def get_trade_fair_zone(self, tenant_id: str, row_id: str):
        row = self.trade_fair_zones.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def list_trade_fair_zones(self, tenant_id: str, trade_fair_id: str):
        return sorted(
            [row for row in self.trade_fair_zones.values() if row.tenant_id == tenant_id and row.trade_fair_id == trade_fair_id],
            key=lambda row: row.zone_code,
        )

    def find_trade_fair_zone(self, tenant_id: str, trade_fair_id: str, zone_type_code: str, zone_code: str, *, exclude_id: str | None = None):
        for row in self.trade_fair_zones.values():
            if (
                row.tenant_id == tenant_id
                and row.trade_fair_id == trade_fair_id
                and row.zone_type_code == zone_type_code
                and row.zone_code == zone_code
                and row.id != exclude_id
            ):
                return row
        return None

    def list_patrol_routes(self, tenant_id: str, filters: OpsMasterFilter) -> list[PatrolRoute]:
        return list(self.patrol_routes.values())

    def get_patrol_route(self, tenant_id: str, row_id: str) -> PatrolRoute | None:
        row = self.patrol_routes.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_patrol_route(self, tenant_id: str, payload: PatrolRouteCreate, actor_user_id: str | None) -> PatrolRoute:
        row = PatrolRoute(
            tenant_id=tenant_id,
            customer_id=payload.customer_id,
            site_id=payload.site_id,
            meeting_address_id=payload.meeting_address_id,
            route_no=payload.route_no,
            name=payload.name,
            start_point_text=payload.start_point_text,
            end_point_text=payload.end_point_text,
            travel_policy_code=payload.travel_policy_code,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        row.checkpoints = []
        self.patrol_routes[row.id] = row
        return row

    def update_patrol_route(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        return None

    def find_patrol_route_by_no(self, tenant_id: str, route_no: str, *, exclude_id: str | None = None) -> PatrolRoute | None:
        for row in self.patrol_routes.values():
            if row.tenant_id == tenant_id and row.route_no == route_no and row.id != exclude_id:
                return row
        return None

    def create_patrol_checkpoint(self, tenant_id: str, payload: PatrolCheckpointCreate, actor_user_id: str | None):
        row = PatrolCheckpoint(
            tenant_id=tenant_id,
            patrol_route_id=payload.patrol_route_id,
            sequence_no=payload.sequence_no,
            checkpoint_code=payload.checkpoint_code,
            label=payload.label,
            latitude=payload.latitude,
            longitude=payload.longitude,
            scan_type_code=payload.scan_type_code,
            expected_token_value=payload.expected_token_value,
            minimum_dwell_seconds=payload.minimum_dwell_seconds,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        row.patrol_route = self.patrol_routes[payload.patrol_route_id]
        self.patrol_checkpoints[row.id] = row
        return row

    def update_patrol_checkpoint(self, tenant_id: str, row_id: str, payload, actor_user_id: str | None):
        row = self.patrol_checkpoints.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        if payload.version_no != row.version_no:
            raise ApiException(409, "planning.patrol_checkpoint.stale_version", "errors.planning.patrol_checkpoint.stale_version")
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.version_no += 1
        row.updated_by_user_id = actor_user_id
        return row

    def get_patrol_checkpoint(self, tenant_id: str, row_id: str):
        row = self.patrol_checkpoints.get(row_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def list_patrol_checkpoints(self, tenant_id: str, patrol_route_id: str):
        return sorted(
            [row for row in self.patrol_checkpoints.values() if row.tenant_id == tenant_id and row.patrol_route_id == patrol_route_id],
            key=lambda row: row.sequence_no,
        )

    def find_patrol_checkpoint_by_sequence(self, tenant_id: str, patrol_route_id: str, sequence_no: int, *, exclude_id: str | None = None):
        for row in self.patrol_checkpoints.values():
            if (
                row.tenant_id == tenant_id
                and row.patrol_route_id == patrol_route_id
                and row.sequence_no == sequence_no
                and row.id != exclude_id
            ):
                return row
        return None

    def find_patrol_checkpoint_by_code(self, tenant_id: str, patrol_route_id: str, checkpoint_code: str, *, exclude_id: str | None = None):
        for row in self.patrol_checkpoints.values():
            if (
                row.tenant_id == tenant_id
                and row.patrol_route_id == patrol_route_id
                and row.checkpoint_code == checkpoint_code
                and row.id != exclude_id
            ):
                return row
        return None


class PlanningOpsMasterFoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakePlanningRepository()
        self.audit_repository = RecordingAuditRepository()
        self.service = PlanningService(self.repository, audit_service=AuditService(self.audit_repository))
        self.context = _context("planning.ops.read", "planning.ops.write")

    def assert_json_safe(self, value) -> None:  # noqa: ANN001
        json.dumps(value)

    def test_create_requirement_type_rejects_duplicate_code(self) -> None:
        payload = RequirementTypeCreate(
            tenant_id="tenant-1",
            customer_id=None,
            code="obj_guard",
            label="Objektschutz",
            default_planning_mode_code="site",
        )
        self.service.create_requirement_type("tenant-1", payload, self.context)
        with self.assertRaises(ApiException) as ctx:
            self.service.create_requirement_type("tenant-1", payload, self.context)
        self.assertEqual(ctx.exception.message_key, "errors.planning.requirement_type.duplicate_code")

    def test_requirement_type_create_and_list_are_tenant_scoped(self) -> None:
        first = self.service.create_requirement_type(
            "tenant-1",
            RequirementTypeCreate(
                tenant_id="tenant-1",
                customer_id=None,
                code="obj_guard",
                label="Objektschutz",
                default_planning_mode_code="site",
            ),
            self.context,
        )
        second = self.service.create_requirement_type(
            "tenant-1",
            RequirementTypeCreate(
                tenant_id="tenant-1",
                customer_id="customer-2",
                code="event_guard",
                label="Eventschutz",
                default_planning_mode_code="event",
            ),
            self.context,
        )

        rows = self.service.list_requirement_types(
            "tenant-1",
            OpsMasterFilter(customer_id="customer-1"),
            self.context,
        )

        self.assertEqual([row.id for row in rows], [second.id, first.id])
        self.assertIsNone(rows[1].customer_id)

    def test_create_requirement_type_normalizes_blank_customer_id_to_none(self) -> None:
        row = self.service.create_requirement_type(
            "tenant-1",
            RequirementTypeCreate(
                tenant_id="tenant-1",
                customer_id="",
                code="blank_customer",
                label="Blank Customer",
                default_planning_mode_code="site",
            ),
            self.context,
        )
        self.assertIsNone(row.customer_id)
        stored = self.repository.get_requirement_type("tenant-1", row.id)
        self.assertIsNotNone(stored)
        self.assertIsNone(stored.customer_id)

    def test_update_requirement_type_normalizes_blank_customer_id_to_none(self) -> None:
        row = self.service.create_requirement_type(
            "tenant-1",
            RequirementTypeCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                code="req_update_blank",
                label="Update Blank",
                default_planning_mode_code="site",
            ),
            self.context,
        )

        updated = self.service.update_requirement_type(
            "tenant-1",
            row.id,
            RequirementTypeUpdate(customer_id="", version_no=row.version_no),
            self.context,
        )

        self.assertIsNone(updated.customer_id)
        stored = self.repository.get_requirement_type("tenant-1", row.id)
        self.assertIsNotNone(stored)
        self.assertIsNone(stored.customer_id)

    def test_requirement_type_notes_round_trip_uses_notes_api_field_and_description_storage(self) -> None:
        created = self.service.create_requirement_type(
            "tenant-1",
            RequirementTypeCreate(
                tenant_id="tenant-1",
                customer_id=None,
                code="req_notes",
                label="Notes",
                default_planning_mode_code="site",
                notes="Initial note",
            ),
            self.context,
        )

        self.assertEqual(created.notes, "Initial note")
        stored = self.repository.get_requirement_type("tenant-1", created.id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored.description, "Initial note")

        updated = self.service.update_requirement_type(
            "tenant-1",
            created.id,
            RequirementTypeUpdate(notes="Updated note", version_no=created.version_no),
            self.context,
        )

        self.assertEqual(updated.notes, "Updated note")
        reopened = self.service.get_requirement_type("tenant-1", created.id, self.context)
        self.assertEqual(reopened.notes, "Updated note")

    def test_requirement_type_accepts_legacy_description_alias_without_losing_value(self) -> None:
        created = self.service.create_requirement_type(
            "tenant-1",
            RequirementTypeCreate(
                tenant_id="tenant-1",
                customer_id=None,
                code="req_legacy_notes",
                label="Legacy Notes",
                default_planning_mode_code="event",
                description="Legacy description note",
            ),
            self.context,
        )

        self.assertEqual(created.notes, "Legacy description note")
        stored = self.repository.get_requirement_type("tenant-1", created.id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored.description, "Legacy description note")

    def test_create_equipment_item_normalizes_blank_customer_id_to_none(self) -> None:
        row = self.service.create_equipment_item(
            "tenant-1",
            EquipmentItemCreate(
                tenant_id="tenant-1",
                customer_id="",
                code="radio",
                label="Radio",
                unit_of_measure_code="pcs",
            ),
            self.context,
        )
        self.assertIsNone(row.customer_id)
        stored = self.repository.get_equipment_item("tenant-1", row.id)
        self.assertIsNotNone(stored)
        self.assertIsNone(stored.customer_id)

    def test_update_equipment_item_normalizes_blank_customer_id_to_none(self) -> None:
        row = self.service.create_equipment_item(
            "tenant-1",
            EquipmentItemCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                code="gear",
                label="Gear",
                unit_of_measure_code="pcs",
            ),
            self.context,
        )

        updated = self.service.update_equipment_item(
            "tenant-1",
            row.id,
            EquipmentItemUpdate(customer_id="", version_no=row.version_no),
            self.context,
        )

        self.assertIsNone(updated.customer_id)
        stored = self.repository.get_equipment_item("tenant-1", row.id)
        self.assertIsNotNone(stored)
        self.assertIsNone(stored.customer_id)

    def test_create_site_requires_existing_customer(self) -> None:
        payload = SiteCreate(tenant_id="tenant-1", customer_id="missing", site_no="S-001", name="Objekt A")
        with self.assertRaises(ApiException) as ctx:
            self.service.create_site("tenant-1", payload, self.context)
        self.assertEqual(ctx.exception.message_key, "errors.planning.customer.not_found")

    def test_create_site_reuses_address(self) -> None:
        payload = SiteCreate(
            tenant_id="tenant-1",
            customer_id="customer-1",
            site_no="S-001",
            name="Objekt A",
            address_id="address-1",
            latitude=Decimal("52.520000"),
            longitude=Decimal("13.405000"),
            watchbook_enabled=True,
        )
        row = self.service.create_site("tenant-1", payload, self.context)
        self.assertEqual(row.address_id, "address-1")
        self.assertTrue(row.watchbook_enabled)

    def test_create_site_records_audit_event_with_decimal_coordinates_serialized_safely(self) -> None:
        payload = SiteCreate(
            tenant_id="tenant-1",
            customer_id="customer-1",
            site_no="S-002",
            name="Objekt B",
            latitude=Decimal("51.662973"),
            longitude=Decimal("8.174013"),
        )

        row = self.service.create_site("tenant-1", payload, self.context)

        self.assertEqual(row.site_no, "S-002")
        self.assertEqual(len(self.audit_repository.audit_events), 1)
        event = self.audit_repository.audit_events[0]
        self.assertEqual(event.event_type, "planning.site.created")
        self.assertEqual(event.after_json["latitude"], "51.662973")
        self.assertEqual(event.after_json["longitude"], "8.174013")
        self.assertEqual(event.after_json["id"], row.id)
        self.assertIsInstance(event.after_json["created_at"], str)
        self.assert_json_safe(event.after_json)

    def test_create_trade_fair_zone_records_json_safe_audit_without_trade_fair_relationship(self) -> None:
        fair = self.repository.create_trade_fair(
            "tenant-1",
            TradeFairCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                fair_no="F-201",
                name="Expo Nord",
                start_date=date(2026, 6, 1),
                end_date=date(2026, 6, 3),
            ),
            "user-1",
        )
        payload = TradeFairZoneCreate(
            tenant_id="tenant-1",
            trade_fair_id=fair.id,
            zone_type_code="hall",
            zone_code="B2",
            label="Halle B2",
            notes="West wing",
        )

        zone = self.service.create_trade_fair_zone("tenant-1", fair.id, payload, self.context)

        self.assertEqual(zone.trade_fair_id, fair.id)
        self.assertEqual(len(self.audit_repository.audit_events), 1)
        event = self.audit_repository.audit_events[0]
        self.assertEqual(event.event_type, "planning.trade_fair_zone.created")
        self.assertNotIn("trade_fair", event.after_json)
        self.assertEqual(event.after_json["trade_fair_id"], fair.id)
        self.assertEqual(event.after_json["zone_code"], "B2")
        self.assertIsInstance(event.after_json["created_at"], str)
        self.assert_json_safe(event.after_json)

    def test_create_patrol_checkpoint_records_json_safe_audit_without_patrol_route_relationship(self) -> None:
        route = self.repository.create_patrol_route(
            "tenant-1",
            PatrolRouteCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                route_no="R-201",
                name="Route 201",
            ),
            "user-1",
        )
        payload = PatrolCheckpointCreate(
            tenant_id="tenant-1",
            patrol_route_id=route.id,
            sequence_no=2,
            checkpoint_code="CP-201",
            label="South gate",
            latitude=Decimal("52.510000"),
            longitude=Decimal("13.410000"),
            scan_type_code="qr",
            expected_token_value="gate-201",
            minimum_dwell_seconds=15,
            notes="Second checkpoint",
        )

        checkpoint = self.service.create_patrol_checkpoint("tenant-1", route.id, payload, self.context)

        self.assertEqual(checkpoint.patrol_route_id, route.id)
        self.assertEqual(len(self.audit_repository.audit_events), 1)
        event = self.audit_repository.audit_events[0]
        self.assertEqual(event.event_type, "planning.patrol_checkpoint.created")
        self.assertNotIn("patrol_route", event.after_json)
        self.assertEqual(event.after_json["patrol_route_id"], route.id)
        self.assertEqual(event.after_json["latitude"], "52.510000")
        self.assertEqual(event.after_json["longitude"], "13.410000")
        self.assert_json_safe(event.after_json)

    def test_trade_fair_rejects_invalid_date_window(self) -> None:
        payload = TradeFairCreate(
            tenant_id="tenant-1",
            customer_id="customer-1",
            fair_no="F-001",
            name="Expo",
            start_date=date(2026, 5, 10),
            end_date=date(2026, 5, 9),
        )
        with self.assertRaises(ApiException) as ctx:
            self.service.create_trade_fair("tenant-1", payload, self.context)
        self.assertEqual(ctx.exception.message_key, "errors.planning.trade_fair.invalid_window")

    def test_trade_fair_requires_matching_customer_for_venue(self) -> None:
        venue = self.repository.create_event_venue(
            "tenant-1",
            type(
                "Payload",
                (),
                {
                    "customer_id": "customer-2",
                    "venue_no": "V-001",
                    "name": "Venue",
                    "address_id": None,
                    "timezone": None,
                    "latitude": None,
                    "longitude": None,
                    "notes": None,
                },
            )(),
            "user-1",
        )
        payload = TradeFairCreate(
            tenant_id="tenant-1",
            customer_id="customer-1",
            venue_id=venue.id,
            fair_no="F-001",
            name="Expo",
            start_date=date(2026, 5, 9),
            end_date=date(2026, 5, 10),
        )
        with self.assertRaises(ApiException) as ctx:
            self.service.create_trade_fair("tenant-1", payload, self.context)
        self.assertEqual(ctx.exception.message_key, "errors.planning.trade_fair.venue_customer_mismatch")

    def test_patrol_route_rejects_site_customer_mismatch(self) -> None:
        site = self.repository.create_site(
            "tenant-1",
            SiteCreate(tenant_id="tenant-1", customer_id="customer-2", site_no="S-900", name="Other"),
            "user-1",
        )
        payload = PatrolRouteCreate(
            tenant_id="tenant-1",
            customer_id="customer-1",
            site_id=site.id,
            route_no="R-001",
            name="Patrol",
        )
        with self.assertRaises(ApiException) as ctx:
            self.service.create_patrol_route("tenant-1", payload, self.context)
        self.assertEqual(ctx.exception.message_key, "errors.planning.patrol_route.site_customer_mismatch")

    def test_requirement_type_listing_hides_archived_by_default(self) -> None:
        active = self.repository.create_requirement_type(
            "tenant-1",
            RequirementTypeCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                code="active",
                label="Aktiv",
                default_planning_mode_code="site",
            ),
            "user-1",
        )
        archived = self.repository.create_requirement_type(
            "tenant-1",
            RequirementTypeCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                code="archived",
                label="Archiviert",
                default_planning_mode_code="site",
            ),
            "user-1",
        )
        archived.archived_at = datetime.now(UTC)
        rows = self.service.list_requirement_types("tenant-1", OpsMasterFilter(), self.context)
        self.assertEqual([row.id for row in rows], [active.id])

    def test_planning_models_use_address_and_customer_foreign_keys(self) -> None:
        metadata = Base.metadata
        site_table = metadata.tables["ops.site"]
        route_table = metadata.tables["ops.patrol_route"]
        checkpoint_table = metadata.tables["ops.patrol_checkpoint"]
        fair_table = metadata.tables["ops.trade_fair"]
        fair_zone_table = metadata.tables["ops.trade_fair_zone"]
        self.assertIn("fk_ops_site_tenant_customer", {fk.name for fk in site_table.foreign_key_constraints})
        self.assertIn("fk_ops_trade_fair_tenant_customer", {fk.name for fk in fair_table.foreign_key_constraints})
        self.assertIn("fk_ops_trade_fair_zone_tenant_fair", {fk.name for fk in fair_zone_table.foreign_key_constraints})
        self.assertIn("uq_ops_trade_fair_zone_tenant_id_id", {constraint.name for constraint in fair_zone_table.constraints})
        self.assertIn("fk_ops_patrol_checkpoint_tenant_route", {fk.name for fk in checkpoint_table.foreign_key_constraints})
        self.assertIn("uq_ops_patrol_checkpoint_tenant_id_id", {constraint.name for constraint in checkpoint_table.constraints})
        self.assertIn("meeting_address_id", route_table.c)
        self.assertTrue(any(isinstance(constraint, CheckConstraint) and "coordinates_valid" in constraint.name for constraint in site_table.constraints))

    def test_trade_fair_zone_rejects_duplicate_tuple(self) -> None:
        fair = self.repository.create_trade_fair(
            "tenant-1",
            TradeFairCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                fair_no="F-100",
                name="Expo",
                start_date=date(2026, 5, 1),
                end_date=date(2026, 5, 2),
            ),
            "user-1",
        )
        payload = TradeFairZoneCreate(
            tenant_id="tenant-1",
            trade_fair_id=fair.id,
            zone_type_code="hall",
            zone_code="A1",
            label="Halle A1",
        )
        self.service.create_trade_fair_zone("tenant-1", fair.id, payload, self.context)
        with self.assertRaises(ApiException) as ctx:
            self.service.create_trade_fair_zone("tenant-1", fair.id, payload, self.context)
        self.assertEqual(ctx.exception.message_key, "errors.planning.trade_fair_zone.duplicate_tuple")

    def test_patrol_checkpoint_rejects_duplicate_sequence(self) -> None:
        route = self.repository.create_patrol_route(
            "tenant-1",
            PatrolRouteCreate(tenant_id="tenant-1", customer_id="customer-1", route_no="R-100", name="Route 100"),
            "user-1",
        )
        self.service.create_patrol_checkpoint(
            "tenant-1",
            route.id,
            PatrolCheckpointCreate(
                tenant_id="tenant-1",
                patrol_route_id=route.id,
                sequence_no=1,
                checkpoint_code="CP-1",
                label="Tor",
                latitude=Decimal("52.520000"),
                longitude=Decimal("13.405000"),
                scan_type_code="qr",
            ),
            self.context,
        )
        with self.assertRaises(ApiException) as ctx:
            self.service.create_patrol_checkpoint(
                "tenant-1",
                route.id,
                PatrolCheckpointCreate(
                    tenant_id="tenant-1",
                    patrol_route_id=route.id,
                    sequence_no=1,
                    checkpoint_code="CP-2",
                    label="Hof",
                    latitude=Decimal("52.520100"),
                    longitude=Decimal("13.405100"),
                    scan_type_code="qr",
                ),
                self.context,
            )
        self.assertEqual(ctx.exception.message_key, "errors.planning.patrol_checkpoint.duplicate_sequence")

    def test_site_location_projection_distinguishes_postal_and_operational_geo(self) -> None:
        site = self.repository.create_site(
            "tenant-1",
            SiteCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                site_no="S-500",
                name="Objekt Nord",
                address_id="address-1",
                latitude=Decimal("52.501000"),
                longitude=Decimal("13.401000"),
                watchbook_enabled=True,
            ),
            "user-1",
        )

        projection = self.service.get_site_location_projection("tenant-1", site.id, self.context)

        self.assertEqual(projection.postal_address_id, "address-1")
        self.assertIsNotNone(projection.postal_address)
        self.assertEqual(projection.postal_address.city, "Berlin")
        self.assertIsNotNone(projection.operational_geo_point)
        self.assertEqual(str(projection.operational_geo_point.latitude), "52.501000")
        self.assertEqual(projection.operational_geo_point.source, "site")
        self.assertTrue(projection.watchbook_enabled)

    def test_patrol_route_location_projection_exposes_site_watchbook_and_checkpoint_geo(self) -> None:
        site = self.repository.create_site(
            "tenant-1",
            SiteCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                site_no="S-700",
                name="Patrol Site",
                address_id="address-1",
                latitude=Decimal("52.700000"),
                longitude=Decimal("13.700000"),
                watchbook_enabled=True,
            ),
            "user-1",
        )
        route = self.repository.create_patrol_route(
            "tenant-1",
            PatrolRouteCreate(
                tenant_id="tenant-1",
                customer_id="customer-1",
                site_id=site.id,
                meeting_address_id="address-1",
                route_no="R-700",
                name="Nachtrunde",
                start_point_text="Nordtor",
                end_point_text="Leitstand",
            ),
            "user-1",
        )
        route.site = site
        route.meeting_address = self.repository.addresses["address-1"]
        checkpoint = self.repository.create_patrol_checkpoint(
            "tenant-1",
            PatrolCheckpointCreate(
                tenant_id="tenant-1",
                patrol_route_id=route.id,
                sequence_no=1,
                checkpoint_code="CP-700",
                label="Nordtor",
                latitude=Decimal("52.701000"),
                longitude=Decimal("13.701000"),
                scan_type_code="qr",
            ),
            "user-1",
        )
        route.__dict__["checkpoints"] = [checkpoint]

        projection = self.service.get_patrol_route_location_projection("tenant-1", route.id, self.context)

        self.assertIsNotNone(projection.linked_site)
        self.assertTrue(projection.linked_site.watchbook_enabled)
        self.assertEqual(projection.meeting_address.city, "Berlin")
        self.assertEqual(len(projection.checkpoint_geo_points), 1)
        self.assertEqual(projection.checkpoint_geo_points[0].geo_point.source, "patrol_checkpoint")
