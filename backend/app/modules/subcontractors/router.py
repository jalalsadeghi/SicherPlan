"""HTTP API for tenant-scoped subcontractor master maintenance."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.core.schemas import AddressCreate, AddressRead
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization, require_permission_only
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import build_object_storage_adapter
from app.modules.subcontractors.repository import SqlAlchemySubcontractorRepository
from app.modules.subcontractors.schemas import (
    SubcontractorContactCreate,
    SubcontractorContactUserOptionRead,
    SubcontractorContactRead,
    SubcontractorContactUpdate,
    SubcontractorCreate,
    SubcontractorFilter,
    SubcontractorFinanceProfileCreate,
    SubcontractorFinanceProfileRead,
    SubcontractorFinanceProfileUpdate,
    SubcontractorHistoryAttachmentLinkCreate,
    SubcontractorHistoryAttachmentRead,
    SubcontractorHistoryEntryCreate,
    SubcontractorHistoryEntryRead,
    SubcontractorLifecycleTransitionRequest,
    SubcontractorListItem,
    SubcontractorReferenceDataRead,
    SubcontractorRead,
    SubcontractorScopeCreate,
    SubcontractorScopeRead,
    SubcontractorScopeUpdate,
    SubcontractorUpdate,
    SubcontractorWorkerCreate,
    SubcontractorWorkerCredentialCreate,
    SubcontractorWorkerCredentialRead,
    SubcontractorWorkerCredentialUpdate,
    SubcontractorWorkerExportRequest,
    SubcontractorWorkerExportResult,
    SubcontractorWorkerFilter,
    SubcontractorWorkerImportDryRunRequest,
    SubcontractorWorkerImportDryRunResult,
    SubcontractorWorkerImportExecuteRequest,
    SubcontractorWorkerImportExecuteResult,
    SubcontractorWorkerListItem,
    SubcontractorWorkerReadinessFilter,
    SubcontractorWorkerReadinessListItem,
    SubcontractorWorkerReadinessRead,
    SubcontractorWorkerQualificationCreate,
    SubcontractorWorkerQualificationProofLinkCreate,
    SubcontractorWorkerQualificationProofRead,
    SubcontractorWorkerQualificationProofUpload,
    SubcontractorWorkerQualificationRead,
    SubcontractorWorkerQualificationUpdate,
    SubcontractorWorkerRead,
    SubcontractorWorkerUpdate,
    SubcontractorWorkforceReadinessSummaryRead,
)
from app.modules.subcontractors.collaboration_service import SubcontractorCollaborationService
from app.modules.subcontractors.ops_service import SubcontractorWorkforceOpsService
from app.modules.subcontractors.readiness_service import SubcontractorReadinessService
from app.modules.subcontractors.service import SubcontractorService
from app.modules.subcontractors.workforce_service import SubcontractorWorkforceService
from app.config import settings


router = APIRouter(prefix="/api/subcontractors/tenants/{tenant_id}/subcontractors", tags=["subcontractors"])


def get_subcontractor_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SubcontractorService:
    return SubcontractorService(
        SqlAlchemySubcontractorRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_subcontractor_collaboration_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SubcontractorCollaborationService:
    return SubcontractorCollaborationService(
        SqlAlchemySubcontractorRepository(session),
        document_repository=SqlAlchemyDocumentRepository(session),
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_subcontractor_workforce_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SubcontractorWorkforceService:
    return SubcontractorWorkforceService(
        SqlAlchemySubcontractorRepository(session),
        document_repository=SqlAlchemyDocumentRepository(session),
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_subcontractor_workforce_ops_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SubcontractorWorkforceOpsService:
    repository = SqlAlchemySubcontractorRepository(session)
    return SubcontractorWorkforceOpsService(
        repository=repository,
        workforce_service=SubcontractorWorkforceService(
            repository,
            document_repository=SqlAlchemyDocumentRepository(session),
            document_service=DocumentService(
                SqlAlchemyDocumentRepository(session),
                storage=build_object_storage_adapter(settings),
                bucket_name=settings.object_storage_bucket,
            ),
            audit_service=AuditService(SqlAlchemyAuditRepository(session)),
        ),
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_subcontractor_readiness_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SubcontractorReadinessService:
    return SubcontractorReadinessService(
        SqlAlchemySubcontractorRepository(session),
        document_repository=SqlAlchemyDocumentRepository(session),
    )


@router.get("", response_model=list[SubcontractorListItem])
def list_subcontractors(
    tenant_id: UUID,
    search: str | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    mandate_id: UUID | None = Query(default=None),
    include_archived: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ] = None,
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)] = None,
) -> list[SubcontractorListItem]:
    return service.list_subcontractors(
        str(tenant_id),
        SubcontractorFilter(
            search=search,
            status=lifecycle_status,
            branch_id=str(branch_id) if branch_id else None,
            mandate_id=str(mandate_id) if mandate_id else None,
            include_archived=include_archived,
        ),
        context,
    )


@router.get("/reference-data", response_model=SubcontractorReferenceDataRead)
def get_reference_data(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> SubcontractorReferenceDataRead:
    return service.get_reference_data(str(tenant_id), context)


@router.post("", response_model=SubcontractorRead, status_code=status.HTTP_201_CREATED)
def create_subcontractor(
    tenant_id: UUID,
    payload: SubcontractorCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> SubcontractorRead:
    return service.create_subcontractor(str(tenant_id), payload, context)


@router.get("/{subcontractor_id}", response_model=SubcontractorRead)
def get_subcontractor(
    tenant_id: UUID,
    subcontractor_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> SubcontractorRead:
    return service.get_subcontractor(str(tenant_id), str(subcontractor_id), context)


@router.patch("/{subcontractor_id}", response_model=SubcontractorRead)
def update_subcontractor(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> SubcontractorRead:
    return service.update_subcontractor(str(tenant_id), str(subcontractor_id), payload, context)


@router.post("/{subcontractor_id}/archive", response_model=SubcontractorRead)
def archive_subcontractor(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorLifecycleTransitionRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorCollaborationService, Depends(get_subcontractor_collaboration_service)],
) -> SubcontractorRead:
    return service.archive_subcontractor(str(tenant_id), str(subcontractor_id), payload, context)


@router.post("/{subcontractor_id}/reactivate", response_model=SubcontractorRead)
def reactivate_subcontractor(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorLifecycleTransitionRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorCollaborationService, Depends(get_subcontractor_collaboration_service)],
) -> SubcontractorRead:
    return service.reactivate_subcontractor(str(tenant_id), str(subcontractor_id), payload, context)


@router.get("/{subcontractor_id}/contacts", response_model=list[SubcontractorContactRead])
def list_contacts(
    tenant_id: UUID,
    subcontractor_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> list[SubcontractorContactRead]:
    return service.list_contacts(str(tenant_id), str(subcontractor_id), context)


@router.get("/{subcontractor_id}/contact-user-options", response_model=list[SubcontractorContactUserOptionRead])
def list_contact_user_options(
    tenant_id: UUID,
    subcontractor_id: UUID,
    search: str = Query(default="", max_length=120),
    limit: int = Query(default=25, ge=1, le=50),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ] = None,
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)] = None,
) -> list[SubcontractorContactUserOptionRead]:
    return service.list_contact_user_options(
        str(tenant_id),
        str(subcontractor_id),
        context,
        search=search,
        limit=limit,
    )


@router.get("/{subcontractor_id}/address-options", response_model=list[AddressRead])
def list_address_options(
    tenant_id: UUID,
    subcontractor_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ] = None,
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)] = None,
) -> list[AddressRead]:
    return service.list_address_options(str(tenant_id), str(subcontractor_id), context)


@router.post("/{subcontractor_id}/address-options", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
def create_address_option(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: AddressCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ] = None,
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)] = None,
) -> AddressRead:
    return service.create_address_option(str(tenant_id), str(subcontractor_id), payload, context)


@router.post("/{subcontractor_id}/contacts", response_model=SubcontractorContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorContactCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> SubcontractorContactRead:
    return service.create_contact(str(tenant_id), str(subcontractor_id), payload, context)


@router.patch("/{subcontractor_id}/contacts/{contact_id}", response_model=SubcontractorContactRead)
def update_contact(
    tenant_id: UUID,
    subcontractor_id: UUID,
    contact_id: UUID,
    payload: SubcontractorContactUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> SubcontractorContactRead:
    return service.update_contact(str(tenant_id), str(subcontractor_id), str(contact_id), payload, context)


@router.get("/{subcontractor_id}/scopes", response_model=list[SubcontractorScopeRead])
def list_scopes(
    tenant_id: UUID,
    subcontractor_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> list[SubcontractorScopeRead]:
    return service.list_scopes(str(tenant_id), str(subcontractor_id), context)


@router.post("/{subcontractor_id}/scopes", response_model=SubcontractorScopeRead, status_code=status.HTTP_201_CREATED)
def create_scope(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorScopeCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> SubcontractorScopeRead:
    return service.create_scope(str(tenant_id), str(subcontractor_id), payload, context)


@router.patch("/{subcontractor_id}/scopes/{scope_id}", response_model=SubcontractorScopeRead)
def update_scope(
    tenant_id: UUID,
    subcontractor_id: UUID,
    scope_id: UUID,
    payload: SubcontractorScopeUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> SubcontractorScopeRead:
    return service.update_scope(str(tenant_id), str(subcontractor_id), str(scope_id), payload, context)


@router.get("/{subcontractor_id}/finance-profile", response_model=SubcontractorFinanceProfileRead)
def get_finance_profile(
    tenant_id: UUID,
    subcontractor_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.finance.read")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> SubcontractorFinanceProfileRead:
    return service.get_finance_profile(str(tenant_id), str(subcontractor_id), context)


@router.get("/{subcontractor_id}/history", response_model=list[SubcontractorHistoryEntryRead])
def list_subcontractor_history(
    tenant_id: UUID,
    subcontractor_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ],
    service: Annotated[SubcontractorCollaborationService, Depends(get_subcontractor_collaboration_service)],
) -> list[SubcontractorHistoryEntryRead]:
    return service.list_history(str(tenant_id), str(subcontractor_id), context)


@router.post("/{subcontractor_id}/history", response_model=SubcontractorHistoryEntryRead, status_code=status.HTTP_201_CREATED)
def create_subcontractor_history_entry(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorHistoryEntryCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorCollaborationService, Depends(get_subcontractor_collaboration_service)],
) -> SubcontractorHistoryEntryRead:
    return service.create_history_entry(str(tenant_id), str(subcontractor_id), payload, context)


@router.post(
    "/{subcontractor_id}/history/{history_entry_id}/attachments",
    response_model=list[SubcontractorHistoryAttachmentRead],
)
def link_subcontractor_history_attachment(
    tenant_id: UUID,
    subcontractor_id: UUID,
    history_entry_id: UUID,
    payload: SubcontractorHistoryAttachmentLinkCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorCollaborationService, Depends(get_subcontractor_collaboration_service)],
) -> list[SubcontractorHistoryAttachmentRead]:
    return service.link_history_attachment(str(tenant_id), str(subcontractor_id), str(history_entry_id), payload, context)


@router.put("/{subcontractor_id}/finance-profile", response_model=SubcontractorFinanceProfileRead)
def put_finance_profile(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorFinanceProfileCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.finance.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> SubcontractorFinanceProfileRead:
    return service.upsert_finance_profile(str(tenant_id), str(subcontractor_id), payload, context)


@router.patch("/{subcontractor_id}/finance-profile", response_model=SubcontractorFinanceProfileRead)
def patch_finance_profile(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorFinanceProfileUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.finance.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorService, Depends(get_subcontractor_service)],
) -> SubcontractorFinanceProfileRead:
    return service.upsert_finance_profile(str(tenant_id), str(subcontractor_id), payload, context)


@router.get("/{subcontractor_id}/workers", response_model=list[SubcontractorWorkerListItem])
def list_workers(
    tenant_id: UUID,
    subcontractor_id: UUID,
    search: str | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("subcontractors.company.read"))] = None,
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)] = None,
) -> list[SubcontractorWorkerListItem]:
    return service.list_workers(
        str(tenant_id),
        str(subcontractor_id),
        SubcontractorWorkerFilter(search=search, status=lifecycle_status, include_archived=include_archived),
        context,
    )


@router.post("/{subcontractor_id}/workers", response_model=SubcontractorWorkerRead, status_code=status.HTTP_201_CREATED)
def create_worker(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorWorkerCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> SubcontractorWorkerRead:
    return service.create_worker(str(tenant_id), str(subcontractor_id), payload, context)


@router.post("/{subcontractor_id}/workers/ops/import/dry-run", response_model=SubcontractorWorkerImportDryRunResult)
def import_workers_dry_run(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorWorkerImportDryRunRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorWorkforceOpsService, Depends(get_subcontractor_workforce_ops_service)],
) -> SubcontractorWorkerImportDryRunResult:
    return service.import_dry_run(str(tenant_id), str(subcontractor_id), payload, context)


@router.post("/{subcontractor_id}/workers/ops/import/execute", response_model=SubcontractorWorkerImportExecuteResult)
def import_workers_execute(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorWorkerImportExecuteRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorWorkforceOpsService, Depends(get_subcontractor_workforce_ops_service)],
) -> SubcontractorWorkerImportExecuteResult:
    return service.execute_import(str(tenant_id), str(subcontractor_id), payload, context)


@router.post("/{subcontractor_id}/workers/ops/export", response_model=SubcontractorWorkerExportResult)
def export_workers(
    tenant_id: UUID,
    subcontractor_id: UUID,
    payload: SubcontractorWorkerExportRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ],
    service: Annotated[SubcontractorWorkforceOpsService, Depends(get_subcontractor_workforce_ops_service)],
) -> SubcontractorWorkerExportResult:
    return service.export_workers(str(tenant_id), str(subcontractor_id), payload, context)


@router.get("/{subcontractor_id}/workers/readiness-summary", response_model=SubcontractorWorkforceReadinessSummaryRead)
def get_worker_readiness_summary(
    tenant_id: UUID,
    subcontractor_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ],
    service: Annotated[SubcontractorReadinessService, Depends(get_subcontractor_readiness_service)],
) -> SubcontractorWorkforceReadinessSummaryRead:
    return service.get_subcontractor_readiness_summary(str(tenant_id), str(subcontractor_id), context)


@router.get("/{subcontractor_id}/workers/readiness", response_model=list[SubcontractorWorkerReadinessListItem])
def list_worker_readiness(
    tenant_id: UUID,
    subcontractor_id: UUID,
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    include_archived: bool = Query(default=False),
    readiness_status: str | None = Query(default=None),
    issue_severity: str | None = Query(default=None),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ] = None,
    service: Annotated[SubcontractorReadinessService, Depends(get_subcontractor_readiness_service)] = None,
) -> list[SubcontractorWorkerReadinessListItem]:
    return service.list_worker_readiness(
        str(tenant_id),
        str(subcontractor_id),
        SubcontractorWorkerReadinessFilter(
            search=search,
            status=status_filter,
            include_archived=include_archived,
            readiness_status=readiness_status,
            issue_severity=issue_severity,
        ),
        context,
    )


@router.get("/{subcontractor_id}/workers/{worker_id}", response_model=SubcontractorWorkerRead)
def get_worker(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("subcontractors.company.read"))],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> SubcontractorWorkerRead:
    return service.get_worker(str(tenant_id), str(subcontractor_id), str(worker_id), context)


@router.get("/{subcontractor_id}/workers/{worker_id}/readiness", response_model=SubcontractorWorkerReadinessRead)
def get_worker_readiness(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ],
    service: Annotated[SubcontractorReadinessService, Depends(get_subcontractor_readiness_service)],
) -> SubcontractorWorkerReadinessRead:
    return service.get_worker_readiness(str(tenant_id), str(subcontractor_id), str(worker_id), context)


@router.patch("/{subcontractor_id}/workers/{worker_id}", response_model=SubcontractorWorkerRead)
def update_worker(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    payload: SubcontractorWorkerUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> SubcontractorWorkerRead:
    return service.update_worker(str(tenant_id), str(subcontractor_id), str(worker_id), payload, context)


@router.get("/{subcontractor_id}/workers/{worker_id}/qualifications", response_model=list[SubcontractorWorkerQualificationRead])
def list_worker_qualifications(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("subcontractors.company.read"))],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> list[SubcontractorWorkerQualificationRead]:
    return service.list_worker_qualifications(str(tenant_id), str(subcontractor_id), str(worker_id), context)


@router.post(
    "/{subcontractor_id}/workers/{worker_id}/qualifications",
    response_model=SubcontractorWorkerQualificationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_worker_qualification(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    payload: SubcontractorWorkerQualificationCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> SubcontractorWorkerQualificationRead:
    return service.create_worker_qualification(str(tenant_id), str(subcontractor_id), str(worker_id), payload, context)


@router.patch(
    "/{subcontractor_id}/workers/{worker_id}/qualifications/{qualification_id}",
    response_model=SubcontractorWorkerQualificationRead,
)
def update_worker_qualification(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    qualification_id: UUID,
    payload: SubcontractorWorkerQualificationUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> SubcontractorWorkerQualificationRead:
    return service.update_worker_qualification(
        str(tenant_id),
        str(subcontractor_id),
        str(worker_id),
        str(qualification_id),
        payload,
        context,
    )


@router.get(
    "/{subcontractor_id}/workers/{worker_id}/qualifications/{qualification_id}/proofs",
    response_model=list[SubcontractorWorkerQualificationProofRead],
)
def list_worker_qualification_proofs(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    qualification_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("subcontractors.company.read"))],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> list[SubcontractorWorkerQualificationProofRead]:
    return service.list_worker_qualification_proofs(
        str(tenant_id),
        str(subcontractor_id),
        str(worker_id),
        str(qualification_id),
        context,
    )


@router.post(
    "/{subcontractor_id}/workers/{worker_id}/qualifications/{qualification_id}/proofs/upload",
    response_model=SubcontractorWorkerQualificationProofRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_worker_qualification_proof(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    qualification_id: UUID,
    payload: SubcontractorWorkerQualificationProofUpload,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> SubcontractorWorkerQualificationProofRead:
    return service.upload_worker_qualification_proof(
        str(tenant_id),
        str(subcontractor_id),
        str(worker_id),
        str(qualification_id),
        payload,
        context,
    )


@router.post(
    "/{subcontractor_id}/workers/{worker_id}/qualifications/{qualification_id}/proofs/link",
    response_model=SubcontractorWorkerQualificationProofRead,
    status_code=status.HTTP_201_CREATED,
)
def link_existing_worker_qualification_proof(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    qualification_id: UUID,
    payload: SubcontractorWorkerQualificationProofLinkCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> SubcontractorWorkerQualificationProofRead:
    return service.link_existing_worker_qualification_proof(
        str(tenant_id),
        str(subcontractor_id),
        str(worker_id),
        str(qualification_id),
        payload,
        context,
    )


@router.get("/{subcontractor_id}/workers/{worker_id}/credentials", response_model=list[SubcontractorWorkerCredentialRead])
def list_worker_credentials(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    context: Annotated[RequestAuthorizationContext, Depends(require_permission_only("subcontractors.company.read"))],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> list[SubcontractorWorkerCredentialRead]:
    return service.list_worker_credentials(str(tenant_id), str(subcontractor_id), str(worker_id), context)


@router.post(
    "/{subcontractor_id}/workers/{worker_id}/credentials",
    response_model=SubcontractorWorkerCredentialRead,
    status_code=status.HTTP_201_CREATED,
)
def create_worker_credential(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    payload: SubcontractorWorkerCredentialCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> SubcontractorWorkerCredentialRead:
    return service.create_worker_credential(str(tenant_id), str(subcontractor_id), str(worker_id), payload, context)


@router.patch(
    "/{subcontractor_id}/workers/{worker_id}/credentials/{credential_id}",
    response_model=SubcontractorWorkerCredentialRead,
)
def update_worker_credential(
    tenant_id: UUID,
    subcontractor_id: UUID,
    worker_id: UUID,
    credential_id: UUID,
    payload: SubcontractorWorkerCredentialUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("subcontractors.company.write", scope="tenant")),
    ],
    service: Annotated[SubcontractorWorkforceService, Depends(get_subcontractor_workforce_service)],
) -> SubcontractorWorkerCredentialRead:
    return service.update_worker_credential(
        str(tenant_id),
        str(subcontractor_id),
        str(worker_id),
        str(credential_id),
        payload,
        context,
    )
