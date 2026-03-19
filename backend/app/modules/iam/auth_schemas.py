"""Pydantic schemas for IAM authentication flows."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    tenant_code: str
    identifier: str
    password: str
    device_label: str | None = None
    device_id: str | None = None


class AuthenticatedRoleScope(BaseModel):
    role_key: str
    scope_type: str
    branch_id: str | None = None
    mandate_id: str | None = None
    customer_id: str | None = None
    subcontractor_id: str | None = None


class AuthenticatedUser(BaseModel):
    id: str
    tenant_id: str
    username: str
    email: str
    full_name: str
    locale: str
    timezone: str
    is_platform_user: bool
    roles: list[AuthenticatedRoleScope] = Field(default_factory=list)


class SessionTokenPair(BaseModel):
    access_token: str
    access_token_type: str = "Bearer"
    access_token_expires_at: datetime
    refresh_token: str
    refresh_token_expires_at: datetime
    session_id: str
    mfa_required: bool = False
    sso_hints: list[str] = Field(default_factory=list)


class LoginResponse(BaseModel):
    user: AuthenticatedUser
    session: SessionTokenPair


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    session: SessionTokenPair


class LogoutResponse(BaseModel):
    message_key: str


class SessionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    refresh_token_family: str
    status: str
    issued_at: datetime
    expires_at: datetime
    last_seen_at: datetime | None
    revoked_at: datetime | None
    device_label: str | None
    device_id: str | None
    ip_address: str | None
    user_agent: str | None
    is_current: bool = False


class CurrentSessionResponse(BaseModel):
    user: AuthenticatedUser
    session: SessionListItem


class SessionListResponse(BaseModel):
    items: list[SessionListItem]


class PasswordResetRequest(BaseModel):
    tenant_code: str
    identifier: str


class PasswordResetRequestResponse(BaseModel):
    message_key: str


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str


class PasswordResetConfirmResponse(BaseModel):
    message_key: str
