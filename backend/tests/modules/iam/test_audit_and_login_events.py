from __future__ import annotations

import unittest
from dataclasses import dataclass
from uuid import uuid4

from app.modules.iam.audit_models import AuditEvent, LoginEvent
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.audit_schemas import AuditEventWrite, LoginEventWrite
from app.modules.iam.auth_service import AuthService, AuthThrottle
from app.modules.iam.auth_schemas import LoginRequest
from app.modules.iam.security import hash_password
from backend.tests.modules.iam.test_auth_flows import FakeAuthRepository, FakeHooks, FakeTenant, FakeUser, RecordingNotifier
from app.modules.core.admin_service import AdminActorContext, CoreAdminService


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.login_events: list[LoginEventWrite] = []
        self.audit_events: list[AuditEventWrite] = []

    def create_login_event(self, payload: LoginEventWrite):
        self.login_events.append(payload)
        return payload

    def create_audit_event(self, payload: AuditEventWrite):
        self.audit_events.append(payload)
        return payload


@dataclass
class FakeTenantRead:
    id: str
    code: str
    name: str
    status: str = "active"
    legal_name: str | None = None
    default_locale: str = "de"
    default_currency: str = "EUR"
    timezone: str = "Europe/Berlin"
    version_no: int = 1


@dataclass
class FakeCoreRepository:
    tenant: FakeTenantRead
    branch: object | None = None
    setting: object | None = None

    def onboard_tenant(self, payload, actor_user_id):  # noqa: ANN001
        return type(
            "Onboarded",
            (),
            {
                "tenant": self.tenant,
                "initial_branch": None,
                "initial_mandate": None,
                "initial_settings": [],
            },
        )()

    def list_tenants(self):
        return []

    def get_tenant(self, tenant_id):  # noqa: ANN001
        return self.tenant

    def update_tenant(self, tenant_id, payload, actor_user_id):  # noqa: ANN001
        self.tenant.name = payload.name or self.tenant.name
        self.tenant.version_no += 1
        return self.tenant

    def transition_tenant_status(self, tenant_id, payload, actor_user_id):  # noqa: ANN001
        self.tenant.status = payload.status
        self.tenant.version_no += 1
        return self.tenant

    def list_branches(self, tenant_id):  # noqa: ANN001
        return [self.branch] if self.branch is not None else []

    def create_branch(self, tenant_id, payload, actor_user_id):  # noqa: ANN001
        raise NotImplementedError

    def update_branch(self, tenant_id, branch_id, payload, actor_user_id):  # noqa: ANN001
        if self.branch is None:
            return None
        self.branch.name = payload.name or self.branch.name
        self.branch.version_no += 1
        return self.branch

    def list_mandates(self, tenant_id):  # noqa: ANN001
        return []

    def create_mandate(self, tenant_id, payload, actor_user_id):  # noqa: ANN001
        raise NotImplementedError

    def update_mandate(self, tenant_id, mandate_id, payload, actor_user_id):  # noqa: ANN001
        raise NotImplementedError

    def list_settings(self, tenant_id):  # noqa: ANN001
        return [self.setting] if self.setting is not None else []

    def create_setting(self, tenant_id, payload, actor_user_id):  # noqa: ANN001
        raise NotImplementedError

    def update_setting(self, tenant_id, setting_id, payload, actor_user_id):  # noqa: ANN001
        if self.setting is None:
            return None
        self.setting.value_json = payload.value_json
        self.setting.version_no += 1
        return self.setting


@dataclass
class FakeBranchRead:
    id: str
    tenant_id: str
    code: str
    name: str
    status: str = "active"
    contact_email: str | None = None
    contact_phone: str | None = None
    version_no: int = 1


@dataclass
class FakeTenantSettingRead:
    id: str
    tenant_id: str
    key: str
    status: str = "active"
    value_json: dict[str, object] | None = None
    version_no: int = 1


