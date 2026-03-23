"""Read-only subcontractor contracts for downstream module consumption."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.iam.authz import RequestAuthorizationContext, require_permission_only
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.subcontractors.contracts import (
    SubcontractorCommercialSummaryRead,
    SubcontractorCredentialResolutionRead,
    SubcontractorDownstreamFilter,
    SubcontractorPartnerContractRead,
    SubcontractorWorkerContractRead,
    SubcontractorWorkerDownstreamFilter,
)
from app.modules.subcontractors.read_model_service import SubcontractorReadModelService
from app.modules.subcontractors.readiness_service import SubcontractorReadinessService
from app.modules.subcontractors.repository import SqlAlchemySubcontractorRepository


router = APIRouter(prefix="/api/subcontractor-read-models/tenants/{tenant_id}", tags=["subcontractor-read-models"])


def get_subcontractor_read_model_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> SubcontractorReadModelService:
    repository = SqlAlchemySubcontractorRepository(session)
    return SubcontractorReadModelService(
        repository,
        readiness_service=SubcontractorReadinessService(
            repository,
            document_repository=SqlAlchemyDocumentRepository(session),
        ),
    )


@router.get("/partners", response_model=list[SubcontractorPartnerContractRead])
def list_partner_contracts(
    tenant_id: UUID,
    search: str | None = Query(default=None),
    branch_id: UUID | None = Query(default=None),
    mandate_id: UUID | None = Query(default=None),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ] = None,
    service: Annotated[SubcontractorReadModelService, Depends(get_subcontractor_read_model_service)] = None,
) -> list[SubcontractorPartnerContractRead]:
    return service.list_partner_contracts(
        str(tenant_id),
        SubcontractorDownstreamFilter(
            search=search,
            branch_id=str(branch_id) if branch_id else None,
            mandate_id=str(mandate_id) if mandate_id else None,
        ),
        context,
    )


@router.get("/partners/{subcontractor_id}/workers", response_model=list[SubcontractorWorkerContractRead])
def list_partner_worker_contracts(
    tenant_id: UUID,
    subcontractor_id: UUID,
    search: str | None = Query(default=None),
    qualification_type_id: UUID | None = Query(default=None),
    credential_type: str | None = Query(default=None),
    ready_only: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ] = None,
    service: Annotated[SubcontractorReadModelService, Depends(get_subcontractor_read_model_service)] = None,
) -> list[SubcontractorWorkerContractRead]:
    return service.list_worker_contracts(
        str(tenant_id),
        str(subcontractor_id),
        SubcontractorWorkerDownstreamFilter(
            search=search,
            qualification_type_id=str(qualification_type_id) if qualification_type_id else None,
            credential_type=credential_type,
            ready_only=ready_only,
        ),
        context,
    )


@router.get("/partners/{subcontractor_id}/commercial-summary", response_model=SubcontractorCommercialSummaryRead)
def get_partner_commercial_summary(
    tenant_id: UUID,
    subcontractor_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.finance.read")),
    ] = None,
    service: Annotated[SubcontractorReadModelService, Depends(get_subcontractor_read_model_service)] = None,
) -> SubcontractorCommercialSummaryRead:
    return service.get_commercial_summary(str(tenant_id), str(subcontractor_id), context)


@router.get("/field/credential-resolution/{encoded_value}", response_model=SubcontractorCredentialResolutionRead | None)
def resolve_field_credential(
    tenant_id: UUID,
    encoded_value: str,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_permission_only("subcontractors.company.read")),
    ] = None,
    service: Annotated[SubcontractorReadModelService, Depends(get_subcontractor_read_model_service)] = None,
) -> SubcontractorCredentialResolutionRead | None:
    return service.resolve_field_credential(str(tenant_id), encoded_value, context)
