"""Service layer for subcontractor aggregate maintenance."""

from __future__ import annotations

from typing import Protocol

from app.errors import ApiException
from app.modules.core.models import Address, Branch, LookupValue, Mandate
from app.modules.core.schemas import AddressCreate, AddressRead
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.iam.models import UserAccount
from app.modules.subcontractors.models import (
    Subcontractor,
    SubcontractorContact,
    SubcontractorFinanceProfile,
    SubcontractorScope,
)
from app.modules.subcontractors.policy import (
    PORTAL_ROLE_KEYS,
    SUBCONTRACTOR_PORTAL_BOUNDARY,
    can_read_subcontractor_internal,
    enforce_subcontractor_internal_read_access,
    enforce_subcontractor_internal_write_access,
)
from app.modules.subcontractors.schemas import (
    SubcontractorContactCreate,
    SubcontractorContactUserOptionRead,
    SubcontractorContactRead,
    SubcontractorContactUpdate,
    SubcontractorCreate,
    SubcontractorFilter,
    SubcontractorFinanceProfileCreate,
    SubcontractorFinanceProfileRead,
    SubcontractorFinanceProfileUpdate,
    SubcontractorListItem,
    SubcontractorReferenceDataRead,
    SubcontractorReferenceOptionRead,
    SubcontractorRead,
    SubcontractorScopeCreate,
    SubcontractorScopeRead,
    SubcontractorScopeUpdate,
    SubcontractorUpdate,
)


