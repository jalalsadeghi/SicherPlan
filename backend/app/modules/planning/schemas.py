"""Pydantic schemas for operational planning master data."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import ClassVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.core.schemas import AddressRead
from app.modules.platform_services.docs_schemas import DocumentRead


class OpsMasterFilter(BaseModel):
    search: str | None = None
    customer_id: str | None = None
    lifecycle_status: str | None = None
    include_archived: bool = False


class PlanningReferenceOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    code: str
    label: str
    description: str | None = None
    sort_order: int = 100


class RequirementTypeCreate(BaseModel):
    tenant_id: str
    customer_id: str | None = None
    code: str
    label: str
    default_planning_mode_code: str
    notes: str | None = Field(default=None, validation_alias=AliasChoices("notes", "description"))


class RequirementTypeUpdate(BaseModel):
    customer_id: str | None = None
    code: str | None = None
    label: str | None = None
    default_planning_mode_code: str | None = None
    notes: str | None = Field(default=None, validation_alias=AliasChoices("notes", "description"))
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EquipmentItemCreate(BaseModel):
    tenant_id: str
    customer_id: str | None = None
    code: str
    label: str
    unit_of_measure_code: str
    notes: str | None = Field(default=None, validation_alias=AliasChoices("notes", "description"))


class EquipmentItemUpdate(BaseModel):
    customer_id: str | None = None
    code: str | None = None
    label: str | None = None
    unit_of_measure_code: str | None = None
    notes: str | None = Field(default=None, validation_alias=AliasChoices("notes", "description"))
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class SiteCreate(BaseModel):
    tenant_id: str
    customer_id: str | None
    site_no: str
    name: str
    address_id: str | None = None
    timezone: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    watchbook_enabled: bool = False
    notes: str | None = None


class SiteUpdate(BaseModel):
    customer_id: str | None = None
    site_no: str | None = None
    name: str | None = None
    address_id: str | None = None
    timezone: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    watchbook_enabled: bool | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class EventVenueCreate(BaseModel):
    tenant_id: str
    customer_id: str | None
    venue_no: str
    name: str
    address_id: str | None = None
    timezone: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    notes: str | None = None


class EventVenueUpdate(BaseModel):
    customer_id: str | None = None
    venue_no: str | None = None
    name: str | None = None
    address_id: str | None = None
    timezone: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class TradeFairCreate(BaseModel):
    tenant_id: str
    customer_id: str
    venue_id: str | None = None
    fair_no: str
    name: str
    address_id: str | None = None
    timezone: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    start_date: date
    end_date: date
    notes: str | None = None


class TradeFairUpdate(BaseModel):
    customer_id: str | None = None
    venue_id: str | None = None
    fair_no: str | None = None
    name: str | None = None
    address_id: str | None = None
    timezone: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class PatrolRouteCreate(BaseModel):
    tenant_id: str
    customer_id: str
    site_id: str | None = None
    meeting_address_id: str | None = None
    route_no: str
    name: str
    start_point_text: str | None = None
    end_point_text: str | None = None
    travel_policy_code: str | None = None
    notes: str | None = None


class PatrolRouteUpdate(BaseModel):
    customer_id: str | None = None
    site_id: str | None = None
    meeting_address_id: str | None = None
    route_no: str | None = None
    name: str | None = None
    start_point_text: str | None = None
    end_point_text: str | None = None
    travel_policy_code: str | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class TradeFairZoneCreate(BaseModel):
    tenant_id: str
    trade_fair_id: str
    zone_type_code: str
    zone_code: str
    label: str
    notes: str | None = None


class TradeFairZoneUpdate(BaseModel):
    zone_type_code: str | None = None
    zone_code: str | None = None
    label: str | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class PatrolCheckpointCreate(BaseModel):
    tenant_id: str
    patrol_route_id: str
    sequence_no: int = Field(ge=1)
    checkpoint_code: str
    label: str
    latitude: Decimal
    longitude: Decimal
    scan_type_code: str
    expected_token_value: str | None = None
    minimum_dwell_seconds: int = Field(default=0, ge=0)
    notes: str | None = None


class PatrolCheckpointUpdate(BaseModel):
    sequence_no: int | None = Field(default=None, ge=1)
    checkpoint_code: str | None = None
    label: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    scan_type_code: str | None = None
    expected_token_value: str | None = None
    minimum_dwell_seconds: int | None = Field(default=None, ge=0)
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class RequirementTypeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str | None
    code: str
    label: str
    default_planning_mode_code: str
    status: str
    version_no: int


class RequirementTypeRead(RequirementTypeListItem):
    notes: str | None = Field(validation_alias=AliasChoices("notes", "description"))
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class EquipmentItemListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str | None
    code: str
    label: str
    unit_of_measure_code: str
    status: str
    version_no: int


class EquipmentItemRead(EquipmentItemListItem):
    notes: str | None = Field(validation_alias=AliasChoices("notes", "description"))
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class SiteListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    site_no: str
    name: str
    timezone: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    watchbook_enabled: bool
    status: str
    version_no: int


class SiteRead(SiteListItem):
    address_id: str | None
    notes: str | None
    address: AddressRead | None = None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class EventVenueListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    venue_no: str
    name: str
    timezone: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    status: str
    version_no: int


class EventVenueRead(EventVenueListItem):
    address_id: str | None
    notes: str | None
    address: AddressRead | None = None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class TradeFairZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    trade_fair_id: str
    zone_type_code: str
    zone_code: str
    label: str
    notes: str | None
    status: str
    version_no: int
    archived_at: datetime | None


class TradeFairListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    venue_id: str | None
    fair_no: str
    name: str
    timezone: str | None
    start_date: date
    end_date: date
    status: str
    version_no: int


class TradeFairRead(TradeFairListItem):
    address_id: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    notes: str | None
    address: AddressRead | None = None
    zones: list[TradeFairZoneRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class PatrolCheckpointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    patrol_route_id: str
    sequence_no: int
    checkpoint_code: str
    label: str
    latitude: Decimal
    longitude: Decimal
    scan_type_code: str
    expected_token_value: str | None
    minimum_dwell_seconds: int
    notes: str | None
    status: str
    version_no: int
    archived_at: datetime | None


class PatrolRouteListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    site_id: str | None
    route_no: str
    name: str
    travel_policy_code: str | None
    status: str
    version_no: int


class PatrolRouteRead(PatrolRouteListItem):
    meeting_address_id: str | None
    start_point_text: str | None
    end_point_text: str | None
    notes: str | None
    meeting_address: AddressRead | None = None
    checkpoints: list[PatrolCheckpointRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class OperationalGeoPointRead(BaseModel):
    latitude: Decimal
    longitude: Decimal
    source: str


class PatrolCheckpointGeoPointRead(BaseModel):
    id: str
    sequence_no: int
    checkpoint_code: str
    label: str
    geo_point: OperationalGeoPointRead
    scan_type_code: str
    minimum_dwell_seconds: int


class SiteCrosslinkRead(BaseModel):
    id: str
    site_no: str
    name: str
    watchbook_enabled: bool
    operational_geo_point: OperationalGeoPointRead | None = None


class SiteLocationProjectionRead(BaseModel):
    id: str
    tenant_id: str
    customer_id: str
    site_no: str
    name: str
    watchbook_enabled: bool
    postal_address_id: str | None
    postal_address: AddressRead | None = None
    operational_geo_point: OperationalGeoPointRead | None = None
    timezone: str | None


class EventVenueLocationProjectionRead(BaseModel):
    id: str
    tenant_id: str
    customer_id: str
    venue_no: str
    name: str
    postal_address_id: str | None
    postal_address: AddressRead | None = None
    operational_geo_point: OperationalGeoPointRead | None = None
    timezone: str | None


class TradeFairLocationProjectionRead(BaseModel):
    id: str
    tenant_id: str
    customer_id: str
    fair_no: str
    name: str
    venue_id: str | None
    venue_name: str | None = None
    postal_address_id: str | None
    postal_address: AddressRead | None = None
    operational_geo_point: OperationalGeoPointRead | None = None
    timezone: str | None
    start_date: date
    end_date: date


class PatrolRouteLocationProjectionRead(BaseModel):
    id: str
    tenant_id: str
    customer_id: str
    route_no: str
    name: str
    linked_site: SiteCrosslinkRead | None = None
    meeting_address_id: str | None
    meeting_address: AddressRead | None = None
    start_point_text: str | None
    end_point_text: str | None
    travel_policy_code: str | None
    checkpoint_geo_points: list[PatrolCheckpointGeoPointRead] = Field(default_factory=list)


class CustomerOrderFilter(BaseModel):
    PLANNING_ENTITY_TYPES: ClassVar[frozenset[str]] = frozenset({"site", "event_venue", "trade_fair", "patrol_route"})

    search: str | None = None
    customer_id: str | None = None
    lifecycle_status: str | None = None
    release_state: str | None = None
    service_from: date | None = None
    service_to: date | None = None
    planning_entity_type: str | None = None
    planning_entity_id: str | None = None
    include_archived: bool = False

    @field_validator("planning_entity_type")
    @classmethod
    def normalize_planning_entity_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        if normalized not in cls.PLANNING_ENTITY_TYPES:
            raise ValueError("Invalid planning entity type")
        return normalized

    @field_validator("planning_entity_id")
    @classmethod
    def normalize_planning_entity_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def ignore_incomplete_planning_entity_filter(self) -> "CustomerOrderFilter":
        if bool(self.planning_entity_type) != bool(self.planning_entity_id):
            self.planning_entity_type = None
            self.planning_entity_id = None
        return self


class OrderEquipmentLineCreate(BaseModel):
    tenant_id: str
    order_id: str
    equipment_item_id: str
    required_qty: int = Field(ge=1)
    notes: str | None = None


class OrderEquipmentLineUpdate(BaseModel):
    equipment_item_id: str | None = None
    required_qty: int | None = Field(default=None, ge=1)
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class OrderRequirementLineCreate(BaseModel):
    tenant_id: str
    order_id: str
    requirement_type_id: str
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    min_qty: int = Field(default=0, ge=0)
    target_qty: int = Field(ge=0)
    notes: str | None = None


class OrderRequirementLineUpdate(BaseModel):
    requirement_type_id: str | None = None
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    min_qty: int | None = Field(default=None, ge=0)
    target_qty: int | None = Field(default=None, ge=0)
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class CustomerOrderCreate(BaseModel):
    tenant_id: str
    customer_id: str
    requirement_type_id: str
    patrol_route_id: str | None = None
    order_no: str
    title: str
    service_category_code: str
    security_concept_text: str | None = None
    service_from: date
    service_to: date
    release_state: str = "draft"
    notes: str | None = None


class CustomerOrderUpdate(BaseModel):
    customer_id: str | None = None
    requirement_type_id: str | None = None
    patrol_route_id: str | None = None
    order_no: str | None = None
    title: str | None = None
    service_category_code: str | None = None
    security_concept_text: str | None = None
    service_from: date | None = None
    service_to: date | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class CustomerOrderReleaseStateUpdate(BaseModel):
    release_state: str
    version_no: int


class CustomerOrderAttachmentCreate(BaseModel):
    tenant_id: str
    title: str
    file_name: str
    content_type: str
    content_base64: str
    document_type_key: str | None = None
    relation_type: str = "attachment"
    label: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class CustomerOrderAttachmentLinkCreate(BaseModel):
    tenant_id: str
    document_id: str
    relation_type: str = "attachment"
    label: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class PlanningRecordAttachmentCreate(BaseModel):
    tenant_id: str
    title: str
    file_name: str
    content_type: str
    content_base64: str
    relation_type: str = "attachment"
    label: str | None = None
    document_type_key: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class PlanningRecordAttachmentLinkCreate(BaseModel):
    tenant_id: str
    document_id: str
    relation_type: str = "attachment"
    label: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class OrderEquipmentLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    order_id: str
    equipment_item_id: str
    required_qty: int
    notes: str | None
    status: str
    version_no: int
    archived_at: datetime | None


class OrderRequirementLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    order_id: str
    requirement_type_id: str
    function_type_id: str | None
    qualification_type_id: str | None
    min_qty: int
    target_qty: int
    notes: str | None
    status: str
    version_no: int
    archived_at: datetime | None


class CustomerOrderListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    requirement_type_id: str
    patrol_route_id: str | None
    order_no: str
    title: str
    service_category_code: str
    service_from: date
    service_to: date
    release_state: str
    released_at: datetime | None
    status: str
    version_no: int


class CustomerOrderRead(CustomerOrderListItem):
    security_concept_text: str | None
    notes: str | None
    released_by_user_id: str | None
    equipment_lines: list[OrderEquipmentLineRead] = Field(default_factory=list)
    requirement_lines: list[OrderRequirementLineRead] = Field(default_factory=list)
    attachments: list[DocumentRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class PlanningRecordFilter(BaseModel):
    search: str | None = None
    customer_id: str | None = None
    order_id: str | None = None
    planning_mode_code: str | None = None
    lifecycle_status: str | None = None
    release_state: str | None = None
    dispatcher_user_id: str | None = None
    planning_from: date | None = None
    planning_to: date | None = None
    include_archived: bool = False


class EventPlanDetailCreate(BaseModel):
    event_venue_id: str
    setup_note: str | None = None


class EventPlanDetailUpdate(BaseModel):
    event_venue_id: str | None = None
    setup_note: str | None = None


class SitePlanDetailCreate(BaseModel):
    site_id: str
    watchbook_scope_note: str | None = None


class SitePlanDetailUpdate(BaseModel):
    site_id: str | None = None
    watchbook_scope_note: str | None = None


class TradeFairPlanDetailCreate(BaseModel):
    trade_fair_id: str
    trade_fair_zone_id: str | None = None
    stand_note: str | None = None


class TradeFairPlanDetailUpdate(BaseModel):
    trade_fair_id: str | None = None
    trade_fair_zone_id: str | None = None
    stand_note: str | None = None


class PatrolPlanDetailCreate(BaseModel):
    patrol_route_id: str
    execution_note: str | None = None


class PatrolPlanDetailUpdate(BaseModel):
    patrol_route_id: str | None = None
    execution_note: str | None = None


class PlanningRecordCreate(BaseModel):
    tenant_id: str
    order_id: str
    parent_planning_record_id: str | None = None
    dispatcher_user_id: str | None = None
    planning_mode_code: str
    name: str
    planning_from: date
    planning_to: date
    release_state: str = "draft"
    notes: str | None = None
    event_detail: EventPlanDetailCreate | None = None
    site_detail: SitePlanDetailCreate | None = None
    trade_fair_detail: TradeFairPlanDetailCreate | None = None
    patrol_detail: PatrolPlanDetailCreate | None = None


class PlanningRecordUpdate(BaseModel):
    dispatcher_user_id: str | None = None
    name: str | None = None
    planning_from: date | None = None
    planning_to: date | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None
    event_detail: EventPlanDetailUpdate | None = None
    site_detail: SitePlanDetailUpdate | None = None
    trade_fair_detail: TradeFairPlanDetailUpdate | None = None
    patrol_detail: PatrolPlanDetailUpdate | None = None


class PlanningRecordReleaseStateUpdate(BaseModel):
    release_state: str
    version_no: int


class EventPlanDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    planning_record_id: str
    tenant_id: str
    event_venue_id: str
    setup_note: str | None


class SitePlanDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    planning_record_id: str
    tenant_id: str
    site_id: str
    watchbook_scope_note: str | None


class TradeFairPlanDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    planning_record_id: str
    tenant_id: str
    trade_fair_id: str
    trade_fair_zone_id: str | None
    stand_note: str | None


class PatrolPlanDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    planning_record_id: str
    tenant_id: str
    patrol_route_id: str
    execution_note: str | None


class PlanningRecordListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    order_id: str
    parent_planning_record_id: str | None
    dispatcher_user_id: str | None
    planning_mode_code: str
    name: str
    planning_from: date
    planning_to: date
    release_state: str
    released_at: datetime | None
    created_at: datetime
    status: str
    version_no: int


class PlanningRecordRead(PlanningRecordListItem):
    released_by_user_id: str | None
    notes: str | None
    event_detail: EventPlanDetailRead | None = None
    site_detail: SitePlanDetailRead | None = None
    trade_fair_detail: TradeFairPlanDetailRead | None = None
    patrol_detail: PatrolPlanDetailRead | None = None
    attachments: list[DocumentRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None


class PlanningDispatcherCandidateRead(BaseModel):
    id: str
    tenant_id: str
    username: str
    email: str | None
    full_name: str
    status: str
    role_keys: list[str] = Field(default_factory=list)
    archived_at: datetime | None


class PlanningCommercialIssueRead(BaseModel):
    code: str
    severity: str
    message_key: str


class PlanningCommercialLinkRead(BaseModel):
    tenant_id: str
    customer_id: str
    order_id: str
    planning_record_id: str | None = None
    billing_profile_id: str | None = None
    default_invoice_party_id: str | None = None
    shipping_method_code: str | None = None
    invoice_layout_code: str | None = None
    dunning_policy_code: str | None = None
    e_invoice_enabled: bool = False
    rate_card_ids: list[str] = Field(default_factory=list)
    is_release_ready: bool = False
    blocking_issues: list[PlanningCommercialIssueRead] = Field(default_factory=list)
    warning_issues: list[PlanningCommercialIssueRead] = Field(default_factory=list)


class PlanningOpsImportDryRunRequest(BaseModel):
    tenant_id: str
    entity_key: str
    csv_content_base64: str = Field(min_length=1)


class PlanningOpsImportExecuteRequest(PlanningOpsImportDryRunRequest):
    continue_on_error: bool = True


class PlanningOpsImportRowResult(BaseModel):
    row_no: int
    entity_ref: str | None = None
    status: str
    messages: list[str] = Field(default_factory=list)
    entity_id: str | None = None


class PlanningOpsImportDryRunResult(BaseModel):
    tenant_id: str
    entity_key: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[PlanningOpsImportRowResult]


class PlanningOpsImportExecuteResult(BaseModel):
    tenant_id: str
    entity_key: str
    job_id: str
    job_status: str
    total_rows: int
    invalid_rows: int
    created_rows: int
    updated_rows: int
    result_document_ids: list[str] = Field(default_factory=list)
    rows: list[PlanningOpsImportRowResult]


class ShiftTemplateCreate(BaseModel):
    tenant_id: str
    code: str
    label: str
    local_start_time: time
    local_end_time: time
    default_break_minutes: int = Field(default=0, ge=0)
    shift_type_code: str
    meeting_point: str | None = None
    location_text: str | None = None
    notes: str | None = None


class ShiftTemplateUpdate(BaseModel):
    code: str | None = None
    label: str | None = None
    local_start_time: time | None = None
    local_end_time: time | None = None
    default_break_minutes: int | None = Field(default=None, ge=0)
    shift_type_code: str | None = None
    meeting_point: str | None = None
    location_text: str | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class ShiftTemplateListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: str
    label: str
    local_start_time: time
    local_end_time: time
    default_break_minutes: int
    shift_type_code: str
    status: str
    version_no: int


class ShiftTemplateRead(ShiftTemplateListItem):
    meeting_point: str | None
    location_text: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class ShiftTypeOptionRead(BaseModel):
    code: str
    label: str


class ShiftPlanFilter(BaseModel):
    planning_record_id: str | None = None
    workforce_scope_code: str | None = None
    lifecycle_status: str | None = None
    include_archived: bool = False


class ShiftPlanCreate(BaseModel):
    tenant_id: str
    planning_record_id: str
    name: str
    workforce_scope_code: str = "internal"
    planning_from: date
    planning_to: date
    remarks: str | None = None


class ShiftPlanUpdate(BaseModel):
    name: str | None = None
    workforce_scope_code: str | None = None
    planning_from: date | None = None
    planning_to: date | None = None
    remarks: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class ShiftSeriesExceptionCreate(BaseModel):
    tenant_id: str
    exception_date: date
    action_code: str
    override_local_start_time: time | None = None
    override_local_end_time: time | None = None
    override_break_minutes: int | None = Field(default=None, ge=0)
    override_shift_type_code: str | None = None
    override_meeting_point: str | None = None
    override_location_text: str | None = None
    customer_visible_flag: bool | None = None
    subcontractor_visible_flag: bool | None = None
    stealth_mode_flag: bool | None = None
    notes: str | None = None


class ShiftSeriesExceptionUpdate(BaseModel):
    action_code: str | None = None
    override_local_start_time: time | None = None
    override_local_end_time: time | None = None
    override_break_minutes: int | None = Field(default=None, ge=0)
    override_shift_type_code: str | None = None
    override_meeting_point: str | None = None
    override_location_text: str | None = None
    customer_visible_flag: bool | None = None
    subcontractor_visible_flag: bool | None = None
    stealth_mode_flag: bool | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class ShiftSeriesExceptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    shift_series_id: str
    exception_date: date
    action_code: str
    override_local_start_time: time | None
    override_local_end_time: time | None
    override_break_minutes: int | None
    override_shift_type_code: str | None
    override_meeting_point: str | None
    override_location_text: str | None
    customer_visible_flag: bool | None
    subcontractor_visible_flag: bool | None
    stealth_mode_flag: bool | None
    notes: str | None
    status: str
    version_no: int
    archived_at: datetime | None


class ShiftSeriesCreate(BaseModel):
    tenant_id: str
    shift_plan_id: str
    shift_template_id: str
    label: str
    recurrence_code: str = "daily"
    interval_count: int = Field(default=1, ge=1)
    weekday_mask: str | None = None
    timezone: str
    date_from: date
    date_to: date
    default_break_minutes: int | None = Field(default=None, ge=0)
    shift_type_code: str | None = None
    meeting_point: str | None = None
    location_text: str | None = None
    customer_visible_flag: bool = False
    subcontractor_visible_flag: bool = False
    stealth_mode_flag: bool = False
    release_state: str = "draft"
    notes: str | None = None


class ShiftSeriesUpdate(BaseModel):
    label: str | None = None
    recurrence_code: str | None = None
    interval_count: int | None = Field(default=None, ge=1)
    weekday_mask: str | None = None
    timezone: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    default_break_minutes: int | None = Field(default=None, ge=0)
    shift_type_code: str | None = None
    meeting_point: str | None = None
    location_text: str | None = None
    customer_visible_flag: bool | None = None
    subcontractor_visible_flag: bool | None = None
    stealth_mode_flag: bool | None = None
    release_state: str | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class ShiftSeriesGenerationRequest(BaseModel):
    from_date: date | None = None
    to_date: date | None = None
    regenerate_existing: bool = False


class ShiftSeriesListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    shift_plan_id: str
    shift_template_id: str
    label: str
    recurrence_code: str
    interval_count: int
    weekday_mask: str | None
    timezone: str
    date_from: date
    date_to: date
    release_state: str
    customer_visible_flag: bool
    subcontractor_visible_flag: bool
    stealth_mode_flag: bool
    status: str
    version_no: int


class ShiftSeriesRead(ShiftSeriesListItem):
    default_break_minutes: int | None
    shift_type_code: str | None
    meeting_point: str | None
    location_text: str | None
    notes: str | None
    exceptions: list[ShiftSeriesExceptionRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class ShiftListFilter(BaseModel):
    shift_plan_id: str | None = None
    planning_record_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    shift_type_code: str | None = None
    release_state: str | None = None
    visibility_state: str | None = None
    lifecycle_status: str | None = None
    include_archived: bool = False


class ShiftCreate(BaseModel):
    tenant_id: str
    shift_plan_id: str
    shift_series_id: str | None = None
    occurrence_date: date | None = None
    starts_at: datetime
    ends_at: datetime
    break_minutes: int = Field(default=0, ge=0)
    shift_type_code: str
    location_text: str | None = None
    meeting_point: str | None = None
    release_state: str = "draft"
    customer_visible_flag: bool = False
    subcontractor_visible_flag: bool = False
    stealth_mode_flag: bool = False
    source_kind_code: str = "manual"
    notes: str | None = None


class ShiftUpdate(BaseModel):
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    break_minutes: int | None = Field(default=None, ge=0)
    shift_type_code: str | None = None
    location_text: str | None = None
    meeting_point: str | None = None
    release_state: str | None = None
    customer_visible_flag: bool | None = None
    subcontractor_visible_flag: bool | None = None
    stealth_mode_flag: bool | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None
    notes: str | None = None


class ShiftCopyRequest(BaseModel):
    source_from: date
    source_to: date
    target_from: date
    duplicate_mode: str = "skip_existing"
    include_generated: bool = True
    include_manual: bool = True


class ShiftCopyResult(BaseModel):
    tenant_id: str
    shift_plan_id: str
    copied_count: int
    skipped_count: int
    target_from: date


class ShiftPlanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    planning_record_id: str
    name: str
    workforce_scope_code: str
    planning_from: date
    planning_to: date
    status: str
    version_no: int


class ShiftListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    shift_plan_id: str
    shift_series_id: str | None
    occurrence_date: date | None
    starts_at: datetime
    ends_at: datetime
    break_minutes: int
    shift_type_code: str
    location_text: str | None
    meeting_point: str | None
    release_state: str
    customer_visible_flag: bool
    subcontractor_visible_flag: bool
    stealth_mode_flag: bool
    source_kind_code: str
    status: str
    version_no: int


class ShiftRead(ShiftListItem):
    released_at: datetime | None
    released_by_user_id: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class ShiftReleaseStateUpdate(BaseModel):
    release_state: str
    version_no: int | None = None


class ShiftVisibilityUpdate(BaseModel):
    customer_visible_flag: bool | None = None
    subcontractor_visible_flag: bool | None = None
    version_no: int | None = None


class ShiftReleaseDiagnosticsRead(BaseModel):
    tenant_id: str
    shift_id: str
    release_state: str
    customer_visible_flag: bool
    subcontractor_visible_flag: bool
    employee_visible: bool
    blocking_count: int
    warning_count: int
    issues: list["PlanningValidationResult"] = Field(default_factory=list)


class PlanningOutputGenerateRequest(BaseModel):
    tenant_id: str
    variant_code: str = Field(min_length=1, max_length=40)
    audience_code: str = Field(default="internal", min_length=1, max_length=40)
    regenerate: bool = False


class PlanningOutputDocumentRead(BaseModel):
    document_id: str
    owner_type: str
    owner_id: str
    variant_code: str
    audience_code: str
    title: str
    relation_type: str
    current_version_no: int
    file_name: str
    content_type: str
    generated_at: datetime
    is_revision_safe_pdf: bool


class PlanningDispatchRecipientPreviewRead(BaseModel):
    recipient_kind: str
    audience_code: str
    audience_ref: str
    destination: str
    display_name: str | None = None
    redacted: bool = False
    metadata_json: dict[str, object] = Field(default_factory=dict)


class PlanningDispatchPreviewRead(BaseModel):
    tenant_id: str
    shift_id: str
    channel: str
    template_key: str
    language_code: str
    audience_codes: list[str] = Field(default_factory=list)
    subject_preview: str | None = None
    body_preview: str
    redacted: bool
    recipients: list[PlanningDispatchRecipientPreviewRead] = Field(default_factory=list)


class PlanningDispatchCreate(BaseModel):
    tenant_id: str
    shift_id: str
    channel: str = Field(default="email", min_length=1, max_length=40)
    language_code: str = Field(default="de", min_length=2, max_length=8)
    template_key: str = Field(default="planning.dispatch.shift_update", min_length=1, max_length=120)
    audience_codes: list[str] = Field(default_factory=list)
    team_ids: list[str] = Field(default_factory=list)
    attachment_document_ids: list[str] = Field(default_factory=list)
    extra_placeholders: dict[str, object] = Field(default_factory=dict)


class PlanningReleasedDocumentRefRead(BaseModel):
    document_id: str
    title: str
    file_name: str | None = None
    content_type: str | None = None
    current_version_no: int | None = None
    relation_type: str = "deployment_output"


class PlanningReleasedCustomerScheduleRead(BaseModel):
    id: str
    customer_id: str
    order_id: str
    schedule_date: date
    shift_label: str
    site_label: str | None = None
    released_at: datetime
    status: str
    documents: list[PlanningReleasedDocumentRefRead] = Field(default_factory=list)


class PlanningReleasedSubcontractorScheduleRead(BaseModel):
    id: str
    subcontractor_id: str
    position_id: str
    shift_label: str
    schedule_date: date
    work_start: datetime
    work_end: datetime
    location_label: str | None = None
    confirmation_status: str
    documents: list[PlanningReleasedDocumentRefRead] = Field(default_factory=list)


class ShiftPlanRead(ShiftPlanListItem):
    remarks: str | None
    series_rows: list[ShiftSeriesListItem] = Field(default_factory=list)
    shifts: list[ShiftListItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class PlanningBoardShiftListItem(BaseModel):
    id: str
    tenant_id: str
    planning_record_id: str
    shift_plan_id: str
    order_id: str
    order_no: str
    planning_record_name: str
    planning_mode_code: str
    workforce_scope_code: str
    starts_at: datetime
    ends_at: datetime
    shift_type_code: str
    release_state: str
    status: str
    customer_visible_flag: bool
    subcontractor_visible_flag: bool
    stealth_mode_flag: bool
    location_text: str | None
    meeting_point: str | None


class PlanningBoardFilter(BaseModel):
    planning_record_id: str | None = None
    order_id: str | None = None
    date_from: datetime
    date_to: datetime
    planning_mode_code: str | None = None
    workforce_scope_code: str | None = None
    release_state: str | None = None
    visibility_state: str | None = None


class DemandGroupCreate(BaseModel):
    tenant_id: str
    shift_id: str
    function_type_id: str
    qualification_type_id: str | None = None
    min_qty: int = Field(ge=0)
    target_qty: int = Field(ge=0)
    mandatory_flag: bool = True
    sort_order: int = 100
    remark: str | None = None


class DemandGroupUpdate(BaseModel):
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    min_qty: int | None = Field(default=None, ge=0)
    target_qty: int | None = Field(default=None, ge=0)
    mandatory_flag: bool | None = None
    sort_order: int | None = None
    remark: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class TeamCreate(BaseModel):
    tenant_id: str
    planning_record_id: str | None = None
    shift_id: str | None = None
    name: str
    role_label: str | None = None
    notes: str | None = None


class TeamUpdate(BaseModel):
    planning_record_id: str | None = None
    shift_id: str | None = None
    name: str | None = None
    role_label: str | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class TeamMemberCreate(BaseModel):
    tenant_id: str
    team_id: str
    employee_id: str | None = None
    subcontractor_worker_id: str | None = None
    role_label: str | None = None
    is_team_lead: bool = False
    valid_from: datetime
    valid_to: datetime | None = None
    notes: str | None = None


class TeamMemberUpdate(BaseModel):
    employee_id: str | None = None
    subcontractor_worker_id: str | None = None
    role_label: str | None = None
    is_team_lead: bool | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class AssignmentCreate(BaseModel):
    tenant_id: str
    shift_id: str
    demand_group_id: str
    team_id: str | None = None
    employee_id: str | None = None
    subcontractor_worker_id: str | None = None
    assignment_status_code: str = "assigned"
    assignment_source_code: str = "dispatcher"
    offered_at: datetime | None = None
    confirmed_at: datetime | None = None
    remarks: str | None = None


class AssignmentUpdate(BaseModel):
    team_id: str | None = None
    employee_id: str | None = None
    subcontractor_worker_id: str | None = None
    assignment_status_code: str | None = None
    assignment_source_code: str | None = None
    offered_at: datetime | None = None
    confirmed_at: datetime | None = None
    remarks: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class SubcontractorReleaseCreate(BaseModel):
    tenant_id: str
    shift_id: str
    demand_group_id: str | None = None
    subcontractor_id: str
    released_qty: int = Field(ge=1)
    release_status_code: str = "draft"
    remarks: str | None = None


class SubcontractorReleaseUpdate(BaseModel):
    demand_group_id: str | None = None
    released_qty: int | None = Field(default=None, ge=1)
    release_status_code: str | None = None
    released_at: datetime | None = None
    revoked_at: datetime | None = None
    remarks: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class StaffingFilter(BaseModel):
    shift_id: str | None = None
    shift_plan_id: str | None = None
    planning_record_id: str | None = None
    demand_group_id: str | None = None
    team_id: str | None = None
    employee_id: str | None = None
    subcontractor_worker_id: str | None = None
    subcontractor_id: str | None = None
    assignment_status_code: str | None = None
    include_archived: bool = False


class DemandGroupListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    shift_id: str
    function_type_id: str
    qualification_type_id: str | None
    min_qty: int
    target_qty: int
    mandatory_flag: bool
    sort_order: int
    status: str
    version_no: int


class DemandGroupRead(DemandGroupListItem):
    remark: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class TeamMemberListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    team_id: str
    employee_id: str | None
    subcontractor_worker_id: str | None
    role_label: str | None
    is_team_lead: bool
    valid_from: datetime
    valid_to: datetime | None
    status: str
    version_no: int


class TeamMemberRead(TeamMemberListItem):
    notes: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class TeamListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    planning_record_id: str | None
    shift_id: str | None
    name: str
    role_label: str | None
    status: str
    version_no: int


class TeamRead(TeamListItem):
    notes: str | None
    members: list[TeamMemberListItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class AssignmentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    shift_id: str
    demand_group_id: str
    team_id: str | None
    employee_id: str | None
    subcontractor_worker_id: str | None
    assignment_status_code: str
    assignment_source_code: str
    offered_at: datetime | None
    confirmed_at: datetime | None
    status: str
    version_no: int


class AssignmentRead(AssignmentListItem):
    remarks: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class SubcontractorReleaseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    shift_id: str
    demand_group_id: str | None
    subcontractor_id: str
    released_qty: int
    release_status_code: str
    released_at: datetime | None
    revoked_at: datetime | None
    status: str
    version_no: int


class SubcontractorReleaseRead(SubcontractorReleaseListItem):
    remarks: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class StaffingAssignCommand(BaseModel):
    tenant_id: str
    shift_id: str
    demand_group_id: str
    team_id: str | None = None
    employee_id: str | None = None
    subcontractor_worker_id: str | None = None
    assignment_source_code: str = "dispatcher"
    offered_at: datetime | None = None
    confirmed_at: datetime | None = None
    remarks: str | None = None


class StaffingUnassignCommand(BaseModel):
    tenant_id: str
    assignment_id: str
    version_no: int
    remarks: str | None = None


class StaffingSubstituteCommand(BaseModel):
    tenant_id: str
    assignment_id: str
    version_no: int
    replacement_team_id: str | None = None
    replacement_employee_id: str | None = None
    replacement_subcontractor_worker_id: str | None = None
    assignment_source_code: str = "dispatcher"
    remarks: str | None = None


class StaffingCommandResult(BaseModel):
    tenant_id: str
    shift_id: str
    assignment_id: str | None = None
    outcome_code: str
    validation_codes: list[str] = Field(default_factory=list)
    validation_results: list["PlanningValidationResult"] = Field(default_factory=list)
    conflict_code: str | None = None
    assignment: AssignmentRead | None = None


class PlanningValidationResult(BaseModel):
    rule_code: str
    severity: str
    message_key: str
    summary: str | None = None
    actor_type: str | None = None
    actor_id: str | None = None
    assignment_id: str | None = None
    shift_id: str
    demand_group_id: str | None = None
    source_refs: dict[str, object] = Field(default_factory=dict)
    policy_code: str | None = None
    override_allowed: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)


class AssignmentValidationRead(BaseModel):
    tenant_id: str
    assignment_id: str
    shift_id: str
    blocking_count: int
    warning_count: int
    info_count: int = 0
    issues: list[PlanningValidationResult] = Field(default_factory=list)


class ShiftReleaseValidationRead(BaseModel):
    tenant_id: str
    shift_id: str
    blocking_count: int
    warning_count: int
    issues: list[PlanningValidationResult] = Field(default_factory=list)


class PlanningRecordReleaseValidationRead(BaseModel):
    tenant_id: str
    planning_record_id: str
    blocking_count: int
    warning_count: int
    issues: list[PlanningValidationResult] = Field(default_factory=list)


class AssignmentValidationOverrideCreate(BaseModel):
    tenant_id: str
    rule_code: str = Field(min_length=1, max_length=120)
    reason_text: str = Field(min_length=3, max_length=4000)


class AssignmentValidationOverrideRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    assignment_id: str
    rule_code: str
    reason_text: str
    created_at: datetime
    created_by_user_id: str | None


class StaffingBoardDemandGroupItem(BaseModel):
    id: str
    shift_id: str
    function_type_id: str
    qualification_type_id: str | None
    min_qty: int
    target_qty: int
    mandatory_flag: bool
    assigned_count: int
    confirmed_count: int
    released_partner_qty: int


class StaffingBoardAssignmentItem(BaseModel):
    id: str
    shift_id: str
    demand_group_id: str
    team_id: str | None
    employee_id: str | None
    subcontractor_worker_id: str | None
    assignment_status_code: str
    assignment_source_code: str
    confirmed_at: datetime | None


class StaffingBoardShiftItem(BaseModel):
    id: str
    tenant_id: str
    planning_record_id: str
    shift_plan_id: str
    order_id: str
    order_no: str
    planning_record_name: str
    planning_mode_code: str
    workforce_scope_code: str
    starts_at: datetime
    ends_at: datetime
    shift_type_code: str
    release_state: str
    status: str
    location_text: str | None
    meeting_point: str | None
    demand_groups: list[StaffingBoardDemandGroupItem] = Field(default_factory=list)
    assignments: list[StaffingBoardAssignmentItem] = Field(default_factory=list)


class StaffingBoardFilter(BaseModel):
    customer_id: str | None = None
    planning_record_id: str | None = None
    shift_plan_id: str | None = None
    shift_id: str | None = None
    order_id: str | None = None
    date_from: datetime
    date_to: datetime
    planning_mode_code: str | None = None
    workforce_scope_code: str | None = None
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    release_state: str | None = None
    visibility_state: str | None = None
    assignment_status_code: str | None = None
    confirmation_state: str | None = None


class CoverageDemandGroupItem(BaseModel):
    demand_group_id: str
    function_type_id: str
    qualification_type_id: str | None
    min_qty: int
    target_qty: int
    assigned_count: int
    confirmed_count: int
    released_partner_qty: int
    coverage_state: str


class CoverageShiftItem(BaseModel):
    shift_id: str
    planning_record_id: str
    shift_plan_id: str
    order_id: str
    order_no: str
    planning_record_name: str
    planning_mode_code: str
    workforce_scope_code: str
    starts_at: datetime
    ends_at: datetime
    shift_type_code: str
    location_text: str | None
    meeting_point: str | None
    min_required_qty: int
    target_required_qty: int
    assigned_count: int
    confirmed_count: int
    released_partner_qty: int
    coverage_state: str
    demand_groups: list[CoverageDemandGroupItem] = Field(default_factory=list)


class CoverageFilter(BaseModel):
    customer_id: str | None = None
    planning_record_id: str | None = None
    shift_plan_id: str | None = None
    order_id: str | None = None
    date_from: datetime
    date_to: datetime
    planning_mode_code: str | None = None
    workforce_scope_code: str | None = None
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    release_state: str | None = None
    visibility_state: str | None = None
    confirmation_state: str | None = None
