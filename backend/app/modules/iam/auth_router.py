"""HTTP router for IAM authentication flows."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db_session
from app.errors import ApiException
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_adapters import DefaultAuthExtensionHooks, LoggingPasswordResetNotifier
from app.modules.iam.auth_repository import SqlAlchemyAuthRepository
from app.modules.iam.auth_schemas import (
    AccessCodesResponse,
    CurrentSessionResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshRequest,
    RefreshResponse,
    SessionListResponse,
)
from app.modules.iam.auth_service import AuthService, AuthThrottle, AuthenticatedSessionContext


router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)
auth_throttle = AuthThrottle(
    max_attempts=settings.auth_login_max_attempts,
    lockout_minutes=settings.auth_lockout_minutes,
)


def get_auth_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> AuthService:
    return AuthService(
        SqlAlchemyAuthRepository(session),
        auth_secret=settings.auth_session_secret,
        access_ttl_minutes=settings.auth_access_token_ttl_minutes,
        refresh_ttl_minutes=settings.auth_refresh_token_ttl_minutes,
        reset_ttl_minutes=settings.auth_password_reset_token_ttl_minutes,
        notifier=LoggingPasswordResetNotifier(),
        extension_hooks=DefaultAuthExtensionHooks(),
        throttle=auth_throttle,
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_current_auth_context(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthenticatedSessionContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiException(401, "iam.auth.invalid_access_token", "errors.iam.auth.invalid_access_token")
    return service.with_request_context(
        service.authenticate_access_token(credentials.credentials),
        request_id=getattr(request.state, "request_id", None),
    )


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _request_id(request: Request) -> str | None:
    state = getattr(request, "state", None)
    return getattr(state, "request_id", None)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    return service.login(
        payload,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        request_id=_request_id(request),
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh(
    payload: RefreshRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> RefreshResponse:
    return service.refresh_session(payload)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    context: Annotated[AuthenticatedSessionContext, Depends(get_current_auth_context)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LogoutResponse:
    return service.logout(context)


@router.get("/me", response_model=CurrentSessionResponse)
def current_session(
    context: Annotated[AuthenticatedSessionContext, Depends(get_current_auth_context)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> CurrentSessionResponse:
    return service.current_session(context)


@router.get("/codes", response_model=AccessCodesResponse)
def access_codes(
    context: Annotated[AuthenticatedSessionContext, Depends(get_current_auth_context)],
) -> AccessCodesResponse:
    return AccessCodesResponse(items=sorted(context.permission_keys))


@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(
    context: Annotated[AuthenticatedSessionContext, Depends(get_current_auth_context)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> SessionListResponse:
    return service.list_sessions(context)


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> PasswordResetRequestResponse:
    return service.request_password_reset(
        payload,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/password-reset/confirm", response_model=PasswordResetConfirmResponse)
def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> PasswordResetConfirmResponse:
    return service.confirm_password_reset(payload)
