from __future__ import annotations

import unittest
from dataclasses import dataclass
from uuid import uuid4

from fastapi.testclient import TestClient

from app.errors import ApiException
from app.main import create_app
from app.modules.core.admin_router import (
    create_branch,
    get_tenant,
    onboard_tenant,
    update_setting,
)
from app.modules.core.admin_service import AdminActorContext
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.core.schemas import (
    BranchCreate,
    BranchRead,
    MandateCreate,
    MandateRead,
    TenantCreate,
    TenantListItem,
    TenantOnboardingCreate,
    TenantOnboardingRead,
    TenantRead,
    TenantSettingCreate,
    TenantSettingRead,
    TenantSettingUpdate,
)


def _tenant_read(
    tenant_id: str,
    code: str,
    name: str,
    status: str = "active",
    version_no: int = 1,
) -> TenantRead:
    return TenantRead(
        id=tenant_id,
        code=code,
        name=name,
        legal_name=None,
        default_locale="de",
        default_currency="EUR",
        timezone="Europe/Berlin",
        status=status,
        version_no=version_no,
        created_at="2026-03-19T00:00:00Z",
        updated_at="2026-03-19T00:00:00Z",
        created_by_user_id=None,
        updated_by_user_id=None,
        archived_at=None,
    )


def _branch_read(
    tenant_id: str,
    branch_id: str,
    code: str,
    name: str,
    version_no: int = 1,
) -> BranchRead:
    return BranchRead(
        id=branch_id,
        tenant_id=tenant_id,
        code=code,
        name=name,
        address_id=None,
        contact_email=None,
        contact_phone=None,
        status="active",
        version_no=version_no,
        created_at="2026-03-19T00:00:00Z",
        updated_at="2026-03-19T00:00:00Z",
        created_by_user_id=None,
        updated_by_user_id=None,
        archived_at=None,
    )


def _mandate_read(
    tenant_id: str,
    branch_id: str,
    mandate_id: str,
    code: str,
    name: str,
) -> MandateRead:
    return MandateRead(
        id=mandate_id,
        tenant_id=tenant_id,
        branch_id=branch_id,
        code=code,
        name=name,
        external_ref=None,
        notes=None,
        status="active",
        version_no=1,
        created_at="2026-03-19T00:00:00Z",
        updated_at="2026-03-19T00:00:00Z",
        created_by_user_id=None,
        updated_by_user_id=None,
        archived_at=None,
    )


def _setting_read(
    tenant_id: str,
    setting_id: str,
    key: str,
    value_json: dict[str, object],
    version_no: int = 1,
) -> TenantSettingRead:
    return TenantSettingRead(
        id=setting_id,
        tenant_id=tenant_id,
        key=key,
        value_json=value_json,
        status="active",
        version_no=version_no,
        created_at="2026-03-19T00:00:00Z",
        updated_at="2026-03-19T00:00:00Z",
        created_by_user_id=None,
        updated_by_user_id=None,
        archived_at=None,
    )


@dataclass
class FakeCoreAdminService:
    tenant: TenantRead
    branch: BranchRead
    mandate: MandateRead
    setting: TenantSettingRead

    def onboard_tenant(
        self,
        payload: TenantOnboardingCreate,
        actor: AdminActorContext,
    ) -> TenantOnboardingRead:
        if not actor.is_platform_admin:
            raise ApiException(
                403,
                "core.authorization.forbidden",
                "errors.core.authorization.forbidden",
            )
        return TenantOnboardingRead(
            tenant=self.tenant,
            initial_branch=self.branch,
            initial_mandate=self.mandate,
            initial_settings=[self.setting],
        )

    def get_tenant(self, tenant_id: str, actor: AdminActorContext) -> TenantRead:
        if actor.is_platform_admin or actor.tenant_id == tenant_id:
            return self.tenant
        raise ApiException(
            403,
            "core.authorization.forbidden",
            "errors.core.authorization.forbidden",
        )

    def create_branch(
        self,
        tenant_id: str,
        payload: BranchCreate,
        actor: AdminActorContext,
    ) -> BranchRead:
        if payload.code == self.branch.code:
            raise ApiException(
                409,
                "core.conflict.branch_code",
                "errors.core.branch.duplicate_code",
            )
        return _branch_read(tenant_id, str(uuid4()), payload.code, payload.name)

    def update_setting(
        self,
        tenant_id: str,
        setting_id: str,
        payload: TenantSettingUpdate,
        actor: AdminActorContext,
    ) -> TenantSettingRead:
        if payload.version_no != self.setting.version_no:
            raise ApiException(
                409,
                "core.conflict.stale_setting_version",
                "errors.core.setting.stale_version",
                {"expected_version_no": self.setting.version_no},
            )
        return _setting_read(
            tenant_id,
            setting_id,
            self.setting.key,
            payload.value_json or self.setting.value_json,
            version_no=self.setting.version_no + 1,
        )


