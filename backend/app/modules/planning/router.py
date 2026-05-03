"""HTTP API for planning operational master maintenance."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.errors import ApiException
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization, require_permission_only
from app.modules.platform_services.comm_repository import SqlAlchemyCommunicationRepository
from app.modules.platform_services.comm_schemas import OutboundMessageRead
from app.modules.platform_services.comm_service import CommunicationService
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import build_object_storage_adapter
from app.modules.planning.communication_service import PlanningCommunicationService
from app.modules.planning.commercial_link_service import PlanningCommercialLinkService
from app.modules.planning.output_service import PlanningOutputService
from app.modules.planning.released_schedule_service import ReleasedScheduleService
from app.modules.planning.repository import SqlAlchemyPlanningRepository
from app.modules.planning.schemas import (
    AssignmentStepApplyRequest,
    AssignmentStepApplyResult,
    AssignmentStepCandidateQueryResult,
    AssignmentStepScopeRequest,
    AssignmentStepSnapshotRead,
    AssignmentValidationOverrideCreate,
    AssignmentValidationOverrideRead,
    AssignmentValidationRead,
    AssignmentCreate,
    AssignmentRead,
    AssignmentUpdate,
    CoverageFilter,
    CoverageShiftItem,
    CustomerOrderAttachmentCreate,
    CustomerOrderAttachmentLinkCreate,
    CustomerOrderCreate,
    CustomerOrderFilter,
    CustomerOrderListItem,
    CustomerOrderRead,
    CustomerOrderReleaseStateUpdate,
    CustomerOrderUpdate,
    EquipmentItemCreate,
    EquipmentItemListItem,
    EventVenueLocationProjectionRead,
    DemandGroupBulkApplyRequest,
    DemandGroupBulkApplyResult,
    DemandGroupBulkUpdateRequest,
    DemandGroupBulkUpdateResult,
    DemandGroupCreate,
    DemandGroupRead,
    DemandGroupUpdate,
    EquipmentItemRead,
    EquipmentItemUpdate,
    EventVenueCreate,
    EventVenueListItem,
    EventVenueRead,
    EventVenueUpdate,
    OpsMasterFilter,
    OrderAttachmentRead,
    OrderEquipmentLineCreate,
    OrderEquipmentLineRead,
    OrderEquipmentLineUpdate,
    OrderRequirementLineCreate,
    OrderRequirementLineRead,
    OrderRequirementLineUpdate,
    PlanningRecordCreate,
    PlanningRecordAttachmentCreate,
    PlanningRecordAttachmentLinkCreate,
    PlanningRecordAttachmentRead,
    PlanningRecordFilter,
    PlanningDispatcherCandidateRead,
    PlanningRecordListItem,
    PlanningRecordRead,
    PlanningRecordReleaseValidationRead,
    PlanningRecordReleaseStateUpdate,
    PlanningRecordUpdate,
    PlanningOpsImportDryRunRequest,
    PlanningOpsImportDryRunResult,
    PlanningOpsImportExecuteRequest,
    PlanningOpsImportExecuteResult,
    PatrolCheckpointCreate,
    PatrolCheckpointRead,
    PatrolCheckpointUpdate,
    PatrolRouteCreate,
    PlanningCommercialLinkRead,
    PatrolRouteLocationProjectionRead,
    PatrolRouteListItem,
    PatrolRouteRead,
    PatrolRouteUpdate,
    PlanningReferenceOptionRead,
    RequirementTypeCreate,
    RequirementTypeListItem,
    RequirementTypeRead,
    RequirementTypeUpdate,
    ServiceCategoryCreate,
    ServiceCategoryListItem,
    ServiceCategoryRead,
    ServiceCategoryUpdate,
    SiteCreate,
    SiteListItem,
    SiteLocationProjectionRead,
    SiteRead,
    SiteUpdate,
    ShiftCopyRequest,
    ShiftCopyResult,
    ShiftCreate,
    ShiftListFilter,
    ShiftListItem,
    ShiftPlanCreate,
    ShiftPlanFilter,
    ShiftPlanListItem,
    ShiftPlanRead,
    ShiftPlanUpdate,
    ShiftRead,
    ShiftSeriesCreate,
    ShiftSeriesExceptionCreate,
    ShiftSeriesExceptionRead,
    ShiftSeriesExceptionUpdate,
    ShiftSeriesGenerationRequest,
    ShiftSeriesListItem,
    ShiftSeriesRead,
    ShiftSeriesUpdate,
    ShiftReleaseDiagnosticsRead,
    ShiftReleaseStateUpdate,
    ShiftReleaseValidationRead,
    ShiftTemplateCreate,
    ShiftTemplateListItem,
    ShiftTypeOptionRead,
    ShiftTemplateRead,
    ShiftTemplateUpdate,
    ShiftUpdate,
    ShiftVisibilityUpdate,
    PlanningBoardFilter,
    PlanningBoardShiftListItem,
    PlanningDispatchCreate,
    PlanningDispatchPreviewRead,
    PlanningOutputDocumentRead,
    PlanningOutputGenerateRequest,
    StaffingAssignCommand,
    StaffingBoardFilter,
    StaffingBoardShiftItem,
    StaffingCommandResult,
    StaffingFilter,
    StaffingSubstituteCommand,
    StaffingUnassignCommand,
    SubcontractorReleaseCreate,
    SubcontractorReleaseRead,
    SubcontractorReleaseUpdate,
    TeamCreate,
    TeamMemberCreate,
    TeamMemberRead,
    TeamMemberUpdate,
    TeamRead,
    TeamUpdate,
    TradeFairCreate,
    TradeFairLocationProjectionRead,
    TradeFairListItem,
    TradeFairRead,
    TradeFairZoneCreate,
    TradeFairZoneRead,
    TradeFairZoneUpdate,
    TradeFairUpdate,
)
from app.modules.planning.ops_service import PlanningOpsService
from app.modules.planning.order_service import CustomerOrderService
from app.modules.planning.planning_record_service import PlanningRecordService
from app.modules.planning.staffing_service import StaffingService
from app.modules.planning.shift_service import ShiftPlanningService
from app.modules.planning.service import PlanningService
from app.modules.planning.validation_service import PlanningValidationService
from app.config import settings


router = APIRouter(prefix="/api/planning/tenants/{tenant_id}/ops", tags=["planning"])


def _build_planning_validation_service(repository: SqlAlchemyPlanningRepository) -> PlanningValidationService:
    return PlanningValidationService(repository)


def get_planning_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> PlanningService:
    return PlanningService(
        SqlAlchemyPlanningRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_planning_ops_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> PlanningOpsService:
    repository = SqlAlchemyPlanningRepository(session)
    return PlanningOpsService(
        planning_service=PlanningService(repository, audit_service=AuditService(SqlAlchemyAuditRepository(session))),
        repository=repository,
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_customer_order_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> CustomerOrderService:
    repository = SqlAlchemyPlanningRepository(session)
    document_repository = SqlAlchemyDocumentRepository(session)
    commercial_link_service = PlanningCommercialLinkService(repository)
    return CustomerOrderService(
        repository,
        document_repository=document_repository,
        document_service=DocumentService(
            document_repository,
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        commercial_link_service=commercial_link_service,
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_planning_record_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> PlanningRecordService:
    repository = SqlAlchemyPlanningRepository(session)
    document_repository = SqlAlchemyDocumentRepository(session)
    commercial_link_service = PlanningCommercialLinkService(repository)
    return PlanningRecordService(
        repository,
        document_repository=document_repository,
        document_service=DocumentService(
            document_repository,
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        commercial_link_service=commercial_link_service,
        validation_service=_build_planning_validation_service(repository),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_planning_commercial_link_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> PlanningCommercialLinkService:
    return PlanningCommercialLinkService(SqlAlchemyPlanningRepository(session))


def get_shift_planning_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> ShiftPlanningService:
    repository = SqlAlchemyPlanningRepository(session)
    return ShiftPlanningService(
        repository,
        validation_service=_build_planning_validation_service(repository),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_staffing_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> StaffingService:
    repository = SqlAlchemyPlanningRepository(session)
    return StaffingService(
        repository,
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_planning_output_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> PlanningOutputService:
    repository = SqlAlchemyPlanningRepository(session)
    return PlanningOutputService(
        repository,
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
    )


def get_planning_communication_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> PlanningCommunicationService:
    document_service = DocumentService(
        SqlAlchemyDocumentRepository(session),
        storage=build_object_storage_adapter(settings),
        bucket_name=settings.object_storage_bucket,
    )
    return PlanningCommunicationService(
        SqlAlchemyPlanningRepository(session),
        communication_service=CommunicationService(
            SqlAlchemyCommunicationRepository(session),
            document_service=document_service,
        ),
    )


def get_released_schedule_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> ReleasedScheduleService:
    return ReleasedScheduleService(SqlAlchemyPlanningRepository(session))


def _filters(
    search: str | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
) -> OpsMasterFilter:
    return OpsMasterFilter(
        search=search,
        customer_id=str(customer_id) if customer_id else None,
        lifecycle_status=lifecycle_status,
        include_archived=include_archived,
    )


def _order_filters(
    search: str | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    release_state: str | None = Query(default=None),
    service_from: date | None = Query(default=None),
    service_to: date | None = Query(default=None),
    planning_entity_type: str | None = Query(default=None),
    planning_entity_id: UUID | None = Query(default=None),
    include_archived: bool = Query(default=False),
) -> CustomerOrderFilter:
    return CustomerOrderFilter(
        search=search,
        customer_id=str(customer_id) if customer_id else None,
        lifecycle_status=lifecycle_status,
        release_state=release_state,
        service_from=service_from,
        service_to=service_to,
        planning_entity_type=planning_entity_type,
        planning_entity_id=str(planning_entity_id) if planning_entity_id else None,
        include_archived=include_archived,
    )


def _planning_record_filters(
    search: str | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    order_id: UUID | None = Query(default=None),
    planning_mode_code: str | None = Query(default=None),
    planning_entity_type: str | None = Query(default=None),
    planning_entity_id: UUID | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    release_state: str | None = Query(default=None),
    dispatcher_user_id: UUID | None = Query(default=None),
    planning_from: date | None = Query(default=None),
    planning_to: date | None = Query(default=None),
    include_archived: bool = Query(default=False),
) -> PlanningRecordFilter:
    return PlanningRecordFilter(
        search=search,
        customer_id=str(customer_id) if customer_id else None,
        order_id=str(order_id) if order_id else None,
        planning_mode_code=planning_mode_code,
        planning_entity_type=planning_entity_type,
        planning_entity_id=str(planning_entity_id) if planning_entity_id else None,
        lifecycle_status=lifecycle_status,
        release_state=release_state,
        dispatcher_user_id=str(dispatcher_user_id) if dispatcher_user_id else None,
        planning_from=planning_from,
        planning_to=planning_to,
        include_archived=include_archived,
    )


def _shift_plan_filters(
    planning_record_id: UUID | None = Query(default=None),
    workforce_scope_code: str | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
) -> ShiftPlanFilter:
    return ShiftPlanFilter(
        planning_record_id=str(planning_record_id) if planning_record_id else None,
        workforce_scope_code=workforce_scope_code,
        lifecycle_status=lifecycle_status,
        include_archived=include_archived,
    )


def _shift_filters(
    shift_plan_id: UUID | None = Query(default=None),
    planning_record_id: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    shift_type_code: str | None = Query(default=None),
    release_state: str | None = Query(default=None),
    visibility_state: str | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
) -> ShiftListFilter:
    return ShiftListFilter(
        shift_plan_id=str(shift_plan_id) if shift_plan_id else None,
        planning_record_id=str(planning_record_id) if planning_record_id else None,
        date_from=date_from,
        date_to=date_to,
        shift_type_code=shift_type_code,
        release_state=release_state,
        visibility_state=visibility_state,
        lifecycle_status=lifecycle_status,
        include_archived=include_archived,
    )


def _board_filters(
    date_from: datetime,
    date_to: datetime,
    planning_record_id: UUID | None = Query(default=None),
    order_id: UUID | None = Query(default=None),
    planning_mode_code: str | None = Query(default=None),
    workforce_scope_code: str | None = Query(default=None),
    release_state: str | None = Query(default=None),
    visibility_state: str | None = Query(default=None),
) -> PlanningBoardFilter:
    return PlanningBoardFilter(
        planning_record_id=str(planning_record_id) if planning_record_id else None,
        order_id=str(order_id) if order_id else None,
        date_from=date_from,
        date_to=date_to,
        planning_mode_code=planning_mode_code,
        workforce_scope_code=workforce_scope_code,
        release_state=release_state,
        visibility_state=visibility_state,
    )


def _staffing_filters(
    shift_id: UUID | None = Query(default=None),
    shift_plan_id: UUID | None = Query(default=None),
    planning_record_id: UUID | None = Query(default=None),
    demand_group_id: UUID | None = Query(default=None),
    team_id: UUID | None = Query(default=None),
    employee_id: UUID | None = Query(default=None),
    subcontractor_worker_id: UUID | None = Query(default=None),
    subcontractor_id: UUID | None = Query(default=None),
    assignment_status_code: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
) -> StaffingFilter:
    return StaffingFilter(
        shift_id=str(shift_id) if shift_id else None,
        shift_plan_id=str(shift_plan_id) if shift_plan_id else None,
        planning_record_id=str(planning_record_id) if planning_record_id else None,
        demand_group_id=str(demand_group_id) if demand_group_id else None,
        team_id=str(team_id) if team_id else None,
        employee_id=str(employee_id) if employee_id else None,
        subcontractor_worker_id=str(subcontractor_worker_id) if subcontractor_worker_id else None,
        subcontractor_id=str(subcontractor_id) if subcontractor_id else None,
        assignment_status_code=assignment_status_code,
        include_archived=include_archived,
    )


def _staffing_board_filters(
    customer_id: UUID | None = Query(default=None),
    planning_record_id: UUID | None = Query(default=None),
    shift_plan_id: UUID | None = Query(default=None),
    shift_id: UUID | None = Query(default=None),
    order_id: UUID | None = Query(default=None),
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    planning_mode_code: str | None = Query(default=None),
    workforce_scope_code: str | None = Query(default=None),
    function_type_id: UUID | None = Query(default=None),
    qualification_type_id: UUID | None = Query(default=None),
    release_state: str | None = Query(default=None),
    visibility_state: str | None = Query(default=None),
    assignment_status_code: str | None = Query(default=None),
    confirmation_state: str | None = Query(default=None),
) -> StaffingBoardFilter:
    return StaffingBoardFilter(
        customer_id=str(customer_id) if customer_id else None,
        planning_record_id=str(planning_record_id) if planning_record_id else None,
        shift_plan_id=str(shift_plan_id) if shift_plan_id else None,
        shift_id=str(shift_id) if shift_id else None,
        order_id=str(order_id) if order_id else None,
        date_from=date_from,
        date_to=date_to,
        planning_mode_code=planning_mode_code,
        workforce_scope_code=workforce_scope_code,
        function_type_id=str(function_type_id) if function_type_id else None,
        qualification_type_id=str(qualification_type_id) if qualification_type_id else None,
        release_state=release_state,
        visibility_state=visibility_state,
        assignment_status_code=assignment_status_code,
        confirmation_state=confirmation_state,
    )


def _coverage_filters(
    customer_id: UUID | None = Query(default=None),
    planning_record_id: UUID | None = Query(default=None),
    shift_plan_id: UUID | None = Query(default=None),
    order_id: UUID | None = Query(default=None),
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    planning_mode_code: str | None = Query(default=None),
    workforce_scope_code: str | None = Query(default=None),
    function_type_id: UUID | None = Query(default=None),
    qualification_type_id: UUID | None = Query(default=None),
    release_state: str | None = Query(default=None),
    visibility_state: str | None = Query(default=None),
    confirmation_state: str | None = Query(default=None),
) -> CoverageFilter:
    return CoverageFilter(
        customer_id=str(customer_id) if customer_id else None,
        planning_record_id=str(planning_record_id) if planning_record_id else None,
        shift_plan_id=str(shift_plan_id) if shift_plan_id else None,
        order_id=str(order_id) if order_id else None,
        date_from=date_from,
        date_to=date_to,
        planning_mode_code=planning_mode_code,
        workforce_scope_code=workforce_scope_code,
        function_type_id=str(function_type_id) if function_type_id else None,
        qualification_type_id=str(qualification_type_id) if qualification_type_id else None,
        release_state=release_state,
        visibility_state=visibility_state,
        confirmation_state=confirmation_state,
    )


@router.get("/requirement-types", response_model=list[RequirementTypeListItem])
def list_requirement_types(
    tenant_id: UUID,
    filters: Annotated[OpsMasterFilter, Depends(_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> list[RequirementTypeListItem]:
    return service.list_requirement_types(str(tenant_id), filters, context)


@router.post("/requirement-types", response_model=RequirementTypeRead, status_code=status.HTTP_201_CREATED)
def create_requirement_type(
    tenant_id: UUID,
    payload: RequirementTypeCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> RequirementTypeRead:
    return service.create_requirement_type(str(tenant_id), payload, context)


@router.get("/requirement-types/{row_id}", response_model=RequirementTypeRead)
def get_requirement_type(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> RequirementTypeRead:
    return service.get_requirement_type(str(tenant_id), str(row_id), context)


@router.patch("/requirement-types/{row_id}", response_model=RequirementTypeRead)
def update_requirement_type(
    tenant_id: UUID,
    row_id: UUID,
    payload: RequirementTypeUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> RequirementTypeRead:
    return service.update_requirement_type(str(tenant_id), str(row_id), payload, context)


@router.get("/equipment-items", response_model=list[EquipmentItemListItem])
def list_equipment_items(
    tenant_id: UUID,
    filters: Annotated[OpsMasterFilter, Depends(_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> list[EquipmentItemListItem]:
    return service.list_equipment_items(str(tenant_id), filters, context)


@router.get("/equipment-unit-options", response_model=list[PlanningReferenceOptionRead])
def list_equipment_unit_options(
    tenant_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> list[PlanningReferenceOptionRead]:
    return service.list_equipment_unit_options(str(tenant_id), context)


@router.get("/service-category-options", response_model=list[PlanningReferenceOptionRead])
def list_service_category_options(
    tenant_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> list[PlanningReferenceOptionRead]:
    return service.list_service_category_options(str(tenant_id), context)


@router.get("/service-categories", response_model=list[ServiceCategoryListItem])
def list_service_categories(
    tenant_id: UUID,
    filters: Annotated[OpsMasterFilter, Depends(_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> list[ServiceCategoryListItem]:
    return service.list_service_categories(str(tenant_id), filters, context)


@router.post("/service-categories", response_model=ServiceCategoryRead, status_code=status.HTTP_201_CREATED)
def create_service_category(
    tenant_id: UUID,
    payload: ServiceCategoryCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> ServiceCategoryRead:
    return service.create_service_category(str(tenant_id), payload, context)


@router.get("/service-categories/{row_id}", response_model=ServiceCategoryRead)
def get_service_category(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> ServiceCategoryRead:
    return service.get_service_category(str(tenant_id), str(row_id), context)


@router.patch("/service-categories/{row_id}", response_model=ServiceCategoryRead)
def update_service_category(
    tenant_id: UUID,
    row_id: UUID,
    payload: ServiceCategoryUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> ServiceCategoryRead:
    return service.update_service_category(str(tenant_id), str(row_id), payload, context)


@router.post("/equipment-items", response_model=EquipmentItemRead, status_code=status.HTTP_201_CREATED)
def create_equipment_item(
    tenant_id: UUID,
    payload: EquipmentItemCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> EquipmentItemRead:
    return service.create_equipment_item(str(tenant_id), payload, context)


@router.get("/equipment-items/{row_id}", response_model=EquipmentItemRead)
def get_equipment_item(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> EquipmentItemRead:
    return service.get_equipment_item(str(tenant_id), str(row_id), context)


@router.patch("/equipment-items/{row_id}", response_model=EquipmentItemRead)
def update_equipment_item(
    tenant_id: UUID,
    row_id: UUID,
    payload: EquipmentItemUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> EquipmentItemRead:
    return service.update_equipment_item(str(tenant_id), str(row_id), payload, context)


@router.get("/sites", response_model=list[SiteListItem])
def list_sites(
    tenant_id: UUID,
    filters: Annotated[OpsMasterFilter, Depends(_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> list[SiteListItem]:
    return service.list_sites(str(tenant_id), filters, context)


@router.post("/sites", response_model=SiteRead, status_code=status.HTTP_201_CREATED)
def create_site(
    tenant_id: UUID,
    payload: SiteCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> SiteRead:
    return service.create_site(str(tenant_id), payload, context)


@router.get("/sites/{row_id}", response_model=SiteRead)
def get_site(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> SiteRead:
    return service.get_site(str(tenant_id), str(row_id), context)


@router.get("/sites/{row_id}/location", response_model=SiteLocationProjectionRead)
def get_site_location_projection(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> SiteLocationProjectionRead:
    return service.get_site_location_projection(str(tenant_id), str(row_id), context)


@router.patch("/sites/{row_id}", response_model=SiteRead)
def update_site(
    tenant_id: UUID,
    row_id: UUID,
    payload: SiteUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> SiteRead:
    return service.update_site(str(tenant_id), str(row_id), payload, context)


@router.get("/event-venues", response_model=list[EventVenueListItem])
def list_event_venues(
    tenant_id: UUID,
    filters: Annotated[OpsMasterFilter, Depends(_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> list[EventVenueListItem]:
    return service.list_event_venues(str(tenant_id), filters, context)


@router.post("/event-venues", response_model=EventVenueRead, status_code=status.HTTP_201_CREATED)
def create_event_venue(
    tenant_id: UUID,
    payload: EventVenueCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> EventVenueRead:
    return service.create_event_venue(str(tenant_id), payload, context)


@router.get("/event-venues/{row_id}", response_model=EventVenueRead)
def get_event_venue(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> EventVenueRead:
    return service.get_event_venue(str(tenant_id), str(row_id), context)


@router.get("/event-venues/{row_id}/location", response_model=EventVenueLocationProjectionRead)
def get_event_venue_location_projection(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> EventVenueLocationProjectionRead:
    return service.get_event_venue_location_projection(str(tenant_id), str(row_id), context)


@router.patch("/event-venues/{row_id}", response_model=EventVenueRead)
def update_event_venue(
    tenant_id: UUID,
    row_id: UUID,
    payload: EventVenueUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> EventVenueRead:
    return service.update_event_venue(str(tenant_id), str(row_id), payload, context)


@router.get("/trade-fairs", response_model=list[TradeFairListItem])
def list_trade_fairs(
    tenant_id: UUID,
    filters: Annotated[OpsMasterFilter, Depends(_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> list[TradeFairListItem]:
    return service.list_trade_fairs(str(tenant_id), filters, context)


@router.post("/trade-fairs", response_model=TradeFairRead, status_code=status.HTTP_201_CREATED)
def create_trade_fair(
    tenant_id: UUID,
    payload: TradeFairCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> TradeFairRead:
    return service.create_trade_fair(str(tenant_id), payload, context)


@router.get("/trade-fairs/{row_id}", response_model=TradeFairRead)
def get_trade_fair(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> TradeFairRead:
    return service.get_trade_fair(str(tenant_id), str(row_id), context)


@router.get("/trade-fairs/{row_id}/location", response_model=TradeFairLocationProjectionRead)
def get_trade_fair_location_projection(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> TradeFairLocationProjectionRead:
    return service.get_trade_fair_location_projection(str(tenant_id), str(row_id), context)


@router.patch("/trade-fairs/{row_id}", response_model=TradeFairRead)
def update_trade_fair(
    tenant_id: UUID,
    row_id: UUID,
    payload: TradeFairUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> TradeFairRead:
    return service.update_trade_fair(str(tenant_id), str(row_id), payload, context)


@router.get("/trade-fairs/{trade_fair_id}/zones", response_model=list[TradeFairZoneRead])
def list_trade_fair_zones(
    tenant_id: UUID,
    trade_fair_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> list[TradeFairZoneRead]:
    return service.list_trade_fair_zones(str(tenant_id), str(trade_fair_id), context)


@router.post("/trade-fairs/{trade_fair_id}/zones", response_model=TradeFairZoneRead, status_code=status.HTTP_201_CREATED)
def create_trade_fair_zone(
    tenant_id: UUID,
    trade_fair_id: UUID,
    payload: TradeFairZoneCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> TradeFairZoneRead:
    return service.create_trade_fair_zone(str(tenant_id), str(trade_fair_id), payload, context)


@router.patch("/trade-fairs/{trade_fair_id}/zones/{row_id}", response_model=TradeFairZoneRead)
def update_trade_fair_zone(
    tenant_id: UUID,
    trade_fair_id: UUID,
    row_id: UUID,
    payload: TradeFairZoneUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> TradeFairZoneRead:
    return service.update_trade_fair_zone(str(tenant_id), str(trade_fair_id), str(row_id), payload, context)


@router.get("/patrol-routes", response_model=list[PatrolRouteListItem])
def list_patrol_routes(
    tenant_id: UUID,
    filters: Annotated[OpsMasterFilter, Depends(_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> list[PatrolRouteListItem]:
    return service.list_patrol_routes(str(tenant_id), filters, context)


@router.post("/patrol-routes", response_model=PatrolRouteRead, status_code=status.HTTP_201_CREATED)
def create_patrol_route(
    tenant_id: UUID,
    payload: PatrolRouteCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> PatrolRouteRead:
    return service.create_patrol_route(str(tenant_id), payload, context)


@router.get("/patrol-routes/{row_id}", response_model=PatrolRouteRead)
def get_patrol_route(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> PatrolRouteRead:
    return service.get_patrol_route(str(tenant_id), str(row_id), context)


@router.get("/patrol-routes/{row_id}/location", response_model=PatrolRouteLocationProjectionRead)
def get_patrol_route_location_projection(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> PatrolRouteLocationProjectionRead:
    return service.get_patrol_route_location_projection(str(tenant_id), str(row_id), context)


@router.patch("/patrol-routes/{row_id}", response_model=PatrolRouteRead)
def update_patrol_route(
    tenant_id: UUID,
    row_id: UUID,
    payload: PatrolRouteUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> PatrolRouteRead:
    return service.update_patrol_route(str(tenant_id), str(row_id), payload, context)


@router.get("/patrol-routes/{patrol_route_id}/checkpoints", response_model=list[PatrolCheckpointRead])
def list_patrol_checkpoints(
    tenant_id: UUID,
    patrol_route_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.ops.read"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> list[PatrolCheckpointRead]:
    return service.list_patrol_checkpoints(str(tenant_id), str(patrol_route_id), context)


@router.post("/patrol-routes/{patrol_route_id}/checkpoints", response_model=PatrolCheckpointRead, status_code=status.HTTP_201_CREATED)
def create_patrol_checkpoint(
    tenant_id: UUID,
    patrol_route_id: UUID,
    payload: PatrolCheckpointCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> PatrolCheckpointRead:
    return service.create_patrol_checkpoint(str(tenant_id), str(patrol_route_id), payload, context)


@router.patch("/patrol-routes/{patrol_route_id}/checkpoints/{row_id}", response_model=PatrolCheckpointRead)
def update_patrol_checkpoint(
    tenant_id: UUID,
    patrol_route_id: UUID,
    row_id: UUID,
    payload: PatrolCheckpointUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningService, Depends(get_planning_service)],
) -> PatrolCheckpointRead:
    return service.update_patrol_checkpoint(str(tenant_id), str(patrol_route_id), str(row_id), payload, context)


@router.get("/orders", response_model=list[CustomerOrderListItem])
def list_customer_orders(
    tenant_id: UUID,
    filters: Annotated[CustomerOrderFilter, Depends(_order_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.order.read"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> list[CustomerOrderListItem]:
    return service.list_orders(str(tenant_id), filters, context)


@router.post("/orders", response_model=CustomerOrderRead, status_code=status.HTTP_201_CREATED)
def create_customer_order(
    tenant_id: UUID,
    payload: CustomerOrderCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> CustomerOrderRead:
    return service.create_order(str(tenant_id), payload, context)


@router.get("/orders/{order_id}", response_model=CustomerOrderRead)
def get_customer_order(
    tenant_id: UUID,
    order_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.order.read"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> CustomerOrderRead:
    return service.get_order(str(tenant_id), str(order_id), context)


@router.patch("/orders/{order_id}", response_model=CustomerOrderRead)
def update_customer_order(
    tenant_id: UUID,
    order_id: UUID,
    payload: CustomerOrderUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> CustomerOrderRead:
    return service.update_order(str(tenant_id), str(order_id), payload, context)


@router.post("/orders/{order_id}/release-state", response_model=CustomerOrderRead)
def set_customer_order_release_state(
    tenant_id: UUID,
    order_id: UUID,
    payload: CustomerOrderReleaseStateUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> CustomerOrderRead:
    return service.set_order_release_state(str(tenant_id), str(order_id), payload, context)


@router.get("/orders/{order_id}/equipment-lines", response_model=list[OrderEquipmentLineRead])
def list_order_equipment_lines(
    tenant_id: UUID,
    order_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.order.read"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> list[OrderEquipmentLineRead]:
    return service.list_order_equipment_lines(str(tenant_id), str(order_id), context)


@router.post("/orders/{order_id}/equipment-lines", response_model=OrderEquipmentLineRead, status_code=status.HTTP_201_CREATED)
def create_order_equipment_line(
    tenant_id: UUID,
    order_id: UUID,
    payload: OrderEquipmentLineCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> OrderEquipmentLineRead:
    return service.create_order_equipment_line(str(tenant_id), str(order_id), payload, context)


@router.patch("/orders/{order_id}/equipment-lines/{row_id}", response_model=OrderEquipmentLineRead)
def update_order_equipment_line(
    tenant_id: UUID,
    order_id: UUID,
    row_id: UUID,
    payload: OrderEquipmentLineUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> OrderEquipmentLineRead:
    return service.update_order_equipment_line(str(tenant_id), str(order_id), str(row_id), payload, context)


@router.delete("/orders/{order_id}/equipment-lines/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_equipment_line(
    tenant_id: UUID,
    order_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> None:
    service.delete_order_equipment_line(str(tenant_id), str(order_id), str(row_id), context)


@router.get("/orders/{order_id}/requirement-lines", response_model=list[OrderRequirementLineRead])
def list_order_requirement_lines(
    tenant_id: UUID,
    order_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.order.read"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> list[OrderRequirementLineRead]:
    return service.list_order_requirement_lines(str(tenant_id), str(order_id), context)


@router.post("/orders/{order_id}/requirement-lines", response_model=OrderRequirementLineRead, status_code=status.HTTP_201_CREATED)
def create_order_requirement_line(
    tenant_id: UUID,
    order_id: UUID,
    payload: OrderRequirementLineCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> OrderRequirementLineRead:
    return service.create_order_requirement_line(str(tenant_id), str(order_id), payload, context)


@router.patch("/orders/{order_id}/requirement-lines/{row_id}", response_model=OrderRequirementLineRead)
def update_order_requirement_line(
    tenant_id: UUID,
    order_id: UUID,
    row_id: UUID,
    payload: OrderRequirementLineUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> OrderRequirementLineRead:
    return service.update_order_requirement_line(str(tenant_id), str(order_id), str(row_id), payload, context)


@router.delete("/orders/{order_id}/requirement-lines/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_requirement_line(
    tenant_id: UUID,
    order_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> None:
    service.delete_order_requirement_line(str(tenant_id), str(order_id), str(row_id), context)


@router.get("/orders/{order_id}/attachments", response_model=list[OrderAttachmentRead])
def list_order_attachments(
    tenant_id: UUID,
    order_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.order.read"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> list[OrderAttachmentRead]:
    return service.list_order_attachments(str(tenant_id), str(order_id), context)


@router.post("/orders/{order_id}/attachments", response_model=OrderAttachmentRead, status_code=status.HTTP_201_CREATED)
def create_order_attachment(
    tenant_id: UUID,
    order_id: UUID,
    payload: CustomerOrderAttachmentCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> OrderAttachmentRead:
    return service.create_order_attachment(str(tenant_id), str(order_id), payload, context)


@router.post("/orders/{order_id}/attachments/link", response_model=OrderAttachmentRead, status_code=status.HTTP_201_CREATED)
def link_order_attachment(
    tenant_id: UUID,
    order_id: UUID,
    payload: CustomerOrderAttachmentLinkCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> OrderAttachmentRead:
    return service.link_order_attachment(str(tenant_id), str(order_id), payload, context)


@router.delete("/orders/{order_id}/attachments/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_order_attachment(
    tenant_id: UUID,
    order_id: UUID,
    document_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.order.write", scope="tenant"))],
    service: Annotated[CustomerOrderService, Depends(get_customer_order_service)],
) -> None:
    service.unlink_order_attachment(str(tenant_id), str(order_id), str(document_id), context)


@router.get("/orders/{order_id}/commercial-link", response_model=PlanningCommercialLinkRead)
def get_order_commercial_link(
    tenant_id: UUID,
    order_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.order.read"))],
    service: Annotated[PlanningCommercialLinkService, Depends(get_planning_commercial_link_service)],
) -> PlanningCommercialLinkRead:
    return service.get_order_commercial_link(str(tenant_id), str(order_id), context)


@router.get("/planning-records", response_model=list[PlanningRecordListItem])
def list_planning_records(
    tenant_id: UUID,
    filters: Annotated[PlanningRecordFilter, Depends(_planning_record_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.record.read"))],
    service: Annotated[PlanningRecordService, Depends(get_planning_record_service)],
) -> list[PlanningRecordListItem]:
    return service.list_planning_records(str(tenant_id), filters, context)


@router.get("/planning-records/dispatcher-candidates", response_model=list[PlanningDispatcherCandidateRead])
def list_planning_dispatcher_candidates(
    tenant_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.record.read"))],
    service: Annotated[PlanningRecordService, Depends(get_planning_record_service)],
) -> list[PlanningDispatcherCandidateRead]:
    return service.list_dispatcher_candidates(str(tenant_id), context)


@router.post("/planning-records", response_model=PlanningRecordRead, status_code=status.HTTP_201_CREATED)
def create_planning_record(
    tenant_id: UUID,
    payload: PlanningRecordCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.record.write", scope="tenant"))],
    service: Annotated[PlanningRecordService, Depends(get_planning_record_service)],
) -> PlanningRecordRead:
    return service.create_planning_record(str(tenant_id), payload, context)


@router.get("/planning-records/{planning_record_id}", response_model=PlanningRecordRead)
def get_planning_record(
    tenant_id: UUID,
    planning_record_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.record.read"))],
    service: Annotated[PlanningRecordService, Depends(get_planning_record_service)],
) -> PlanningRecordRead:
    return service.get_planning_record(str(tenant_id), str(planning_record_id), context)


@router.patch("/planning-records/{planning_record_id}", response_model=PlanningRecordRead)
def update_planning_record(
    tenant_id: UUID,
    planning_record_id: UUID,
    payload: PlanningRecordUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.record.write", scope="tenant"))],
    service: Annotated[PlanningRecordService, Depends(get_planning_record_service)],
) -> PlanningRecordRead:
    return service.update_planning_record(str(tenant_id), str(planning_record_id), payload, context)


@router.post("/planning-records/{planning_record_id}/release-state", response_model=PlanningRecordRead)
def set_planning_record_release_state(
    tenant_id: UUID,
    planning_record_id: UUID,
    payload: PlanningRecordReleaseStateUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.record.write", scope="tenant"))],
    service: Annotated[PlanningRecordService, Depends(get_planning_record_service)],
) -> PlanningRecordRead:
    return service.set_planning_record_release_state(str(tenant_id), str(planning_record_id), payload, context)


@router.get("/planning-records/{planning_record_id}/attachments", response_model=list[PlanningRecordAttachmentRead])
def list_planning_record_attachments(
    tenant_id: UUID,
    planning_record_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.record.read"))],
    service: Annotated[PlanningRecordService, Depends(get_planning_record_service)],
) -> list[PlanningRecordAttachmentRead]:
    return service.list_planning_record_attachments(str(tenant_id), str(planning_record_id), context)


@router.post("/planning-records/{planning_record_id}/attachments", response_model=PlanningRecordAttachmentRead, status_code=status.HTTP_201_CREATED)
def create_planning_record_attachment(
    tenant_id: UUID,
    planning_record_id: UUID,
    payload: PlanningRecordAttachmentCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.record.write", scope="tenant"))],
    service: Annotated[PlanningRecordService, Depends(get_planning_record_service)],
) -> PlanningRecordAttachmentRead:
    return service.create_planning_record_attachment(str(tenant_id), str(planning_record_id), payload, context)


@router.post("/planning-records/{planning_record_id}/attachments/link", response_model=PlanningRecordAttachmentRead, status_code=status.HTTP_201_CREATED)
def link_planning_record_attachment(
    tenant_id: UUID,
    planning_record_id: UUID,
    payload: PlanningRecordAttachmentLinkCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.record.write", scope="tenant"))],
    service: Annotated[PlanningRecordService, Depends(get_planning_record_service)],
) -> PlanningRecordAttachmentRead:
    return service.link_planning_record_attachment(str(tenant_id), str(planning_record_id), payload, context)


@router.delete("/planning-records/{planning_record_id}/attachments/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_planning_record_attachment(
    tenant_id: UUID,
    planning_record_id: UUID,
    document_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.record.write", scope="tenant"))],
    service: Annotated[PlanningRecordService, Depends(get_planning_record_service)],
) -> None:
    service.unlink_planning_record_attachment(str(tenant_id), str(planning_record_id), str(document_id), context)


@router.get("/planning-records/{planning_record_id}/commercial-link", response_model=PlanningCommercialLinkRead)
def get_planning_record_commercial_link(
    tenant_id: UUID,
    planning_record_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.record.read"))],
    service: Annotated[PlanningCommercialLinkService, Depends(get_planning_commercial_link_service)],
) -> PlanningCommercialLinkRead:
    return service.get_planning_record_commercial_link(str(tenant_id), str(planning_record_id), context)


@router.get("/shift-templates", response_model=list[ShiftTemplateListItem])
def list_shift_templates(
    tenant_id: UUID,
    filters: Annotated[OpsMasterFilter, Depends(_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> list[ShiftTemplateListItem]:
    return service.list_shift_templates(str(tenant_id), filters, context)


@router.get("/shift-type-options", response_model=list[ShiftTypeOptionRead])
def list_shift_type_options(
    tenant_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> list[ShiftTypeOptionRead]:
    return service.list_shift_type_options(str(tenant_id), context)


@router.post("/shift-templates", response_model=ShiftTemplateRead, status_code=status.HTTP_201_CREATED)
def create_shift_template(
    tenant_id: UUID,
    payload: ShiftTemplateCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftTemplateRead:
    return service.create_shift_template(str(tenant_id), payload, context)


@router.get("/shift-templates/{template_id}", response_model=ShiftTemplateRead)
def get_shift_template(
    tenant_id: UUID,
    template_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftTemplateRead:
    return service.get_shift_template(str(tenant_id), str(template_id), context)


@router.patch("/shift-templates/{template_id}", response_model=ShiftTemplateRead)
def update_shift_template(
    tenant_id: UUID,
    template_id: UUID,
    payload: ShiftTemplateUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftTemplateRead:
    return service.update_shift_template(str(tenant_id), str(template_id), payload, context)


@router.get("/shift-plans", response_model=list[ShiftPlanListItem])
def list_shift_plans(
    tenant_id: UUID,
    filters: Annotated[ShiftPlanFilter, Depends(_shift_plan_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> list[ShiftPlanListItem]:
    return service.list_shift_plans(str(tenant_id), filters, context)


@router.post("/shift-plans", response_model=ShiftPlanRead, status_code=status.HTTP_201_CREATED)
def create_shift_plan(
    tenant_id: UUID,
    payload: ShiftPlanCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftPlanRead:
    return service.create_shift_plan(str(tenant_id), payload, context)


@router.get("/shift-plans/{shift_plan_id}", response_model=ShiftPlanRead)
def get_shift_plan(
    tenant_id: UUID,
    shift_plan_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftPlanRead:
    return service.get_shift_plan(str(tenant_id), str(shift_plan_id), context)


@router.patch("/shift-plans/{shift_plan_id}", response_model=ShiftPlanRead)
def update_shift_plan(
    tenant_id: UUID,
    shift_plan_id: UUID,
    payload: ShiftPlanUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftPlanRead:
    return service.update_shift_plan(str(tenant_id), str(shift_plan_id), payload, context)


@router.get("/shift-plans/{shift_plan_id}/series", response_model=list[ShiftSeriesListItem])
def list_shift_series(
    tenant_id: UUID,
    shift_plan_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> list[ShiftSeriesListItem]:
    return service.list_shift_series(str(tenant_id), str(shift_plan_id), context)


@router.post("/shift-plans/{shift_plan_id}/series", response_model=ShiftSeriesRead, status_code=status.HTTP_201_CREATED)
def create_shift_series(
    tenant_id: UUID,
    shift_plan_id: UUID,
    payload: ShiftSeriesCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftSeriesRead:
    if payload.shift_plan_id != str(shift_plan_id):
        raise ApiException(400, "planning.shift.scope_mismatch", "errors.planning.shift.scope_mismatch")
    return service.create_shift_series(str(tenant_id), payload, context)


@router.get("/shift-series/{shift_series_id}", response_model=ShiftSeriesRead)
def get_shift_series(
    tenant_id: UUID,
    shift_series_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftSeriesRead:
    return service.get_shift_series(str(tenant_id), str(shift_series_id), context)


@router.patch("/shift-series/{shift_series_id}", response_model=ShiftSeriesRead)
def update_shift_series(
    tenant_id: UUID,
    shift_series_id: UUID,
    payload: ShiftSeriesUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftSeriesRead:
    return service.update_shift_series(str(tenant_id), str(shift_series_id), payload, context)


@router.post("/shift-series/{shift_series_id}/generate", response_model=list[ShiftRead])
def generate_shift_series(
    tenant_id: UUID,
    shift_series_id: UUID,
    payload: ShiftSeriesGenerationRequest,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> list[ShiftRead]:
    return service.generate_shift_series(str(tenant_id), str(shift_series_id), payload, context)


@router.get("/shift-series/{shift_series_id}/exceptions", response_model=list[ShiftSeriesExceptionRead])
def list_shift_series_exceptions(
    tenant_id: UUID,
    shift_series_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> list[ShiftSeriesExceptionRead]:
    return service.list_shift_series_exceptions(str(tenant_id), str(shift_series_id), context)


@router.post("/shift-series/{shift_series_id}/exceptions", response_model=ShiftSeriesExceptionRead, status_code=status.HTTP_201_CREATED)
def create_shift_series_exception(
    tenant_id: UUID,
    shift_series_id: UUID,
    payload: ShiftSeriesExceptionCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftSeriesExceptionRead:
    return service.create_shift_series_exception(str(tenant_id), str(shift_series_id), payload, context)


@router.patch("/shift-series-exceptions/{row_id}", response_model=ShiftSeriesExceptionRead)
def update_shift_series_exception(
    tenant_id: UUID,
    row_id: UUID,
    payload: ShiftSeriesExceptionUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftSeriesExceptionRead:
    return service.update_shift_series_exception(str(tenant_id), str(row_id), payload, context)


@router.delete("/shift-series-exceptions/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shift_series_exception(
    tenant_id: UUID,
    row_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> None:
    service.delete_shift_series_exception(str(tenant_id), str(row_id), context)


@router.get("/shifts", response_model=list[ShiftListItem])
def list_shifts(
    tenant_id: UUID,
    filters: Annotated[ShiftListFilter, Depends(_shift_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> list[ShiftListItem]:
    return service.list_shifts(str(tenant_id), filters, context)


@router.post("/shifts", response_model=ShiftRead, status_code=status.HTTP_201_CREATED)
def create_shift(
    tenant_id: UUID,
    payload: ShiftCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftRead:
    return service.create_shift(str(tenant_id), payload, context)


@router.get("/shifts/{shift_id}", response_model=ShiftRead)
def get_shift(
    tenant_id: UUID,
    shift_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftRead:
    return service.get_shift(str(tenant_id), str(shift_id), context)


@router.get("/shifts/{shift_id}/release-diagnostics", response_model=ShiftReleaseDiagnosticsRead)
def get_shift_release_diagnostics(
    tenant_id: UUID,
    shift_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftReleaseDiagnosticsRead:
    return service.get_shift_release_diagnostics(str(tenant_id), str(shift_id), context)


@router.patch("/shifts/{shift_id}", response_model=ShiftRead)
def update_shift(
    tenant_id: UUID,
    shift_id: UUID,
    payload: ShiftUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftRead:
    return service.update_shift(str(tenant_id), str(shift_id), payload, context)


@router.post("/shifts/{shift_id}/release-state", response_model=ShiftRead)
def set_shift_release_state(
    tenant_id: UUID,
    shift_id: UUID,
    payload: ShiftReleaseStateUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftRead:
    return service.set_shift_release_state(str(tenant_id), str(shift_id), payload, context)


@router.post("/shifts/{shift_id}/visibility", response_model=ShiftRead)
def update_shift_visibility(
    tenant_id: UUID,
    shift_id: UUID,
    payload: ShiftVisibilityUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftRead:
    return service.update_shift_visibility(str(tenant_id), str(shift_id), payload, context)


@router.get("/shifts/{shift_id}/outputs", response_model=list[PlanningOutputDocumentRead])
def list_shift_outputs(
    tenant_id: UUID,
    shift_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[PlanningOutputService, Depends(get_planning_output_service)],
) -> list[PlanningOutputDocumentRead]:
    return service.list_shift_outputs(str(tenant_id), str(shift_id), context)


@router.post("/shifts/{shift_id}/outputs", response_model=PlanningOutputDocumentRead, status_code=status.HTTP_201_CREATED)
def generate_shift_output(
    tenant_id: UUID,
    shift_id: UUID,
    payload: PlanningOutputGenerateRequest,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[PlanningOutputService, Depends(get_planning_output_service)],
) -> PlanningOutputDocumentRead:
    return service.generate_shift_output(str(tenant_id), str(shift_id), payload, context)


@router.post("/shifts/{shift_id}/dispatch-preview", response_model=PlanningDispatchPreviewRead)
def preview_shift_dispatch(
    tenant_id: UUID,
    shift_id: UUID,
    payload: PlanningDispatchCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[PlanningCommunicationService, Depends(get_planning_communication_service)],
) -> PlanningDispatchPreviewRead:
    if payload.shift_id != str(shift_id):
        raise ApiException(400, "planning.shift.scope_mismatch", "errors.planning.shift.scope_mismatch")
    return service.preview_message(str(tenant_id), payload, context)


@router.post("/shifts/{shift_id}/dispatch-messages", response_model=OutboundMessageRead, status_code=status.HTTP_201_CREATED)
def queue_shift_dispatch_message(
    tenant_id: UUID,
    shift_id: UUID,
    payload: PlanningDispatchCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[PlanningCommunicationService, Depends(get_planning_communication_service)],
) -> OutboundMessageRead:
    if payload.shift_id != str(shift_id):
        raise ApiException(400, "planning.shift.scope_mismatch", "errors.planning.shift.scope_mismatch")
    return service.queue_message(str(tenant_id), payload, context)


@router.get("/dispatch-messages/{message_id}", response_model=OutboundMessageRead)
def get_shift_dispatch_message(
    tenant_id: UUID,
    message_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[PlanningCommunicationService, Depends(get_planning_communication_service)],
) -> OutboundMessageRead:
    return service.get_message(str(tenant_id), str(message_id), context)


@router.post("/shift-plans/{shift_plan_id}/copy", response_model=ShiftCopyResult)
def copy_shift_slice(
    tenant_id: UUID,
    shift_plan_id: UUID,
    payload: ShiftCopyRequest,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.shift.write", scope="tenant"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> ShiftCopyResult:
    return service.copy_shift_slice(str(tenant_id), str(shift_plan_id), payload, context)


@router.get("/board/shifts", response_model=list[PlanningBoardShiftListItem])
def list_board_shifts(
    tenant_id: UUID,
    filters: Annotated[PlanningBoardFilter, Depends(_board_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.shift.read"))],
    service: Annotated[ShiftPlanningService, Depends(get_shift_planning_service)],
) -> list[PlanningBoardShiftListItem]:
    return service.list_board_shifts(str(tenant_id), filters, context)


@router.get("/demand-groups", response_model=list[DemandGroupRead])
def list_demand_groups(
    tenant_id: UUID,
    filters: Annotated[StaffingFilter, Depends(_staffing_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> list[DemandGroupRead]:
    return service.list_demand_groups(str(tenant_id), filters, context)


@router.post("/demand-groups", response_model=DemandGroupRead, status_code=status.HTTP_201_CREATED)
def create_demand_group(
    tenant_id: UUID,
    payload: DemandGroupCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> DemandGroupRead:
    return service.create_demand_group(str(tenant_id), payload, context)


@router.post("/demand-groups/bulk-apply", response_model=DemandGroupBulkApplyResult, status_code=status.HTTP_200_OK)
def bulk_apply_demand_groups(
    tenant_id: UUID,
    payload: DemandGroupBulkApplyRequest,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> DemandGroupBulkApplyResult:
    return service.bulk_apply_demand_groups(str(tenant_id), payload, context)


@router.patch("/demand-groups/bulk-update", response_model=DemandGroupBulkUpdateResult, status_code=status.HTTP_200_OK)
def bulk_update_demand_groups(
    tenant_id: UUID,
    payload: DemandGroupBulkUpdateRequest,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> DemandGroupBulkUpdateResult:
    return service.bulk_update_demand_groups(str(tenant_id), payload, context)


@router.get("/demand-groups/{demand_group_id}", response_model=DemandGroupRead)
def get_demand_group(
    tenant_id: UUID,
    demand_group_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> DemandGroupRead:
    return service.get_demand_group(str(tenant_id), str(demand_group_id), context)


@router.patch("/demand-groups/{demand_group_id}", response_model=DemandGroupRead)
def update_demand_group(
    tenant_id: UUID,
    demand_group_id: UUID,
    payload: DemandGroupUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> DemandGroupRead:
    return service.update_demand_group(str(tenant_id), str(demand_group_id), payload, context)


@router.get("/teams", response_model=list[TeamRead])
def list_teams(
    tenant_id: UUID,
    filters: Annotated[StaffingFilter, Depends(_staffing_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> list[TeamRead]:
    return service.list_teams(str(tenant_id), filters, context)


@router.post("/teams", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(
    tenant_id: UUID,
    payload: TeamCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> TeamRead:
    return service.create_team(str(tenant_id), payload, context)


@router.get("/teams/{team_id}", response_model=TeamRead)
def get_team(
    tenant_id: UUID,
    team_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> TeamRead:
    return service.get_team(str(tenant_id), str(team_id), context)


@router.patch("/teams/{team_id}", response_model=TeamRead)
def update_team(
    tenant_id: UUID,
    team_id: UUID,
    payload: TeamUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> TeamRead:
    return service.update_team(str(tenant_id), str(team_id), payload, context)


@router.get("/team-members", response_model=list[TeamMemberRead])
def list_team_members(
    tenant_id: UUID,
    filters: Annotated[StaffingFilter, Depends(_staffing_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> list[TeamMemberRead]:
    return service.list_team_members(str(tenant_id), filters, context)


@router.post("/team-members", response_model=TeamMemberRead, status_code=status.HTTP_201_CREATED)
def create_team_member(
    tenant_id: UUID,
    payload: TeamMemberCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> TeamMemberRead:
    return service.create_team_member(str(tenant_id), payload, context)


@router.patch("/team-members/{team_member_id}", response_model=TeamMemberRead)
def update_team_member(
    tenant_id: UUID,
    team_member_id: UUID,
    payload: TeamMemberUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> TeamMemberRead:
    return service.update_team_member(str(tenant_id), str(team_member_id), payload, context)


@router.get("/assignments", response_model=list[AssignmentRead])
def list_assignments(
    tenant_id: UUID,
    filters: Annotated[StaffingFilter, Depends(_staffing_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> list[AssignmentRead]:
    return service.list_assignments(str(tenant_id), filters, context)


@router.post("/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(
    tenant_id: UUID,
    payload: AssignmentCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> AssignmentRead:
    return service.create_assignment(str(tenant_id), payload, context)


@router.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(
    tenant_id: UUID,
    assignment_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> AssignmentRead:
    return service.get_assignment(str(tenant_id), str(assignment_id), context)


@router.patch("/assignments/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    tenant_id: UUID,
    assignment_id: UUID,
    payload: AssignmentUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> AssignmentRead:
    return service.update_assignment(str(tenant_id), str(assignment_id), payload, context)


@router.get("/assignments/{assignment_id}/validations", response_model=AssignmentValidationRead)
def get_assignment_validations(
    tenant_id: UUID,
    assignment_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> AssignmentValidationRead:
    return service.get_assignment_validations(str(tenant_id), str(assignment_id), context)


@router.get("/assignments/{assignment_id}/validation-overrides", response_model=list[AssignmentValidationOverrideRead])
def list_assignment_validation_overrides(
    tenant_id: UUID,
    assignment_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> list[AssignmentValidationOverrideRead]:
    return service.list_assignment_validation_overrides(str(tenant_id), str(assignment_id), context)


@router.post("/assignments/{assignment_id}/validation-overrides", response_model=AssignmentValidationOverrideRead, status_code=status.HTTP_201_CREATED)
def create_assignment_validation_override(
    tenant_id: UUID,
    assignment_id: UUID,
    payload: AssignmentValidationOverrideCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.override", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> AssignmentValidationOverrideRead:
    return service.create_assignment_validation_override(str(tenant_id), str(assignment_id), payload, context)


@router.post("/staffing-board/assign", response_model=StaffingCommandResult)
def assign_staffing(
    tenant_id: UUID,
    payload: StaffingAssignCommand,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> StaffingCommandResult:
    return service.assign(str(tenant_id), payload, context)


@router.post("/staffing-board/unassign", response_model=StaffingCommandResult)
def unassign_staffing(
    tenant_id: UUID,
    payload: StaffingUnassignCommand,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> StaffingCommandResult:
    return service.unassign(str(tenant_id), payload, context)


@router.post("/staffing-board/substitute", response_model=StaffingCommandResult)
def substitute_staffing(
    tenant_id: UUID,
    payload: StaffingSubstituteCommand,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> StaffingCommandResult:
    return service.substitute(str(tenant_id), payload, context)


@router.get("/staffing-board", response_model=list[StaffingBoardShiftItem])
def get_staffing_board(
    tenant_id: UUID,
    filters: Annotated[StaffingBoardFilter, Depends(_staffing_board_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> list[StaffingBoardShiftItem]:
    return service.staffing_board(str(tenant_id), filters, context)


@router.get("/subcontractor-releases", response_model=list[SubcontractorReleaseRead])
def list_subcontractor_releases(
    tenant_id: UUID,
    filters: Annotated[StaffingFilter, Depends(_staffing_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> list[SubcontractorReleaseRead]:
    return service.list_subcontractor_releases(str(tenant_id), filters, context)


@router.post("/subcontractor-releases", response_model=SubcontractorReleaseRead, status_code=status.HTTP_201_CREATED)
def create_subcontractor_release(
    tenant_id: UUID,
    payload: SubcontractorReleaseCreate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> SubcontractorReleaseRead:
    return service.create_subcontractor_release(str(tenant_id), payload, context)


@router.patch("/subcontractor-releases/{release_id}", response_model=SubcontractorReleaseRead)
def update_subcontractor_release(
    tenant_id: UUID,
    release_id: UUID,
    payload: SubcontractorReleaseUpdate,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> SubcontractorReleaseRead:
    return service.update_subcontractor_release(str(tenant_id), str(release_id), payload, context)


@router.get("/coverage", response_model=list[CoverageShiftItem])
def get_staffing_coverage(
    tenant_id: UUID,
    filters: Annotated[CoverageFilter, Depends(_coverage_filters)],
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> list[CoverageShiftItem]:
    return service.coverage(str(tenant_id), filters, context)


@router.post("/assignment-step/snapshot", response_model=AssignmentStepSnapshotRead)
def get_assignment_step_snapshot(
    tenant_id: UUID,
    payload: AssignmentStepScopeRequest,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> AssignmentStepSnapshotRead:
    return service.get_assignment_step_snapshot(str(tenant_id), payload, context)


@router.post("/assignment-step/candidates", response_model=AssignmentStepCandidateQueryResult)
def list_assignment_step_candidates(
    tenant_id: UUID,
    payload: AssignmentStepScopeRequest,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> AssignmentStepCandidateQueryResult:
    return service.list_assignment_step_candidates(str(tenant_id), payload, context)


@router.post("/assignment-step/preview-apply", response_model=AssignmentStepApplyResult)
def preview_assignment_step_apply(
    tenant_id: UUID,
    payload: AssignmentStepApplyRequest,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> AssignmentStepApplyResult:
    return service.preview_assignment_step_apply(str(tenant_id), payload, context)


@router.post("/assignment-step/apply", response_model=AssignmentStepApplyResult)
def apply_assignment_step(
    tenant_id: UUID,
    payload: AssignmentStepApplyRequest,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.staffing.write", scope="tenant"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> AssignmentStepApplyResult:
    return service.apply_assignment_step(str(tenant_id), payload, context)


@router.get("/shifts/{shift_id}/release-validations", response_model=ShiftReleaseValidationRead)
def get_shift_release_validations(
    tenant_id: UUID,
    shift_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> ShiftReleaseValidationRead:
    return service.get_shift_release_validations(str(tenant_id), str(shift_id), context)


@router.get("/planning-records/{planning_record_id}/release-validations", response_model=PlanningRecordReleaseValidationRead)
def get_planning_record_release_validations(
    tenant_id: UUID,
    planning_record_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("planning.staffing.read"))],
    service: Annotated[StaffingService, Depends(get_staffing_service)],
) -> PlanningRecordReleaseValidationRead:
    return service.get_planning_record_release_validations(str(tenant_id), str(planning_record_id), context)


@router.post("/import/dry-run", response_model=PlanningOpsImportDryRunResult)
def import_ops_dry_run(
    tenant_id: UUID,
    payload: PlanningOpsImportDryRunRequest,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningOpsService, Depends(get_planning_ops_service)],
) -> PlanningOpsImportDryRunResult:
    return service.import_dry_run(str(tenant_id), payload, context)


@router.post("/import/execute", response_model=PlanningOpsImportExecuteResult, status_code=status.HTTP_201_CREATED)
def import_ops_execute(
    tenant_id: UUID,
    payload: PlanningOpsImportExecuteRequest,
    context: Annotated[RequestAuthorizationContext, Depends(require_authorization("planning.ops.write", scope="tenant"))],
    service: Annotated[PlanningOpsService, Depends(get_planning_ops_service)],
) -> PlanningOpsImportExecuteResult:
    return service.import_execute(str(tenant_id), payload, context)
