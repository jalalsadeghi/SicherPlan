"""Tenant-scoped customer portal access management service."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.customers.models import Customer, CustomerContact
from app.modules.customers.policy import enforce_customer_module_access
from app.modules.customers.schemas import (
    CustomerPortalAccessCreate,
    CustomerPortalAccessListItemRead,
    CustomerPortalAccessPasswordResetRequest,
    CustomerPortalAccessPasswordResetResponse,
    CustomerPortalAccessStatusUpdate,
    CustomerPortalAccessUnlinkResponse,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.iam.security import hash_password


@dataclass(frozen=True, slots=True)
class CustomerPortalAccessAuditContext:
    actor_user_id: str | None
    actor_session_id: str | None
    tenant_id: str
    request_id: str | None


class CustomerPortalAccessRepository(Protocol):
    def tenant_exists(self, tenant_id: str) -> bool: ...
    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None: ...
    def get_contact(self, tenant_id: str, contact_id: str) -> CustomerContact | None: ...
    def list_portal_access(self, tenant_id: str, customer_id: str) -> list[CustomerPortalAccessListItemRead]: ...
    def get_portal_access_user(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: str,
    ) -> CustomerPortalAccessListItemRead | None: ...
    def create_portal_access_user(
        self,
        payload: CustomerPortalAccessCreate,
        password_hash: str,
        actor_user_id: str | None,
    ) -> CustomerPortalAccessListItemRead: ...
    def update_portal_access_status(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: str,
        status: str,
        actor_user_id: str | None,
    ) -> CustomerPortalAccessListItemRead | None: ...
    def reset_portal_access_password(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: str,
        password_hash: str,
        actor_user_id: str | None,
        at_time: datetime,
    ) -> CustomerPortalAccessListItemRead | None: ...
    def unlink_portal_access(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: str,
        actor_user_id: str | None,
        at_time: datetime | None = None,
    ) -> bool: ...


class CustomerPortalAccessService:
    def __init__(
        self,
        repository: CustomerPortalAccessRepository,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_portal_access(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerPortalAccessListItemRead]:
        self._require_customer(tenant_id, customer_id, actor)
        return self.repository.list_portal_access(tenant_id, customer_id)

    def create_portal_access(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerPortalAccessCreate,
        actor: RequestAuthorizationContext,
    ) -> CustomerPortalAccessPasswordResetResponse:
        customer = self._require_customer(tenant_id, customer_id, actor)
        self._validate_path(tenant_id, customer_id, payload)
        contact = self._require_contact(tenant_id, payload.contact_id)
        self._validate_contact_for_customer(contact, customer_id)
        self._ensure_active_customer(customer)
        self._ensure_active_contact(contact)
        if contact.user_id:
            raise ApiException(
                409,
                "customers.portal_access.contact_already_linked",
                "errors.customers.portal_access.contact_already_linked",
            )
        normalized = self._normalize_create_payload(payload)
        temporary_password = normalized.temporary_password or self._generate_temporary_password()
        created = self.repository.create_portal_access_user(
            CustomerPortalAccessCreate(**normalized.model_dump(exclude={"temporary_password"}), temporary_password=None),
            hash_password(temporary_password),
            actor.user_id,
        )
        self._record_event(
            actor,
            event_type="customers.portal_access.created",
            entity_id=created.user_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            contact_id=created.contact_id,
            after_json=self._access_snapshot(created),
        )
        return CustomerPortalAccessPasswordResetResponse(
            message_key="messages.customers.portal_access.created",
            temporary_password=temporary_password,
        )

    def update_portal_access_status(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: str,
        payload: CustomerPortalAccessStatusUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerPortalAccessListItemRead:
        self._require_customer(tenant_id, customer_id, actor)
        before = self.repository.get_portal_access_user(tenant_id, customer_id, user_id)
        if before is None:
            raise self._not_found("portal_access")
        updated = self.repository.update_portal_access_status(
            tenant_id,
            customer_id,
            user_id,
            payload.status,
            actor.user_id,
        )
        if updated is None:
            raise self._not_found("portal_access")
        self._record_event(
            actor,
            event_type="customers.portal_access.lifecycle_changed",
            entity_id=updated.user_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            contact_id=updated.contact_id,
            before_json=self._access_snapshot(before),
            after_json=self._access_snapshot(updated),
            metadata_json={"status": payload.status},
        )
        return updated

    def reset_portal_access_password(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: str,
        payload: CustomerPortalAccessPasswordResetRequest,
        actor: RequestAuthorizationContext,
    ) -> CustomerPortalAccessPasswordResetResponse:
        self._require_customer(tenant_id, customer_id, actor)
        before = self.repository.get_portal_access_user(tenant_id, customer_id, user_id)
        if before is None:
            raise self._not_found("portal_access")
        temporary_password = self._normalize_optional(payload.temporary_password) or self._generate_temporary_password()
        updated = self.repository.reset_portal_access_password(
            tenant_id,
            customer_id,
            user_id,
            hash_password(temporary_password),
            actor.user_id,
            datetime.now(UTC),
        )
        if updated is None:
            raise self._not_found("portal_access")
        self._record_event(
            actor,
            event_type="customers.portal_access.password_reset",
            entity_id=updated.user_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            contact_id=updated.contact_id,
            before_json=self._access_snapshot(before),
            after_json=self._access_snapshot(updated),
        )
        return CustomerPortalAccessPasswordResetResponse(
            message_key="messages.customers.portal_access.password_reset",
            temporary_password=temporary_password,
        )

    def unlink_portal_access(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: str,
        actor: RequestAuthorizationContext,
    ) -> CustomerPortalAccessUnlinkResponse:
        self._require_customer(tenant_id, customer_id, actor)
        before = self.repository.get_portal_access_user(tenant_id, customer_id, user_id)
        if before is None:
            raise self._not_found("portal_access")
        changed = self.repository.unlink_portal_access(
            tenant_id,
            customer_id,
            user_id,
            actor.user_id,
            datetime.now(UTC),
        )
        if not changed:
            raise self._not_found("portal_access")
        self._record_event(
            actor,
            event_type="customers.portal_access.unlinked",
            entity_id=before.user_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            contact_id=before.contact_id,
            before_json=self._access_snapshot(before),
            after_json={"contact_id": before.contact_id, "linked": False},
        )
        return CustomerPortalAccessUnlinkResponse(
            message_key="messages.customers.portal_access.unlinked",
        )

    def _require_customer(self, tenant_id: str, customer_id: str, actor: RequestAuthorizationContext) -> Customer:
        self._ensure_tenant_scope(actor, tenant_id)
        if not self.repository.tenant_exists(tenant_id):
            raise self._not_found("tenant")
        customer = self.repository.get_customer(tenant_id, customer_id)
        if customer is None:
            raise self._not_found("customer")
        return customer

    def _require_contact(self, tenant_id: str, contact_id: str) -> CustomerContact:
        contact = self.repository.get_contact(tenant_id, contact_id)
        if contact is None:
            raise self._not_found("contact")
        return contact

    @staticmethod
    def _validate_path(tenant_id: str, customer_id: str, payload: CustomerPortalAccessCreate) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "customers.portal_access.tenant_mismatch",
                "errors.customers.contact.tenant_mismatch",
                {"tenant_id": tenant_id},
            )
        if payload.customer_id != customer_id:
            raise ApiException(
                400,
                "customers.portal_access.customer_mismatch",
                "errors.customers.contact.customer_mismatch",
                {"customer_id": customer_id},
            )

    @staticmethod
    def _validate_contact_for_customer(contact: CustomerContact, customer_id: str) -> None:
        if contact.customer_id != customer_id:
            raise ApiException(
                400,
                "customers.portal_access.contact_customer_mismatch",
                "errors.customers.portal_access.contact_customer_mismatch",
                {"customer_id": customer_id, "contact_id": contact.id},
            )

    @staticmethod
    def _ensure_active_customer(customer: Customer) -> None:
        if customer.status != "active" or customer.archived_at is not None:
            raise ApiException(
                409,
                "customers.portal_access.customer_inactive",
                "errors.customers.portal.customer_inactive",
            )

    @staticmethod
    def _ensure_active_contact(contact: CustomerContact) -> None:
        if contact.status != "active" or contact.archived_at is not None:
            raise ApiException(
                409,
                "customers.portal_access.contact_inactive",
                "errors.customers.portal.contact_inactive",
            )

    @staticmethod
    def _normalize_create_payload(payload: CustomerPortalAccessCreate) -> CustomerPortalAccessCreate:
        username = payload.username.strip()
        email = payload.email.strip().lower()
        full_name = payload.full_name.strip()
        locale = payload.locale.strip().lower() or "de"
        timezone = payload.timezone.strip() or "Europe/Berlin"
        status = payload.status.strip().lower() or "active"
        if not username:
            raise ApiException(400, "customers.portal_access.username_required", "errors.iam.user.username_required")
        if "@" not in email:
            raise ApiException(400, "customers.portal_access.invalid_email", "errors.iam.user.invalid_email")
        if not full_name:
            raise ApiException(400, "customers.portal_access.full_name_required", "errors.iam.user.full_name_required")
        if status not in {"active", "inactive"}:
            raise ApiException(400, "customers.portal_access.invalid_status", "errors.iam.user.invalid_status")
        return CustomerPortalAccessCreate(
            tenant_id=payload.tenant_id,
            customer_id=payload.customer_id,
            contact_id=payload.contact_id,
            username=username,
            email=email,
            full_name=full_name,
            locale=locale,
            timezone=timezone,
            status=status,
            temporary_password=CustomerPortalAccessService._normalize_optional(payload.temporary_password),
        )

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        normalized = (value or "").strip()
        return normalized or None

    @staticmethod
    def _generate_temporary_password() -> str:
        return f"SP-{secrets.token_urlsafe(9)}!A1"

    @staticmethod
    def _ensure_tenant_scope(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        enforce_customer_module_access(actor, tenant_id=tenant_id)

    @staticmethod
    def _not_found(entity: str) -> ApiException:
        return ApiException(404, f"customers.portal_access.{entity}.not_found", f"errors.customers.{entity}.not_found")

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
        *,
        event_type: str,
        entity_id: str,
        tenant_id: str,
        customer_id: str,
        contact_id: str,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=actor.tenant_id,
                user_id=actor.user_id,
                session_id=actor.session_id,
                request_id=actor.request_id,
            ),
            event_type=event_type,
            entity_type="iam.user_account",
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=after_json,
            metadata_json={"customer_id": customer_id, "contact_id": contact_id, **(metadata_json or {})},
        )

    @staticmethod
    def _access_snapshot(item: CustomerPortalAccessListItemRead | None) -> dict[str, object] | None:
        if item is None:
            return None
        return {
            "user_id": item.user_id,
            "contact_id": item.contact_id,
            "contact_name": item.contact_name,
            "username": item.username,
            "email": item.email,
            "full_name": item.full_name,
            "locale": item.locale,
            "role_key": item.role_key,
            "status": item.status,
            "role_assignment_status": item.role_assignment_status,
            "is_password_login_enabled": item.is_password_login_enabled,
            "last_login_at": item.last_login_at.isoformat() if item.last_login_at else None,
        }
