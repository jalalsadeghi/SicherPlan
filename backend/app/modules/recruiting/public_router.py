"""Public applicant intake endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db_session
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.storage import build_object_storage_adapter
from app.modules.recruiting.public_service import (
    PublicApplicantService,
    PublicApplicantThrottle,
    PublicRequestContext,
)
from app.modules.recruiting.repository import SqlAlchemyRecruitingRepository
from app.modules.recruiting.schemas import (
    PublicApplicantFormConfigRead,
    PublicApplicantSubmissionCreate,
    PublicApplicantSubmissionResponse,
)


router = APIRouter(prefix="/api/public/recruiting", tags=["recruiting-public"])

_public_applicant_throttle = PublicApplicantThrottle(max_attempts=10, lockout_minutes=15)


def get_public_applicant_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> PublicApplicantService:
    return PublicApplicantService(
        SqlAlchemyRecruitingRepository(session),
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
        throttle=_public_applicant_throttle,
    )


def _request_origin(request: Request) -> str | None:
    origin = request.headers.get("origin")
    if origin:
        return origin
    referer = request.headers.get("referer")
    return referer or None


def _request_context(request: Request) -> PublicRequestContext:
    return PublicRequestContext(
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_origin=_request_origin(request),
    )


@router.get("/applicant-form/{tenant_code}", response_model=PublicApplicantFormConfigRead)
def get_public_applicant_form(
    tenant_code: str,
    request: Request,
    service: Annotated[PublicApplicantService, Depends(get_public_applicant_service)],
) -> PublicApplicantFormConfigRead:
    return service.get_public_form(tenant_code, _request_context(request))


@router.post(
    "/applicant-form/{tenant_code}",
    response_model=PublicApplicantSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_public_application(
    tenant_code: str,
    payload: PublicApplicantSubmissionCreate,
    request: Request,
    service: Annotated[PublicApplicantService, Depends(get_public_applicant_service)],
) -> PublicApplicantSubmissionResponse:
    return service.submit_public_application(tenant_code, payload, _request_context(request))
