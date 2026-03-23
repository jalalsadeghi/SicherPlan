"""Platform-scoped IAM admin flows for tenant admin account management."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.schemas import (
    TenantAdminPasswordResetRequest,
    TenantAdminPasswordResetResponse,
    TenantAdminUserCreate,
    TenantAdminUserListItem,
    TenantAdminUserStatusUpdate,
)
from app.modules.iam.security import hash_password


@dataclass(frozen=True, slots=True)
class IamAdminActorContext:
    actor_role: str
    tenant_id: str | None = None
    actor_user_id: str | None = None
    actor_session_id: str | None = None
    request_id: str | None = None

    @property
    def is_platform_admin(self) -> bool:
        return self.actor_role == "platform_admin"


class IamAdminRepository(Protocol):
    def tenant_exists(self, tenant_id: str) -> bool: ...
    def list_tenant_admin_users(self, tenant_id: str) -> list[TenantAdminUserListItem]: ...
    def create_tenant_admin_user(self, payload: TenantAdminUserCreate, password_hash: str, actor_user_id: str | None) -> TenantAdminUserListItem: ...
    def get_tenant_admin_user(self, tenant_id: str, user_id: str) -> TenantAdminUserListItem | None: ...
    def update_tenant_admin_user_status(
        self,
        tenant_id: str,
        user_id: str,
        status: str,
        actor_user_id: str | None,
    ) -> TenantAdminUserListItem | None: ...
    def reset_tenant_admin_password(
        self,
        tenant_id: str,
        user_id: str,
        password_hash: str,
        actor_user_id: str | None,
        at_time: datetime,
    ) -> TenantAdminUserListItem | None: ...


class IamAdminService:
    def __init__(self, repository: IamAdminRepository, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_tenant_admin_users(self, tenant_id: str, actor: IamAdminActorContext) -> list[TenantAdminUserListItem]:
        self._require_platform_admin(actor)
        self._ensure_tenant_exists(tenant_id)
        return self.repository.list_tenant_admin_users(tenant_id)

    def create_tenant_admin_user(
        self,
        payload: TenantAdminUserCreate,
        actor: IamAdminActorContext,
    ) -> TenantAdminPasswordResetResponse:
        self._require_platform_admin(actor)
        self._ensure_tenant_exists(payload.tenant_id)
        normalized = self._normalize_create_payload(payload)
        temporary_password = normalized.temporary_password or self._generate_temporary_password()
        created = self.repository.create_tenant_admin_user(
            TenantAdminUserCreate(**normalized.model_dump(exclude={"temporary_password"}), temporary_password=None),
            hash_password(temporary_password),
            actor.actor_user_id,
        )
        self._record_event(
            actor,
            event_type="iam.tenant_admin_user.created",
            entity_id=created.id,
            tenant_id=created.tenant_id,
            after_json=self._user_snapshot(created),
        )
        return TenantAdminPasswordResetResponse(
            message_key="messages.iam.tenant_admin_user.created",
            temporary_password=temporary_password,
        )

    def update_tenant_admin_user_status(
        self,
        tenant_id: str,
        user_id: str,
        payload: TenantAdminUserStatusUpdate,
        actor: IamAdminActorContext,
    ) -> TenantAdminUserListItem:
        self._require_platform_admin(actor)
        self._ensure_tenant_exists(tenant_id)
        before = self.repository.get_tenant_admin_user(tenant_id, user_id)
        if before is None:
            raise self._not_found("tenant_admin_user")
        updated = self.repository.update_tenant_admin_user_status(tenant_id, user_id, payload.status, actor.actor_user_id)
        if updated is None:
            raise self._not_found("tenant_admin_user")
        self._record_event(
            actor,
            event_type="iam.tenant_admin_user.lifecycle_changed",
            entity_id=updated.id,
            tenant_id=updated.tenant_id,
            before_json=self._user_snapshot(before),
            after_json=self._user_snapshot(updated),
            metadata_json={"status": payload.status},
        )
        return updated

    def reset_tenant_admin_password(
        self,
        tenant_id: str,
        user_id: str,
        payload: TenantAdminPasswordResetRequest,
        actor: IamAdminActorContext,
    ) -> TenantAdminPasswordResetResponse:
        self._require_platform_admin(actor)
        self._ensure_tenant_exists(tenant_id)
        before = self.repository.get_tenant_admin_user(tenant_id, user_id)
        if before is None:
            raise self._not_found("tenant_admin_user")
        temporary_password = self._normalize_optional(payload.temporary_password) or self._generate_temporary_password()
        updated = self.repository.reset_tenant_admin_password(
            tenant_id,
            user_id,
            hash_password(temporary_password),
            actor.actor_user_id,
            datetime.now(UTC),
        )
        if updated is None:
            raise self._not_found("tenant_admin_user")
        self._record_event(
            actor,
            event_type="iam.tenant_admin_user.password_reset",
            entity_id=updated.id,
            tenant_id=updated.tenant_id,
            before_json=self._user_snapshot(before),
            after_json=self._user_snapshot(updated),
        )
        return TenantAdminPasswordResetResponse(
            message_key="messages.iam.tenant_admin_user.password_reset",
            temporary_password=temporary_password,
        )

    def _ensure_tenant_exists(self, tenant_id: str) -> None:
        if not self.repository.tenant_exists(tenant_id):
            raise self._not_found("tenant")

    @staticmethod
    def _normalize_create_payload(payload: TenantAdminUserCreate) -> TenantAdminUserCreate:
        username = payload.username.strip()
        email = payload.email.strip().lower()
        full_name = payload.full_name.strip()
        locale = payload.locale.strip().lower() or "de"
        timezone = payload.timezone.strip() or "Europe/Berlin"
        status = payload.status.strip().lower() or "active"
        if not username:
            raise ApiException(400, "iam.validation.username_required", "errors.iam.user.username_required")
        if not full_name:
            raise ApiException(400, "iam.validation.full_name_required", "errors.iam.user.full_name_required")
        if "@" not in email:
            raise ApiException(400, "iam.validation.invalid_email", "errors.iam.user.invalid_email")
        if status not in {"active", "inactive"}:
            raise ApiException(400, "iam.validation.invalid_status", "errors.iam.user.invalid_status")
        return TenantAdminUserCreate(
            tenant_id=payload.tenant_id,
            username=username,
            email=email,
            full_name=full_name,
            locale=locale,
            timezone=timezone,
            status=status,
            temporary_password=IamAdminService._normalize_optional(payload.temporary_password),
        )

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        normalized = (value or "").strip()
        return normalized or None

    @staticmethod
    def _generate_temporary_password() -> str:
        return f"SP-{secrets.token_urlsafe(9)}!A1"

    @staticmethod
    def _require_platform_admin(actor: IamAdminActorContext) -> None:
        if not actor.is_platform_admin:
            raise ApiException(403, "iam.authorization.platform_admin_required", "errors.iam.authorization.scope_denied")

    @staticmethod
    def _not_found(entity: str) -> ApiException:
        return ApiException(404, f"iam.{entity}.not_found", f"errors.iam.{entity}.not_found")

    def _record_event(
        self,
        actor: IamAdminActorContext,
        *,
        event_type: str,
        entity_id: str,
        tenant_id: str,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=actor.tenant_id,
                user_id=actor.actor_user_id,
                session_id=actor.actor_session_id,
                request_id=actor.request_id,
            ),
            event_type=event_type,
            entity_type="iam.user_account",
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=after_json,
            metadata_json=metadata_json,
        )

    @staticmethod
    def _user_snapshot(user: TenantAdminUserListItem | None) -> dict[str, object] | None:
        if user is None:
            return None
        return {
            "id": user.id,
            "tenant_id": user.tenant_id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "locale": user.locale,
            "timezone": user.timezone,
            "status": user.status,
            "role_assignment_status": user.role_assignment_status,
            "role_key": user.role_key,
            "scope_type": user.scope_type,
        }
