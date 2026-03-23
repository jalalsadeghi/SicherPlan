from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.errors import ApiException
from app.modules.iam.admin_router import (
    create_tenant_admin_user,
    list_tenant_admin_users,
    reset_tenant_admin_user_password,
    update_tenant_admin_user_status,
)
from app.modules.iam.admin_service import IamAdminActorContext
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.iam.schemas import (
    TenantAdminPasswordResetRequest,
    TenantAdminPasswordResetResponse,
    TenantAdminUserCreate,
    TenantAdminUserListItem,
    TenantAdminUserStatusUpdate,
)


def _tenant_user(
    tenant_id: str,
    user_id: str,
    username: str,
    status: str = "active",
) -> TenantAdminUserListItem:
    return TenantAdminUserListItem(
        id=user_id,
        tenant_id=tenant_id,
        username=username,
        email=f"{username}@example.invalid",
        full_name=username.title(),
        locale="de",
        timezone="Europe/Berlin",
        status=status,
        is_password_login_enabled=True,
        last_login_at=None,
        role_assignment_id=str(uuid4()),
        role_assignment_status=status,
        role_key="tenant_admin",
        scope_type="tenant",
        created_at="2026-03-21T00:00:00Z",
        updated_at="2026-03-21T00:00:00Z",
        version_no=1,
    )


@dataclass
class FakeIamAdminService:
    tenant_id: str
    users: list[TenantAdminUserListItem] = field(default_factory=list)

    def list_tenant_admin_users(self, tenant_id: str, actor: IamAdminActorContext) -> list[TenantAdminUserListItem]:
        if not actor.is_platform_admin:
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")
        if tenant_id != self.tenant_id:
            raise ApiException(404, "iam.tenant.not_found", "errors.iam.tenant.not_found")
        return list(self.users)

    def create_tenant_admin_user(
        self,
        payload: TenantAdminUserCreate,
        actor: IamAdminActorContext,
    ) -> TenantAdminPasswordResetResponse:
        if not actor.is_platform_admin:
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")
        self.users.append(_tenant_user(payload.tenant_id, str(uuid4()), payload.username, payload.status))
        return TenantAdminPasswordResetResponse(
            message_key="messages.iam.tenant_admin_user.created",
            temporary_password=payload.temporary_password or "TempPassword!123",
        )

    def update_tenant_admin_user_status(
        self,
        tenant_id: str,
        user_id: str,
        payload: TenantAdminUserStatusUpdate,
        actor: IamAdminActorContext,
    ) -> TenantAdminUserListItem:
        if not actor.is_platform_admin:
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")
        for index, user in enumerate(self.users):
            if user.id == user_id and user.tenant_id == tenant_id:
                updated = user.model_copy(update={"status": payload.status, "role_assignment_status": payload.status})
                self.users[index] = updated
                return updated
        raise ApiException(404, "iam.tenant_admin_user.not_found", "errors.iam.tenant_admin_user.not_found")

    def reset_tenant_admin_password(
        self,
        tenant_id: str,
        user_id: str,
        payload: TenantAdminPasswordResetRequest,
        actor: IamAdminActorContext,
    ) -> TenantAdminPasswordResetResponse:
        if not actor.is_platform_admin:
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")
        if not any(user.id == user_id and user.tenant_id == tenant_id for user in self.users):
            raise ApiException(404, "iam.tenant_admin_user.not_found", "errors.iam.tenant_admin_user.not_found")
        return TenantAdminPasswordResetResponse(
            message_key="messages.iam.tenant_admin_user.password_reset",
            temporary_password=payload.temporary_password or "ResetPassword!123",
        )


class TestTenantAdminUserRouter(unittest.TestCase):
    def setUp(self) -> None:
        self.tenant_id = str(uuid4())
        self.user_id = str(uuid4())
        self.actor_platform = RequestAuthorizationContext(
            session_id="session-platform",
            user_id=str(uuid4()),
            tenant_id=self.tenant_id,
            role_keys=frozenset({"platform_admin"}),
            permission_keys=frozenset({"core.admin.tenant.create", "core.admin.tenant.read", "core.admin.tenant.write"}),
            scopes=(AuthenticatedRoleScope(role_key="platform_admin", scope_type="tenant"),),
        )
        self.fake_service = FakeIamAdminService(
            tenant_id=self.tenant_id,
            users=[_tenant_user(self.tenant_id, self.user_id, "tenant-admin")],
        )

    def test_list_handler_returns_users(self) -> None:
        result = list_tenant_admin_users(
            UUID(self.tenant_id),
            self.actor_platform,
            self.fake_service,  # type: ignore[arg-type]
        )
        self.assertEqual(1, len(result))
        self.assertEqual("tenant-admin", result[0].username)

    def test_create_handler_returns_temp_password(self) -> None:
        result = create_tenant_admin_user(
            UUID(self.tenant_id),
            TenantAdminUserCreate(
                tenant_id=self.tenant_id,
                username="new-admin",
                email="new-admin@example.invalid",
                full_name="New Admin",
                temporary_password="ChangeMe!123",
            ),
            self.actor_platform,
            self.fake_service,  # type: ignore[arg-type]
        )
        self.assertEqual("ChangeMe!123", result.temporary_password)

    def test_status_handler_updates_status(self) -> None:
        result = update_tenant_admin_user_status(
            UUID(self.tenant_id),
            UUID(self.user_id),
            TenantAdminUserStatusUpdate(status="inactive"),
            self.actor_platform,
            self.fake_service,  # type: ignore[arg-type]
        )
        self.assertEqual("inactive", result.status)
        self.assertEqual("inactive", result.role_assignment_status)

    def test_password_reset_handler_returns_reset_password(self) -> None:
        result = reset_tenant_admin_user_password(
            UUID(self.tenant_id),
            UUID(self.user_id),
            TenantAdminPasswordResetRequest(temporary_password="Reset!12345"),
            self.actor_platform,
            self.fake_service,  # type: ignore[arg-type]
        )
        self.assertEqual("Reset!12345", result.temporary_password)


class TestTenantAdminUserServiceNormalization(unittest.TestCase):
    def test_normalize_create_payload_trims_and_keeps_temp_password(self) -> None:
        from app.modules.iam.admin_service import IamAdminService

        payload = TenantAdminUserCreate(
            tenant_id=str(uuid4()),
            username="  ops-admin  ",
            email="  OPS-ADMIN@EXAMPLE.INVALID  ",
            full_name="  Ops Admin  ",
            locale=" DE ",
            timezone=" Europe/Berlin ",
            status=" ACTIVE ",
            temporary_password="  Temp!12345  ",
        )

        normalized = IamAdminService._normalize_create_payload(payload)

        self.assertEqual("ops-admin", normalized.username)
        self.assertEqual("ops-admin@example.invalid", normalized.email)
        self.assertEqual("Ops Admin", normalized.full_name)
        self.assertEqual("de", normalized.locale)
        self.assertEqual("Europe/Berlin", normalized.timezone)
        self.assertEqual("active", normalized.status)
        self.assertEqual("Temp!12345", normalized.temporary_password)
