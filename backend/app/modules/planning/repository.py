"""SQLAlchemy repository for planning operational master data."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.errors import ApiException
from app.modules.core.models import Address, TenantSetting
from app.modules.customers.models import Customer, CustomerBillingProfile, CustomerInvoiceParty, CustomerRateCard
from app.modules.customers.models import CustomerEmployeeBlock
from app.modules.employees.models import EmployeeAbsence, EmployeeQualification, EmployeeTimeAccount, EmployeeTimeAccountTxn, FunctionType, QualificationType
from app.modules.iam.models import Role, UserAccount, UserRoleAssignment
from app.modules.platform_services.docs_models import Document, DocumentLink
from app.modules.platform_services.integration_models import ImportExportJob
from app.modules.planning.models import (
    Assignment,
    AssignmentValidationOverride,
    CustomerOrder,
    DemandGroup,
    EventPlanDetail,
    EquipmentItem,
    EventVenue,
    OrderEquipmentLine,
    OrderRequirementLine,
    PatrolCheckpoint,
    PatrolPlanDetail,
    PatrolRoute,
    PlanningRecord,
    RequirementType,
    Site,
    SitePlanDetail,
    Shift,
    ShiftPlan,
    ShiftSeries,
    ShiftSeriesException,
    ShiftTemplate,
    SubcontractorRelease,
    Team,
    TeamMember,
    TradeFair,
    TradeFairPlanDetail,
    TradeFairZone,
)
from app.modules.planning.schemas import (
    CustomerOrderCreate,
    CustomerOrderFilter,
    CustomerOrderUpdate,
    EventPlanDetailCreate,
    EventPlanDetailUpdate,
    EquipmentItemCreate,
    EquipmentItemUpdate,
    EventVenueCreate,
    EventVenueUpdate,
    OpsMasterFilter,
    OrderEquipmentLineCreate,
    OrderEquipmentLineUpdate,
    OrderRequirementLineCreate,
    OrderRequirementLineUpdate,
    PatrolPlanDetailCreate,
    PatrolPlanDetailUpdate,
    PatrolCheckpointCreate,
    PatrolCheckpointUpdate,
    PatrolRouteCreate,
    PatrolRouteUpdate,
    PlanningRecordCreate,
    PlanningDispatcherCandidateRead,
    PlanningRecordFilter,
    PlanningRecordUpdate,
    RequirementTypeCreate,
    RequirementTypeUpdate,
    SitePlanDetailCreate,
    SitePlanDetailUpdate,
    SiteCreate,
    SiteUpdate,
    ShiftCreate,
    ShiftListFilter,
    ShiftPlanCreate,
    ShiftPlanFilter,
    ShiftPlanUpdate,
    ShiftSeriesCreate,
    ShiftSeriesExceptionCreate,
    ShiftSeriesExceptionUpdate,
    ShiftSeriesUpdate,
    ShiftTemplateCreate,
    ShiftTemplateUpdate,
    ShiftUpdate,
    StaffingFilter,
    SubcontractorReleaseCreate,
    SubcontractorReleaseUpdate,
    TeamCreate,
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamUpdate,
    DemandGroupCreate,
    DemandGroupUpdate,
    AssignmentCreate,
    AssignmentUpdate,
    PlanningBoardFilter,
    TradeFairCreate,
    TradeFairPlanDetailCreate,
    TradeFairPlanDetailUpdate,
    TradeFairUpdate,
    TradeFairZoneCreate,
    TradeFairZoneUpdate,
)
from app.modules.subcontractors.models import Subcontractor, SubcontractorWorker, SubcontractorWorkerQualification


class SqlAlchemyPlanningRepository:
    STALE_RESOURCE_CODES = {
        "RequirementType": "requirement_type",
        "EquipmentItem": "equipment_item",
        "Site": "site",
        "EventVenue": "event_venue",
        "TradeFair": "trade_fair",
        "PatrolRoute": "patrol_route",
        "TradeFairZone": "trade_fair_zone",
        "PatrolCheckpoint": "patrol_checkpoint",
        "CustomerOrder": "customer_order",
        "OrderEquipmentLine": "order_equipment",
        "OrderRequirementLine": "order_requirement_line",
        "PlanningRecord": "planning_record",
        "ShiftTemplate": "shift_template",
        "ShiftPlan": "shift_plan",
        "ShiftSeries": "shift_series",
        "ShiftSeriesException": "shift_series_exception",
        "Shift": "shift",
        "DemandGroup": "demand_group",
        "Team": "team",
        "TeamMember": "team_member",
        "Assignment": "assignment",
        "SubcontractorRelease": "subcontractor_release",
    }
    TENANT_SCOPED_OPS_MODELS = {RequirementType, EquipmentItem}

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None:
        statement = select(Customer).where(Customer.tenant_id == tenant_id, Customer.id == customer_id)
        return self.session.scalars(statement).one_or_none()

    def get_customer_billing_profile(self, tenant_id: str, customer_id: str) -> CustomerBillingProfile | None:
        statement = select(CustomerBillingProfile).where(
            CustomerBillingProfile.tenant_id == tenant_id,
            CustomerBillingProfile.customer_id == customer_id,
        )
        return self.session.scalars(statement).one_or_none()

    def list_customer_invoice_parties(self, tenant_id: str, customer_id: str) -> list[CustomerInvoiceParty]:
        statement = select(CustomerInvoiceParty).where(
            CustomerInvoiceParty.tenant_id == tenant_id,
            CustomerInvoiceParty.customer_id == customer_id,
        )
        return list(self.session.scalars(statement).all())

    def list_customer_rate_cards(self, tenant_id: str, customer_id: str) -> list[CustomerRateCard]:
        statement = select(CustomerRateCard).where(
            CustomerRateCard.tenant_id == tenant_id,
            CustomerRateCard.customer_id == customer_id,
        )
        return list(self.session.scalars(statement).all())

    def create_job(self, row: ImportExportJob) -> ImportExportJob:
        self.session.add(row)
        self._commit_or_raise()
        return row

    def save_job(self, row: ImportExportJob) -> ImportExportJob:
        self._commit_or_raise()
        return row

    def get_address(self, address_id: str) -> Address | None:
        statement = select(Address).where(Address.id == address_id)
        return self.session.scalars(statement).one_or_none()

    def get_function_type(self, tenant_id: str, function_type_id: str) -> FunctionType | None:
        statement = select(FunctionType).where(FunctionType.tenant_id == tenant_id, FunctionType.id == function_type_id)
        return self.session.scalars(statement).one_or_none()

    def get_qualification_type(self, tenant_id: str, qualification_type_id: str) -> QualificationType | None:
        statement = select(QualificationType).where(
            QualificationType.tenant_id == tenant_id,
            QualificationType.id == qualification_type_id,
        )
        return self.session.scalars(statement).one_or_none()

    def get_user_account(self, tenant_id: str, user_id: str) -> UserAccount | None:
        statement = select(UserAccount).where(UserAccount.tenant_id == tenant_id, UserAccount.id == user_id)
        return self.session.scalars(statement).one_or_none()

    def list_dispatcher_candidates(self, tenant_id: str) -> list[PlanningDispatcherCandidateRead]:
        now = datetime.now(UTC)
        statement = (
            select(UserAccount, Role.key)
            .join(UserRoleAssignment, UserRoleAssignment.user_account_id == UserAccount.id)
            .join(Role, Role.id == UserRoleAssignment.role_id)
            .where(
                UserAccount.tenant_id == tenant_id,
                UserAccount.archived_at.is_(None),
                UserAccount.status == "active",
                UserRoleAssignment.tenant_id == tenant_id,
                UserRoleAssignment.archived_at.is_(None),
                UserRoleAssignment.status == "active",
                UserRoleAssignment.scope_type.in_(("tenant", "branch", "mandate")),
                or_(UserRoleAssignment.valid_from.is_(None), UserRoleAssignment.valid_from <= now),
                or_(UserRoleAssignment.valid_until.is_(None), UserRoleAssignment.valid_until >= now),
                Role.key.in_(("platform_admin", "tenant_admin", "dispatcher", "controller_qm", "accounting")),
            )
            .order_by(func.lower(UserAccount.full_name), func.lower(UserAccount.username))
        )
        rows = self.session.execute(statement).all()
        candidates: dict[str, PlanningDispatcherCandidateRead] = {}
        for user, role_key in rows:
            if user.id not in candidates:
                candidates[user.id] = PlanningDispatcherCandidateRead(
                    id=user.id,
                    tenant_id=user.tenant_id,
                    username=user.username,
                    email=user.email,
                    full_name=user.full_name,
                    status=user.status,
                    role_keys=[],
                    archived_at=user.archived_at,
                )
            if role_key not in candidates[user.id].role_keys:
                candidates[user.id].role_keys.append(role_key)
        return list(candidates.values())

    def get_tenant_setting_value(self, tenant_id: str, key: str) -> dict[str, object] | None:
        statement = select(TenantSetting).where(TenantSetting.tenant_id == tenant_id, TenantSetting.key == key)
        row = self.session.scalars(statement).one_or_none()
        return row.value_json if row is not None else None

    def get_tenant_setting_json(self, tenant_id: str, key: str) -> object | None:
        statement = select(TenantSetting).where(TenantSetting.tenant_id == tenant_id, TenantSetting.key == key)
        row = self.session.scalars(statement).one_or_none()
        return row.value_json if row is not None else None

    def get_employee(self, tenant_id: str, employee_id: str):
        from app.modules.employees.models import Employee

        statement = select(Employee).where(Employee.tenant_id == tenant_id, Employee.id == employee_id)
        return self.session.scalars(statement).one_or_none()

    def find_employee_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None):
        from app.modules.employees.models import Employee

        statement = select(Employee).where(Employee.tenant_id == tenant_id, Employee.user_id == user_id)
        if exclude_id is not None:
            statement = statement.where(Employee.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None:
        statement = select(Subcontractor).where(Subcontractor.tenant_id == tenant_id, Subcontractor.id == subcontractor_id)
        return self.session.scalars(statement).one_or_none()

    def get_subcontractor_worker(self, tenant_id: str, worker_id: str) -> SubcontractorWorker | None:
        statement = select(SubcontractorWorker).where(
            SubcontractorWorker.tenant_id == tenant_id,
            SubcontractorWorker.id == worker_id,
        )
        return self.session.scalars(statement).one_or_none()

    def list_employee_qualifications(self, tenant_id: str, employee_id: str) -> list[EmployeeQualification]:
        statement = (
            select(EmployeeQualification)
            .where(EmployeeQualification.tenant_id == tenant_id, EmployeeQualification.employee_id == employee_id)
            .options(selectinload(EmployeeQualification.qualification_type))
        )
        return list(self.session.scalars(statement).all())

    def list_worker_qualifications(self, tenant_id: str, worker_id: str) -> list[object]:
        statement = (
            select(SubcontractorWorkerQualification)
            .where(SubcontractorWorkerQualification.tenant_id == tenant_id, SubcontractorWorkerQualification.worker_id == worker_id)
            .options(selectinload(SubcontractorWorkerQualification.qualification_type))
        )
        return list(self.session.scalars(statement).all())

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]:
        statement = (
            select(Document)
            .join(DocumentLink, DocumentLink.document_id == Document.id)
            .where(
                Document.tenant_id == tenant_id,
                DocumentLink.tenant_id == tenant_id,
                DocumentLink.owner_type == owner_type,
                DocumentLink.owner_id == owner_id,
            )
        )
        return list(self.session.scalars(statement).unique().all())

    def list_customer_employee_blocks(self, tenant_id: str, customer_id: str, employee_id: str, on_date: date) -> list[CustomerEmployeeBlock]:
        statement = select(CustomerEmployeeBlock).where(
            CustomerEmployeeBlock.tenant_id == tenant_id,
            CustomerEmployeeBlock.customer_id == customer_id,
            CustomerEmployeeBlock.employee_id == employee_id,
            CustomerEmployeeBlock.archived_at.is_(None),
            CustomerEmployeeBlock.effective_from <= on_date,
            or_(CustomerEmployeeBlock.effective_to.is_(None), CustomerEmployeeBlock.effective_to >= on_date),
        )
        return list(self.session.scalars(statement).all())

    def list_requirement_types(self, tenant_id: str, filters: OpsMasterFilter) -> list[RequirementType]:
        return self._list_rows(RequirementType, tenant_id, filters)

    def get_requirement_type(self, tenant_id: str, row_id: str) -> RequirementType | None:
        return self._get_row(RequirementType, tenant_id, row_id)

    def create_requirement_type(
        self,
        tenant_id: str,
        payload: RequirementTypeCreate,
        actor_user_id: str | None,
    ) -> RequirementType:
        row = RequirementType(
            tenant_id=tenant_id,
            customer_id=self._normalize_optional_uuid_value(payload.customer_id),
            code=payload.code,
            label=payload.label,
            default_planning_mode_code=payload.default_planning_mode_code,
            description=getattr(payload, "notes", getattr(payload, "description", None)),
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_requirement_type(
        self,
        tenant_id: str,
        row_id: str,
        payload: RequirementTypeUpdate,
        actor_user_id: str | None,
    ) -> RequirementType | None:
        return self._update_row(
            RequirementType,
            tenant_id,
            row_id,
            payload,
            actor_user_id,
            normalize_blank_uuid_fields={"customer_id"},
        )

    def find_requirement_type_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> RequirementType | None:
        return self._find_by_code(RequirementType, tenant_id, code, exclude_id=exclude_id)

    def list_equipment_items(self, tenant_id: str, filters: OpsMasterFilter) -> list[EquipmentItem]:
        return self._list_rows(EquipmentItem, tenant_id, filters)

    def get_equipment_item(self, tenant_id: str, row_id: str) -> EquipmentItem | None:
        return self._get_row(EquipmentItem, tenant_id, row_id)

    def create_equipment_item(
        self,
        tenant_id: str,
        payload: EquipmentItemCreate,
        actor_user_id: str | None,
    ) -> EquipmentItem:
        row = EquipmentItem(
            tenant_id=tenant_id,
            customer_id=self._normalize_optional_uuid_value(payload.customer_id),
            code=payload.code,
            label=payload.label,
            unit_of_measure_code=payload.unit_of_measure_code,
            description=payload.description,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_equipment_item(
        self,
        tenant_id: str,
        row_id: str,
        payload: EquipmentItemUpdate,
        actor_user_id: str | None,
    ) -> EquipmentItem | None:
        return self._update_row(
            EquipmentItem,
            tenant_id,
            row_id,
            payload,
            actor_user_id,
            normalize_blank_uuid_fields={"customer_id"},
        )

    def find_equipment_item_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> EquipmentItem | None:
        return self._find_by_code(EquipmentItem, tenant_id, code, exclude_id=exclude_id)

    def list_sites(self, tenant_id: str, filters: OpsMasterFilter) -> list[Site]:
        return self._list_rows(Site, tenant_id, filters, extra_options=(selectinload(Site.address),))

    def get_site(self, tenant_id: str, row_id: str) -> Site | None:
        return self._get_row(Site, tenant_id, row_id, extra_options=(selectinload(Site.address),))

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
        return self._create_row(row)

    def update_site(self, tenant_id: str, row_id: str, payload: SiteUpdate, actor_user_id: str | None) -> Site | None:
        return self._update_row(Site, tenant_id, row_id, payload, actor_user_id, extra_options=(selectinload(Site.address),))

    def find_site_by_no(self, tenant_id: str, site_no: str, *, exclude_id: str | None = None) -> Site | None:
        return self._find_by_code(Site, tenant_id, site_no, field_name="site_no", exclude_id=exclude_id)

    def list_event_venues(self, tenant_id: str, filters: OpsMasterFilter) -> list[EventVenue]:
        return self._list_rows(EventVenue, tenant_id, filters, extra_options=(selectinload(EventVenue.address),))

    def get_event_venue(self, tenant_id: str, row_id: str) -> EventVenue | None:
        return self._get_row(EventVenue, tenant_id, row_id, extra_options=(selectinload(EventVenue.address),))

    def create_event_venue(self, tenant_id: str, payload: EventVenueCreate, actor_user_id: str | None) -> EventVenue:
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
        return self._create_row(row)

    def update_event_venue(
        self,
        tenant_id: str,
        row_id: str,
        payload: EventVenueUpdate,
        actor_user_id: str | None,
    ) -> EventVenue | None:
        return self._update_row(EventVenue, tenant_id, row_id, payload, actor_user_id, extra_options=(selectinload(EventVenue.address),))

    def find_event_venue_by_no(self, tenant_id: str, venue_no: str, *, exclude_id: str | None = None) -> EventVenue | None:
        return self._find_by_code(EventVenue, tenant_id, venue_no, field_name="venue_no", exclude_id=exclude_id)

    def list_trade_fairs(self, tenant_id: str, filters: OpsMasterFilter) -> list[TradeFair]:
        return self._list_rows(
            TradeFair,
            tenant_id,
            filters,
            extra_options=(selectinload(TradeFair.address), selectinload(TradeFair.zones)),
        )

    def get_trade_fair(self, tenant_id: str, row_id: str) -> TradeFair | None:
        return self._get_row(
            TradeFair,
            tenant_id,
            row_id,
            extra_options=(selectinload(TradeFair.address), selectinload(TradeFair.zones)),
        )

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
        return self._create_row(row)

    def update_trade_fair(self, tenant_id: str, row_id: str, payload: TradeFairUpdate, actor_user_id: str | None) -> TradeFair | None:
        return self._update_row(
            TradeFair,
            tenant_id,
            row_id,
            payload,
            actor_user_id,
            extra_options=(selectinload(TradeFair.address), selectinload(TradeFair.zones)),
        )

    def find_trade_fair_by_no(self, tenant_id: str, fair_no: str, *, exclude_id: str | None = None) -> TradeFair | None:
        return self._find_by_code(TradeFair, tenant_id, fair_no, field_name="fair_no", exclude_id=exclude_id)

    def list_patrol_routes(self, tenant_id: str, filters: OpsMasterFilter) -> list[PatrolRoute]:
        return self._list_rows(
            PatrolRoute,
            tenant_id,
            filters,
            extra_options=(selectinload(PatrolRoute.meeting_address), selectinload(PatrolRoute.checkpoints)),
        )

    def get_patrol_route(self, tenant_id: str, row_id: str) -> PatrolRoute | None:
        return self._get_row(
            PatrolRoute,
            tenant_id,
            row_id,
            extra_options=(selectinload(PatrolRoute.meeting_address), selectinload(PatrolRoute.checkpoints)),
        )

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
        return self._create_row(row)

    def update_patrol_route(
        self,
        tenant_id: str,
        row_id: str,
        payload: PatrolRouteUpdate,
        actor_user_id: str | None,
    ) -> PatrolRoute | None:
        return self._update_row(
            PatrolRoute,
            tenant_id,
            row_id,
            payload,
            actor_user_id,
            extra_options=(selectinload(PatrolRoute.meeting_address), selectinload(PatrolRoute.checkpoints)),
        )

    def find_patrol_route_by_no(self, tenant_id: str, route_no: str, *, exclude_id: str | None = None) -> PatrolRoute | None:
        return self._find_by_code(PatrolRoute, tenant_id, route_no, field_name="route_no", exclude_id=exclude_id)

    def create_trade_fair_zone(self, tenant_id: str, payload: TradeFairZoneCreate, actor_user_id: str | None) -> TradeFairZone:
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
        return self._create_row(row)

    def update_trade_fair_zone(
        self,
        tenant_id: str,
        row_id: str,
        payload: TradeFairZoneUpdate,
        actor_user_id: str | None,
    ) -> TradeFairZone | None:
        return self._update_row(TradeFairZone, tenant_id, row_id, payload, actor_user_id)

    def get_trade_fair_zone(self, tenant_id: str, row_id: str) -> TradeFairZone | None:
        return self._get_row(TradeFairZone, tenant_id, row_id)

    def list_trade_fair_zones(self, tenant_id: str, trade_fair_id: str) -> list[TradeFairZone]:
        statement = (
            select(TradeFairZone)
            .where(TradeFairZone.tenant_id == tenant_id, TradeFairZone.trade_fair_id == trade_fair_id)
            .order_by(TradeFairZone.zone_code)
        )
        return list(self.session.scalars(statement).all())

    def find_trade_fair_zone(
        self,
        tenant_id: str,
        trade_fair_id: str,
        zone_type_code: str,
        zone_code: str,
        *,
        exclude_id: str | None = None,
    ) -> TradeFairZone | None:
        statement = select(TradeFairZone).where(
            TradeFairZone.tenant_id == tenant_id,
            TradeFairZone.trade_fair_id == trade_fair_id,
            TradeFairZone.zone_type_code == zone_type_code,
            TradeFairZone.zone_code == zone_code,
        )
        if exclude_id is not None:
            statement = statement.where(TradeFairZone.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_patrol_checkpoint(
        self,
        tenant_id: str,
        payload: PatrolCheckpointCreate,
        actor_user_id: str | None,
    ) -> PatrolCheckpoint:
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
        return self._create_row(row)

    def update_patrol_checkpoint(
        self,
        tenant_id: str,
        row_id: str,
        payload: PatrolCheckpointUpdate,
        actor_user_id: str | None,
    ) -> PatrolCheckpoint | None:
        return self._update_row(PatrolCheckpoint, tenant_id, row_id, payload, actor_user_id)

    def get_patrol_checkpoint(self, tenant_id: str, row_id: str) -> PatrolCheckpoint | None:
        return self._get_row(PatrolCheckpoint, tenant_id, row_id)

    def list_patrol_checkpoints(self, tenant_id: str, patrol_route_id: str) -> list[PatrolCheckpoint]:
        statement = (
            select(PatrolCheckpoint)
            .where(PatrolCheckpoint.tenant_id == tenant_id, PatrolCheckpoint.patrol_route_id == patrol_route_id)
            .order_by(PatrolCheckpoint.sequence_no)
        )
        return list(self.session.scalars(statement).all())

    def find_patrol_checkpoint_by_sequence(
        self,
        tenant_id: str,
        patrol_route_id: str,
        sequence_no: int,
        *,
        exclude_id: str | None = None,
    ) -> PatrolCheckpoint | None:
        statement = select(PatrolCheckpoint).where(
            PatrolCheckpoint.tenant_id == tenant_id,
            PatrolCheckpoint.patrol_route_id == patrol_route_id,
            PatrolCheckpoint.sequence_no == sequence_no,
        )
        if exclude_id is not None:
            statement = statement.where(PatrolCheckpoint.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def find_patrol_checkpoint_by_code(
        self,
        tenant_id: str,
        patrol_route_id: str,
        checkpoint_code: str,
        *,
        exclude_id: str | None = None,
    ) -> PatrolCheckpoint | None:
        statement = select(PatrolCheckpoint).where(
            PatrolCheckpoint.tenant_id == tenant_id,
            PatrolCheckpoint.patrol_route_id == patrol_route_id,
            PatrolCheckpoint.checkpoint_code == checkpoint_code,
        )
        if exclude_id is not None:
            statement = statement.where(PatrolCheckpoint.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def list_customer_orders(self, tenant_id: str, filters: CustomerOrderFilter) -> list[CustomerOrder]:
        statement = (
            select(CustomerOrder)
            .where(CustomerOrder.tenant_id == tenant_id)
            .options(
                selectinload(CustomerOrder.equipment_lines),
                selectinload(CustomerOrder.requirement_lines),
            )
            .order_by(CustomerOrder.order_no)
        )
        if not filters.include_archived:
            statement = statement.where(CustomerOrder.archived_at.is_(None))
        if filters.customer_id is not None:
            statement = statement.where(CustomerOrder.customer_id == filters.customer_id)
        if filters.lifecycle_status is not None:
            statement = statement.where(CustomerOrder.status == filters.lifecycle_status)
        if filters.release_state is not None:
            statement = statement.where(CustomerOrder.release_state == filters.release_state)
        if filters.service_from is not None:
            statement = statement.where(CustomerOrder.service_to >= filters.service_from)
        if filters.service_to is not None:
            statement = statement.where(CustomerOrder.service_from <= filters.service_to)
        if filters.search:
            like_term = f"%{filters.search.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(func.coalesce(CustomerOrder.order_no, "")).like(like_term),
                    func.lower(func.coalesce(CustomerOrder.title, "")).like(like_term),
                )
            )
        return list(self.session.scalars(statement).all())

    def get_customer_order(self, tenant_id: str, order_id: str) -> CustomerOrder | None:
        return self.session.scalars(
            select(CustomerOrder)
            .where(CustomerOrder.tenant_id == tenant_id, CustomerOrder.id == order_id)
            .options(
                selectinload(CustomerOrder.equipment_lines),
                selectinload(CustomerOrder.requirement_lines),
                selectinload(CustomerOrder.patrol_route),
            )
        ).one_or_none()

    def find_customer_order_by_no(self, tenant_id: str, order_no: str, *, exclude_id: str | None = None) -> CustomerOrder | None:
        statement = select(CustomerOrder).where(CustomerOrder.tenant_id == tenant_id, CustomerOrder.order_no == order_no)
        if exclude_id is not None:
            statement = statement.where(CustomerOrder.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_customer_order(self, tenant_id: str, payload: CustomerOrderCreate, actor_user_id: str | None) -> CustomerOrder:
        row = CustomerOrder(
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
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_customer_order(
        self,
        tenant_id: str,
        order_id: str,
        payload: CustomerOrderUpdate,
        actor_user_id: str | None,
    ) -> CustomerOrder | None:
        return self._update_row(CustomerOrder, tenant_id, order_id, payload, actor_user_id)

    def save_customer_order(self, row: CustomerOrder) -> CustomerOrder:
        self._commit_or_raise()
        return self.get_customer_order(row.tenant_id, row.id) or row

    def list_order_equipment_lines(self, tenant_id: str, order_id: str) -> list[OrderEquipmentLine]:
        statement = (
            select(OrderEquipmentLine)
            .where(OrderEquipmentLine.tenant_id == tenant_id, OrderEquipmentLine.order_id == order_id)
            .options(selectinload(OrderEquipmentLine.equipment_item))
            .order_by(OrderEquipmentLine.created_at)
        )
        return list(self.session.scalars(statement).all())

    def get_order_equipment_line(self, tenant_id: str, row_id: str) -> OrderEquipmentLine | None:
        return self.session.scalars(
            select(OrderEquipmentLine)
            .where(OrderEquipmentLine.tenant_id == tenant_id, OrderEquipmentLine.id == row_id)
            .options(selectinload(OrderEquipmentLine.equipment_item))
        ).one_or_none()

    def create_order_equipment_line(self, tenant_id: str, payload: OrderEquipmentLineCreate, actor_user_id: str | None) -> OrderEquipmentLine:
        row = OrderEquipmentLine(
            tenant_id=tenant_id,
            order_id=payload.order_id,
            equipment_item_id=payload.equipment_item_id,
            required_qty=payload.required_qty,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_order_equipment_line(
        self,
        tenant_id: str,
        row_id: str,
        payload: OrderEquipmentLineUpdate,
        actor_user_id: str | None,
    ) -> OrderEquipmentLine | None:
        return self._update_row(OrderEquipmentLine, tenant_id, row_id, payload, actor_user_id)

    def find_order_equipment_line(self, tenant_id: str, order_id: str, equipment_item_id: str, *, exclude_id: str | None = None) -> OrderEquipmentLine | None:
        statement = select(OrderEquipmentLine).where(
            OrderEquipmentLine.tenant_id == tenant_id,
            OrderEquipmentLine.order_id == order_id,
            OrderEquipmentLine.equipment_item_id == equipment_item_id,
        )
        if exclude_id is not None:
            statement = statement.where(OrderEquipmentLine.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def list_order_requirement_lines(self, tenant_id: str, order_id: str) -> list[OrderRequirementLine]:
        statement = (
            select(OrderRequirementLine)
            .where(OrderRequirementLine.tenant_id == tenant_id, OrderRequirementLine.order_id == order_id)
            .options(
                selectinload(OrderRequirementLine.requirement_type),
                selectinload(OrderRequirementLine.function_type),
                selectinload(OrderRequirementLine.qualification_type),
            )
            .order_by(OrderRequirementLine.created_at)
        )
        return list(self.session.scalars(statement).all())

    def get_order_requirement_line(self, tenant_id: str, row_id: str) -> OrderRequirementLine | None:
        return self.session.scalars(
            select(OrderRequirementLine)
            .where(OrderRequirementLine.tenant_id == tenant_id, OrderRequirementLine.id == row_id)
            .options(
                selectinload(OrderRequirementLine.requirement_type),
                selectinload(OrderRequirementLine.function_type),
                selectinload(OrderRequirementLine.qualification_type),
            )
        ).one_or_none()

    def create_order_requirement_line(
        self,
        tenant_id: str,
        payload: OrderRequirementLineCreate,
        actor_user_id: str | None,
    ) -> OrderRequirementLine:
        row = OrderRequirementLine(
            tenant_id=tenant_id,
            order_id=payload.order_id,
            requirement_type_id=payload.requirement_type_id,
            function_type_id=payload.function_type_id,
            qualification_type_id=payload.qualification_type_id,
            min_qty=payload.min_qty,
            target_qty=payload.target_qty,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_order_requirement_line(
        self,
        tenant_id: str,
        row_id: str,
        payload: OrderRequirementLineUpdate,
        actor_user_id: str | None,
    ) -> OrderRequirementLine | None:
        return self._update_row(OrderRequirementLine, tenant_id, row_id, payload, actor_user_id)

    def list_planning_records(self, tenant_id: str, filters: PlanningRecordFilter) -> list[PlanningRecord]:
        statement = (
            select(PlanningRecord)
            .join(CustomerOrder, CustomerOrder.id == PlanningRecord.order_id)
            .where(PlanningRecord.tenant_id == tenant_id, CustomerOrder.tenant_id == tenant_id)
            .options(
                selectinload(PlanningRecord.event_detail),
                selectinload(PlanningRecord.site_detail),
                selectinload(PlanningRecord.trade_fair_detail),
                selectinload(PlanningRecord.patrol_detail),
            )
            .order_by(PlanningRecord.planning_from, PlanningRecord.name)
        )
        if not filters.include_archived:
            statement = statement.where(PlanningRecord.archived_at.is_(None))
        if filters.order_id is not None:
            statement = statement.where(PlanningRecord.order_id == filters.order_id)
        if filters.customer_id is not None:
            statement = statement.where(CustomerOrder.customer_id == filters.customer_id)
        if filters.planning_mode_code is not None:
            statement = statement.where(PlanningRecord.planning_mode_code == filters.planning_mode_code)
        if filters.lifecycle_status is not None:
            statement = statement.where(PlanningRecord.status == filters.lifecycle_status)
        if filters.release_state is not None:
            statement = statement.where(PlanningRecord.release_state == filters.release_state)
        if filters.dispatcher_user_id is not None:
            statement = statement.where(PlanningRecord.dispatcher_user_id == filters.dispatcher_user_id)
        if filters.planning_from is not None:
            statement = statement.where(PlanningRecord.planning_to >= filters.planning_from)
        if filters.planning_to is not None:
            statement = statement.where(PlanningRecord.planning_from <= filters.planning_to)
        if filters.search:
            like_term = f"%{filters.search.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(func.coalesce(PlanningRecord.name, "")).like(like_term),
                    func.lower(func.coalesce(CustomerOrder.order_no, "")).like(like_term),
                    func.lower(func.coalesce(CustomerOrder.title, "")).like(like_term),
                )
            )
        return list(self.session.scalars(statement).all())

    def get_planning_record(self, tenant_id: str, planning_record_id: str) -> PlanningRecord | None:
        return self.session.scalars(
            select(PlanningRecord)
            .where(PlanningRecord.tenant_id == tenant_id, PlanningRecord.id == planning_record_id)
            .options(
                selectinload(PlanningRecord.event_detail),
                selectinload(PlanningRecord.site_detail),
                selectinload(PlanningRecord.trade_fair_detail),
                selectinload(PlanningRecord.patrol_detail),
            )
        ).one_or_none()

    def find_planning_record_by_name(self, tenant_id: str, order_id: str, name: str, *, exclude_id: str | None = None) -> PlanningRecord | None:
        statement = select(PlanningRecord).where(
            PlanningRecord.tenant_id == tenant_id,
            PlanningRecord.order_id == order_id,
            PlanningRecord.name == name,
        )
        if exclude_id is not None:
            statement = statement.where(PlanningRecord.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_planning_record(self, tenant_id: str, payload: PlanningRecordCreate, actor_user_id: str | None) -> PlanningRecord:
        row = PlanningRecord(
            tenant_id=tenant_id,
            order_id=payload.order_id,
            parent_planning_record_id=payload.parent_planning_record_id,
            dispatcher_user_id=payload.dispatcher_user_id,
            planning_mode_code=payload.planning_mode_code,
            name=payload.name,
            planning_from=payload.planning_from,
            planning_to=payload.planning_to,
            release_state=payload.release_state,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_planning_record(self, tenant_id: str, planning_record_id: str, payload: PlanningRecordUpdate, actor_user_id: str | None) -> PlanningRecord | None:
        return self._update_row(
            PlanningRecord,
            tenant_id,
            planning_record_id,
            payload,
            actor_user_id,
            exclude_fields={"event_detail", "site_detail", "trade_fair_detail", "patrol_detail"},
        )

    def save_planning_record(self, row: PlanningRecord) -> PlanningRecord:
        self._commit_or_raise()
        return self.get_planning_record(row.tenant_id, row.id) or row

    def create_event_plan_detail(self, tenant_id: str, planning_record_id: str, payload: EventPlanDetailCreate) -> EventPlanDetail:
        row = EventPlanDetail(tenant_id=tenant_id, planning_record_id=planning_record_id, event_venue_id=payload.event_venue_id, setup_note=payload.setup_note)
        return self._create_row(row)

    def update_event_plan_detail(self, tenant_id: str, planning_record_id: str, payload: EventPlanDetailUpdate) -> EventPlanDetail | None:
        row = self.get_event_plan_detail(tenant_id, planning_record_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        self._commit_or_raise()
        return self.get_event_plan_detail(tenant_id, planning_record_id) or row

    def get_event_plan_detail(self, tenant_id: str, planning_record_id: str) -> EventPlanDetail | None:
        statement = select(EventPlanDetail).where(EventPlanDetail.tenant_id == tenant_id, EventPlanDetail.planning_record_id == planning_record_id)
        return self.session.scalars(statement).one_or_none()

    def create_site_plan_detail(self, tenant_id: str, planning_record_id: str, payload: SitePlanDetailCreate) -> SitePlanDetail:
        row = SitePlanDetail(tenant_id=tenant_id, planning_record_id=planning_record_id, site_id=payload.site_id, watchbook_scope_note=payload.watchbook_scope_note)
        return self._create_row(row)

    def update_site_plan_detail(self, tenant_id: str, planning_record_id: str, payload: SitePlanDetailUpdate) -> SitePlanDetail | None:
        row = self.get_site_plan_detail(tenant_id, planning_record_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        self._commit_or_raise()
        return self.get_site_plan_detail(tenant_id, planning_record_id) or row

    def get_site_plan_detail(self, tenant_id: str, planning_record_id: str) -> SitePlanDetail | None:
        statement = select(SitePlanDetail).where(SitePlanDetail.tenant_id == tenant_id, SitePlanDetail.planning_record_id == planning_record_id)
        return self.session.scalars(statement).one_or_none()

    def create_trade_fair_plan_detail(self, tenant_id: str, planning_record_id: str, payload: TradeFairPlanDetailCreate) -> TradeFairPlanDetail:
        row = TradeFairPlanDetail(
            tenant_id=tenant_id,
            planning_record_id=planning_record_id,
            trade_fair_id=payload.trade_fair_id,
            trade_fair_zone_id=payload.trade_fair_zone_id,
            stand_note=payload.stand_note,
        )
        return self._create_row(row)

    def update_trade_fair_plan_detail(self, tenant_id: str, planning_record_id: str, payload: TradeFairPlanDetailUpdate) -> TradeFairPlanDetail | None:
        row = self.get_trade_fair_plan_detail(tenant_id, planning_record_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        self._commit_or_raise()
        return self.get_trade_fair_plan_detail(tenant_id, planning_record_id) or row

    def get_trade_fair_plan_detail(self, tenant_id: str, planning_record_id: str) -> TradeFairPlanDetail | None:
        statement = select(TradeFairPlanDetail).where(
            TradeFairPlanDetail.tenant_id == tenant_id,
            TradeFairPlanDetail.planning_record_id == planning_record_id,
        )
        return self.session.scalars(statement).one_or_none()

    def create_patrol_plan_detail(self, tenant_id: str, planning_record_id: str, payload: PatrolPlanDetailCreate) -> PatrolPlanDetail:
        row = PatrolPlanDetail(
            tenant_id=tenant_id,
            planning_record_id=planning_record_id,
            patrol_route_id=payload.patrol_route_id,
            execution_note=payload.execution_note,
        )
        return self._create_row(row)

    def update_patrol_plan_detail(self, tenant_id: str, planning_record_id: str, payload: PatrolPlanDetailUpdate) -> PatrolPlanDetail | None:
        row = self.get_patrol_plan_detail(tenant_id, planning_record_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        self._commit_or_raise()
        return self.get_patrol_plan_detail(tenant_id, planning_record_id) or row

    def get_patrol_plan_detail(self, tenant_id: str, planning_record_id: str) -> PatrolPlanDetail | None:
        statement = select(PatrolPlanDetail).where(PatrolPlanDetail.tenant_id == tenant_id, PatrolPlanDetail.planning_record_id == planning_record_id)
        return self.session.scalars(statement).one_or_none()

    def list_shift_templates(self, tenant_id: str, filters: OpsMasterFilter) -> list[ShiftTemplate]:
        return self._list_rows(ShiftTemplate, tenant_id, filters)

    def get_shift_template(self, tenant_id: str, row_id: str) -> ShiftTemplate | None:
        return self._get_row(ShiftTemplate, tenant_id, row_id)

    def find_shift_template_by_code(self, tenant_id: str, code: str, *, exclude_id: str | None = None) -> ShiftTemplate | None:
        return self._find_by_code(ShiftTemplate, tenant_id, code, exclude_id=exclude_id)

    def create_shift_template(self, tenant_id: str, payload: ShiftTemplateCreate, actor_user_id: str | None) -> ShiftTemplate:
        row = ShiftTemplate(
            tenant_id=tenant_id,
            code=payload.code,
            label=payload.label,
            local_start_time=payload.local_start_time,
            local_end_time=payload.local_end_time,
            default_break_minutes=payload.default_break_minutes,
            shift_type_code=payload.shift_type_code,
            meeting_point=payload.meeting_point,
            location_text=payload.location_text,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_shift_template(self, tenant_id: str, row_id: str, payload: ShiftTemplateUpdate, actor_user_id: str | None) -> ShiftTemplate | None:
        return self._update_row(ShiftTemplate, tenant_id, row_id, payload, actor_user_id)

    def list_shift_plans(self, tenant_id: str, filters: ShiftPlanFilter) -> list[ShiftPlan]:
        statement = (
            select(ShiftPlan)
            .where(ShiftPlan.tenant_id == tenant_id)
            .options(selectinload(ShiftPlan.series_rows), selectinload(ShiftPlan.shifts))
            .order_by(ShiftPlan.planning_from, ShiftPlan.name)
        )
        if not filters.include_archived:
            statement = statement.where(ShiftPlan.archived_at.is_(None))
        if filters.planning_record_id is not None:
            statement = statement.where(ShiftPlan.planning_record_id == filters.planning_record_id)
        if filters.workforce_scope_code is not None:
            statement = statement.where(ShiftPlan.workforce_scope_code == filters.workforce_scope_code)
        if filters.lifecycle_status is not None:
            statement = statement.where(ShiftPlan.status == filters.lifecycle_status)
        return list(self.session.scalars(statement).all())

    def get_shift_plan(self, tenant_id: str, row_id: str) -> ShiftPlan | None:
        return self.session.scalars(
            select(ShiftPlan)
            .where(ShiftPlan.tenant_id == tenant_id, ShiftPlan.id == row_id)
            .options(
                selectinload(ShiftPlan.series_rows).selectinload(ShiftSeries.exceptions),
                selectinload(ShiftPlan.shifts),
            )
        ).one_or_none()

    def find_shift_plan_by_name(self, tenant_id: str, planning_record_id: str, name: str, *, exclude_id: str | None = None) -> ShiftPlan | None:
        statement = select(ShiftPlan).where(
            ShiftPlan.tenant_id == tenant_id,
            ShiftPlan.planning_record_id == planning_record_id,
            ShiftPlan.name == name,
        )
        if exclude_id is not None:
            statement = statement.where(ShiftPlan.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_shift_plan(self, tenant_id: str, payload: ShiftPlanCreate, actor_user_id: str | None) -> ShiftPlan:
        row = ShiftPlan(
            tenant_id=tenant_id,
            planning_record_id=payload.planning_record_id,
            name=payload.name,
            workforce_scope_code=payload.workforce_scope_code,
            planning_from=payload.planning_from,
            planning_to=payload.planning_to,
            remarks=payload.remarks,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_shift_plan(self, tenant_id: str, row_id: str, payload: ShiftPlanUpdate, actor_user_id: str | None) -> ShiftPlan | None:
        return self._update_row(
            ShiftPlan,
            tenant_id,
            row_id,
            payload,
            actor_user_id,
            extra_options=(selectinload(ShiftPlan.series_rows), selectinload(ShiftPlan.shifts)),
        )

    def save_shift_plan(self, row: ShiftPlan) -> ShiftPlan:
        self._commit_or_raise()
        return self.get_shift_plan(row.tenant_id, row.id) or row

    def list_shift_series(self, tenant_id: str, shift_plan_id: str) -> list[ShiftSeries]:
        statement = (
            select(ShiftSeries)
            .where(ShiftSeries.tenant_id == tenant_id, ShiftSeries.shift_plan_id == shift_plan_id)
            .options(selectinload(ShiftSeries.exceptions))
            .order_by(ShiftSeries.date_from, ShiftSeries.label)
        )
        return list(self.session.scalars(statement).all())

    def get_shift_series(self, tenant_id: str, row_id: str) -> ShiftSeries | None:
        return self.session.scalars(
            select(ShiftSeries)
            .where(ShiftSeries.tenant_id == tenant_id, ShiftSeries.id == row_id)
            .options(selectinload(ShiftSeries.exceptions), selectinload(ShiftSeries.shift_template))
        ).one_or_none()

    def create_shift_series(self, tenant_id: str, payload: ShiftSeriesCreate, actor_user_id: str | None) -> ShiftSeries:
        row = ShiftSeries(
            tenant_id=tenant_id,
            shift_plan_id=payload.shift_plan_id,
            shift_template_id=payload.shift_template_id,
            label=payload.label,
            recurrence_code=payload.recurrence_code,
            interval_count=payload.interval_count,
            weekday_mask=payload.weekday_mask,
            timezone=payload.timezone,
            date_from=payload.date_from,
            date_to=payload.date_to,
            default_break_minutes=payload.default_break_minutes,
            shift_type_code=payload.shift_type_code,
            meeting_point=payload.meeting_point,
            location_text=payload.location_text,
            customer_visible_flag=payload.customer_visible_flag,
            subcontractor_visible_flag=payload.subcontractor_visible_flag,
            stealth_mode_flag=payload.stealth_mode_flag,
            release_state=payload.release_state,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_shift_series(self, tenant_id: str, row_id: str, payload: ShiftSeriesUpdate, actor_user_id: str | None) -> ShiftSeries | None:
        return self._update_row(
            ShiftSeries,
            tenant_id,
            row_id,
            payload,
            actor_user_id,
            extra_options=(selectinload(ShiftSeries.exceptions), selectinload(ShiftSeries.shift_template)),
        )

    def save_shift_series(self, row: ShiftSeries) -> ShiftSeries:
        self._commit_or_raise()
        return self.get_shift_series(row.tenant_id, row.id) or row

    def list_shift_series_exceptions(self, tenant_id: str, shift_series_id: str) -> list[ShiftSeriesException]:
        statement = (
            select(ShiftSeriesException)
            .where(
                ShiftSeriesException.tenant_id == tenant_id,
                ShiftSeriesException.shift_series_id == shift_series_id,
            )
            .order_by(ShiftSeriesException.exception_date)
        )
        return list(self.session.scalars(statement).all())

    def get_shift_series_exception(self, tenant_id: str, row_id: str) -> ShiftSeriesException | None:
        return self._get_row(ShiftSeriesException, tenant_id, row_id)

    def get_shift_series_exception_by_date(self, tenant_id: str, shift_series_id: str, exception_date) -> ShiftSeriesException | None:  # noqa: ANN001
        statement = select(ShiftSeriesException).where(
            ShiftSeriesException.tenant_id == tenant_id,
            ShiftSeriesException.shift_series_id == shift_series_id,
            ShiftSeriesException.exception_date == exception_date,
        )
        return self.session.scalars(statement).one_or_none()

    def create_shift_series_exception(
        self,
        tenant_id: str,
        shift_series_id: str,
        payload: ShiftSeriesExceptionCreate,
        actor_user_id: str | None,
    ) -> ShiftSeriesException:
        row = ShiftSeriesException(
            tenant_id=tenant_id,
            shift_series_id=shift_series_id,
            exception_date=payload.exception_date,
            action_code=payload.action_code,
            override_local_start_time=payload.override_local_start_time,
            override_local_end_time=payload.override_local_end_time,
            override_break_minutes=payload.override_break_minutes,
            override_shift_type_code=payload.override_shift_type_code,
            override_meeting_point=payload.override_meeting_point,
            override_location_text=payload.override_location_text,
            customer_visible_flag=payload.customer_visible_flag,
            subcontractor_visible_flag=payload.subcontractor_visible_flag,
            stealth_mode_flag=payload.stealth_mode_flag,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_shift_series_exception(
        self,
        tenant_id: str,
        row_id: str,
        payload: ShiftSeriesExceptionUpdate,
        actor_user_id: str | None,
    ) -> ShiftSeriesException | None:
        return self._update_row(ShiftSeriesException, tenant_id, row_id, payload, actor_user_id)

    def list_shifts(self, tenant_id: str, filters: ShiftListFilter) -> list[Shift]:
        statement = (
            select(Shift)
            .where(Shift.tenant_id == tenant_id)
            .options(selectinload(Shift.shift_plan).selectinload(ShiftPlan.planning_record).selectinload(PlanningRecord.order))
            .order_by(Shift.starts_at, Shift.id)
        )
        if not filters.include_archived:
            statement = statement.where(Shift.archived_at.is_(None))
        if filters.shift_plan_id is not None:
            statement = statement.where(Shift.shift_plan_id == filters.shift_plan_id)
        if filters.date_from is not None:
            statement = statement.where(Shift.starts_at >= filters.date_from)
        if filters.date_to is not None:
            statement = statement.where(Shift.starts_at < filters.date_to)
        if filters.shift_type_code is not None:
            statement = statement.where(Shift.shift_type_code == filters.shift_type_code)
        if filters.release_state is not None:
            statement = statement.where(Shift.release_state == filters.release_state)
        if filters.lifecycle_status is not None:
            statement = statement.where(Shift.status == filters.lifecycle_status)
        visibility_state = getattr(filters, "visibility_state", None)
        if visibility_state == "customer":
            statement = statement.where(Shift.customer_visible_flag.is_(True))
        elif visibility_state == "subcontractor":
            statement = statement.where(Shift.subcontractor_visible_flag.is_(True))
        elif visibility_state == "stealth":
            statement = statement.where(Shift.stealth_mode_flag.is_(True))
        if filters.planning_record_id is not None:
            statement = statement.join(ShiftPlan, ShiftPlan.id == Shift.shift_plan_id).where(
                ShiftPlan.tenant_id == tenant_id,
                ShiftPlan.planning_record_id == filters.planning_record_id,
            )
        return list(self.session.scalars(statement).all())

    def get_shift(self, tenant_id: str, row_id: str) -> Shift | None:
        statement = (
            select(Shift)
            .where(Shift.tenant_id == tenant_id, Shift.id == row_id)
            .options(
                selectinload(Shift.shift_plan).selectinload(ShiftPlan.planning_record).selectinload(PlanningRecord.order),
            )
        )
        return self.session.scalars(statement).one_or_none()

    def list_shifts_for_planning_record(self, tenant_id: str, planning_record_id: str) -> list[Shift]:
        return self.list_shifts(
            tenant_id,
            ShiftListFilter(planning_record_id=planning_record_id, include_archived=False),
        )

    def find_shift_duplicate(
        self,
        tenant_id: str,
        shift_plan_id: str,
        starts_at,
        ends_at,
        shift_type_code: str,
        *,
        exclude_id: str | None = None,
    ) -> Shift | None:
        statement = select(Shift).where(
            Shift.tenant_id == tenant_id,
            Shift.shift_plan_id == shift_plan_id,
            Shift.starts_at == starts_at,
            Shift.ends_at == ends_at,
            Shift.shift_type_code == shift_type_code,
            Shift.archived_at.is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(Shift.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_shift(self, tenant_id: str, payload: ShiftCreate, actor_user_id: str | None) -> Shift:
        row = Shift(
            tenant_id=tenant_id,
            shift_plan_id=payload.shift_plan_id,
            shift_series_id=payload.shift_series_id,
            occurrence_date=payload.occurrence_date,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            break_minutes=payload.break_minutes,
            shift_type_code=payload.shift_type_code,
            location_text=payload.location_text,
            meeting_point=payload.meeting_point,
            release_state=payload.release_state,
            customer_visible_flag=payload.customer_visible_flag,
            subcontractor_visible_flag=payload.subcontractor_visible_flag,
            stealth_mode_flag=payload.stealth_mode_flag,
            source_kind_code=payload.source_kind_code,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_shift(self, tenant_id: str, row_id: str, payload: ShiftUpdate, actor_user_id: str | None) -> Shift | None:
        return self._update_row(Shift, tenant_id, row_id, payload, actor_user_id)

    def save_shift(self, row: Shift) -> Shift:
        self._commit_or_raise()
        return self.get_shift(row.tenant_id, row.id) or row

    def delete_shift(self, tenant_id: str, row_id: str) -> None:
        row = self.get_shift(tenant_id, row_id)
        if row is None:
            return
        self.session.delete(row)
        self._commit_or_raise()

    def delete_shift_by_series_occurrence(self, tenant_id: str, shift_series_id: str, occurrence_date) -> None:  # noqa: ANN001
        row = self.session.scalars(
            select(Shift).where(
                Shift.tenant_id == tenant_id,
                Shift.shift_series_id == shift_series_id,
                Shift.occurrence_date == occurrence_date,
            )
        ).one_or_none()
        if row is None:
            return
        self.session.delete(row)
        self._commit_or_raise()

    def list_board_shifts(self, tenant_id: str, filters: PlanningBoardFilter) -> list[dict[str, object]]:
        statement = (
            select(
                Shift.id,
                Shift.tenant_id,
                ShiftPlan.planning_record_id,
                Shift.shift_plan_id,
                PlanningRecord.order_id,
                CustomerOrder.order_no,
                PlanningRecord.name.label("planning_record_name"),
                PlanningRecord.planning_mode_code,
                ShiftPlan.workforce_scope_code,
                Shift.starts_at,
                Shift.ends_at,
                Shift.shift_type_code,
                Shift.release_state,
                Shift.status,
                Shift.customer_visible_flag,
                Shift.subcontractor_visible_flag,
                Shift.stealth_mode_flag,
                Shift.location_text,
                Shift.meeting_point,
            )
            .join(ShiftPlan, (ShiftPlan.id == Shift.shift_plan_id) & (ShiftPlan.tenant_id == Shift.tenant_id))
            .join(
                PlanningRecord,
                (PlanningRecord.id == ShiftPlan.planning_record_id) & (PlanningRecord.tenant_id == ShiftPlan.tenant_id),
            )
            .join(CustomerOrder, (CustomerOrder.id == PlanningRecord.order_id) & (CustomerOrder.tenant_id == PlanningRecord.tenant_id))
            .where(
                Shift.tenant_id == tenant_id,
                Shift.archived_at.is_(None),
                Shift.starts_at >= filters.date_from,
                Shift.starts_at < filters.date_to,
            )
            .order_by(Shift.starts_at, Shift.id)
        )
        if filters.planning_record_id is not None:
            statement = statement.where(PlanningRecord.id == filters.planning_record_id)
        if filters.order_id is not None:
            statement = statement.where(CustomerOrder.id == filters.order_id)
        if filters.planning_mode_code is not None:
            statement = statement.where(PlanningRecord.planning_mode_code == filters.planning_mode_code)
        if filters.workforce_scope_code is not None:
            statement = statement.where(ShiftPlan.workforce_scope_code == filters.workforce_scope_code)
        if filters.release_state is not None:
            statement = statement.where(Shift.release_state == filters.release_state)
        visibility_state = getattr(filters, "visibility_state", None)
        if visibility_state == "customer":
            statement = statement.where(Shift.customer_visible_flag.is_(True))
        elif visibility_state == "subcontractor":
            statement = statement.where(Shift.subcontractor_visible_flag.is_(True))
        elif visibility_state == "stealth":
            statement = statement.where(Shift.stealth_mode_flag.is_(True))
        rows = self.session.execute(statement).mappings().all()
        return [dict(row) for row in rows]

    def list_demand_groups(self, tenant_id: str, filters: StaffingFilter) -> list[DemandGroup]:
        statement = (
            select(DemandGroup)
            .where(DemandGroup.tenant_id == tenant_id)
            .options(selectinload(DemandGroup.assignments), selectinload(DemandGroup.subcontractor_releases))
            .order_by(DemandGroup.sort_order, DemandGroup.id)
        )
        if not filters.include_archived:
            statement = statement.where(DemandGroup.archived_at.is_(None))
        if filters.shift_id is not None:
            statement = statement.where(DemandGroup.shift_id == filters.shift_id)
        if filters.demand_group_id is not None:
            statement = statement.where(DemandGroup.id == filters.demand_group_id)
        return list(self.session.scalars(statement).all())

    def list_demand_groups_in_shift(self, tenant_id: str, shift_id: str) -> list[DemandGroup]:
        return self.list_demand_groups(tenant_id, StaffingFilter(shift_id=shift_id, include_archived=False))

    def get_demand_group(self, tenant_id: str, row_id: str) -> DemandGroup | None:
        statement = (
            select(DemandGroup)
            .where(DemandGroup.tenant_id == tenant_id, DemandGroup.id == row_id)
            .options(selectinload(DemandGroup.assignments), selectinload(DemandGroup.subcontractor_releases))
        )
        return self.session.scalars(statement).one_or_none()

    def create_demand_group(self, tenant_id: str, payload: DemandGroupCreate, actor_user_id: str | None) -> DemandGroup:
        row = DemandGroup(
            tenant_id=tenant_id,
            shift_id=payload.shift_id,
            function_type_id=payload.function_type_id,
            qualification_type_id=payload.qualification_type_id,
            min_qty=payload.min_qty,
            target_qty=payload.target_qty,
            mandatory_flag=payload.mandatory_flag,
            sort_order=payload.sort_order,
            remark=payload.remark,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_demand_group(self, tenant_id: str, row_id: str, payload: DemandGroupUpdate, actor_user_id: str | None) -> DemandGroup | None:
        return self._update_row(DemandGroup, tenant_id, row_id, payload, actor_user_id)

    def list_teams(self, tenant_id: str, filters: StaffingFilter) -> list[Team]:
        statement = (
            select(Team)
            .where(Team.tenant_id == tenant_id)
            .options(selectinload(Team.members), selectinload(Team.assignments))
            .order_by(Team.name, Team.id)
        )
        if not filters.include_archived:
            statement = statement.where(Team.archived_at.is_(None))
        if filters.planning_record_id is not None:
            statement = statement.where(Team.planning_record_id == filters.planning_record_id)
        if filters.shift_id is not None:
            statement = statement.where(Team.shift_id == filters.shift_id)
        if filters.team_id is not None:
            statement = statement.where(Team.id == filters.team_id)
        return list(self.session.scalars(statement).all())

    def get_team(self, tenant_id: str, row_id: str) -> Team | None:
        statement = (
            select(Team)
            .where(Team.tenant_id == tenant_id, Team.id == row_id)
            .options(selectinload(Team.members), selectinload(Team.assignments))
        )
        return self.session.scalars(statement).one_or_none()

    def create_team(self, tenant_id: str, payload: TeamCreate, actor_user_id: str | None) -> Team:
        row = Team(
            tenant_id=tenant_id,
            planning_record_id=payload.planning_record_id,
            shift_id=payload.shift_id,
            name=payload.name,
            role_label=payload.role_label,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_team(self, tenant_id: str, row_id: str, payload: TeamUpdate, actor_user_id: str | None) -> Team | None:
        return self._update_row(Team, tenant_id, row_id, payload, actor_user_id)

    def list_team_members(self, tenant_id: str, filters: StaffingFilter) -> list[TeamMember]:
        statement = (
            select(TeamMember)
            .where(TeamMember.tenant_id == tenant_id)
            .options(selectinload(TeamMember.employee), selectinload(TeamMember.subcontractor_worker))
            .order_by(TeamMember.valid_from, TeamMember.id)
        )
        if not filters.include_archived:
            statement = statement.where(TeamMember.archived_at.is_(None))
        if filters.team_id is not None:
            statement = statement.where(TeamMember.team_id == filters.team_id)
        if filters.employee_id is not None:
            statement = statement.where(TeamMember.employee_id == filters.employee_id)
        if filters.subcontractor_worker_id is not None:
            statement = statement.where(TeamMember.subcontractor_worker_id == filters.subcontractor_worker_id)
        return list(self.session.scalars(statement).all())

    def get_team_member(self, tenant_id: str, row_id: str) -> TeamMember | None:
        statement = (
            select(TeamMember)
            .where(TeamMember.tenant_id == tenant_id, TeamMember.id == row_id)
            .options(selectinload(TeamMember.employee), selectinload(TeamMember.subcontractor_worker))
        )
        return self.session.scalars(statement).one_or_none()

    def create_team_member(self, tenant_id: str, payload: TeamMemberCreate, actor_user_id: str | None) -> TeamMember:
        row = TeamMember(
            tenant_id=tenant_id,
            team_id=payload.team_id,
            employee_id=payload.employee_id,
            subcontractor_worker_id=payload.subcontractor_worker_id,
            role_label=payload.role_label,
            is_team_lead=payload.is_team_lead,
            valid_from=payload.valid_from,
            valid_to=payload.valid_to,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_team_member(self, tenant_id: str, row_id: str, payload: TeamMemberUpdate, actor_user_id: str | None) -> TeamMember | None:
        return self._update_row(TeamMember, tenant_id, row_id, payload, actor_user_id)

    def list_assignments(self, tenant_id: str, filters: StaffingFilter) -> list[Assignment]:
        statement = (
            select(Assignment)
            .where(Assignment.tenant_id == tenant_id)
            .options(selectinload(Assignment.employee), selectinload(Assignment.subcontractor_worker))
            .order_by(Assignment.created_at, Assignment.id)
        )
        if not filters.include_archived:
            statement = statement.where(Assignment.archived_at.is_(None))
        if filters.shift_id is not None:
            statement = statement.where(Assignment.shift_id == filters.shift_id)
        if filters.demand_group_id is not None:
            statement = statement.where(Assignment.demand_group_id == filters.demand_group_id)
        if filters.team_id is not None:
            statement = statement.where(Assignment.team_id == filters.team_id)
        if filters.employee_id is not None:
            statement = statement.where(Assignment.employee_id == filters.employee_id)
        if filters.subcontractor_worker_id is not None:
            statement = statement.where(Assignment.subcontractor_worker_id == filters.subcontractor_worker_id)
        if filters.assignment_status_code is not None:
            statement = statement.where(Assignment.assignment_status_code == filters.assignment_status_code)
        return list(self.session.scalars(statement).all())

    def list_assignments_in_shift(self, tenant_id: str, shift_id: str) -> list[Assignment]:
        statement = (
            select(Assignment)
            .where(Assignment.tenant_id == tenant_id, Assignment.shift_id == shift_id, Assignment.archived_at.is_(None))
            .options(selectinload(Assignment.employee), selectinload(Assignment.subcontractor_worker))
            .order_by(Assignment.created_at, Assignment.id)
        )
        return list(self.session.scalars(statement).all())

    def get_assignment(self, tenant_id: str, row_id: str) -> Assignment | None:
        statement = (
            select(Assignment)
            .where(Assignment.tenant_id == tenant_id, Assignment.id == row_id)
            .options(
                selectinload(Assignment.employee),
                selectinload(Assignment.subcontractor_worker),
                selectinload(Assignment.validation_overrides),
            )
        )
        return self.session.scalars(statement).one_or_none()

    def create_assignment(self, tenant_id: str, payload: AssignmentCreate, actor_user_id: str | None) -> Assignment:
        row = Assignment(
            tenant_id=tenant_id,
            shift_id=payload.shift_id,
            demand_group_id=payload.demand_group_id,
            team_id=payload.team_id,
            employee_id=payload.employee_id,
            subcontractor_worker_id=payload.subcontractor_worker_id,
            assignment_status_code=payload.assignment_status_code,
            assignment_source_code=payload.assignment_source_code,
            offered_at=payload.offered_at,
            confirmed_at=payload.confirmed_at,
            remarks=payload.remarks,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def update_assignment(self, tenant_id: str, row_id: str, payload: AssignmentUpdate, actor_user_id: str | None) -> Assignment | None:
        return self._update_row(Assignment, tenant_id, row_id, payload, actor_user_id)

    def list_overlapping_assignments(
        self,
        tenant_id: str,
        *,
        starts_at: datetime,
        ends_at: datetime,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
        exclude_assignment_id: str | None = None,
    ) -> list[Assignment]:
        statement = select(Assignment).join(Shift, and_(Shift.tenant_id == Assignment.tenant_id, Shift.id == Assignment.shift_id)).where(
            Assignment.tenant_id == tenant_id,
            Assignment.archived_at.is_(None),
            Assignment.assignment_status_code != "removed",
            Shift.archived_at.is_(None),
            Shift.starts_at < ends_at,
            Shift.ends_at > starts_at,
        )
        if employee_id is not None:
            statement = statement.where(Assignment.employee_id == employee_id)
        if subcontractor_worker_id is not None:
            statement = statement.where(Assignment.subcontractor_worker_id == subcontractor_worker_id)
        if exclude_assignment_id is not None:
            statement = statement.where(Assignment.id != exclude_assignment_id)
        return list(self.session.scalars(statement).all())

    def list_assignments_for_actor_in_window(
        self,
        tenant_id: str,
        *,
        employee_id: str | None,
        subcontractor_worker_id: str | None,
        window_start: datetime,
        window_end: datetime,
        exclude_assignment_id: str | None = None,
    ) -> list[Assignment]:
        return self.list_overlapping_assignments(
            tenant_id,
            starts_at=window_start,
            ends_at=window_end,
            employee_id=employee_id,
            subcontractor_worker_id=subcontractor_worker_id,
            exclude_assignment_id=exclude_assignment_id,
        )

    def list_subcontractor_releases(self, tenant_id: str, filters: StaffingFilter) -> list[SubcontractorRelease]:
        statement = (
            select(SubcontractorRelease)
            .where(SubcontractorRelease.tenant_id == tenant_id)
            .options(selectinload(SubcontractorRelease.subcontractor))
            .order_by(SubcontractorRelease.created_at, SubcontractorRelease.id)
        )
        if not filters.include_archived:
            statement = statement.where(SubcontractorRelease.archived_at.is_(None))
        if filters.shift_id is not None:
            statement = statement.where(SubcontractorRelease.shift_id == filters.shift_id)
        if filters.demand_group_id is not None:
            statement = statement.where(SubcontractorRelease.demand_group_id == filters.demand_group_id)
        if filters.subcontractor_id is not None:
            statement = statement.where(SubcontractorRelease.subcontractor_id == filters.subcontractor_id)
        return list(self.session.scalars(statement).all())

    def list_subcontractor_releases_for_shift(self, tenant_id: str, shift_id: str) -> list[SubcontractorRelease]:
        return self.list_subcontractor_releases(tenant_id, StaffingFilter(shift_id=shift_id, include_archived=False))

    def get_subcontractor_release(self, tenant_id: str, row_id: str) -> SubcontractorRelease | None:
        statement = (
            select(SubcontractorRelease)
            .where(SubcontractorRelease.tenant_id == tenant_id, SubcontractorRelease.id == row_id)
            .options(selectinload(SubcontractorRelease.subcontractor))
        )
        return self.session.scalars(statement).one_or_none()

    def create_subcontractor_release(self, tenant_id: str, payload: SubcontractorReleaseCreate, actor_user_id: str | None) -> SubcontractorRelease:
        row = SubcontractorRelease(
            tenant_id=tenant_id,
            shift_id=payload.shift_id,
            demand_group_id=payload.demand_group_id,
            subcontractor_id=payload.subcontractor_id,
            released_qty=payload.released_qty,
            release_status_code=payload.release_status_code,
            remarks=payload.remarks,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        return self._create_row(row)

    def list_assignment_validation_overrides(self, tenant_id: str, assignment_id: str) -> list[AssignmentValidationOverride]:
        statement = (
            select(AssignmentValidationOverride)
            .where(
                AssignmentValidationOverride.tenant_id == tenant_id,
                AssignmentValidationOverride.assignment_id == assignment_id,
            )
            .order_by(AssignmentValidationOverride.created_at, AssignmentValidationOverride.id)
        )
        return list(self.session.scalars(statement).all())

    def create_assignment_validation_override(self, row: AssignmentValidationOverride) -> AssignmentValidationOverride:
        self.session.add(row)
        self._commit_or_raise()
        self.session.refresh(row)
        return row

    def update_subcontractor_release(self, tenant_id: str, row_id: str, payload: SubcontractorReleaseUpdate, actor_user_id: str | None) -> SubcontractorRelease | None:
        return self._update_row(SubcontractorRelease, tenant_id, row_id, payload, actor_user_id)

    def _list_rows(
        self,
        model,
        tenant_id: str,
        filters: OpsMasterFilter,
        *,
        extra_options: Sequence[object] = (),
    ) -> list:
        statement = select(model).where(model.tenant_id == tenant_id).options(*extra_options).order_by(model.code if hasattr(model, "code") else model.id)
        if hasattr(model, "site_no"):
            statement = statement.order_by(model.site_no)
        elif hasattr(model, "venue_no"):
            statement = statement.order_by(model.venue_no)
        elif hasattr(model, "fair_no"):
            statement = statement.order_by(model.fair_no)
        elif hasattr(model, "route_no"):
            statement = statement.order_by(model.route_no)
        if not filters.include_archived:
            statement = statement.where(model.archived_at.is_(None))
        if filters.lifecycle_status is not None:
            statement = statement.where(model.status == filters.lifecycle_status)
        if (
            filters.customer_id is not None
            and hasattr(model, "customer_id")
            and model not in self.TENANT_SCOPED_OPS_MODELS
        ):
            statement = statement.where(model.customer_id == filters.customer_id)
        if filters.search:
            like_term = f"%{filters.search.strip().lower()}%"
            fields = []
            for field_name in ("code", "label", "site_no", "venue_no", "fair_no", "route_no", "name"):
                if hasattr(model, field_name):
                    fields.append(func.lower(func.coalesce(getattr(model, field_name), "")).like(like_term))
            if fields:
                statement = statement.where(or_(*fields))
        return list(self.session.scalars(statement).all())

    def _get_row(
        self,
        model,
        tenant_id: str,
        row_id: str,
        *,
        extra_options: Sequence[object] = (),
    ):
        statement = select(model).where(model.tenant_id == tenant_id, model.id == row_id).options(*extra_options)
        return self.session.scalars(statement).one_or_none()

    def _create_row(self, row):
        self.session.add(row)
        self._commit_or_raise()
        return row

    def _update_row(
        self,
        model,
        tenant_id: str,
        row_id: str,
        payload,
        actor_user_id: str | None,
        *,
        extra_options: Sequence[object] = (),
        exclude_fields: set[str] | None = None,
        normalize_blank_uuid_fields: set[str] | None = None,
    ):
        row = self._get_row(model, tenant_id, row_id, extra_options=extra_options)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, model.__name__)
        excluded = {"version_no"}
        if exclude_fields:
            excluded.update(exclude_fields)
        for key, value in payload.model_dump(exclude_unset=True, exclude=excluded).items():
            if normalize_blank_uuid_fields and key in normalize_blank_uuid_fields:
                value = self._normalize_optional_uuid_value(value)
            setattr(row, key, value)
        row.updated_by_user_id = actor_user_id
        row.version_no += 1
        self._commit_or_raise()
        return self._get_row(model, tenant_id, row_id, extra_options=extra_options) or row

    @staticmethod
    def _normalize_optional_uuid_value(value: str | None) -> str | None:
        if value == "":
            return None
        return value

    def _find_by_code(self, model, tenant_id: str, code: str, *, field_name: str = "code", exclude_id: str | None = None):
        statement = select(model).where(model.tenant_id == tenant_id, getattr(model, field_name) == code)
        if exclude_id is not None:
            statement = statement.where(model.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def _assert_version(self, current_version: int, provided_version: int | None, resource_key: str) -> None:
        if provided_version is None or provided_version != current_version:
            resource_code = self.STALE_RESOURCE_CODES.get(resource_key, resource_key.lower())
            raise ApiException(
                409,
                f"planning.{resource_key}.stale_version",
                f"errors.planning.{resource_code}.stale_version",
                {"current_version": current_version},
            )

    def _commit_or_raise(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ApiException(409, "planning.conflict.integrity", "errors.planning.conflict.integrity") from exc
