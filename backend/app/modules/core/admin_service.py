"""Core admin service layer for tenant onboarding and maintenance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.errors import ApiException
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.core.schemas import (
    BranchCreate,
    BranchRead,
    BranchUpdate,
    MandateCreate,
    MandateRead,
    MandateUpdate,
    TenantCreate,
    TenantListItem,
    TenantOnboardingCreate,
    TenantOnboardingRead,
    TenantRead,
    TenantSettingCreate,
    TenantSettingRead,
    TenantSettingUpdate,
    TenantStatusUpdate,
    TenantUpdate,
)


@dataclass(frozen=True, slots=True)
class AdminActorContext:
    actor_role: str
    tenant_id: str | None = None
    actor_user_id: str | None = None
    actor_session_id: str | None = None
    request_id: str | None = None
    permission_keys: frozenset[str] = frozenset()
    branch_ids: frozenset[str] = frozenset()
    mandate_ids: frozenset[str] = frozenset()

    @property
    def is_platform_admin(self) -> bool:
        return self.actor_role == "platform_admin"

    @property
    def is_tenant_admin(self) -> bool:
        return self.actor_role == "tenant_admin"


class CoreAdminRepository(Protocol):
    def onboard_tenant(self, payload: TenantOnboardingCreate, actor_user_id: str | None) -> TenantOnboardingRead: ...
    def list_tenants(self) -> list[TenantListItem]: ...
    def get_tenant(self, tenant_id: str) -> TenantRead | None: ...
    def update_tenant(self, tenant_id: str, payload: TenantUpdate, actor_user_id: str | None) -> TenantRead | None: ...
    def transition_tenant_status(
        self,
        tenant_id: str,
        payload: TenantStatusUpdate,
        actor_user_id: str | None,
    ) -> TenantRead | None: ...
    def list_branches(self, tenant_id: str) -> list[BranchRead]: ...
    def create_branch(self, tenant_id: str, payload: BranchCreate, actor_user_id: str | None) -> BranchRead: ...
    def update_branch(
        self,
        tenant_id: str,
        branch_id: str,
        payload: BranchUpdate,
        actor_user_id: str | None,
    ) -> BranchRead | None: ...
    def list_mandates(self, tenant_id: str) -> list[MandateRead]: ...
    def create_mandate(self, tenant_id: str, payload: MandateCreate, actor_user_id: str | None) -> MandateRead: ...
    def update_mandate(
        self,
        tenant_id: str,
        mandate_id: str,
        payload: MandateUpdate,
        actor_user_id: str | None,
    ) -> MandateRead | None: ...
    def list_settings(self, tenant_id: str) -> list[TenantSettingRead]: ...
    def create_setting(
        self,
        tenant_id: str,
        payload: TenantSettingCreate,
        actor_user_id: str | None,
    ) -> TenantSettingRead: ...
    def update_setting(
        self,
        tenant_id: str,
        setting_id: str,
        payload: TenantSettingUpdate,
        actor_user_id: str | None,
    ) -> TenantSettingRead | None: ...


class CoreAdminService:
    def __init__(self, repository: CoreAdminRepository, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def onboard_tenant(
        self,
        payload: TenantOnboardingCreate,
        actor: AdminActorContext,
    ) -> TenantOnboardingRead:
        self._require_platform_admin(actor)
        result = self.repository.onboard_tenant(payload, actor.actor_user_id)
        self._record_event(
            actor,
            event_type="core.tenant.onboarded",
            entity_type="core.tenant",
            entity_id=result.tenant.id,
            tenant_id=result.tenant.id,
            after_json={"code": result.tenant.code, "name": result.tenant.name, "status": result.tenant.status},
        )
        return result

    def list_tenants(self, actor: AdminActorContext) -> list[TenantListItem]:
        if actor.is_platform_admin:
            return self.repository.list_tenants()

        if actor.is_tenant_admin and actor.tenant_id:
            tenant = self.repository.get_tenant(actor.tenant_id)
            return [TenantListItem.model_validate(tenant)] if tenant else []

        raise self._forbidden()

    def get_tenant(self, tenant_id: str, actor: AdminActorContext) -> TenantRead:
        self._ensure_tenant_scope(actor, tenant_id)
        tenant = self.repository.get_tenant(tenant_id)
        if tenant is None:
            raise self._not_found("tenant")
        return tenant

    def update_tenant(self, tenant_id: str, payload: TenantUpdate, actor: AdminActorContext) -> TenantRead:
        self._ensure_tenant_scope(actor, tenant_id)
        before_json = self._tenant_snapshot(self.repository.get_tenant(tenant_id))
        tenant = self.repository.update_tenant(tenant_id, payload, actor.actor_user_id)
        if tenant is None:
            raise self._not_found("tenant")
        self._record_event(
            actor,
            event_type="core.tenant.updated",
            entity_type="core.tenant",
            entity_id=tenant.id,
            tenant_id=tenant.id,
            before_json=before_json,
            after_json=self._tenant_snapshot(tenant),
        )
        return tenant

    def transition_tenant_status(
        self,
        tenant_id: str,
        payload: TenantStatusUpdate,
        actor: AdminActorContext,
    ) -> TenantRead:
        self._ensure_tenant_scope(actor, tenant_id)
        before_json = self._tenant_snapshot(self.repository.get_tenant(tenant_id))
        tenant = self.repository.transition_tenant_status(tenant_id, payload, actor.actor_user_id)
        if tenant is None:
            raise self._not_found("tenant")
        self._record_event(
            actor,
            event_type="core.tenant.lifecycle_changed",
            entity_type="core.tenant",
            entity_id=tenant.id,
            tenant_id=tenant.id,
            before_json=before_json,
            after_json=self._tenant_snapshot(tenant),
            metadata_json={"requested_status": payload.status},
        )
        return tenant

    def list_branches(self, tenant_id: str, actor: AdminActorContext) -> list[BranchRead]:
        self._ensure_tenant_scope(actor, tenant_id)
        return self.repository.list_branches(tenant_id)

    def create_branch(self, tenant_id: str, payload: BranchCreate, actor: AdminActorContext) -> BranchRead:
        self._ensure_tenant_scope(actor, tenant_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                status_code=400,
                code="core.validation.branch_tenant_mismatch",
                message_key="errors.core.branch.tenant_mismatch",
                details={"tenant_id": tenant_id},
            )
        branch = self.repository.create_branch(tenant_id, payload, actor.actor_user_id)
        self._record_event(
            actor,
            event_type="core.branch.created",
            entity_type="core.branch",
            entity_id=branch.id,
            tenant_id=branch.tenant_id,
            after_json=self._branch_snapshot(branch),
        )
        return branch

    def update_branch(
        self,
        tenant_id: str,
        branch_id: str,
        payload: BranchUpdate,
        actor: AdminActorContext,
    ) -> BranchRead:
        self._ensure_tenant_scope(actor, tenant_id)
        before_json = self._branch_snapshot(
            next((branch for branch in self.repository.list_branches(tenant_id) if branch.id == branch_id), None)
        )
        branch = self.repository.update_branch(tenant_id, branch_id, payload, actor.actor_user_id)
        if branch is None:
            raise self._not_found("branch")
        self._record_event(
            actor,
            event_type="core.branch.updated",
            entity_type="core.branch",
            entity_id=branch.id,
            tenant_id=branch.tenant_id,
            before_json=before_json,
            after_json=self._branch_snapshot(branch),
        )
        return branch

    def list_mandates(self, tenant_id: str, actor: AdminActorContext) -> list[MandateRead]:
        self._ensure_tenant_scope(actor, tenant_id)
        return self.repository.list_mandates(tenant_id)

    def create_mandate(
        self,
        tenant_id: str,
        payload: MandateCreate,
        actor: AdminActorContext,
    ) -> MandateRead:
        self._ensure_tenant_scope(actor, tenant_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                status_code=400,
                code="core.validation.mandate_tenant_mismatch",
                message_key="errors.core.mandate.tenant_mismatch",
                details={"tenant_id": tenant_id},
            )
        mandate = self.repository.create_mandate(tenant_id, payload, actor.actor_user_id)
        self._record_event(
            actor,
            event_type="core.mandate.created",
            entity_type="core.mandate",
            entity_id=mandate.id,
            tenant_id=mandate.tenant_id,
            after_json=self._mandate_snapshot(mandate),
        )
        return mandate

    def update_mandate(
        self,
        tenant_id: str,
        mandate_id: str,
        payload: MandateUpdate,
        actor: AdminActorContext,
    ) -> MandateRead:
        self._ensure_tenant_scope(actor, tenant_id)
        before_json = self._mandate_snapshot(
            next((mandate for mandate in self.repository.list_mandates(tenant_id) if mandate.id == mandate_id), None)
        )
        mandate = self.repository.update_mandate(tenant_id, mandate_id, payload, actor.actor_user_id)
        if mandate is None:
            raise self._not_found("mandate")
        self._record_event(
            actor,
            event_type="core.mandate.updated",
            entity_type="core.mandate",
            entity_id=mandate.id,
            tenant_id=mandate.tenant_id,
            before_json=before_json,
            after_json=self._mandate_snapshot(mandate),
        )
        return mandate

    def list_settings(self, tenant_id: str, actor: AdminActorContext) -> list[TenantSettingRead]:
        self._ensure_tenant_scope(actor, tenant_id)
        return self.repository.list_settings(tenant_id)

    def create_setting(
        self,
        tenant_id: str,
        payload: TenantSettingCreate,
        actor: AdminActorContext,
    ) -> TenantSettingRead:
        self._ensure_tenant_scope(actor, tenant_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                status_code=400,
                code="core.validation.setting_tenant_mismatch",
                message_key="errors.core.setting.tenant_mismatch",
                details={"tenant_id": tenant_id},
            )
        setting = self.repository.create_setting(tenant_id, payload, actor.actor_user_id)
        self._record_event(
            actor,
            event_type="core.tenant_setting.created",
            entity_type="core.tenant_setting",
            entity_id=setting.id,
            tenant_id=setting.tenant_id,
            after_json=self._setting_snapshot(setting),
        )
        return setting

    def update_setting(
        self,
        tenant_id: str,
        setting_id: str,
        payload: TenantSettingUpdate,
        actor: AdminActorContext,
    ) -> TenantSettingRead:
        self._ensure_tenant_scope(actor, tenant_id)
        before_json = self._setting_snapshot(
            next((setting for setting in self.repository.list_settings(tenant_id) if setting.id == setting_id), None)
        )
        setting = self.repository.update_setting(tenant_id, setting_id, payload, actor.actor_user_id)
        if setting is None:
            raise self._not_found("tenant_setting")
        self._record_event(
            actor,
            event_type="core.tenant_setting.updated",
            entity_type="core.tenant_setting",
            entity_id=setting.id,
            tenant_id=setting.tenant_id,
            before_json=before_json,
            after_json=self._setting_snapshot(setting),
        )
        return setting

    def _ensure_tenant_scope(self, actor: AdminActorContext, tenant_id: str) -> None:
        if actor.is_platform_admin:
            return
        if actor.is_tenant_admin and actor.tenant_id == tenant_id:
            return
        raise self._forbidden()

    @staticmethod
    def _require_platform_admin(actor: AdminActorContext) -> None:
        if not actor.is_platform_admin:
            raise CoreAdminService._forbidden()

    @staticmethod
    def _forbidden() -> ApiException:
        return ApiException(
            status_code=403,
            code="core.authorization.forbidden",
            message_key="errors.core.authorization.forbidden",
        )

    @staticmethod
    def _not_found(entity: str) -> ApiException:
        return ApiException(
            status_code=404,
            code=f"core.not_found.{entity}",
            message_key=f"errors.core.{entity}.not_found",
        )

    def _record_event(
        self,
        actor: AdminActorContext,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str | None = None,
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
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=after_json,
            metadata_json=metadata_json,
        )

    @staticmethod
    def _tenant_snapshot(tenant: TenantRead | None) -> dict[str, object]:
        if tenant is None:
            return {}
        return {
            "id": tenant.id,
            "code": tenant.code,
            "name": tenant.name,
            "status": tenant.status,
            "default_locale": tenant.default_locale,
            "default_currency": tenant.default_currency,
            "timezone": tenant.timezone,
            "version_no": tenant.version_no,
        }

    @staticmethod
    def _branch_snapshot(branch: BranchRead | None) -> dict[str, object]:
        if branch is None:
            return {}
        return {
            "id": branch.id,
            "tenant_id": branch.tenant_id,
            "code": branch.code,
            "name": branch.name,
            "status": branch.status,
            "contact_email": branch.contact_email,
            "contact_phone": branch.contact_phone,
            "version_no": branch.version_no,
        }

    @staticmethod
    def _mandate_snapshot(mandate: MandateRead | None) -> dict[str, object]:
        if mandate is None:
            return {}
        return {
            "id": mandate.id,
            "tenant_id": mandate.tenant_id,
            "branch_id": mandate.branch_id,
            "code": mandate.code,
            "name": mandate.name,
            "status": mandate.status,
            "external_ref": mandate.external_ref,
            "version_no": mandate.version_no,
        }

    @staticmethod
    def _setting_snapshot(setting: TenantSettingRead | None) -> dict[str, object]:
        if setting is None:
            return {}
        return {
            "id": setting.id,
            "tenant_id": setting.tenant_id,
            "key": setting.key,
            "status": setting.status,
            "value_json": setting.value_json,
            "version_no": setting.version_no,
        }
