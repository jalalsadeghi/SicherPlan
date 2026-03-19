from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.modules.iam.auth_adapters import AuthExtensionHooks, PasswordResetDelivery, PasswordResetNotifier
from app.modules.iam.auth_router import (
    confirm_password_reset,
    current_session,
    list_sessions,
    login as login_endpoint,
    logout as logout_endpoint,
    refresh as refresh_endpoint,
    request_password_reset as request_password_reset_endpoint,
)
from app.modules.iam.auth_schemas import (
    AuthenticatedRoleScope,
    AuthenticatedUser,
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
    SessionListItem,
    SessionListResponse,
    SessionTokenPair,
)
from app.modules.iam.auth_service import AuthService, AuthThrottle, AuthenticatedSessionContext
from app.modules.iam.security import hash_password, hash_session_token


@dataclass
class FakeUser:
    id: str
    tenant_id: str
    username: str
    email: str
    full_name: str
    password_hash: str
    locale: str = "de"
    timezone: str = "Europe/Berlin"
    is_platform_user: bool = False
    is_password_login_enabled: bool = True
    status: str = "active"
    archived_at: str | None = None
    last_login_at: datetime | None = None
    updated_at: datetime | None = None
    version_no: int = 1


@dataclass
class FakeTenant:
    id: str
    code: str


@dataclass
class FakeSession:
    id: str
    tenant_id: str
    user_account_id: str
    session_token_hash: str
    refresh_token_family: str
    expires_at: datetime
    status: str = "active"
    issued_at: datetime = datetime.now(UTC)
    last_seen_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    device_label: str | None = None
    device_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata_json: dict[str, object] | None = None
    user_account: FakeUser | None = None


@dataclass
class FakeResetToken:
    id: str
    tenant_id: str
    user_account_id: str
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None
    requested_ip: str | None = None
    requested_user_agent: str | None = None
    delivery_channel: str = "email"
    delivery_reference: str | None = None


class RecordingNotifier(PasswordResetNotifier):
    def __init__(self) -> None:
        self.deliveries: list[PasswordResetDelivery] = []

    def send_password_reset(self, delivery: PasswordResetDelivery) -> str | None:
        self.deliveries.append(delivery)
        return f"queued:{delivery.token_id}"


class FakeHooks(AuthExtensionHooks):
    def mfa_required(self, user_id: str) -> bool:
        return False

    def sso_hints(self) -> list[str]:
        return ["oidc-ready"]


