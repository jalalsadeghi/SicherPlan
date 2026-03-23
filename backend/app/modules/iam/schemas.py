"""Pydantic schemas for IAM persistence and seed bootstrap."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RoleScopeType = Literal["tenant", "branch", "mandate", "customer", "subcontractor"]


class UserAccountCreate(BaseModel):
    tenant_id: str
    username: str
    email: str
    full_name: str
    password_hash: str | None = None
    locale: str = "de"
    timezone: str = "Europe/Berlin"
    is_platform_user: bool = False
    is_password_login_enabled: bool = True


class UserAccountUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    password_hash: str | None = None
    locale: str | None = None
    timezone: str | None = None
    is_password_login_enabled: bool | None = None
    last_login_at: datetime | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class UserAccountListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    username: str
    email: str
    full_name: str
    status: str
    is_platform_user: bool
    version_no: int


class UserAccountRead(UserAccountListItem):
    locale: str
    timezone: str
    password_hash: str | None
    is_password_login_enabled: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class UserAccountFilter(BaseModel):
    tenant_id: str | None = None
    status: str | None = None
    role_key: str | None = None


class ExternalIdentityCreate(BaseModel):
    user_account_id: str
    provider: str
    subject: str
    provider_user_name: str | None = None
    provider_email: str | None = None
    claims_json: dict[str, object] = Field(default_factory=dict)


class ExternalIdentityUpdate(BaseModel):
    provider_user_name: str | None = None
    provider_email: str | None = None
    claims_json: dict[str, object] | None = None
    last_verified_at: datetime | None = None


class ExternalIdentityListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_account_id: str
    provider: str
    subject: str
    provider_user_name: str | None


class ExternalIdentityRead(ExternalIdentityListItem):
    provider_email: str | None
    claims_json: dict[str, object]
    linked_at: datetime
    last_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ExternalIdentityFilter(BaseModel):
    user_account_id: str | None = None
    provider: str | None = None


class RoleCreate(BaseModel):
    key: str
    name: str
    description: str | None = None
    is_portal_role: bool = False
    is_system_role: bool = True


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_portal_role: bool | None = None
    is_system_role: bool | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class RoleListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: str
    name: str
    status: str
    is_portal_role: bool
    is_system_role: bool
    version_no: int


class RoleRead(RoleListItem):
    description: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class RoleFilter(BaseModel):
    status: str | None = None
    is_portal_role: bool | None = None


class PermissionCreate(BaseModel):
    key: str
    module: str
    action: str
    description: str | None = None


class PermissionUpdate(BaseModel):
    description: str | None = None


class PermissionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: str
    module: str
    action: str


class PermissionRead(PermissionListItem):
    description: str | None


class PermissionFilter(BaseModel):
    module: str | None = None
    action: str | None = None


class RolePermissionCreate(BaseModel):
    role_id: str
    permission_id: str


class RolePermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role_id: str
    permission_id: str
    granted_at: datetime


class RolePermissionFilter(BaseModel):
    role_id: str | None = None
    permission_id: str | None = None


class UserRoleAssignmentCreate(BaseModel):
    tenant_id: str
    user_account_id: str
    role_id: str
    scope_type: RoleScopeType = "tenant"
    branch_id: str | None = None
    mandate_id: str | None = None
    customer_id: str | None = None
    subcontractor_id: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class UserRoleAssignmentUpdate(BaseModel):
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class UserRoleAssignmentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    user_account_id: str
    role_id: str
    scope_type: RoleScopeType
    branch_id: str | None
    mandate_id: str | None
    customer_id: str | None
    subcontractor_id: str | None
    status: str
    version_no: int


class UserRoleAssignmentRead(UserRoleAssignmentListItem):
    valid_from: datetime | None
    valid_until: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class UserRoleAssignmentFilter(BaseModel):
    tenant_id: str | None = None
    user_account_id: str | None = None
    role_id: str | None = None
    scope_type: RoleScopeType | None = None


class TenantAdminUserCreate(BaseModel):
    tenant_id: str
    username: str
    email: str
    full_name: str
    locale: str = "de"
    timezone: str = "Europe/Berlin"
    status: str = "active"
    temporary_password: str | None = None


class TenantAdminUserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    username: str
    email: str
    full_name: str
    locale: str
    timezone: str
    status: str
    is_password_login_enabled: bool
    last_login_at: datetime | None
    role_assignment_id: str
    role_assignment_status: str
    role_key: str
    scope_type: RoleScopeType
    created_at: datetime
    updated_at: datetime
    version_no: int


class TenantAdminUserStatusUpdate(BaseModel):
    status: Literal["active", "inactive"]


class TenantAdminPasswordResetRequest(BaseModel):
    temporary_password: str | None = None


class TenantAdminPasswordResetResponse(BaseModel):
    message_key: str
    temporary_password: str


class UserSessionCreate(BaseModel):
    tenant_id: str
    user_account_id: str
    session_token_hash: str
    refresh_token_family: str
    expires_at: datetime
    device_label: str | None = None
    device_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class UserSessionUpdate(BaseModel):
    status: str | None = None
    last_seen_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    metadata_json: dict[str, object] | None = None


class UserSessionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    user_account_id: str
    refresh_token_family: str
    status: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    device_label: str | None
    device_id: str | None


class UserSessionRead(UserSessionListItem):
    session_token_hash: str
    last_seen_at: datetime | None
    revoked_reason: str | None
    ip_address: str | None
    user_agent: str | None
    metadata_json: dict[str, object]
    created_at: datetime
    updated_at: datetime


class UserSessionFilter(BaseModel):
    tenant_id: str | None = None
    user_account_id: str | None = None
    status: str | None = None