class SubcontractorRepository(Protocol):
    def list_subcontractors(self, tenant_id: str, filters: SubcontractorFilter) -> list[Subcontractor]: ...
    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None: ...
    def create_subcontractor(self, tenant_id: str, payload: SubcontractorCreate, actor_user_id: str | None) -> Subcontractor: ...
    def update_subcontractor(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorUpdate,
        actor_user_id: str | None,
    ) -> Subcontractor | None: ...
    def list_contacts(self, tenant_id: str, subcontractor_id: str) -> list[SubcontractorContact]: ...
    def get_contact(self, tenant_id: str, subcontractor_id: str, contact_id: str) -> SubcontractorContact | None: ...
    def create_contact(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorContactCreate,
        actor_user_id: str | None,
    ) -> SubcontractorContact: ...
    def update_contact(
        self,
        tenant_id: str,
        subcontractor_id: str,
        contact_id: str,
        payload: SubcontractorContactUpdate,
        actor_user_id: str | None,
    ) -> SubcontractorContact | None: ...
    def list_scopes(self, tenant_id: str, subcontractor_id: str) -> list[SubcontractorScope]: ...
    def get_scope(self, tenant_id: str, subcontractor_id: str, scope_id: str) -> SubcontractorScope | None: ...
    def create_scope(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorScopeCreate,
        actor_user_id: str | None,
    ) -> SubcontractorScope: ...
    def update_scope(
        self,
        tenant_id: str,
        subcontractor_id: str,
        scope_id: str,
        payload: SubcontractorScopeUpdate,
        actor_user_id: str | None,
    ) -> SubcontractorScope | None: ...
    def get_finance_profile(self, tenant_id: str, subcontractor_id: str) -> SubcontractorFinanceProfile | None: ...
    def create_finance_profile(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorFinanceProfileCreate,
        actor_user_id: str | None,
    ) -> SubcontractorFinanceProfile: ...
    def update_finance_profile(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorFinanceProfileUpdate,
        actor_user_id: str | None,
    ) -> SubcontractorFinanceProfile | None: ...
    def find_subcontractor_by_number(self, tenant_id: str, subcontractor_number: str, *, exclude_id: str | None = None) -> Subcontractor | None: ...
    def has_primary_contact(self, tenant_id: str, subcontractor_id: str, *, exclude_id: str | None = None) -> bool: ...
    def find_contact_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None) -> SubcontractorContact | None: ...
    def find_overlapping_scope(
        self,
        tenant_id: str,
        subcontractor_id: str,
        branch_id: str,
        mandate_id: str | None,
        valid_from,
        valid_to,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorScope | None: ...
    def get_lookup_value(self, lookup_id: str) -> LookupValue | None: ...
    def list_lookup_values(self, tenant_id: str, domain: str) -> list[LookupValue]: ...
    def get_branch(self, tenant_id: str, branch_id: str) -> Branch | None: ...
    def get_mandate(self, tenant_id: str, mandate_id: str) -> Mandate | None: ...
    def get_user_account(self, tenant_id: str, user_id: str) -> UserAccount | None: ...
    def list_contact_user_options(self, tenant_id: str, search: str = "", limit: int = 25) -> list[UserAccount]: ...
    def get_address(self, address_id: str) -> Address | None: ...
    def create_address(self, row: Address) -> Address: ...


class SubcontractorService:
    LOOKUP_DOMAINS = {
        "legal_form_lookup_id": "legal_form",
        "subcontractor_status_lookup_id": "subcontractor_status",
        "invoice_delivery_method_lookup_id": "invoice_delivery_method",
        "invoice_status_mode_lookup_id": "subcontractor_invoice_status_mode",
    }

    def __init__(self, repository: SubcontractorRepository, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_subcontractors(
        self,
        tenant_id: str,
        filters: SubcontractorFilter,
        actor: RequestAuthorizationContext,
    ) -> list[SubcontractorListItem]:
        rows = self.repository.list_subcontractors(tenant_id, filters)
        return [
            SubcontractorListItem.model_validate(row)
            for row in rows
            if can_read_subcontractor_internal(actor, tenant_id=tenant_id, subcontractor=row)
        ]

    def get_subcontractor(self, tenant_id: str, subcontractor_id: str, actor: RequestAuthorizationContext) -> SubcontractorRead:
        row = self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        return self._serialize_subcontractor(row, actor)

    def get_reference_data(self, tenant_id: str, actor: RequestAuthorizationContext) -> SubcontractorReferenceDataRead:
        self._enforce_internal_reference_read_access(actor, tenant_id)
        return SubcontractorReferenceDataRead(
            legal_forms=[
                self._serialize_reference_option(row)
                for row in self.repository.list_lookup_values(tenant_id, "legal_form")
                if row.archived_at is None
            ]
        )

    def create_subcontractor(
        self,
        tenant_id: str,
        payload: SubcontractorCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorRead:
        enforce_subcontractor_internal_write_access(actor, tenant_id=tenant_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "subcontractors.validation.tenant_mismatch", "errors.subcontractors.subcontractor.tenant_mismatch")
        self._validate_subcontractor_payload(tenant_id, payload)
        if self.repository.find_subcontractor_by_number(tenant_id, payload.subcontractor_number) is not None:
            raise ApiException(409, "subcontractors.conflict.number", "errors.subcontractors.subcontractor.duplicate_number")
        row = self.repository.create_subcontractor(tenant_id, payload, actor.user_id)
        self._record_event(
            actor,
            "subcontractors.company.created",
            "partner.subcontractor",
            row.id,
            tenant_id,
            after_json=self._subcontractor_snapshot(row),
        )
        return self._serialize_subcontractor(row, actor)

    def update_subcontractor(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorUpdate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorRead:
        current = self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        before_json = self._subcontractor_snapshot(current)
        next_number = payload.subcontractor_number or current.subcontractor_number
        if self.repository.find_subcontractor_by_number(tenant_id, next_number, exclude_id=subcontractor_id) is not None:
            raise ApiException(409, "subcontractors.conflict.number", "errors.subcontractors.subcontractor.duplicate_number")
        self._validate_subcontractor_payload(
            tenant_id,
            SubcontractorCreate(
                tenant_id=tenant_id,
                subcontractor_number=next_number,
                legal_name=self._field_value(payload, "legal_name", current.legal_name),
                display_name=self._field_value(payload, "display_name", current.display_name),
                legal_form_lookup_id=self._field_value(payload, "legal_form_lookup_id", current.legal_form_lookup_id),
                subcontractor_status_lookup_id=(
                    self._field_value(payload, "subcontractor_status_lookup_id", current.subcontractor_status_lookup_id)
                ),
                managing_director_name=self._field_value(payload, "managing_director_name", current.managing_director_name),
                address_id=self._field_value(payload, "address_id", current.address_id),
                latitude=self._field_value(payload, "latitude", current.latitude),
                longitude=self._field_value(payload, "longitude", current.longitude),
                notes=self._field_value(payload, "notes", current.notes),
            ),
        )
        updated = self.repository.update_subcontractor(tenant_id, subcontractor_id, payload, actor.user_id)
        if updated is None:
            raise self._not_found("subcontractor")
        after_json = self._subcontractor_snapshot(updated)
        self._record_event(
            actor,
            "subcontractors.company.updated",
            "partner.subcontractor",
            updated.id,
            tenant_id,
            before_json=before_json,
            after_json=after_json,
            metadata_json={"changed_fields": self._changed_fields(before_json, after_json)},
        )
        return self._serialize_subcontractor(updated, actor)

    def list_contacts(self, tenant_id: str, subcontractor_id: str, actor: RequestAuthorizationContext) -> list[SubcontractorContactRead]:
        self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        return [self._serialize_contact(row, actor) for row in self.repository.list_contacts(tenant_id, subcontractor_id)]

    def list_contact_user_options(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
        *,
        search: str = "",
        limit: int = 25,
    ) -> list[SubcontractorContactUserOptionRead]:
        self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        return [
            SubcontractorContactUserOptionRead(
                id=row.id,
                username=row.username,
                email=row.email,
                full_name=row.full_name,
                status=row.status,
            )
            for row in self.repository.list_contact_user_options(tenant_id, search=search, limit=limit)
        ]

    def list_address_options(self, tenant_id: str, subcontractor_id: str, actor: RequestAuthorizationContext) -> list[AddressRead]:
        row = self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        if row.address_id is None:
            return []
        address = self.repository.get_address(row.address_id)
        return [AddressRead.model_validate(address)] if address is not None else []

    def create_address_option(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: AddressCreate,
        actor: RequestAuthorizationContext,
    ) -> AddressRead:
        self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        normalized = AddressCreate(
            street_line_1=payload.street_line_1.strip(),
            street_line_2=payload.street_line_2.strip() if payload.street_line_2 and payload.street_line_2.strip() else None,
            postal_code=payload.postal_code.strip(),
            city=payload.city.strip(),
            state=payload.state.strip() if payload.state and payload.state.strip() else None,
            country_code=payload.country_code.strip().upper(),
        )
        row = self.repository.create_address(
            Address(
                street_line_1=normalized.street_line_1,
                street_line_2=normalized.street_line_2,
                postal_code=normalized.postal_code,
                city=normalized.city,
                state=normalized.state,
                country_code=normalized.country_code,
            )
        )
        return AddressRead.model_validate(row)

    def create_contact(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorContactCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorContactRead:
        self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        self._validate_contact_path(tenant_id, subcontractor_id, payload)
        self._validate_contact_constraints(tenant_id, subcontractor_id, payload)
        row = self.repository.create_contact(tenant_id, subcontractor_id, payload, actor.user_id)
        after_json = self._contact_snapshot(row)
        self._record_event(
            actor,
            "subcontractors.contact.created",
            "partner.subcontractor_contact",
            row.id,
            tenant_id,
            after_json=after_json,
            metadata_json={"subcontractor_id": subcontractor_id},
        )
        if row.portal_enabled or row.user_id is not None:
            self._record_event(
                actor,
                "subcontractors.contact.portal_link_changed",
                "partner.subcontractor_contact",
                row.id,
                tenant_id,
                after_json=after_json,
                metadata_json={"subcontractor_id": subcontractor_id, "changed_fields": ["portal_enabled", "user_id"]},
            )
        return self._serialize_contact(row, actor)

    def update_contact(
        self,
        tenant_id: str,
        subcontractor_id: str,
        contact_id: str,
        payload: SubcontractorContactUpdate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorContactRead:
        self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        current = self.repository.get_contact(tenant_id, subcontractor_id, contact_id)
        if current is None:
            raise self._not_found("contact")
        before_json = self._contact_snapshot(current)
        effective_payload = SubcontractorContactCreate(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            full_name=self._field_value(payload, "full_name", current.full_name),
            title=self._field_value(payload, "title", current.title),
            function_label=self._field_value(payload, "function_label", current.function_label),
            email=self._field_value(payload, "email", current.email),
            phone=self._field_value(payload, "phone", current.phone),
            mobile=self._field_value(payload, "mobile", current.mobile),
            is_primary_contact=self._field_value(payload, "is_primary_contact", current.is_primary_contact),
            portal_enabled=self._field_value(payload, "portal_enabled", current.portal_enabled),
            user_id=self._field_value(payload, "user_id", current.user_id),
            notes=self._field_value(payload, "notes", current.notes),
        )
        self._validate_contact_constraints(tenant_id, subcontractor_id, effective_payload, exclude_id=contact_id)
        row = self.repository.update_contact(tenant_id, subcontractor_id, contact_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("contact")
        after_json = self._contact_snapshot(row)
        changed_fields = self._changed_fields(before_json, after_json)
        self._record_event(
            actor,
            "subcontractors.contact.updated",
            "partner.subcontractor_contact",
            row.id,
            tenant_id,
            before_json=before_json,
            after_json=after_json,
            metadata_json={"subcontractor_id": subcontractor_id, "changed_fields": changed_fields},
        )
        if {"portal_enabled", "user_id"} & set(changed_fields):
            self._record_event(
                actor,
                "subcontractors.contact.portal_link_changed",
                "partner.subcontractor_contact",
                row.id,
                tenant_id,
                before_json=before_json,
                after_json=after_json,
                metadata_json={"subcontractor_id": subcontractor_id, "changed_fields": changed_fields},
            )
        return self._serialize_contact(row, actor)

    def list_scopes(self, tenant_id: str, subcontractor_id: str, actor: RequestAuthorizationContext) -> list[SubcontractorScopeRead]:
        self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        return [SubcontractorScopeRead.model_validate(row) for row in self.repository.list_scopes(tenant_id, subcontractor_id)]

    def create_scope(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorScopeCreate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorScopeRead:
        self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        self._validate_scope_path(tenant_id, subcontractor_id, payload)
        self._validate_scope_constraints(tenant_id, subcontractor_id, payload)
        row = self.repository.create_scope(tenant_id, subcontractor_id, payload, actor.user_id)
        self._record_event(actor, "subcontractors.scope.created", "partner.subcontractor_scope", row.id, tenant_id)
        return SubcontractorScopeRead.model_validate(row)

    def update_scope(
        self,
        tenant_id: str,
        subcontractor_id: str,
        scope_id: str,
        payload: SubcontractorScopeUpdate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorScopeRead:
        self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        current = self.repository.get_scope(tenant_id, subcontractor_id, scope_id)
        if current is None:
            raise self._not_found("scope")
        effective = SubcontractorScopeCreate(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            branch_id=self._field_value(payload, "branch_id", current.branch_id),
            mandate_id=self._field_value(payload, "mandate_id", current.mandate_id),
            valid_from=self._field_value(payload, "valid_from", current.valid_from),
            valid_to=self._field_value(payload, "valid_to", current.valid_to),
            notes=self._field_value(payload, "notes", current.notes),
        )
        self._validate_scope_constraints(tenant_id, subcontractor_id, effective, exclude_id=scope_id)
        row = self.repository.update_scope(tenant_id, subcontractor_id, scope_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("scope")
        self._record_event(actor, "subcontractors.scope.updated", "partner.subcontractor_scope", row.id, tenant_id)
        return SubcontractorScopeRead.model_validate(row)

    def get_finance_profile(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorFinanceProfileRead:
        self._require_subcontractor_for_read(tenant_id, subcontractor_id, actor)
        row = self.repository.get_finance_profile(tenant_id, subcontractor_id)
        if row is None:
            raise self._not_found("finance_profile")
        return SubcontractorFinanceProfileRead.model_validate(row)

    def upsert_finance_profile(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorFinanceProfileCreate | SubcontractorFinanceProfileUpdate,
        actor: RequestAuthorizationContext,
    ) -> SubcontractorFinanceProfileRead:
        self._require_subcontractor_for_write(tenant_id, subcontractor_id, actor)
        self._validate_finance_path(tenant_id, subcontractor_id, payload)
        effective = payload
        existing = self.repository.get_finance_profile(tenant_id, subcontractor_id)
        before_json = self._finance_snapshot(existing) if existing is not None else None
        if isinstance(payload, SubcontractorFinanceProfileUpdate) and existing is not None:
            effective = SubcontractorFinanceProfileCreate(
                tenant_id=tenant_id,
                subcontractor_id=subcontractor_id,
                invoice_email=self._field_value(payload, "invoice_email", existing.invoice_email),
                payment_terms_days=self._field_value(payload, "payment_terms_days", existing.payment_terms_days),
                payment_terms_note=self._field_value(payload, "payment_terms_note", existing.payment_terms_note),
                tax_number=self._field_value(payload, "tax_number", existing.tax_number),
                vat_id=self._field_value(payload, "vat_id", existing.vat_id),
                bank_account_holder=self._field_value(payload, "bank_account_holder", existing.bank_account_holder),
                bank_iban=self._field_value(payload, "bank_iban", existing.bank_iban),
                bank_bic=self._field_value(payload, "bank_bic", existing.bank_bic),
                bank_name=self._field_value(payload, "bank_name", existing.bank_name),
                invoice_delivery_method_lookup_id=self._field_value(
                    payload,
                    "invoice_delivery_method_lookup_id",
                    existing.invoice_delivery_method_lookup_id,
                ),
                invoice_status_mode_lookup_id=self._field_value(
                    payload,
                    "invoice_status_mode_lookup_id",
                    existing.invoice_status_mode_lookup_id,
                ),
                billing_note=self._field_value(payload, "billing_note", existing.billing_note),
            )
        self._validate_finance_constraints(tenant_id, effective)
        if existing is None:
            if not isinstance(payload, SubcontractorFinanceProfileCreate):
                raise self._not_found("finance_profile")
            row = self.repository.create_finance_profile(tenant_id, subcontractor_id, payload, actor.user_id)
            self._record_event(
                actor,
                "subcontractors.finance.created",
                "partner.subcontractor_finance_profile",
                row.id,
                tenant_id,
                after_json=self._finance_snapshot(row),
                metadata_json={"subcontractor_id": subcontractor_id},
            )
            return SubcontractorFinanceProfileRead.model_validate(row)
        row = self.repository.update_finance_profile(tenant_id, subcontractor_id, payload, actor.user_id)
        if row is None:
            raise self._not_found("finance_profile")
        after_json = self._finance_snapshot(row)
        self._record_event(
            actor,
            "subcontractors.finance.updated",
            "partner.subcontractor_finance_profile",
            row.id,
            tenant_id,
            before_json=before_json,
            after_json=after_json,
            metadata_json={"subcontractor_id": subcontractor_id, "changed_fields": self._changed_fields(before_json or {}, after_json)},
        )
        return SubcontractorFinanceProfileRead.model_validate(row)

    def _validate_subcontractor_payload(self, tenant_id: str, payload: SubcontractorCreate) -> None:
        if payload.address_id is not None and self.repository.get_address(payload.address_id) is None:
            raise ApiException(404, "subcontractors.validation.address_not_found", "errors.subcontractors.subcontractor.address_not_found")
        self._validate_lookup(tenant_id, payload.legal_form_lookup_id, "legal_form_lookup_id")
        self._validate_lookup(tenant_id, payload.subcontractor_status_lookup_id, "subcontractor_status_lookup_id")

    def _validate_contact_path(self, tenant_id: str, subcontractor_id: str, payload: SubcontractorContactCreate) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "subcontractors.validation.contact_tenant_mismatch", "errors.subcontractors.contact.tenant_mismatch")
        if payload.subcontractor_id != subcontractor_id:
            raise ApiException(
                400,
                "subcontractors.validation.contact_company_mismatch",
                "errors.subcontractors.contact.subcontractor_mismatch",
            )

    def _validate_contact_constraints(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorContactCreate,
        *,
        exclude_id: str | None = None,
    ) -> None:
        if payload.is_primary_contact and self.repository.has_primary_contact(tenant_id, subcontractor_id, exclude_id=exclude_id):
            raise ApiException(409, "subcontractors.conflict.primary_contact", "errors.subcontractors.contact.primary_conflict")
        if payload.user_id is not None:
            user = self.repository.get_user_account(tenant_id, payload.user_id)
            if user is None:
                raise ApiException(404, "subcontractors.validation.user_not_found", "errors.subcontractors.contact.user_not_found")
            duplicate = self.repository.find_contact_by_user_id(tenant_id, payload.user_id, exclude_id=exclude_id)
            if duplicate is not None:
                raise ApiException(409, "subcontractors.conflict.user_link", "errors.subcontractors.contact.duplicate_user_link")
        if payload.portal_enabled and payload.user_id is None:
            raise ApiException(400, "subcontractors.validation.portal_user_required", "errors.subcontractors.contact.portal_user_required")

    def _validate_scope_path(self, tenant_id: str, subcontractor_id: str, payload: SubcontractorScopeCreate) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "subcontractors.validation.scope_tenant_mismatch", "errors.subcontractors.scope.tenant_mismatch")
        if payload.subcontractor_id != subcontractor_id:
            raise ApiException(400, "subcontractors.validation.scope_company_mismatch", "errors.subcontractors.scope.subcontractor_mismatch")

    def _validate_scope_constraints(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorScopeCreate,
        *,
        exclude_id: str | None = None,
    ) -> None:
        branch = self.repository.get_branch(tenant_id, payload.branch_id)
        if branch is None:
            raise ApiException(404, "subcontractors.validation.branch_not_found", "errors.subcontractors.scope.branch_not_found")
        if payload.valid_to is not None and payload.valid_to < payload.valid_from:
            raise ApiException(400, "subcontractors.validation.scope_window_invalid", "errors.subcontractors.scope.invalid_window")
        if payload.mandate_id is not None:
            mandate = self.repository.get_mandate(tenant_id, payload.mandate_id)
            if mandate is None:
                raise ApiException(404, "subcontractors.validation.mandate_not_found", "errors.subcontractors.scope.mandate_not_found")
            if mandate.branch_id != branch.id:
                raise ApiException(400, "subcontractors.validation.scope_branch_mismatch", "errors.subcontractors.scope.mandate_branch_mismatch")
        overlap = self.repository.find_overlapping_scope(
            tenant_id,
            subcontractor_id,
            payload.branch_id,
            payload.mandate_id,
            payload.valid_from,
            payload.valid_to,
            exclude_id=exclude_id,
        )
        if overlap is not None:
            raise ApiException(409, "subcontractors.conflict.scope_overlap", "errors.subcontractors.scope.overlap")

    def _validate_finance_path(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorFinanceProfileCreate | SubcontractorFinanceProfileUpdate,
    ) -> None:
        if isinstance(payload, SubcontractorFinanceProfileCreate):
            if payload.tenant_id != tenant_id:
                raise ApiException(400, "subcontractors.validation.finance_tenant_mismatch", "errors.subcontractors.finance_profile.tenant_mismatch")
            if payload.subcontractor_id != subcontractor_id:
                raise ApiException(
                    400,
                    "subcontractors.validation.finance_company_mismatch",
                    "errors.subcontractors.finance_profile.subcontractor_mismatch",
                )

    def _validate_finance_constraints(self, tenant_id: str, payload: SubcontractorFinanceProfileCreate) -> None:
        self._validate_lookup(tenant_id, payload.invoice_delivery_method_lookup_id, "invoice_delivery_method_lookup_id")
        self._validate_lookup(tenant_id, payload.invoice_status_mode_lookup_id, "invoice_status_mode_lookup_id")

    def _validate_lookup(self, tenant_id: str, lookup_id: str | None, field_name: str) -> None:
        if lookup_id is None:
            return
        lookup = self.repository.get_lookup_value(lookup_id)
        if lookup is None:
            raise ApiException(404, "subcontractors.validation.lookup_not_found", "errors.subcontractors.lookup.not_found")
        expected_domain = self.LOOKUP_DOMAINS[field_name]
        if lookup.domain != expected_domain:
            raise ApiException(400, "subcontractors.validation.lookup_invalid_domain", "errors.subcontractors.lookup.invalid_domain")
        if lookup.tenant_id not in (None, tenant_id):
            raise ApiException(400, "subcontractors.validation.lookup_scope_mismatch", "errors.subcontractors.lookup.scope_mismatch")

    def _require_subcontractor_for_read(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
    ) -> Subcontractor:
        row = self.repository.get_subcontractor(tenant_id, subcontractor_id)
        if row is None:
            raise self._not_found("subcontractor")
        enforce_subcontractor_internal_read_access(actor, tenant_id=tenant_id, subcontractor=row)
        return row

    def _require_subcontractor_for_write(
        self,
        tenant_id: str,
        subcontractor_id: str,
        actor: RequestAuthorizationContext,
    ) -> Subcontractor:
        enforce_subcontractor_internal_write_access(actor, tenant_id=tenant_id)
        row = self.repository.get_subcontractor(tenant_id, subcontractor_id)
        if row is None:
            raise self._not_found("subcontractor")
        return row

    @staticmethod
    def _not_found(entity_name: str) -> ApiException:
        return ApiException(404, f"subcontractors.{entity_name}.not_found", f"errors.subcontractors.{entity_name}.not_found")

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
        event_type: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        *,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
    ) -> None:
        if self.audit_service is None:
            return
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=tenant_id,
                user_id=actor.user_id,
                session_id=actor.session_id,
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
    def _field_value(payload, field_name: str, current_value):  # noqa: ANN001
        if field_name in payload.model_fields_set:
            return getattr(payload, field_name)
        return current_value

    def _serialize_subcontractor(self, row: Subcontractor, actor: RequestAuthorizationContext) -> SubcontractorRead:
        contact_reads = [self._serialize_contact(contact, actor) for contact in row.contacts]
        finance_profile = (
            SubcontractorFinanceProfileRead.model_validate(row.finance_profile)
            if row.finance_profile is not None and actor.has_permission("subcontractors.finance.read")
            else None
        )
        return SubcontractorRead.model_validate(row).model_copy(
            update={"contacts": contact_reads, "finance_profile": finance_profile}
        )

    @staticmethod
    def _serialize_contact(row: SubcontractorContact, actor: RequestAuthorizationContext) -> SubcontractorContactRead:
        update: dict[str, object] = {}
        if not actor.has_permission("subcontractors.company.write"):
            update["user_id"] = None
        return SubcontractorContactRead.model_validate(row).model_copy(update=update)

    @staticmethod
    def _enforce_internal_reference_read_access(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.is_platform_admin:
            return
        if actor.tenant_id != tenant_id:
            raise ApiException(
                403,
                "iam.authorization.scope_denied",
                "errors.iam.authorization.scope_denied",
                {"tenant_id": tenant_id},
            )
        if actor.role_keys & PORTAL_ROLE_KEYS:
            raise ApiException(
                403,
                "subcontractors.authorization.portal_forbidden",
                "errors.subcontractors.authorization.portal_forbidden",
                {"privacy_boundary": SUBCONTRACTOR_PORTAL_BOUNDARY},
            )
        if not any(scope.scope_type in {"tenant", "branch", "mandate", "subcontractor"} for scope in actor.scopes):
            raise ApiException(
                403,
                "subcontractors.authorization.internal_scope_required",
                "errors.subcontractors.authorization.internal_scope_required",
                {"tenant_id": tenant_id},
            )

    @staticmethod
    def _serialize_reference_option(row: LookupValue) -> SubcontractorReferenceOptionRead:
        return SubcontractorReferenceOptionRead(
            id=row.id,
            code=row.code,
            label=row.label or row.code,
            description=row.description,
            is_active=row.status == "active" and row.archived_at is None,
            status=row.status,
            archived_at=row.archived_at,
        )

    @staticmethod
    def _subcontractor_snapshot(row: Subcontractor) -> dict[str, object]:
        return {
            "subcontractor_number": row.subcontractor_number,
            "legal_name": row.legal_name,
            "display_name": row.display_name,
            "legal_form_lookup_id": row.legal_form_lookup_id,
            "subcontractor_status_lookup_id": row.subcontractor_status_lookup_id,
            "managing_director_name": row.managing_director_name,
            "address_id": row.address_id,
            "status": row.status,
            "archived_at": row.archived_at.isoformat() if row.archived_at else None,
            "version_no": row.version_no,
        }

    @staticmethod
    def _contact_snapshot(row: SubcontractorContact) -> dict[str, object]:
        return {
            "full_name": row.full_name,
            "email": row.email,
            "phone": row.phone,
            "mobile": row.mobile,
            "is_primary_contact": row.is_primary_contact,
            "portal_enabled": row.portal_enabled,
            "user_id": row.user_id,
            "status": row.status,
        }

    @staticmethod
    def _finance_snapshot(row: SubcontractorFinanceProfile | None) -> dict[str, object]:
        if row is None:
            return {}
        iban = (row.bank_iban or "").strip()
        return {
            "invoice_email": row.invoice_email,
            "payment_terms_days": row.payment_terms_days,
            "payment_terms_note": row.payment_terms_note,
            "tax_number_present": bool(row.tax_number),
            "vat_id_present": bool(row.vat_id),
            "bank_account_holder": row.bank_account_holder,
            "bank_iban_last4": iban[-4:] if iban else None,
            "bank_bic_present": bool(row.bank_bic),
            "bank_name": row.bank_name,
            "invoice_delivery_method_lookup_id": row.invoice_delivery_method_lookup_id,
            "invoice_status_mode_lookup_id": row.invoice_status_mode_lookup_id,
            "billing_note_present": bool(row.billing_note),
            "status": row.status,
            "version_no": row.version_no,
        }

    @staticmethod
    def _changed_fields(before_json: dict[str, object], after_json: dict[str, object]) -> list[str]:
        return [key for key, value in after_json.items() if before_json.get(key) != value]
