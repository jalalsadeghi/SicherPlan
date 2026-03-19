"""Auth service for login, refresh, logout, and password reset flows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.audit_service import AuditService, AuditActor
from app.modules.iam.audit_schemas import LoginEventWrite
from app.modules.iam.auth_adapters import AuthExtensionHooks, PasswordResetDelivery, PasswordResetNotifier
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
from app.modules.iam.models import PasswordResetToken, UserAccount, UserSession
from app.modules.iam.security import (
    hash_password,
    hash_session_token,
    verify_password,
    verify_signed_access_token,
    sign_access_token,
)


class AuthRepository(Protocol):
    def find_user_by_tenant_and_identifier(self, tenant_code: str, identifier: str): ...  # noqa: ANN001
    def get_user_by_id(self, user_account_id: str): ...  # noqa: ANN001
    def list_role_scopes_for_user(self, user_account_id: str, at_time: datetime | None = None): ...  # noqa: ANN001
    def list_permission_keys_for_user(self, user_account_id: str, at_time: datetime | None = None): ...  # noqa: ANN001
    def create_session(self, session_row: UserSession) -> UserSession: ...
    def get_session_by_id(self, session_id: str) -> UserSession | None: ...
    def get_session_by_token_hash(self, token_hash: str) -> UserSession | None: ...
    def list_sessions_for_user(self, user_account_id: str) -> list[UserSession]: ...
    def update_session(self, session_row: UserSession) -> UserSession: ...
    def revoke_session(self, session_row: UserSession, *, reason: str, at_time: datetime) -> UserSession: ...
    def revoke_all_sessions_for_user(
        self,
        user_account_id: str,
        *,
        except_session_id: str | None,
        reason: str,
        at_time: datetime,
    ) -> int: ...
    def touch_user_login(self, user_account: UserAccount, at_time: datetime) -> UserAccount: ...
    def update_user_password(self, user_account: UserAccount, password_hash: str, at_time: datetime) -> UserAccount: ...
    def invalidate_active_reset_tokens(self, user_account_id: str, at_time: datetime) -> int: ...
    def create_password_reset_token(self, token_row: PasswordResetToken) -> PasswordResetToken: ...
    def update_password_reset_token(self, token_row: PasswordResetToken) -> PasswordResetToken: ...
    def get_password_reset_token_by_hash(self, token_hash: str) -> PasswordResetToken | None: ...
    def mark_password_reset_token_used(self, token_row: PasswordResetToken, at_time: datetime) -> PasswordResetToken: ...


@dataclass(slots=True)
class AccessTokenPayload:
    session_id: str
    user_account_id: str
    tenant_id: str
    exp: int


@dataclass(slots=True)
class AuthenticatedSessionContext:
    session: UserSession
    user: UserAccount
    roles: list[AuthenticatedRoleScope]
    permission_keys: frozenset[str]
    request_id: str | None = None


class AuthThrottle:
    def __init__(self, max_attempts: int, lockout_minutes: int) -> None:
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        self._entries: dict[str, tuple[int, datetime | None]] = {}

    def assert_allowed(self, key: str, now: datetime) -> None:
        attempts, locked_until = self._entries.get(key, (0, None))
        if locked_until is not None and locked_until > now:
            raise ApiException(
                429,
                "iam.auth.rate_limited",
                "errors.iam.auth.rate_limited",
            )
        if locked_until is not None and locked_until <= now:
            self._entries.pop(key, None)

    def register_failure(self, key: str, now: datetime) -> None:
        attempts, _ = self._entries.get(key, (0, None))
        attempts += 1
        if attempts >= self.max_attempts:
            self._entries[key] = (attempts, now + timedelta(minutes=self.lockout_minutes))
            return
        self._entries[key] = (attempts, None)

    def register_success(self, key: str) -> None:
        self._entries.pop(key, None)


class AuthService:
    def __init__(
        self,
        repository: AuthRepository,
        *,
        auth_secret: str,
        access_ttl_minutes: int,
        refresh_ttl_minutes: int,
        reset_ttl_minutes: int,
        notifier: PasswordResetNotifier,
        extension_hooks: AuthExtensionHooks,
        throttle: AuthThrottle,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.auth_secret = auth_secret
        self.access_ttl_minutes = access_ttl_minutes
        self.refresh_ttl_minutes = refresh_ttl_minutes
        self.reset_ttl_minutes = reset_ttl_minutes
        self.notifier = notifier
        self.extension_hooks = extension_hooks
        self.throttle = throttle
        self.audit_service = audit_service

    def login(
        self,
        payload: LoginRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
        request_id: str | None = None,
    ) -> LoginResponse:
        now = datetime.now(UTC)
        throttle_key = f"{payload.tenant_code}:{payload.identifier}".lower()
        self.throttle.assert_allowed(throttle_key, now)

        row = self.repository.find_user_by_tenant_and_identifier(payload.tenant_code, payload.identifier)
        if row is None:
            self.throttle.register_failure(throttle_key, now)
            self._record_login_event(
                LoginEventWrite(
                    tenant_code=payload.tenant_code,
                    identifier=payload.identifier,
                    outcome="failure",
                    failure_reason="invalid_credentials",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                )
            )
            raise self._invalid_credentials()

        user_account, _tenant = row
        if (
            user_account.status != "active"
            or user_account.archived_at is not None
            or not user_account.is_password_login_enabled
            or not user_account.password_hash
            or not verify_password(payload.password, user_account.password_hash)
        ):
            self.throttle.register_failure(throttle_key, now)
            self._record_login_event(
                LoginEventWrite(
                    tenant_id=user_account.tenant_id,
                    user_account_id=user_account.id,
                    tenant_code=payload.tenant_code,
                    identifier=payload.identifier,
                    outcome="failure",
                    failure_reason="invalid_credentials",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                )
            )
            raise self._invalid_credentials()

        self.throttle.register_success(throttle_key)
        self.repository.touch_user_login(user_account, now)

        refresh_token = token_urlsafe(48)
        refresh_token_hash = hash_session_token(refresh_token)
        session_row = self.repository.create_session(
            UserSession(
                tenant_id=user_account.tenant_id,
                user_account_id=user_account.id,
                session_token_hash=refresh_token_hash,
                refresh_token_family=token_urlsafe(18),
                expires_at=now + timedelta(minutes=self.refresh_ttl_minutes),
                last_seen_at=now,
                device_label=payload.device_label,
                device_id=payload.device_id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata_json={"mfa_required": self.extension_hooks.mfa_required(user_account.id)},
            )
        )
        roles = self._build_roles(user_account.id, now)
        self._record_login_event(
            LoginEventWrite(
                tenant_id=user_account.tenant_id,
                user_account_id=user_account.id,
                session_id=session_row.id,
                tenant_code=payload.tenant_code,
                identifier=payload.identifier,
                outcome="success",
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                metadata_json={"role_keys": [role.role_key for role in roles]},
            )
        )
        return LoginResponse(
            user=self._build_user(user_account, roles),
            session=self._build_session_pair(
                session_row=session_row,
                refresh_token=refresh_token,
                roles=roles,
            ),
        )

    def refresh_session(self, payload: RefreshRequest) -> RefreshResponse:
        now = datetime.now(UTC)
        refresh_hash = hash_session_token(payload.refresh_token)
        session_row = self.repository.get_session_by_token_hash(refresh_hash)
        if (
            session_row is None
            or session_row.user_account is None
            or session_row.status != "active"
            or session_row.revoked_at is not None
            or session_row.expires_at <= now
        ):
            raise ApiException(
                401,
                "iam.auth.invalid_refresh_token",
                "errors.iam.auth.invalid_refresh_token",
            )

        new_refresh_token = token_urlsafe(48)
        session_row.session_token_hash = hash_session_token(new_refresh_token)
        session_row.expires_at = now + timedelta(minutes=self.refresh_ttl_minutes)
        session_row.last_seen_at = now
        session_row.updated_at = now
        updated = self.repository.update_session(session_row)
        roles = self._build_roles(updated.user_account_id, now)
        return RefreshResponse(
            session=self._build_session_pair(
                session_row=updated,
                refresh_token=new_refresh_token,
                roles=roles,
            )
        )

    def authenticate_access_token(self, token: str) -> AuthenticatedSessionContext:
        payload = verify_signed_access_token(token, self.auth_secret)
        session_row = self.repository.get_session_by_id(payload["sid"])
        now = datetime.now(UTC)
        if (
            session_row is None
            or session_row.user_account is None
            or session_row.user_account.id != payload["sub"]
            or session_row.status != "active"
            or session_row.revoked_at is not None
            or session_row.expires_at <= now
            or session_row.user_account.status != "active"
            or session_row.user_account.archived_at is not None
        ):
            raise ApiException(
                401,
                "iam.auth.invalid_access_token",
                "errors.iam.auth.invalid_access_token",
            )

        session_row.last_seen_at = now
        self.repository.update_session(session_row)
        roles = self._build_roles(session_row.user_account_id, now)
        permissions = frozenset(self.repository.list_permission_keys_for_user(session_row.user_account_id, now))
        return AuthenticatedSessionContext(
            session=session_row,
            user=session_row.user_account,
            roles=roles,
            permission_keys=permissions,
        )

    def with_request_context(
        self,
        context: AuthenticatedSessionContext,
        *,
        request_id: str | None,
    ) -> AuthenticatedSessionContext:
        context.request_id = request_id
        return context

    def current_session(self, context: AuthenticatedSessionContext) -> CurrentSessionResponse:
        return CurrentSessionResponse(
            user=self._build_user(context.user, context.roles),
            session=self._build_session_list_item(context.session, is_current=True),
        )

    def list_sessions(self, context: AuthenticatedSessionContext) -> SessionListResponse:
        sessions = self.repository.list_sessions_for_user(context.user.id)
        return SessionListResponse(
            items=[
                self._build_session_list_item(session_row, is_current=session_row.id == context.session.id)
                for session_row in sessions
            ]
        )

    def logout(self, context: AuthenticatedSessionContext) -> LogoutResponse:
        self.repository.revoke_session(
            context.session,
            reason="logout",
            at_time=datetime.now(UTC),
        )
        self._record_business_event(
            actor=AuditActor(
                tenant_id=context.user.tenant_id,
                user_id=context.user.id,
                session_id=context.session.id,
                request_id=context.request_id,
            ),
            event_type="iam.auth.logout",
            entity_type="iam.user_session",
            entity_id=context.session.id,
            after_json={"status": "revoked"},
            metadata_json={"reason": "logout"},
        )
        return LogoutResponse(message_key="messages.iam.auth.logout_success")

    def request_password_reset(
        self,
        payload: PasswordResetRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> PasswordResetRequestResponse:
        now = datetime.now(UTC)
        row = self.repository.find_user_by_tenant_and_identifier(payload.tenant_code, payload.identifier)
        if row is None:
            return PasswordResetRequestResponse(message_key="messages.iam.auth.password_reset_requested")

        user_account, _tenant = row
        if (
            user_account.status != "active"
            or user_account.archived_at is not None
            or not user_account.is_password_login_enabled
            or not user_account.email
        ):
            return PasswordResetRequestResponse(message_key="messages.iam.auth.password_reset_requested")

        self.repository.invalidate_active_reset_tokens(user_account.id, now)
        raw_token = token_urlsafe(48)
        token_row = self.repository.create_password_reset_token(
            PasswordResetToken(
                tenant_id=user_account.tenant_id,
                user_account_id=user_account.id,
                token_hash=hash_session_token(raw_token),
                expires_at=now + timedelta(minutes=self.reset_ttl_minutes),
                requested_ip=ip_address,
                requested_user_agent=user_agent,
                delivery_channel="email",
            )
        )
        delivery_reference = self.notifier.send_password_reset(
            PasswordResetDelivery(
                token_id=token_row.id,
                tenant_id=user_account.tenant_id,
                user_account_id=user_account.id,
                email=user_account.email,
                locale=user_account.locale,
                reset_token=raw_token,
            )
        )
        if delivery_reference is not None:
            token_row.delivery_reference = delivery_reference
            self.repository.update_password_reset_token(token_row)
        return PasswordResetRequestResponse(message_key="messages.iam.auth.password_reset_requested")

    def confirm_password_reset(self, payload: PasswordResetConfirmRequest) -> PasswordResetConfirmResponse:
        now = datetime.now(UTC)
        token_row = self.repository.get_password_reset_token_by_hash(hash_session_token(payload.token))
        if token_row is None or token_row.used_at is not None or token_row.expires_at <= now:
            raise ApiException(
                400,
                "iam.auth.invalid_reset_token",
                "errors.iam.auth.invalid_reset_token",
            )

        user_account = self.repository.get_user_by_id(token_row.user_account_id)
        if user_account is None or user_account.archived_at is not None:
            raise ApiException(
                400,
                "iam.auth.invalid_reset_token",
                "errors.iam.auth.invalid_reset_token",
            )

        self.repository.update_user_password(user_account, hash_password(payload.new_password), now)
        self.repository.mark_password_reset_token_used(token_row, now)
        self.repository.revoke_all_sessions_for_user(
            user_account.id,
            except_session_id=None,
            reason="password_reset",
            at_time=now,
        )
        self._record_business_event(
            actor=AuditActor(
                tenant_id=user_account.tenant_id,
                user_id=user_account.id,
                session_id=None,
                request_id=None,
            ),
            event_type="iam.auth.password_reset_confirmed",
            entity_type="iam.user_account",
            entity_id=user_account.id,
            metadata_json={"token_id": token_row.id},
        )
        return PasswordResetConfirmResponse(message_key="messages.iam.auth.password_reset_confirmed")

    def _build_roles(self, user_account_id: str, at_time: datetime) -> list[AuthenticatedRoleScope]:
        return [
            AuthenticatedRoleScope(
                role_key=row.role_key,
                scope_type=row.scope_type,
                branch_id=row.branch_id,
                mandate_id=row.mandate_id,
                customer_id=row.customer_id,
                subcontractor_id=row.subcontractor_id,
            )
            for row in self.repository.list_role_scopes_for_user(user_account_id, at_time)
        ]

    def _build_user(self, user_account: UserAccount, roles: list[AuthenticatedRoleScope]) -> AuthenticatedUser:
        return AuthenticatedUser(
            id=user_account.id,
            tenant_id=user_account.tenant_id,
            username=user_account.username,
            email=user_account.email,
            full_name=user_account.full_name,
            locale=user_account.locale,
            timezone=user_account.timezone,
            is_platform_user=user_account.is_platform_user,
            roles=roles,
        )

    def _build_session_pair(
        self,
        *,
        session_row: UserSession,
        refresh_token: str,
        roles: list[AuthenticatedRoleScope],
    ) -> SessionTokenPair:
        access_expires_at = datetime.now(UTC) + timedelta(minutes=self.access_ttl_minutes)
        access_token = sign_access_token(
            {
                "sid": session_row.id,
                "sub": session_row.user_account_id,
                "tid": session_row.tenant_id,
                "roles": [role.role_key for role in roles],
                "exp": int(access_expires_at.timestamp()),
            },
            self.auth_secret,
        )
        return SessionTokenPair(
            access_token=access_token,
            access_token_expires_at=access_expires_at,
            refresh_token=refresh_token,
            refresh_token_expires_at=session_row.expires_at,
            session_id=session_row.id,
            mfa_required=self.extension_hooks.mfa_required(session_row.user_account_id),
            sso_hints=self.extension_hooks.sso_hints(),
        )

    @staticmethod
    def _build_session_list_item(session_row: UserSession, *, is_current: bool) -> SessionListItem:
        return SessionListItem(
            id=session_row.id,
            tenant_id=session_row.tenant_id,
            refresh_token_family=session_row.refresh_token_family,
            status=session_row.status,
            issued_at=session_row.issued_at,
            expires_at=session_row.expires_at,
            last_seen_at=session_row.last_seen_at,
            revoked_at=session_row.revoked_at,
            device_label=session_row.device_label,
            device_id=session_row.device_id,
            ip_address=session_row.ip_address,
            user_agent=session_row.user_agent,
            is_current=is_current,
        )

    @staticmethod
    def _invalid_credentials() -> ApiException:
        return ApiException(
            401,
            "iam.auth.invalid_credentials",
            "errors.iam.auth.invalid_credentials",
        )

    def _record_login_event(self, payload: LoginEventWrite) -> None:
        if self.audit_service is not None:
            self.audit_service.record_login_attempt(payload)

    def _record_business_event(
        self,
        *,
        actor: AuditActor,
        event_type: str,
        entity_type: str,
        entity_id: str,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is not None:
            self.audit_service.record_business_event(
                actor=actor,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                before_json=before_json,
                after_json=after_json,
                metadata_json=metadata_json,
            )