class FakeAuthRepository:
    def __init__(self, user: FakeUser, tenant: FakeTenant) -> None:
        self.user = user
        self.tenant = tenant
        self.sessions: dict[str, FakeSession] = {}
        self.reset_tokens: dict[str, FakeResetToken] = {}
        self.role_scopes = [
            AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),
        ]

    def find_user_by_tenant_and_identifier(self, tenant_code: str, identifier: str):
        if tenant_code == self.tenant.code and identifier in {self.user.username, self.user.email}:
            return self.user, self.tenant
        return None

    def get_user_by_id(self, user_account_id: str):
        if user_account_id == self.user.id:
            return self.user
        return None

    def list_role_scopes_for_user(self, user_account_id: str, at_time: datetime | None = None):
        if user_account_id != self.user.id:
            return []
        return [
            type(
                "RoleRecord",
                (),
                {
                    "role_key": role.role_key,
                    "scope_type": role.scope_type,
                    "branch_id": role.branch_id,
                    "mandate_id": role.mandate_id,
                    "customer_id": role.customer_id,
                    "subcontractor_id": role.subcontractor_id,
                },
            )()
            for role in self.role_scopes
        ]

    def list_permission_keys_for_user(self, user_account_id: str, at_time: datetime | None = None):
        if user_account_id != self.user.id:
            return []
        return [
            "core.admin.access",
            "core.admin.tenant.read",
            "core.admin.tenant.write",
            "core.admin.branch.read",
            "core.admin.branch.write",
            "core.admin.mandate.read",
            "core.admin.mandate.write",
            "core.admin.setting.read",
            "core.admin.setting.write",
        ]

    def create_session(self, session_row):
        fake_session = FakeSession(
            id=str(uuid4()),
            tenant_id=session_row.tenant_id,
            user_account_id=session_row.user_account_id,
            session_token_hash=session_row.session_token_hash,
            refresh_token_family=session_row.refresh_token_family,
            expires_at=session_row.expires_at,
            status=session_row.status or "active",
            issued_at=getattr(session_row, "issued_at", datetime.now(UTC)) or datetime.now(UTC),
            last_seen_at=session_row.last_seen_at,
            revoked_at=session_row.revoked_at,
            revoked_reason=session_row.revoked_reason,
            device_label=session_row.device_label,
            device_id=session_row.device_id,
            ip_address=session_row.ip_address,
            user_agent=session_row.user_agent,
            metadata_json=session_row.metadata_json or {},
            user_account=self.user,
        )
        self.sessions[fake_session.id] = fake_session
        return fake_session

    def get_session_by_id(self, session_id: str):
        return self.sessions.get(session_id)

    def get_session_by_token_hash(self, token_hash: str):
        for session_row in self.sessions.values():
            if session_row.session_token_hash == token_hash:
                return session_row
        return None

    def list_sessions_for_user(self, user_account_id: str):
        if user_account_id != self.user.id:
            return []
        return list(self.sessions.values())

    def update_session(self, session_row):
        self.sessions[session_row.id] = session_row
        return session_row

    def revoke_session(self, session_row, *, reason: str, at_time: datetime):
        session_row.status = "revoked"
        session_row.revoked_at = at_time
        session_row.revoked_reason = reason
        self.sessions[session_row.id] = session_row
        return session_row

    def revoke_all_sessions_for_user(self, user_account_id: str, *, except_session_id: str | None, reason: str, at_time: datetime):
        count = 0
        for session_row in self.sessions.values():
            if session_row.user_account_id != user_account_id or session_row.id == except_session_id:
                continue
            session_row.status = "revoked"
            session_row.revoked_at = at_time
            session_row.revoked_reason = reason
            count += 1
        return count

    def touch_user_login(self, user_account, at_time: datetime):
        user_account.last_login_at = at_time
        return user_account

    def update_user_password(self, user_account, password_hash: str, at_time: datetime):
        user_account.password_hash = password_hash
        user_account.updated_at = at_time
        return user_account

    def invalidate_active_reset_tokens(self, user_account_id: str, at_time: datetime):
        count = 0
        for token_row in self.reset_tokens.values():
            if token_row.user_account_id == user_account_id and token_row.used_at is None:
                token_row.used_at = at_time
                count += 1
        return count

    def create_password_reset_token(self, token_row):
        fake_token = FakeResetToken(
            id=str(uuid4()),
            tenant_id=token_row.tenant_id,
            user_account_id=token_row.user_account_id,
            token_hash=token_row.token_hash,
            expires_at=token_row.expires_at,
            used_at=token_row.used_at,
            requested_ip=token_row.requested_ip,
            requested_user_agent=token_row.requested_user_agent,
            delivery_channel=token_row.delivery_channel,
            delivery_reference=token_row.delivery_reference,
        )
        self.reset_tokens[fake_token.id] = fake_token
        return fake_token

    def get_password_reset_token_by_hash(self, token_hash: str):
        for token_row in self.reset_tokens.values():
            if token_row.token_hash == token_hash:
                return token_row
        return None

    def update_password_reset_token(self, token_row):
        self.reset_tokens[token_row.id] = token_row
        return token_row

    def mark_password_reset_token_used(self, token_row, at_time: datetime):
        token_row.used_at = at_time
        self.reset_tokens[token_row.id] = token_row
        return token_row


class TestAuthFlows(unittest.TestCase):
    def setUp(self) -> None:
        self.user = FakeUser(
            id=str(uuid4()),
            tenant_id=str(uuid4()),
            username="nina",
            email="nina@example.invalid",
            full_name="Nina Nord",
            password_hash=hash_password("CorrectHorseBattery"),
        )
        self.tenant = FakeTenant(id=self.user.tenant_id, code="nord")
        self.repository = FakeAuthRepository(self.user, self.tenant)
        self.notifier = RecordingNotifier()
        self.service = AuthService(
            self.repository,
            auth_secret="test-secret",
            access_ttl_minutes=15,
            refresh_ttl_minutes=60,
            reset_ttl_minutes=30,
            notifier=self.notifier,
            extension_hooks=FakeHooks(),
            throttle=AuthThrottle(max_attempts=3, lockout_minutes=1),
        )

    def test_login_refresh_logout_and_session_listing(self) -> None:
        login = self.service.login(
            LoginRequest(
                tenant_code="nord",
                identifier="nina",
                password="CorrectHorseBattery",
                device_label="Browser",
            ),
            ip_address="127.0.0.1",
            user_agent="UnitTest",
        )
        self.assertEqual(login.user.username, "nina")
        self.assertEqual(login.session.sso_hints, ["oidc-ready"])

        context = self.service.authenticate_access_token(login.session.access_token)
        current = self.service.current_session(context)
        self.assertEqual(current.session.id, login.session.session_id)

        sessions = self.service.list_sessions(context)
        self.assertEqual(len(sessions.items), 1)
        self.assertTrue(sessions.items[0].is_current)

        refreshed = self.service.refresh_session(RefreshRequest(refresh_token=login.session.refresh_token))
        self.assertNotEqual(refreshed.session.refresh_token, login.session.refresh_token)

        logout = self.service.logout(self.service.authenticate_access_token(refreshed.session.access_token))
        self.assertEqual(logout.message_key, "messages.iam.auth.logout_success")

        with self.assertRaises(Exception):
            self.service.refresh_session(RefreshRequest(refresh_token=login.session.refresh_token))

    def test_invalid_credentials_and_rate_limit(self) -> None:
        for _ in range(3):
            with self.assertRaises(Exception):
                self.service.login(
                    LoginRequest(tenant_code="nord", identifier="nina", password="wrong"),
                    ip_address="127.0.0.1",
                    user_agent="UnitTest",
                )
        with self.assertRaises(Exception):
            self.service.login(
                LoginRequest(tenant_code="nord", identifier="nina", password="wrong"),
                ip_address="127.0.0.1",
                user_agent="UnitTest",
            )

    def test_password_reset_request_and_confirm_invalidates_old_sessions(self) -> None:
        login = self.service.login(
            LoginRequest(tenant_code="nord", identifier="nina@example.invalid", password="CorrectHorseBattery"),
            ip_address="127.0.0.1",
            user_agent="UnitTest",
        )
        request_response = self.service.request_password_reset(
            PasswordResetRequest(tenant_code="nord", identifier="nina"),
            ip_address="127.0.0.1",
            user_agent="UnitTest",
        )
        self.assertEqual(request_response.message_key, "messages.iam.auth.password_reset_requested")
        self.assertEqual(len(self.notifier.deliveries), 1)

        raw_token = self.notifier.deliveries[0].reset_token
        confirm = self.service.confirm_password_reset(
            PasswordResetConfirmRequest(token=raw_token, new_password="NewCorrectHorseBattery"),
        )
        self.assertEqual(confirm.message_key, "messages.iam.auth.password_reset_confirmed")
        session_row = self.repository.sessions[login.session.session_id]
        self.assertEqual(session_row.status, "revoked")

        with self.assertRaises(Exception):
            self.service.confirm_password_reset(
                PasswordResetConfirmRequest(token=raw_token, new_password="AnotherPassword123"),
            )


