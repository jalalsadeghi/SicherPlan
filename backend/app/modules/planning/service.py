"""Service layer for planning operational master data."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Protocol
from uuid import UUID

from sqlalchemy import inspect as sa_inspect

from app.errors import ApiException
from app.modules.core.models import Address, LookupValue
from app.modules.customers.models import Customer
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.models import EquipmentItem, EventVenue, PatrolRoute, RequirementType, ServiceCategory, Site, TradeFair
from app.modules.planning.schemas import (
    EquipmentItemCreate,
    EquipmentItemListItem,
    EquipmentItemRead,
    EquipmentItemUpdate,
    EventVenueCreate,
    EventVenueLocationProjectionRead,
    EventVenueListItem,
    EventVenueRead,
    EventVenueUpdate,
    OpsMasterFilter,
    OperationalGeoPointRead,
    PlanningReferenceOptionRead,
    PatrolCheckpointCreate,
    PatrolCheckpointGeoPointRead,
    PatrolCheckpointRead,
    PatrolCheckpointUpdate,
    PatrolRouteCreate,
    PatrolRouteLocationProjectionRead,
    PatrolRouteListItem,
    PatrolRouteRead,
    PatrolRouteUpdate,
    RequirementTypeCreate,
    RequirementTypeListItem,
    RequirementTypeRead,
    RequirementTypeUpdate,
    ServiceCategoryCreate,
    ServiceCategoryListItem,
    ServiceCategoryRead,
    ServiceCategoryUpdate,
    SiteCreate,
    SiteCrosslinkRead,
    SiteListItem,
    SiteLocationProjectionRead,
    SiteRead,
    SiteUpdate,
    TradeFairCreate,
    TradeFairLocationProjectionRead,
    TradeFairListItem,
    TradeFairRead,
    TradeFairZoneCreate,
    TradeFairZoneRead,
    TradeFairZoneUpdate,
    TradeFairUpdate,
)


class PlanningRepository(Protocol):
    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None: ...
    def get_address(self, address_id: str) -> Address | None: ...
    def list_lookup_values(self, tenant_id: str | None, domain: str) -> list[LookupValue]: ...
    def list_requirement_types(self, tenant_id: str, filters: OpsMasterFilter) -> list[RequirementType]: ...
    def get_requirement_type(self, tenant_id: str, row_id: str) -> RequirementType | None: ...
    def create_requirement_type(self, tenant_id: str, payload: RequirementTypeCreate, actor_user_id: str | None) -> RequirementType: ...
    def update_requirement_type(self, tenant_id: str, row_id: str, payload: RequirementTypeUpdate, actor_user_id: str | None) -> RequirementType | None: ...
    def find_requirement_type_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> RequirementType | None: ...
    def list_equipment_items(self, tenant_id: str, filters: OpsMasterFilter) -> list[EquipmentItem]: ...
    def get_equipment_item(self, tenant_id: str, row_id: str) -> EquipmentItem | None: ...
    def create_equipment_item(self, tenant_id: str, payload: EquipmentItemCreate, actor_user_id: str | None) -> EquipmentItem: ...
    def update_equipment_item(self, tenant_id: str, row_id: str, payload: EquipmentItemUpdate, actor_user_id: str | None) -> EquipmentItem | None: ...
    def find_equipment_item_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> EquipmentItem | None: ...
    def list_service_categories(self, tenant_id: str, filters: OpsMasterFilter) -> list[ServiceCategory]: ...
    def get_service_category(self, tenant_id: str, row_id: str) -> ServiceCategory | None: ...
    def create_service_category(self, tenant_id: str, payload: ServiceCategoryCreate, actor_user_id: str | None) -> ServiceCategory: ...
    def update_service_category(self, tenant_id: str, row_id: str, payload: ServiceCategoryUpdate, actor_user_id: str | None) -> ServiceCategory | None: ...
    def find_service_category_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> ServiceCategory | None: ...
    def list_sites(self, tenant_id: str, filters: OpsMasterFilter) -> list[Site]: ...
    def get_site(self, tenant_id: str, row_id: str) -> Site | None: ...
    def create_site(self, tenant_id: str, payload: SiteCreate, actor_user_id: str | None) -> Site: ...
    def update_site(self, tenant_id: str, row_id: str, payload: SiteUpdate, actor_user_id: str | None) -> Site | None: ...
    def find_site_by_no(self, tenant_id: str, site_no: str, *, exclude_id: str | None = None) -> Site | None: ...
    def list_event_venues(self, tenant_id: str, filters: OpsMasterFilter) -> list[EventVenue]: ...
    def get_event_venue(self, tenant_id: str, row_id: str) -> EventVenue | None: ...
    def create_event_venue(self, tenant_id: str, payload: EventVenueCreate, actor_user_id: str | None) -> EventVenue: ...
    def update_event_venue(self, tenant_id: str, row_id: str, payload: EventVenueUpdate, actor_user_id: str | None) -> EventVenue | None: ...
    def find_event_venue_by_no(self, tenant_id: str, venue_no: str, *, exclude_id: str | None = None) -> EventVenue | None: ...
    def list_trade_fairs(self, tenant_id: str, filters: OpsMasterFilter) -> list[TradeFair]: ...
    def get_trade_fair(self, tenant_id: str, row_id: str) -> TradeFair | None: ...
    def create_trade_fair(self, tenant_id: str, payload: TradeFairCreate, actor_user_id: str | None) -> TradeFair: ...
    def update_trade_fair(self, tenant_id: str, row_id: str, payload: TradeFairUpdate, actor_user_id: str | None) -> TradeFair | None: ...
    def find_trade_fair_by_no(self, tenant_id: str, fair_no: str, *, exclude_id: str | None = None) -> TradeFair | None: ...
    def create_trade_fair_zone(self, tenant_id: str, payload: TradeFairZoneCreate, actor_user_id: str | None): ...
    def update_trade_fair_zone(self, tenant_id: str, row_id: str, payload: TradeFairZoneUpdate, actor_user_id: str | None): ...
    def get_trade_fair_zone(self, tenant_id: str, row_id: str): ...
    def list_trade_fair_zones(self, tenant_id: str, trade_fair_id: str): ...
    def find_trade_fair_zone(self, tenant_id: str, trade_fair_id: str, zone_type_code: str, zone_code: str, *, exclude_id: str | None = None): ...
    def list_patrol_routes(self, tenant_id: str, filters: OpsMasterFilter) -> list[PatrolRoute]: ...
    def get_patrol_route(self, tenant_id: str, row_id: str) -> PatrolRoute | None: ...
    def create_patrol_route(self, tenant_id: str, payload: PatrolRouteCreate, actor_user_id: str | None) -> PatrolRoute: ...
    def update_patrol_route(self, tenant_id: str, row_id: str, payload: PatrolRouteUpdate, actor_user_id: str | None) -> PatrolRoute | None: ...
    def find_patrol_route_by_no(self, tenant_id: str, route_no: str, *, exclude_id: str | None = None) -> PatrolRoute | None: ...
    def create_patrol_checkpoint(self, tenant_id: str, payload: PatrolCheckpointCreate, actor_user_id: str | None): ...
    def update_patrol_checkpoint(self, tenant_id: str, row_id: str, payload: PatrolCheckpointUpdate, actor_user_id: str | None): ...
    def get_patrol_checkpoint(self, tenant_id: str, row_id: str): ...
    def list_patrol_checkpoints(self, tenant_id: str, patrol_route_id: str): ...
    def find_patrol_checkpoint_by_sequence(self, tenant_id: str, patrol_route_id: str, sequence_no: int, *, exclude_id: str | None = None): ...
    def find_patrol_checkpoint_by_code(self, tenant_id: str, patrol_route_id: str, checkpoint_code: str, *, exclude_id: str | None = None): ...


class PlanningService:
    EQUIPMENT_UNIT_DOMAIN = "unit_of_measure"
    EQUIPMENT_UNIT_FALLBACK_OPTIONS: tuple[dict[str, object], ...] = (
        {"code": "pcs", "label": "Stueck", "description": "Einzelteil oder einzelnes Geraet", "sort_order": 10},
        {"code": "set", "label": "Satz", "description": "Zusammengehoeriger Satz mehrerer Teile", "sort_order": 20},
        {"code": "kit", "label": "Kit", "description": "Vorkonfiguriertes Ausruestungsset", "sort_order": 30},
        {"code": "box", "label": "Box", "description": "Gebinde oder Boxeinheit", "sort_order": 40},
        {"code": "pallet", "label": "Palette", "description": "Paletteneinheit fuer groessere Mengen", "sort_order": 50},
    )
    SERVICE_CATEGORY_DOMAIN = "service_category"
    SERVICE_CATEGORY_FALLBACK_OPTIONS: tuple[dict[str, object], ...] = (
        {
            "code": "object_security",
            "label": "Objektschutz",
            "description": "Objekt- oder standortbezogene Sicherheitsleistung",
            "sort_order": 10,
        },
        {
            "code": "event_security",
            "label": "Veranstaltungsschutz",
            "description": "Veranstaltungsbezogene Sicherheitsleistung",
            "sort_order": 20,
        },
        {
            "code": "trade_fair_security",
            "label": "Messebewachung",
            "description": "Messe- oder standbezogene Sicherheitsleistung",
            "sort_order": 30,
        },
        {
            "code": "patrol_service",
            "label": "Revier- / Patrouillendienst",
            "description": "Patrouillen-, Revier- oder Alarmfahrdienst",
            "sort_order": 40,
        },
    )

    def __init__(self, repository: PlanningRepository, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_requirement_types(
        self,
        tenant_id: str,
        filters: OpsMasterFilter,
        _actor: RequestAuthorizationContext,
    ) -> list[RequirementTypeListItem]:
        return [RequirementTypeListItem.model_validate(row) for row in self.repository.list_requirement_types(tenant_id, filters)]

    def get_requirement_type(self, tenant_id: str, row_id: str, _actor: RequestAuthorizationContext) -> RequirementTypeRead:
        row = self.repository.get_requirement_type(tenant_id, row_id)
        if row is None:
            raise self._not_found("requirement_type")
        return RequirementTypeRead.model_validate(row)

    def create_requirement_type(self, tenant_id: str, payload: RequirementTypeCreate, actor: RequestAuthorizationContext) -> RequirementTypeRead:
        payload = self._normalize_optional_customer_id(payload)
        if self.repository.find_requirement_type_by_code(tenant_id, payload.code) is not None:
            raise self._duplicate("requirement_type")
        row = self.repository.create_requirement_type(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.requirement_type.created", "ops.requirement_type", row.id, tenant_id, after_json=self._snapshot(row))
        return RequirementTypeRead.model_validate(row)

    def update_requirement_type(
        self,
        tenant_id: str,
        row_id: str,
        payload: RequirementTypeUpdate,
        actor: RequestAuthorizationContext,
    ) -> RequirementTypeRead:
        payload = self._normalize_optional_customer_id(payload)
        current = self.repository.get_requirement_type(tenant_id, row_id)
        if current is None:
            raise self._not_found("requirement_type")
        before_json = self._snapshot(current)
        next_code = self._field_value(payload, "code", current.code)
        if self.repository.find_requirement_type_by_code(tenant_id, next_code, exclude_id=row_id) is not None:
            raise self._duplicate("requirement_type")
        row = self.repository.update_requirement_type(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("requirement_type")
        self._record_event(actor, "planning.requirement_type.updated", "ops.requirement_type", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return RequirementTypeRead.model_validate(row)

    def list_equipment_items(self, tenant_id: str, filters: OpsMasterFilter, _actor: RequestAuthorizationContext) -> list[EquipmentItemListItem]:
        return [EquipmentItemListItem.model_validate(row) for row in self.repository.list_equipment_items(tenant_id, filters)]

    def list_equipment_unit_options(
        self,
        tenant_id: str,
        _actor: RequestAuthorizationContext,
    ) -> list[PlanningReferenceOptionRead]:
        lookup_rows = self.repository.list_lookup_values(tenant_id, self.EQUIPMENT_UNIT_DOMAIN)
        preferred_rows_by_code: dict[str, LookupValue] = {}
        for row in lookup_rows:
            existing = preferred_rows_by_code.get(row.code)
            if existing is None or (existing.tenant_id is None and row.tenant_id == tenant_id):
                preferred_rows_by_code[row.code] = row

        if preferred_rows_by_code:
            return [
                PlanningReferenceOptionRead.model_validate(row)
                for row in sorted(preferred_rows_by_code.values(), key=lambda row: (row.sort_order, row.label))
            ]

        return [PlanningReferenceOptionRead.model_validate(row) for row in self.EQUIPMENT_UNIT_FALLBACK_OPTIONS]

    def list_service_category_options(
        self,
        tenant_id: str,
        _actor: RequestAuthorizationContext,
    ) -> list[PlanningReferenceOptionRead]:
        catalog_rows = self.repository.list_service_categories(
            tenant_id,
            OpsMasterFilter(lifecycle_status="active"),
        )
        if catalog_rows:
            return [
                PlanningReferenceOptionRead(
                    id=row.id,
                    code=row.code,
                    label=row.label,
                    description=row.description,
                    sort_order=row.sort_order,
                )
                for row in sorted(catalog_rows, key=lambda row: (row.sort_order, row.label))
            ]

        canonical_by_code = {
            row["code"]: row
            for row in self.SERVICE_CATEGORY_FALLBACK_OPTIONS
        }
        lookup_rows = [
            row
            for row in self.repository.list_lookup_values(None, self.SERVICE_CATEGORY_DOMAIN)
            if row.code in canonical_by_code
        ]
        preferred_rows_by_code: dict[str, LookupValue] = {}
        for row in lookup_rows:
            existing = preferred_rows_by_code.get(row.code)
            if existing is None:
                preferred_rows_by_code[row.code] = row

        resolved_rows: list[PlanningReferenceOptionRead] = []
        for fallback in self.SERVICE_CATEGORY_FALLBACK_OPTIONS:
            lookup_row = preferred_rows_by_code.get(fallback["code"])
            resolved_rows.append(
                PlanningReferenceOptionRead.model_validate(lookup_row or fallback)
            )

        return resolved_rows

    def list_service_categories(self, tenant_id: str, filters: OpsMasterFilter, _actor: RequestAuthorizationContext) -> list[ServiceCategoryListItem]:
        return [ServiceCategoryListItem.model_validate(row) for row in self.repository.list_service_categories(tenant_id, filters)]

    def get_service_category(self, tenant_id: str, row_id: str, _actor: RequestAuthorizationContext) -> ServiceCategoryRead:
        row = self.repository.get_service_category(tenant_id, row_id)
        if row is None:
            raise self._not_found("service_category")
        return ServiceCategoryRead.model_validate(row)

    def create_service_category(self, tenant_id: str, payload: ServiceCategoryCreate, actor: RequestAuthorizationContext) -> ServiceCategoryRead:
        if self.repository.find_service_category_by_code(tenant_id, payload.code) is not None:
            raise self._duplicate("service_category")
        row = self.repository.create_service_category(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.service_category.created", "ops.service_category", row.id, tenant_id, after_json=self._snapshot(row))
        return ServiceCategoryRead.model_validate(row)

    def update_service_category(
        self,
        tenant_id: str,
        row_id: str,
        payload: ServiceCategoryUpdate,
        actor: RequestAuthorizationContext,
    ) -> ServiceCategoryRead:
        current = self.repository.get_service_category(tenant_id, row_id)
        if current is None:
            raise self._not_found("service_category")
        before_json = self._snapshot(current)
        next_code = self._field_value(payload, "code", current.code)
        if self.repository.find_service_category_by_code(tenant_id, next_code, exclude_id=row_id) is not None:
            raise self._duplicate("service_category")
        row = self.repository.update_service_category(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("service_category")
        self._record_event(actor, "planning.service_category.updated", "ops.service_category", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return ServiceCategoryRead.model_validate(row)

    def get_equipment_item(self, tenant_id: str, row_id: str, _actor: RequestAuthorizationContext) -> EquipmentItemRead:
        row = self.repository.get_equipment_item(tenant_id, row_id)
        if row is None:
            raise self._not_found("equipment_item")
        return EquipmentItemRead.model_validate(row)

    def create_equipment_item(self, tenant_id: str, payload: EquipmentItemCreate, actor: RequestAuthorizationContext) -> EquipmentItemRead:
        payload = self._normalize_optional_customer_id(payload)
        if self.repository.find_equipment_item_by_code(tenant_id, payload.code) is not None:
            raise self._duplicate("equipment_item")
        self.ensure_equipment_unit_of_measure_code(tenant_id, payload.unit_of_measure_code)
        row = self.repository.create_equipment_item(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.equipment_item.created", "ops.equipment_item", row.id, tenant_id, after_json=self._snapshot(row))
        return EquipmentItemRead.model_validate(row)

    def update_equipment_item(self, tenant_id: str, row_id: str, payload: EquipmentItemUpdate, actor: RequestAuthorizationContext) -> EquipmentItemRead:
        payload = self._normalize_optional_customer_id(payload)
        current = self.repository.get_equipment_item(tenant_id, row_id)
        if current is None:
            raise self._not_found("equipment_item")
        before_json = self._snapshot(current)
        next_code = self._field_value(payload, "code", current.code)
        if self.repository.find_equipment_item_by_code(tenant_id, next_code, exclude_id=row_id) is not None:
            raise self._duplicate("equipment_item")
        next_unit = self._field_value(payload, "unit_of_measure_code", current.unit_of_measure_code)
        self.ensure_equipment_unit_of_measure_code(
            tenant_id,
            next_unit,
            current_value=current.unit_of_measure_code,
        )
        row = self.repository.update_equipment_item(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("equipment_item")
        self._record_event(actor, "planning.equipment_item.updated", "ops.equipment_item", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return EquipmentItemRead.model_validate(row)

    def list_sites(self, tenant_id: str, filters: OpsMasterFilter, _actor: RequestAuthorizationContext) -> list[SiteListItem]:
        return [SiteListItem.model_validate(row) for row in self.repository.list_sites(tenant_id, filters)]

    def get_site(self, tenant_id: str, row_id: str, _actor: RequestAuthorizationContext) -> SiteRead:
        row = self.repository.get_site(tenant_id, row_id)
        if row is None:
            raise self._not_found("site")
        return SiteRead.model_validate(row)

    def get_site_location_projection(
        self,
        tenant_id: str,
        row_id: str,
        _actor: RequestAuthorizationContext,
    ) -> SiteLocationProjectionRead:
        row = self.repository.get_site(tenant_id, row_id)
        if row is None:
            raise self._not_found("site")
        return SiteLocationProjectionRead(
            id=row.id,
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            site_no=row.site_no,
            name=row.name,
            watchbook_enabled=row.watchbook_enabled,
            postal_address_id=row.address_id,
            postal_address=self._address_read(row.address),
            operational_geo_point=self._geo_point(row.latitude, row.longitude, source="site"),
            timezone=row.timezone,
        )

    def create_site(self, tenant_id: str, payload: SiteCreate, actor: RequestAuthorizationContext) -> SiteRead:
        self._validate_customer_path(tenant_id, payload.customer_id)
        self._validate_address(payload.address_id)
        if self.repository.find_site_by_no(tenant_id, payload.site_no) is not None:
            raise self._duplicate("site")
        row = self.repository.create_site(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.site.created", "ops.site", row.id, tenant_id, after_json=self._snapshot(row))
        return SiteRead.model_validate(row)

    def update_site(self, tenant_id: str, row_id: str, payload: SiteUpdate, actor: RequestAuthorizationContext) -> SiteRead:
        current = self.repository.get_site(tenant_id, row_id)
        if current is None:
            raise self._not_found("site")
        before_json = self._snapshot(current)
        next_customer_id = self._field_value(payload, "customer_id", current.customer_id)
        self._validate_customer_path(tenant_id, next_customer_id)
        self._validate_address(self._field_value(payload, "address_id", current.address_id))
        next_no = self._field_value(payload, "site_no", current.site_no)
        if self.repository.find_site_by_no(tenant_id, next_no, exclude_id=row_id) is not None:
            raise self._duplicate("site")
        row = self.repository.update_site(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("site")
        self._record_event(actor, "planning.site.updated", "ops.site", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return SiteRead.model_validate(row)

    def list_event_venues(self, tenant_id: str, filters: OpsMasterFilter, _actor: RequestAuthorizationContext) -> list[EventVenueListItem]:
        return [EventVenueListItem.model_validate(row) for row in self.repository.list_event_venues(tenant_id, filters)]

    def get_event_venue(self, tenant_id: str, row_id: str, _actor: RequestAuthorizationContext) -> EventVenueRead:
        row = self.repository.get_event_venue(tenant_id, row_id)
        if row is None:
            raise self._not_found("event_venue")
        return EventVenueRead.model_validate(row)

    def get_event_venue_location_projection(
        self,
        tenant_id: str,
        row_id: str,
        _actor: RequestAuthorizationContext,
    ) -> EventVenueLocationProjectionRead:
        row = self.repository.get_event_venue(tenant_id, row_id)
        if row is None:
            raise self._not_found("event_venue")
        return EventVenueLocationProjectionRead(
            id=row.id,
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            venue_no=row.venue_no,
            name=row.name,
            postal_address_id=row.address_id,
            postal_address=self._address_read(row.address),
            operational_geo_point=self._geo_point(row.latitude, row.longitude, source="event_venue"),
            timezone=row.timezone,
        )

    def create_event_venue(self, tenant_id: str, payload: EventVenueCreate, actor: RequestAuthorizationContext) -> EventVenueRead:
        self._validate_customer_path(tenant_id, payload.customer_id)
        self._validate_address(payload.address_id)
        if self.repository.find_event_venue_by_no(tenant_id, payload.venue_no) is not None:
            raise self._duplicate("event_venue")
        row = self.repository.create_event_venue(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.event_venue.created", "ops.event_venue", row.id, tenant_id, after_json=self._snapshot(row))
        return EventVenueRead.model_validate(row)

    def update_event_venue(self, tenant_id: str, row_id: str, payload: EventVenueUpdate, actor: RequestAuthorizationContext) -> EventVenueRead:
        current = self.repository.get_event_venue(tenant_id, row_id)
        if current is None:
            raise self._not_found("event_venue")
        before_json = self._snapshot(current)
        next_customer_id = self._field_value(payload, "customer_id", current.customer_id)
        self._validate_customer_path(tenant_id, next_customer_id)
        self._validate_address(self._field_value(payload, "address_id", current.address_id))
        next_no = self._field_value(payload, "venue_no", current.venue_no)
        if self.repository.find_event_venue_by_no(tenant_id, next_no, exclude_id=row_id) is not None:
            raise self._duplicate("event_venue")
        row = self.repository.update_event_venue(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("event_venue")
        self._record_event(actor, "planning.event_venue.updated", "ops.event_venue", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return EventVenueRead.model_validate(row)

    def list_trade_fairs(self, tenant_id: str, filters: OpsMasterFilter, _actor: RequestAuthorizationContext) -> list[TradeFairListItem]:
        return [TradeFairListItem.model_validate(row) for row in self.repository.list_trade_fairs(tenant_id, filters)]

    def get_trade_fair(self, tenant_id: str, row_id: str, _actor: RequestAuthorizationContext) -> TradeFairRead:
        row = self.repository.get_trade_fair(tenant_id, row_id)
        if row is None:
            raise self._not_found("trade_fair")
        return TradeFairRead.model_validate(row)

    def get_trade_fair_location_projection(
        self,
        tenant_id: str,
        row_id: str,
        _actor: RequestAuthorizationContext,
    ) -> TradeFairLocationProjectionRead:
        row = self.repository.get_trade_fair(tenant_id, row_id)
        if row is None:
            raise self._not_found("trade_fair")
        return TradeFairLocationProjectionRead(
            id=row.id,
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            fair_no=row.fair_no,
            name=row.name,
            venue_id=row.venue_id,
            venue_name=row.venue.name if row.venue is not None else None,
            postal_address_id=row.address_id,
            postal_address=self._address_read(row.address),
            operational_geo_point=self._geo_point(row.latitude, row.longitude, source="trade_fair"),
            timezone=row.timezone,
            start_date=row.start_date,
            end_date=row.end_date,
        )

    def create_trade_fair(self, tenant_id: str, payload: TradeFairCreate, actor: RequestAuthorizationContext) -> TradeFairRead:
        self._validate_customer_path(tenant_id, payload.customer_id)
        self._validate_address(payload.address_id)
        self._validate_trade_fair_window(payload.start_date, payload.end_date)
        self._validate_venue_scope(tenant_id, payload.customer_id, payload.venue_id)
        if self.repository.find_trade_fair_by_no(tenant_id, payload.fair_no) is not None:
            raise self._duplicate("trade_fair")
        row = self.repository.create_trade_fair(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.trade_fair.created", "ops.trade_fair", row.id, tenant_id, after_json=self._snapshot(row))
        return TradeFairRead.model_validate(row)

    def update_trade_fair(self, tenant_id: str, row_id: str, payload: TradeFairUpdate, actor: RequestAuthorizationContext) -> TradeFairRead:
        current = self.repository.get_trade_fair(tenant_id, row_id)
        if current is None:
            raise self._not_found("trade_fair")
        before_json = self._snapshot(current)
        next_customer_id = self._field_value(payload, "customer_id", current.customer_id)
        self._validate_customer_path(tenant_id, next_customer_id)
        self._validate_address(self._field_value(payload, "address_id", current.address_id))
        self._validate_trade_fair_window(
            self._field_value(payload, "start_date", current.start_date),
            self._field_value(payload, "end_date", current.end_date),
        )
        self._validate_venue_scope(tenant_id, next_customer_id, self._field_value(payload, "venue_id", current.venue_id))
        next_no = self._field_value(payload, "fair_no", current.fair_no)
        if self.repository.find_trade_fair_by_no(tenant_id, next_no, exclude_id=row_id) is not None:
            raise self._duplicate("trade_fair")
        row = self.repository.update_trade_fair(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("trade_fair")
        self._record_event(actor, "planning.trade_fair.updated", "ops.trade_fair", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return TradeFairRead.model_validate(row)

    def list_trade_fair_zones(self, tenant_id: str, trade_fair_id: str, _actor: RequestAuthorizationContext) -> list[TradeFairZoneRead]:
        self._require_trade_fair(tenant_id, trade_fair_id)
        return [TradeFairZoneRead.model_validate(row) for row in self.repository.list_trade_fair_zones(tenant_id, trade_fair_id)]

    def create_trade_fair_zone(
        self,
        tenant_id: str,
        trade_fair_id: str,
        payload: TradeFairZoneCreate,
        actor: RequestAuthorizationContext,
    ) -> TradeFairZoneRead:
        self._require_trade_fair(tenant_id, trade_fair_id)
        if payload.trade_fair_id != trade_fair_id:
            raise ApiException(400, "planning.trade_fair_zone.trade_fair_mismatch", "errors.planning.trade_fair_zone.trade_fair_mismatch")
        if self.repository.find_trade_fair_zone(tenant_id, trade_fair_id, payload.zone_type_code, payload.zone_code) is not None:
            raise ApiException(409, "planning.trade_fair_zone.duplicate_tuple", "errors.planning.trade_fair_zone.duplicate_tuple")
        row = self.repository.create_trade_fair_zone(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.trade_fair_zone.created", "ops.trade_fair_zone", row.id, tenant_id, after_json=self._snapshot(row))
        return TradeFairZoneRead.model_validate(row)

    def update_trade_fair_zone(
        self,
        tenant_id: str,
        trade_fair_id: str,
        row_id: str,
        payload: TradeFairZoneUpdate,
        actor: RequestAuthorizationContext,
    ) -> TradeFairZoneRead:
        self._require_trade_fair(tenant_id, trade_fair_id)
        current = self.repository.get_trade_fair_zone(tenant_id, row_id)
        if current is None or current.trade_fair_id != trade_fair_id:
            raise self._not_found("trade_fair_zone")
        before_json = self._snapshot(current)
        zone_type_code = self._field_value(payload, "zone_type_code", current.zone_type_code)
        zone_code = self._field_value(payload, "zone_code", current.zone_code)
        if self.repository.find_trade_fair_zone(tenant_id, trade_fair_id, zone_type_code, zone_code, exclude_id=row_id) is not None:
            raise ApiException(409, "planning.trade_fair_zone.duplicate_tuple", "errors.planning.trade_fair_zone.duplicate_tuple")
        row = self.repository.update_trade_fair_zone(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("trade_fair_zone")
        self._record_event(actor, "planning.trade_fair_zone.updated", "ops.trade_fair_zone", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return TradeFairZoneRead.model_validate(row)

    def list_patrol_routes(self, tenant_id: str, filters: OpsMasterFilter, _actor: RequestAuthorizationContext) -> list[PatrolRouteListItem]:
        return [PatrolRouteListItem.model_validate(row) for row in self.repository.list_patrol_routes(tenant_id, filters)]

    def get_patrol_route(self, tenant_id: str, row_id: str, _actor: RequestAuthorizationContext) -> PatrolRouteRead:
        row = self.repository.get_patrol_route(tenant_id, row_id)
        if row is None:
            raise self._not_found("patrol_route")
        return PatrolRouteRead.model_validate(row)

    def get_patrol_route_location_projection(
        self,
        tenant_id: str,
        row_id: str,
        _actor: RequestAuthorizationContext,
    ) -> PatrolRouteLocationProjectionRead:
        row = self.repository.get_patrol_route(tenant_id, row_id)
        if row is None:
            raise self._not_found("patrol_route")
        linked_site = None
        if row.site is not None:
            linked_site = SiteCrosslinkRead(
                id=row.site.id,
                site_no=row.site.site_no,
                name=row.site.name,
                watchbook_enabled=row.site.watchbook_enabled,
                operational_geo_point=self._geo_point(row.site.latitude, row.site.longitude, source="site"),
            )
        return PatrolRouteLocationProjectionRead(
            id=row.id,
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            route_no=row.route_no,
            name=row.name,
            linked_site=linked_site,
            meeting_address_id=row.meeting_address_id,
            meeting_address=self._address_read(row.meeting_address),
            start_point_text=row.start_point_text,
            end_point_text=row.end_point_text,
            travel_policy_code=row.travel_policy_code,
            checkpoint_geo_points=[
                PatrolCheckpointGeoPointRead(
                    id=checkpoint.id,
                    sequence_no=checkpoint.sequence_no,
                    checkpoint_code=checkpoint.checkpoint_code,
                    label=checkpoint.label,
                    geo_point=OperationalGeoPointRead(
                        latitude=checkpoint.latitude,
                        longitude=checkpoint.longitude,
                        source="patrol_checkpoint",
                    ),
                    scan_type_code=checkpoint.scan_type_code,
                    minimum_dwell_seconds=checkpoint.minimum_dwell_seconds,
                )
                for checkpoint in row.checkpoints
            ],
        )

    def create_patrol_route(self, tenant_id: str, payload: PatrolRouteCreate, actor: RequestAuthorizationContext) -> PatrolRouteRead:
        self._validate_customer_path(tenant_id, payload.customer_id)
        self._validate_address(payload.meeting_address_id)
        self._validate_route_site_scope(tenant_id, payload.customer_id, payload.site_id)
        if self.repository.find_patrol_route_by_no(tenant_id, payload.route_no) is not None:
            raise self._duplicate("patrol_route")
        row = self.repository.create_patrol_route(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.patrol_route.created", "ops.patrol_route", row.id, tenant_id, after_json=self._snapshot(row))
        return PatrolRouteRead.model_validate(row)

    def update_patrol_route(self, tenant_id: str, row_id: str, payload: PatrolRouteUpdate, actor: RequestAuthorizationContext) -> PatrolRouteRead:
        current = self.repository.get_patrol_route(tenant_id, row_id)
        if current is None:
            raise self._not_found("patrol_route")
        before_json = self._snapshot(current)
        next_customer_id = self._field_value(payload, "customer_id", current.customer_id)
        self._validate_customer_path(tenant_id, next_customer_id)
        self._validate_address(self._field_value(payload, "meeting_address_id", current.meeting_address_id))
        self._validate_route_site_scope(tenant_id, next_customer_id, self._field_value(payload, "site_id", current.site_id))
        next_no = self._field_value(payload, "route_no", current.route_no)
        if self.repository.find_patrol_route_by_no(tenant_id, next_no, exclude_id=row_id) is not None:
            raise self._duplicate("patrol_route")
        row = self.repository.update_patrol_route(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("patrol_route")
        self._record_event(actor, "planning.patrol_route.updated", "ops.patrol_route", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return PatrolRouteRead.model_validate(row)

    def list_patrol_checkpoints(self, tenant_id: str, patrol_route_id: str, _actor: RequestAuthorizationContext) -> list[PatrolCheckpointRead]:
        self._require_patrol_route(tenant_id, patrol_route_id)
        return [PatrolCheckpointRead.model_validate(row) for row in self.repository.list_patrol_checkpoints(tenant_id, patrol_route_id)]

    def create_patrol_checkpoint(
        self,
        tenant_id: str,
        patrol_route_id: str,
        payload: PatrolCheckpointCreate,
        actor: RequestAuthorizationContext,
    ) -> PatrolCheckpointRead:
        self._require_patrol_route(tenant_id, patrol_route_id)
        if payload.patrol_route_id != patrol_route_id:
            raise ApiException(400, "planning.patrol_checkpoint.route_mismatch", "errors.planning.patrol_checkpoint.route_mismatch")
        self._validate_checkpoint_constraints(tenant_id, patrol_route_id, payload.sequence_no, payload.checkpoint_code)
        row = self.repository.create_patrol_checkpoint(tenant_id, payload, actor.user_id)
        self._record_event(actor, "planning.patrol_checkpoint.created", "ops.patrol_checkpoint", row.id, tenant_id, after_json=self._snapshot(row))
        return PatrolCheckpointRead.model_validate(row)

    def update_patrol_checkpoint(
        self,
        tenant_id: str,
        patrol_route_id: str,
        row_id: str,
        payload: PatrolCheckpointUpdate,
        actor: RequestAuthorizationContext,
    ) -> PatrolCheckpointRead:
        self._require_patrol_route(tenant_id, patrol_route_id)
        current = self.repository.get_patrol_checkpoint(tenant_id, row_id)
        if current is None or current.patrol_route_id != patrol_route_id:
            raise self._not_found("patrol_checkpoint")
        before_json = self._snapshot(current)
        sequence_no = self._field_value(payload, "sequence_no", current.sequence_no)
        checkpoint_code = self._field_value(payload, "checkpoint_code", current.checkpoint_code)
        self._validate_checkpoint_constraints(tenant_id, patrol_route_id, sequence_no, checkpoint_code, exclude_id=row_id)
        row = self.repository.update_patrol_checkpoint(tenant_id, row_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("patrol_checkpoint")
        self._record_event(actor, "planning.patrol_checkpoint.updated", "ops.patrol_checkpoint", row.id, tenant_id, before_json=before_json, after_json=self._snapshot(row))
        return PatrolCheckpointRead.model_validate(row)

    def _validate_customer_path(self, tenant_id: str, customer_id: str) -> None:
        if self.repository.get_customer(tenant_id, customer_id) is None:
            raise ApiException(404, "planning.customer.not_found", "errors.planning.customer.not_found")

    def ensure_equipment_unit_of_measure_code(
        self,
        tenant_id: str,
        unit_of_measure_code: str,
        *,
        current_value: str | None = None,
    ) -> None:
        allowed_codes = {option.code for option in self.list_equipment_unit_options(tenant_id, self._system_actor(tenant_id))}
        if unit_of_measure_code in allowed_codes:
            return
        if current_value is not None and unit_of_measure_code == current_value:
            return
        raise ApiException(
            400,
            "planning.equipment_item.invalid_unit_of_measure_code",
            "errors.planning.equipment_item.invalid_unit_of_measure_code",
        )

    def _validate_address(self, address_id: str | None) -> None:
        if address_id is None:
            return
        if self.repository.get_address(address_id) is None:
            raise ApiException(404, "planning.address.not_found", "errors.planning.address.not_found")

    def _validate_trade_fair_window(self, start_date, end_date) -> None:
        if end_date < start_date:
            raise ApiException(400, "planning.trade_fair.invalid_window", "errors.planning.trade_fair.invalid_window")

    def _validate_venue_scope(self, tenant_id: str, customer_id: str, venue_id: str | None) -> None:
        if venue_id is None:
            return
        venue = self.repository.get_event_venue(tenant_id, venue_id)
        if venue is None:
            raise ApiException(404, "planning.event_venue.not_found", "errors.planning.event_venue.not_found")
        if venue.customer_id != customer_id:
            raise ApiException(400, "planning.trade_fair.venue_customer_mismatch", "errors.planning.trade_fair.venue_customer_mismatch")

    def _validate_route_site_scope(self, tenant_id: str, customer_id: str, site_id: str | None) -> None:
        if site_id is None:
            return
        site = self.repository.get_site(tenant_id, site_id)
        if site is None:
            raise ApiException(404, "planning.site.not_found", "errors.planning.site.not_found")
        if site.customer_id != customer_id:
            raise ApiException(400, "planning.patrol_route.site_customer_mismatch", "errors.planning.patrol_route.site_customer_mismatch")

    def _require_trade_fair(self, tenant_id: str, trade_fair_id: str) -> TradeFair:
        row = self.repository.get_trade_fair(tenant_id, trade_fair_id)
        if row is None:
            raise self._not_found("trade_fair")
        return row

    def _require_patrol_route(self, tenant_id: str, patrol_route_id: str) -> PatrolRoute:
        row = self.repository.get_patrol_route(tenant_id, patrol_route_id)
        if row is None:
            raise self._not_found("patrol_route")
        return row

    def _validate_checkpoint_constraints(
        self,
        tenant_id: str,
        patrol_route_id: str,
        sequence_no: int,
        checkpoint_code: str,
        *,
        exclude_id: str | None = None,
    ) -> None:
        if self.repository.find_patrol_checkpoint_by_sequence(tenant_id, patrol_route_id, sequence_no, exclude_id=exclude_id) is not None:
            raise ApiException(409, "planning.patrol_checkpoint.duplicate_sequence", "errors.planning.patrol_checkpoint.duplicate_sequence")
        if self.repository.find_patrol_checkpoint_by_code(tenant_id, patrol_route_id, checkpoint_code, exclude_id=exclude_id) is not None:
            raise ApiException(409, "planning.patrol_checkpoint.duplicate_code", "errors.planning.patrol_checkpoint.duplicate_code")

    def _not_found(self, resource: str) -> ApiException:
        return ApiException(404, f"planning.{resource}.not_found", f"errors.planning.{resource}.not_found")

    def _duplicate(self, resource: str) -> ApiException:
        resource_key = "requirement_type" if resource == "requirement_type" else resource
        return ApiException(409, f"planning.{resource}.duplicate", f"errors.planning.{resource_key}.duplicate_code")

    @staticmethod
    def _system_actor(tenant_id: str) -> RequestAuthorizationContext:
        return RequestAuthorizationContext(
            session_id="planning-system",
            user_id="planning-system",
            tenant_id=tenant_id,
            role_keys=frozenset({"tenant_admin"}),
            permission_keys=frozenset({"planning.ops.read"}),
            scopes=(),
            request_id="planning-system",
        )

    @staticmethod
    def _normalize_optional_customer_id(payload):
        if "customer_id" not in getattr(payload, "model_fields_set", set()):
            return payload
        if payload.customer_id != "":
            return payload
        return payload.model_copy(update={"customer_id": None})

    @staticmethod
    def _field_value(payload, field_name: str, current_value):
        return payload.model_dump(exclude_unset=True).get(field_name, current_value)

    @staticmethod
    def _address_read(address: Address | None):
        if address is None:
            return None
        from app.modules.core.schemas import AddressRead

        return AddressRead.model_validate(address)

    @staticmethod
    def _geo_point(latitude, longitude, *, source: str) -> OperationalGeoPointRead | None:
        if latitude is None or longitude is None:
            return None
        return OperationalGeoPointRead(latitude=latitude, longitude=longitude, source=source)

    @staticmethod
    def _snapshot(row) -> dict[str, object]:
        mapper = sa_inspect(row).mapper
        return {
            attribute.key: PlanningService._json_safe_value(getattr(row, attribute.key))
            for attribute in mapper.column_attrs
        }

    @classmethod
    def _json_safe_value(cls, value: object) -> object:
        if value is None or isinstance(value, bool | int | float | str):
            return value
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, datetime | date | time):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, Enum):
            return cls._json_safe_value(value.value)
        if isinstance(value, dict):
            return {str(key): cls._json_safe_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._json_safe_value(item) for item in value]
        if isinstance(value, tuple):
            return [cls._json_safe_value(item) for item in value]
        return value

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        *,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                user_id=actor.user_id,
                tenant_id=tenant_id,
                request_id=actor.request_id,
                session_id=actor.session_id,
            ),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=after_json,
        )