class TestAuditAndLoginEvents(unittest.TestCase):
    def test_login_attempts_create_success_and_failure_events(self) -> None:
        user = FakeUser(
            id=str(uuid4()),
            tenant_id=str(uuid4()),
            username="nina",
            email="nina@example.invalid",
            full_name="Nina Nord",
            password_hash=hash_password("CorrectHorseBattery"),
        )
        tenant = FakeTenant(id=user.tenant_id, code="nord")
        audit_repo = RecordingAuditRepository()
        service = AuthService(
            FakeAuthRepository(user, tenant),
            auth_secret="test-secret",
            access_ttl_minutes=15,
            refresh_ttl_minutes=60,
            reset_ttl_minutes=30,
            notifier=RecordingNotifier(),
            extension_hooks=FakeHooks(),
            throttle=AuthThrottle(max_attempts=3, lockout_minutes=1),
            audit_service=AuditService(audit_repo),
        )

        with self.assertRaises(Exception):
            service.login(
                LoginRequest(tenant_code="nord", identifier="nina", password="wrong"),
                ip_address="127.0.0.1",
                user_agent="UnitTest",
                request_id="req-failure",
            )

        service.login(
            LoginRequest(tenant_code="nord", identifier="nina", password="CorrectHorseBattery"),
            ip_address="127.0.0.1",
            user_agent="UnitTest",
            request_id="req-success",
        )

        self.assertEqual(len(audit_repo.login_events), 2)
        self.assertEqual(audit_repo.login_events[0].outcome, "failure")
        self.assertEqual(audit_repo.login_events[1].outcome, "success")
        self.assertEqual(audit_repo.login_events[1].request_id, "req-success")

    def test_business_audit_event_is_emitted_for_tenant_update(self) -> None:
        audit_repo = RecordingAuditRepository()
        service = CoreAdminService(
            FakeCoreRepository(FakeTenantRead(id="tenant-1", code="nord", name="Nord")),
            audit_service=AuditService(audit_repo),
        )

        actor = AdminActorContext(
            actor_role="tenant_admin",
            tenant_id="tenant-1",
            actor_user_id="user-1",
            actor_session_id="session-1",
            request_id="req-core",
        )
        payload = type("TenantUpdate", (), {"name": "Nord Updated"})()
        payload.legal_name = None
        payload.default_locale = None
        payload.default_currency = None
        payload.timezone = None
        payload.status = None
        payload.archived_at = None
        payload.model_dump = lambda exclude_unset=True: {"name": "Nord Updated"}

        updated = service.update_tenant("tenant-1", payload, actor)

        self.assertEqual(updated.name, "Nord Updated")
        self.assertEqual(len(audit_repo.audit_events), 1)
        event = audit_repo.audit_events[0]
        self.assertEqual(event.event_type, "core.tenant.updated")
        self.assertEqual(event.entity_id, "tenant-1")
        self.assertEqual(event.request_id, "req-core")
        self.assertEqual(event.tenant_id, "tenant-1")
        self.assertEqual(event.before_json["name"], "Nord")
        self.assertEqual(event.after_json["name"], "Nord Updated")

    def test_audit_service_does_not_strip_meaningful_metadata_but_keeps_no_secrets(self) -> None:
        audit_repo = RecordingAuditRepository()
        audit_service = AuditService(audit_repo)

        audit_service.record_login_attempt(
            LoginEventWrite(
                identifier="nina",
                outcome="failure",
                metadata_json={"failure_bucket": "invalid_credentials", "password": "secret"},
            )
        )

        self.assertEqual(audit_repo.login_events[0].metadata_json, {"failure_bucket": "invalid_credentials"})

    def test_business_audit_event_uses_affected_tenant_for_platform_actor(self) -> None:
        audit_repo = RecordingAuditRepository()
        service = CoreAdminService(
            FakeCoreRepository(FakeTenantRead(id="tenant-9", code="west", name="West")),
            audit_service=AuditService(audit_repo),
        )

        actor = AdminActorContext(
            actor_role="platform_admin",
            actor_user_id="user-9",
            actor_session_id="session-9",
            request_id="req-platform",
        )
        payload = type("TenantUpdate", (), {"name": "West Updated"})()
        payload.legal_name = None
        payload.default_locale = None
        payload.default_currency = None
        payload.timezone = None
        payload.status = None
        payload.archived_at = None
        payload.model_dump = lambda exclude_unset=True: {"name": "West Updated"}

        service.update_tenant("tenant-9", payload, actor)

        self.assertEqual(audit_repo.audit_events[0].tenant_id, "tenant-9")

    def test_branch_audit_keeps_before_snapshot_when_repository_mutates_in_place(self) -> None:
        audit_repo = RecordingAuditRepository()
        branch = FakeBranchRead(id="branch-1", tenant_id="tenant-1", code="hh", name="Hamburg")
        service = CoreAdminService(
            FakeCoreRepository(FakeTenantRead(id="tenant-1", code="nord", name="Nord"), branch=branch),
            audit_service=AuditService(audit_repo),
        )
        actor = AdminActorContext(actor_role="tenant_admin", tenant_id="tenant-1", request_id="req-branch")
        payload = type("BranchUpdate", (), {"name": "Hamburg Mitte"})()

        service.update_branch("tenant-1", "branch-1", payload, actor)

        event = audit_repo.audit_events[0]
        self.assertEqual(event.before_json["name"], "Hamburg")
        self.assertEqual(event.after_json["name"], "Hamburg Mitte")

    def test_business_audit_redacts_sensitive_nested_values(self) -> None:
        audit_repo = RecordingAuditRepository()
        service = CoreAdminService(
            FakeCoreRepository(
                FakeTenantRead(id="tenant-1", code="nord", name="Nord"),
                setting=FakeTenantSettingRead(
                    id="setting-1",
                    tenant_id="tenant-1",
                    key="mail.smtp",
                    value_json={"username": "mailer", "client_secret": "hidden", "nested": {"refresh_token": "x"}},
                ),
            ),
            audit_service=AuditService(audit_repo),
        )
        actor = AdminActorContext(actor_role="tenant_admin", tenant_id="tenant-1")
        payload = type("TenantSettingUpdate", (), {"value_json": {"username": "mailer-2", "api_key": "nope"}})()

        service.update_setting("tenant-1", "setting-1", payload, actor)

        event = audit_repo.audit_events[0]
        self.assertEqual(event.before_json["value_json"], {"username": "mailer", "nested": {}})
        self.assertEqual(event.after_json["value_json"], {"username": "mailer-2"})

    def test_audit_models_are_append_only_oriented(self) -> None:
        for model in (LoginEvent, AuditEvent):
            column_names = {column.name for column in model.__table__.columns}
            self.assertNotIn("updated_at", column_names)
            self.assertNotIn("version_no", column_names)
            self.assertNotIn("archived_at", column_names)
            self.assertIn("created_at", column_names)
        self.assertFalse(hasattr(AuditService, "update_audit_event"))
        self.assertFalse(hasattr(AuditService, "update_login_event"))