class TestTenantAdminApi(unittest.TestCase):
    def setUp(self) -> None:
        self.tenant_id = str(uuid4())
        self.branch_id = str(uuid4())
        self.mandate_id = str(uuid4())
        self.setting_id = str(uuid4())
        self.actor_platform = RequestAuthorizationContext(
            session_id="session-platform",
            user_id=str(uuid4()),
            tenant_id=self.tenant_id,
            role_keys=frozenset({"platform_admin"}),
            permission_keys=frozenset({"core.admin.tenant.create", "core.admin.tenant.read", "core.admin.setting.write"}),
            scopes=(AuthenticatedRoleScope(role_key="platform_admin", scope_type="tenant"),),
        )
        self.actor_wrong_tenant = RequestAuthorizationContext(
            session_id="session-wrong",
            user_id=str(uuid4()),
            tenant_id=str(uuid4()),
            role_keys=frozenset({"tenant_admin"}),
            permission_keys=frozenset({"core.admin.tenant.read"}),
            scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        )
        self.actor_tenant = RequestAuthorizationContext(
            session_id="session-tenant",
            user_id=str(uuid4()),
            tenant_id=self.tenant_id,
            role_keys=frozenset({"tenant_admin"}),
            permission_keys=frozenset({"core.admin.tenant.read", "core.admin.setting.write"}),
            scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        )
        self.fake_service = FakeCoreAdminService(
            tenant=_tenant_read(self.tenant_id, "nord", "SicherPlan Nord"),
            branch=_branch_read(self.tenant_id, self.branch_id, "hq", "Hamburg"),
            mandate=_mandate_read(
                self.tenant_id,
                self.branch_id,
                self.mandate_id,
                "prime",
                "Prime",
            ),
            setting=_setting_read(
                self.tenant_id,
                self.setting_id,
                "ui.theme",
                {"mode": "light"},
            ),
        )

    def test_platform_admin_can_onboard_tenant(self) -> None:
        result = onboard_tenant(
            TenantOnboardingCreate(
                tenant=TenantCreate(code="west", name="SicherPlan West"),
                initial_branch=BranchCreate(
                    tenant_id=self.tenant_id,
                    code="west-hq",
                    name="Koeln",
                ),
                initial_mandate=MandateCreate(
                    tenant_id=self.tenant_id,
                    branch_id=self.branch_id,
                    code="main",
                    name="Main",
                ),
                initial_settings=[
                    TenantSettingCreate(
                        tenant_id=self.tenant_id,
                        key="ui.theme",
                        value_json={"mode": "light"},
                    ),
                ],
            ),
            self.actor_platform,
            self.fake_service,
        )
        self.assertEqual(result.tenant.code, "nord")

    def test_tenant_admin_cannot_read_other_tenant(self) -> None:
        with self.assertRaises(ApiException) as context:
            get_tenant(
                self.tenant_id,  # type: ignore[arg-type]
                self.actor_wrong_tenant,
                self.fake_service,
            )
        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(
            context.exception.message_key,
            "errors.core.authorization.forbidden",
        )

    def test_duplicate_branch_conflict_is_stable(self) -> None:
        with self.assertRaises(ApiException) as context:
            create_branch(
                self.tenant_id,  # type: ignore[arg-type]
                BranchCreate(tenant_id=self.tenant_id, code="hq", name="Duplicate"),
                self.actor_platform,
                self.fake_service,
            )
        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(
            context.exception.message_key,
            "errors.core.branch.duplicate_code",
        )

    def test_setting_update_rejects_stale_version(self) -> None:
        with self.assertRaises(ApiException) as context:
            update_setting(
                self.tenant_id,  # type: ignore[arg-type]
                self.setting_id,  # type: ignore[arg-type]
                TenantSettingUpdate(value_json={"mode": "dark"}, version_no=99),
                self.actor_tenant,
                self.fake_service,
            )
        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(
            context.exception.code,
            "core.conflict.stale_setting_version",
        )
        self.assertEqual(context.exception.details["expected_version_no"], 1)

    def test_core_admin_routes_are_registered(self) -> None:
        app = create_app()
        paths = {route.path for route in app.routes}
        self.assertIn("/api/core/admin/tenants/onboard", paths)
        self.assertIn("/api/core/admin/tenants/{tenant_id}/branches", paths)
        self.assertIn("/api/core/admin/tenants/{tenant_id}/mandates", paths)
        self.assertIn("/api/core/admin/tenants/{tenant_id}/settings/{setting_id}", paths)

    def test_core_admin_tenant_list_supports_cors_preflight(self) -> None:
        app = create_app()
        client = TestClient(app)

        response = client.options(
            "/api/core/admin/tenants",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type,x-request-id",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://localhost:5173")
        self.assertIn("GET", response.headers.get("access-control-allow-methods", ""))