class _FakeRequest:
    def __init__(self, user_agent: str = "UnitTest", ip_address: str = "127.0.0.1") -> None:
        self.headers = {"user-agent": user_agent}
        self.client = type("Client", (), {"host": ip_address})()


class TestAuthRouterFunctions(unittest.TestCase):
    def setUp(self) -> None:
        user = FakeUser(
            id=str(uuid4()),
            tenant_id=str(uuid4()),
            username="nina",
            email="nina@example.invalid",
            full_name="Nina Nord",
            password_hash=hash_password("CorrectHorseBattery"),
        )
        tenant = FakeTenant(id=user.tenant_id, code="nord")
        repository = FakeAuthRepository(user, tenant)
        self.notifier = RecordingNotifier()
        self.service = AuthService(
            repository,
            auth_secret="test-secret",
            access_ttl_minutes=15,
            refresh_ttl_minutes=60,
            reset_ttl_minutes=30,
            notifier=self.notifier,
            extension_hooks=FakeHooks(),
            throttle=AuthThrottle(max_attempts=5, lockout_minutes=1),
        )

    def test_login_current_session_refresh_and_list_routes(self) -> None:
        login_response = login_endpoint(
            LoginRequest(tenant_code="nord", identifier="nina", password="CorrectHorseBattery"),
            _FakeRequest(),
            self.service,
        )
        self.assertEqual(login_response.user.username, "nina")

        context = self.service.authenticate_access_token(login_response.session.access_token)
        current = current_session(context, self.service)
        self.assertEqual(current.user.username, "nina")

        sessions = list_sessions(context, self.service)
        self.assertEqual(len(sessions.items), 1)

        refreshed = refresh_endpoint(
            RefreshRequest(refresh_token=login_response.session.refresh_token),
            self.service,
        )
        self.assertNotEqual(refreshed.session.refresh_token, login_response.session.refresh_token)

    def test_password_reset_confirm_and_logout_routes(self) -> None:
        login_response = login_endpoint(
            LoginRequest(tenant_code="nord", identifier="nina", password="CorrectHorseBattery"),
            _FakeRequest(),
            self.service,
        )
        context = self.service.authenticate_access_token(login_response.session.access_token)

        reset_request = request_password_reset_endpoint(
            PasswordResetRequest(tenant_code="nord", identifier="nina"),
            _FakeRequest(),
            self.service,
        )
        self.assertEqual(reset_request.message_key, "messages.iam.auth.password_reset_requested")
        self.assertEqual(len(self.notifier.deliveries), 1)

        reset_confirm = confirm_password_reset(
            PasswordResetConfirmRequest(
                token=self.notifier.deliveries[0].reset_token,
                new_password="NewCorrectHorseBattery",
            ),
            self.service,
        )
        self.assertEqual(reset_confirm.message_key, "messages.iam.auth.password_reset_confirmed")

        logout_response = logout_endpoint(context, self.service)
        self.assertEqual(logout_response.message_key, "messages.iam.auth.logout_success")


if __name__ == "__main__":
    unittest.main()
