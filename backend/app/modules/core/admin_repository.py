"""SQLAlchemy repository for core admin flows."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ApiException
from app.modules.core.config_seed import seed_default_tenant_settings
from app.modules.core.lookup_seed import seed_lookup_values
from app.modules.core.models import Branch, LookupValue, Mandate, Tenant, TenantSetting
from app.modules.employees.catalog_seed import seed_baseline_employee_catalogs
from app.modules.core.schemas import (
    BranchCreate,
    BranchRead,
    BranchUpdate,
    LookupValueCreate,
    LookupValueRead,
    LookupValueUpdate,
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


class SqlAlchemyCoreAdminRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def onboard_tenant(self, payload: TenantOnboardingCreate, actor_user_id: str | None) -> TenantOnboardingRead:
        tenant = Tenant(
            code=payload.tenant.code,
            name=payload.tenant.name,
            legal_name=payload.tenant.legal_name,
            default_locale=payload.tenant.default_locale,
            default_currency=payload.tenant.default_currency,
            timezone=payload.tenant.timezone,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(tenant)
        self.session.flush()

        branch = Branch(
            tenant_id=tenant.id,
            code=payload.initial_branch.code,
            name=payload.initial_branch.name,
            address_id=payload.initial_branch.address_id,
            contact_email=payload.initial_branch.contact_email,
            contact_phone=payload.initial_branch.contact_phone,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(branch)
        self.session.flush()

        mandate = Mandate(
            tenant_id=tenant.id,
            branch_id=branch.id,
            code=payload.initial_mandate.code,
            name=payload.initial_mandate.name,
            external_ref=payload.initial_mandate.external_ref,
            notes=payload.initial_mandate.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(mandate)

        settings = []
        for setting_payload in payload.initial_settings:
            settings.append(
                TenantSetting(
                    tenant_id=tenant.id,
                    key=setting_payload.key,
                    value_json=setting_payload.value_json,
                    created_by_user_id=actor_user_id,
                    updated_by_user_id=actor_user_id,
                )
            )
        self.session.add_all(settings)
        self.session.flush()

        seed_default_tenant_settings(
            self.session,
            tenant_id=tenant.id,
            actor_user_id=actor_user_id,
        )

        seed_lookup_values(
            self.session,
            actor_user_id=actor_user_id,
        )

        seed_lookup_values(
            self.session,
            tenant_id=tenant.id,
            actor_user_id=actor_user_id,
        )

        seed_baseline_employee_catalogs(
            self.session,
            tenant_id=tenant.id,
            actor_user_id=actor_user_id,
        )

        self._commit_or_raise()
        self.session.refresh(tenant)
        self.session.refresh(branch)
        self.session.refresh(mandate)
        for setting in settings:
            self.session.refresh(setting)

        return TenantOnboardingRead(
            tenant=TenantRead.model_validate(tenant),
            initial_branch=BranchRead.model_validate(branch),
            initial_mandate=MandateRead.model_validate(mandate),
            initial_settings=[TenantSettingRead.model_validate(setting) for setting in settings],
        )

    def list_tenants(self) -> list[TenantListItem]:
        tenants = self.session.scalars(select(Tenant).order_by(Tenant.code)).all()
        return [TenantListItem.model_validate(tenant) for tenant in tenants]

    def get_tenant(self, tenant_id: str) -> TenantRead | None:
        tenant = self.session.get(Tenant, tenant_id)
        return TenantRead.model_validate(tenant) if tenant else None

    def update_tenant(self, tenant_id: str, payload: TenantUpdate, actor_user_id: str | None) -> TenantRead | None:
        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            return None
        self._apply_update(
            tenant,
            payload,
            (
                "name",
                "legal_name",
                "default_locale",
                "default_currency",
                "timezone",
                "status",
                "archived_at",
            ),
            actor_user_id,
        )
        self._commit_or_raise()
        self.session.refresh(tenant)
        return TenantRead.model_validate(tenant)

    def transition_tenant_status(
        self,
        tenant_id: str,
        payload: TenantStatusUpdate,
        actor_user_id: str | None,
    ) -> TenantRead | None:
        tenant = self.session.get(Tenant, tenant_id)
        if tenant is None:
            return None
        self._apply_lifecycle_status(tenant, payload.status, actor_user_id)
        self._commit_or_raise()
        self.session.refresh(tenant)
        return TenantRead.model_validate(tenant)

    def list_branches(self, tenant_id: str) -> list[BranchRead]:
        branches = self.session.scalars(
            select(Branch).where(Branch.tenant_id == tenant_id).order_by(Branch.code)
        ).all()
        return [BranchRead.model_validate(branch) for branch in branches]

    def create_branch(self, tenant_id: str, payload: BranchCreate, actor_user_id: str | None) -> BranchRead:
        branch = Branch(
            tenant_id=tenant_id,
            code=payload.code,
            name=payload.name,
            address_id=payload.address_id,
            contact_email=payload.contact_email,
            contact_phone=payload.contact_phone,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(branch)
        self._commit_or_raise()
        self.session.refresh(branch)
        return BranchRead.model_validate(branch)

    def update_branch(
        self,
        tenant_id: str,
        branch_id: str,
        payload: BranchUpdate,
        actor_user_id: str | None,
    ) -> BranchRead | None:
        branch = self._tenant_scoped_get(Branch, tenant_id, branch_id)
        if branch is None:
            return None
        self._apply_update(
            branch,
            payload,
            ("name", "address_id", "contact_email", "contact_phone", "status", "archived_at"),
            actor_user_id,
        )
        self._commit_or_raise()
        self.session.refresh(branch)
        return BranchRead.model_validate(branch)

    def list_mandates(self, tenant_id: str) -> list[MandateRead]:
        mandates = self.session.scalars(
            select(Mandate).where(Mandate.tenant_id == tenant_id).order_by(Mandate.code)
        ).all()
        return [MandateRead.model_validate(mandate) for mandate in mandates]

    def create_mandate(self, tenant_id: str, payload: MandateCreate, actor_user_id: str | None) -> MandateRead:
        mandate = Mandate(
            tenant_id=tenant_id,
            branch_id=payload.branch_id,
            code=payload.code,
            name=payload.name,
            external_ref=payload.external_ref,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(mandate)
        self._commit_or_raise()
        self.session.refresh(mandate)
        return MandateRead.model_validate(mandate)

    def update_mandate(
        self,
        tenant_id: str,
        mandate_id: str,
        payload: MandateUpdate,
        actor_user_id: str | None,
    ) -> MandateRead | None:
        mandate = self._tenant_scoped_get(Mandate, tenant_id, mandate_id)
        if mandate is None:
            return None
        self._apply_update(
            mandate,
            payload,
            ("name", "external_ref", "notes", "status", "archived_at"),
            actor_user_id,
        )
        self._commit_or_raise()
        self.session.refresh(mandate)
        return MandateRead.model_validate(mandate)

    def list_settings(self, tenant_id: str) -> list[TenantSettingRead]:
        settings = self.session.scalars(
            select(TenantSetting).where(TenantSetting.tenant_id == tenant_id).order_by(TenantSetting.key)
        ).all()
        return [TenantSettingRead.model_validate(setting) for setting in settings]

    def create_setting(
        self,
        tenant_id: str,
        payload: TenantSettingCreate,
        actor_user_id: str | None,
    ) -> TenantSettingRead:
        setting = TenantSetting(
            tenant_id=tenant_id,
            key=payload.key,
            value_json=payload.value_json,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(setting)
        self._commit_or_raise()
        self.session.refresh(setting)
        return TenantSettingRead.model_validate(setting)

    def update_setting(
        self,
        tenant_id: str,
        setting_id: str,
        payload: TenantSettingUpdate,
        actor_user_id: str | None,
    ) -> TenantSettingRead | None:
        setting = self._tenant_scoped_get(TenantSetting, tenant_id, setting_id)
        if setting is None:
            return None
        if payload.version_no is None or payload.version_no != setting.version_no:
            raise ApiException(
                status_code=409,
                code="core.conflict.stale_setting_version",
                message_key="errors.core.setting.stale_version",
                details={"expected_version_no": setting.version_no},
            )
        self._apply_update(
            setting,
            payload,
            ("value_json", "status", "archived_at"),
            actor_user_id,
        )
        self._commit_or_raise()
        self.session.refresh(setting)
        return TenantSettingRead.model_validate(setting)

    def list_lookup_values(self, tenant_id: str, domain: str) -> list[LookupValueRead]:
        rows = self.session.scalars(
            select(LookupValue)
            .where(
                LookupValue.domain == domain,
                LookupValue.archived_at.is_(None),
                (LookupValue.tenant_id.is_(None)) | (LookupValue.tenant_id == tenant_id),
            )
            .order_by(LookupValue.sort_order.asc(), LookupValue.label.asc())
        ).all()
        return [LookupValueRead.model_validate(row) for row in rows]

    def create_lookup_value(
        self,
        tenant_id: str,
        payload: LookupValueCreate,
        actor_user_id: str | None,
    ) -> LookupValueRead:
        row = LookupValue(
            tenant_id=tenant_id,
            domain=payload.domain,
            code=payload.code,
            label=payload.label,
            description=payload.description,
            sort_order=payload.sort_order,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        self.session.refresh(row)
        return LookupValueRead.model_validate(row)

    def update_lookup_value(
        self,
        tenant_id: str,
        lookup_value_id: str,
        payload: LookupValueUpdate,
        actor_user_id: str | None,
    ) -> LookupValueRead | None:
        row = self._tenant_scoped_get(LookupValue, tenant_id, lookup_value_id)
        if row is None:
            return None
        if payload.version_no is None or payload.version_no != row.version_no:
            raise ApiException(
                status_code=409,
                code="core.conflict.stale_lookup_value_version",
                message_key="errors.core.lookup_value.stale_version",
                details={"expected_version_no": row.version_no},
            )
        self._apply_update(
            row,
            payload,
            ("label", "description", "sort_order", "status", "archived_at"),
            actor_user_id,
        )
        self._commit_or_raise()
        self.session.refresh(row)
        return LookupValueRead.model_validate(row)

    def _tenant_scoped_get(self, model: type[Branch | Mandate | TenantSetting | LookupValue], tenant_id: str, object_id: str):
        statement = select(model).where(model.id == object_id, model.tenant_id == tenant_id)
        return self.session.scalars(statement).one_or_none()

    def _apply_update(self, model: object, payload: object, fields: tuple[str, ...], actor_user_id: str | None) -> None:
        payload_data = payload.model_dump(exclude_unset=True)
        for field in fields:
            if field in payload_data:
                setattr(model, field, payload_data[field])
        setattr(model, "updated_by_user_id", actor_user_id)
        setattr(model, "version_no", getattr(model, "version_no") + 1)

    @staticmethod
    def _apply_lifecycle_status(model: Tenant, status: str, actor_user_id: str | None) -> None:
        if model.archived_at is not None and status != "archived":
            raise ApiException(
                status_code=409,
                code="core.conflict.archived_record",
                message_key="errors.core.lifecycle.archived_record",
            )
        model.status = status
        model.updated_by_user_id = actor_user_id
        model.version_no += 1

    def _commit_or_raise(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise self._translate_integrity_error(exc) from exc

    @staticmethod
    def _translate_integrity_error(exc: IntegrityError) -> ApiException:
        message = str(exc.orig)
        if "uq_core_tenant_code" in message:
            return ApiException(409, "core.conflict.tenant_code", "errors.core.tenant.duplicate_code")
        if "uq_core_branch_tenant_code" in message:
            return ApiException(409, "core.conflict.branch_code", "errors.core.branch.duplicate_code")
        if "uq_core_mandate_tenant_code" in message:
            return ApiException(409, "core.conflict.mandate_code", "errors.core.mandate.duplicate_code")
        if "uq_core_tenant_setting_tenant_key" in message:
            return ApiException(409, "core.conflict.setting_key", "errors.core.setting.duplicate_key")
        if "uq_core_lookup_value_tenant_domain_code" in message:
            return ApiException(409, "core.conflict.lookup_value_code", "errors.core.lookup_value.duplicate_code")
        if "fk_core_mandate_tenant_branch" in message:
            return ApiException(400, "core.validation.branch_scope", "errors.core.mandate.invalid_branch_scope")
        return ApiException(409, "core.conflict.integrity", "errors.core.conflict.integrity")
