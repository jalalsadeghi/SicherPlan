"""Authenticated recruiting workflow endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization
from app.modules.recruiting.conversion_service import ApplicantConversionService
from app.modules.recruiting.repository import SqlAlchemyRecruitingRepository
from app.modules.recruiting.schemas import (
    ApplicantActivityCreate,
    ApplicantActivityEventRead,
    ApplicantConversionRead,
    ApplicantDetailRead,
    ApplicantListItem,
    ApplicantTimelineRead,
    ApplicantTransitionRequest,
)
from app.modules.recruiting.workflow_service import ApplicantWorkflowService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService


router = APIRouter(prefix="/api/recruiting/tenants/{tenant_id}/applicants", tags=["recruiting"])


def get_workflow_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> ApplicantWorkflowService:
    return ApplicantWorkflowService(
        SqlAlchemyRecruitingRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_conversion_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> ApplicantConversionService:
    return ApplicantConversionService(SqlAlchemyRecruitingRepository(session))


@router.get("", response_model=list[ApplicantListItem])
def list_applicants(
    tenant_id: UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    source_channel: str | None = Query(default=None),
    search: str | None = Query(default=None),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("recruiting.applicant.read", scope="tenant")),
    ] = None,
    service: Annotated[ApplicantWorkflowService, Depends(get_workflow_service)] = None,
) -> list[ApplicantListItem]:
    return service.list_applicants(
        str(tenant_id),
        context,
        status=status_filter,
        source_channel=source_channel,
        search=search,
    )


@router.get("/{applicant_id}", response_model=ApplicantDetailRead)
def get_applicant_detail(
    tenant_id: UUID,
    applicant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("recruiting.applicant.read", scope="tenant")),
    ] = None,
    service: Annotated[ApplicantWorkflowService, Depends(get_workflow_service)] = None,
) -> ApplicantDetailRead:
    return service.get_detail(str(tenant_id), str(applicant_id), context)


@router.post("/{applicant_id}/transitions", response_model=ApplicantTimelineRead, status_code=status.HTTP_200_OK)
def transition_applicant(
    tenant_id: UUID,
    applicant_id: UUID,
    payload: ApplicantTransitionRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("recruiting.applicant.write", scope="tenant")),
    ],
    service: Annotated[ApplicantWorkflowService, Depends(get_workflow_service)],
) -> ApplicantTimelineRead:
    return service.transition_applicant(str(tenant_id), str(applicant_id), payload, context)


@router.post("/{applicant_id}/activities", response_model=ApplicantActivityEventRead, status_code=status.HTTP_201_CREATED)
def add_applicant_activity(
    tenant_id: UUID,
    applicant_id: UUID,
    payload: ApplicantActivityCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("recruiting.applicant.write", scope="tenant")),
    ],
    service: Annotated[ApplicantWorkflowService, Depends(get_workflow_service)],
) -> ApplicantActivityEventRead:
    return service.add_activity(str(tenant_id), str(applicant_id), payload, context)


@router.post("/{applicant_id}/convert", response_model=ApplicantConversionRead, status_code=status.HTTP_200_OK)
def convert_applicant(
    tenant_id: UUID,
    applicant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("recruiting.applicant.write", scope="tenant")),
    ],
    service: Annotated[ApplicantConversionService, Depends(get_conversion_service)],
) -> ApplicantConversionRead:
    return service.convert_applicant(str(tenant_id), str(applicant_id), context)
