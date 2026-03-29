"""Service layer for CRM-owned customer commercial settings."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.errors import ApiException
from app.modules.customers.models import (
    CustomerBillingProfile,
    CustomerInvoiceParty,
    CustomerRateCard,
    CustomerRateLine,
    CustomerSurchargeRule,
)
from app.modules.customers.policy import enforce_customer_module_access
from app.modules.customers.schemas import (
    CustomerBillingProfileCreate,
    CustomerBillingProfileRead,
    CustomerBillingProfileUpdate,
    CustomerCommercialProfileRead,
    CustomerInvoicePartyCreate,
    CustomerInvoicePartyRead,
    CustomerInvoicePartyUpdate,
    CustomerPricingProfileRead,
    CustomerRateCardCreate,
    CustomerRateCardRead,
    CustomerRateCardUpdate,
    CustomerRateLineCreate,
    CustomerRateLineRead,
    CustomerRateLineUpdate,
    CustomerSurchargeRuleCreate,
    CustomerSurchargeRuleRead,
    CustomerSurchargeRuleUpdate,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext


class CustomerCommercialRepository(Protocol):
    def get_customer(self, tenant_id: str, customer_id: str): ...  # noqa: ANN001
    def get_billing_profile(self, tenant_id: str, customer_id: str) -> CustomerBillingProfile | None: ...
    def create_billing_profile(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerBillingProfileCreate,
        actor_user_id: str | None,
    ) -> CustomerBillingProfile: ...
    def update_billing_profile(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerBillingProfileUpdate,
        actor_user_id: str | None,
    ) -> CustomerBillingProfile | None: ...
    def list_invoice_parties(self, tenant_id: str, customer_id: str) -> list[CustomerInvoiceParty]: ...
    def get_invoice_party(self, tenant_id: str, customer_id: str, invoice_party_id: str) -> CustomerInvoiceParty | None: ...
    def create_invoice_party(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerInvoicePartyCreate,
        actor_user_id: str | None,
    ) -> CustomerInvoiceParty: ...
    def update_invoice_party(
        self,
        tenant_id: str,
        customer_id: str,
        invoice_party_id: str,
        payload: CustomerInvoicePartyUpdate,
        actor_user_id: str | None,
    ) -> CustomerInvoiceParty | None: ...
    def has_default_invoice_party(self, tenant_id: str, customer_id: str, *, exclude_id: str | None = None) -> bool: ...
    def list_rate_cards(self, tenant_id: str, customer_id: str) -> list[CustomerRateCard]: ...
    def get_rate_card(self, tenant_id: str, customer_id: str, rate_card_id: str) -> CustomerRateCard | None: ...
    def create_rate_card(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerRateCardCreate,
        actor_user_id: str | None,
    ) -> CustomerRateCard: ...
    def update_rate_card(
        self,
        tenant_id: str,
        customer_id: str,
        rate_card_id: str,
        payload: CustomerRateCardUpdate,
        actor_user_id: str | None,
    ) -> CustomerRateCard | None: ...
    def list_overlapping_rate_cards(
        self,
        tenant_id: str,
        customer_id: str,
        *,
        rate_kind: str,
        effective_from: date,
        effective_to: date | None,
        exclude_id: str | None = None,
    ) -> list[CustomerRateCard]: ...
    def list_rate_lines(self, tenant_id: str, rate_card_id: str) -> list[CustomerRateLine]: ...
    def get_rate_line(self, tenant_id: str, rate_card_id: str, rate_line_id: str) -> CustomerRateLine | None: ...
    def create_rate_line(
        self,
        tenant_id: str,
        rate_card_id: str,
        payload: CustomerRateLineCreate,
        actor_user_id: str | None,
    ) -> CustomerRateLine: ...
    def update_rate_line(
        self,
        tenant_id: str,
        rate_card_id: str,
        rate_line_id: str,
        payload: CustomerRateLineUpdate,
        actor_user_id: str | None,
    ) -> CustomerRateLine | None: ...
    def find_duplicate_rate_line(
        self,
        tenant_id: str,
        rate_card_id: str,
        *,
        line_kind: str,
        function_type_id: str | None,
        qualification_type_id: str | None,
        planning_mode_code: str | None,
        billing_unit: str,
        exclude_id: str | None = None,
    ) -> CustomerRateLine | None: ...
    def list_surcharge_rules(self, tenant_id: str, rate_card_id: str) -> list[CustomerSurchargeRule]: ...
    def get_surcharge_rule(
        self,
        tenant_id: str,
        rate_card_id: str,
        surcharge_rule_id: str,
    ) -> CustomerSurchargeRule | None: ...
    def create_surcharge_rule(
        self,
        tenant_id: str,
        rate_card_id: str,
        payload: CustomerSurchargeRuleCreate,
        actor_user_id: str | None,
    ) -> CustomerSurchargeRule: ...
    def update_surcharge_rule(
        self,
        tenant_id: str,
        rate_card_id: str,
        surcharge_rule_id: str,
        payload: CustomerSurchargeRuleUpdate,
        actor_user_id: str | None,
    ) -> CustomerSurchargeRule | None: ...
    def get_lookup_value(self, lookup_id: str): ...  # noqa: ANN001
    def find_lookup_by_domain_code(self, tenant_id: str | None, domain: str, code: str): ...  # noqa: ANN001
    def get_address(self, address_id: str): ...  # noqa: ANN001


class CustomerCommercialService:
    def __init__(self, repository: CustomerCommercialRepository, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def get_commercial_profile(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> CustomerCommercialProfileRead:
        self._require_customer(tenant_id, customer_id, actor)
        billing_profile = self.repository.get_billing_profile(tenant_id, customer_id)
        invoice_parties = self.repository.list_invoice_parties(tenant_id, customer_id)
        return CustomerCommercialProfileRead(
            customer_id=customer_id,
            tenant_id=tenant_id,
            billing_profile=CustomerBillingProfileRead.model_validate(billing_profile) if billing_profile else None,
            invoice_parties=[CustomerInvoicePartyRead.model_validate(row) for row in invoice_parties],
            rate_cards=[CustomerRateCardRead.model_validate(row) for row in self.repository.list_rate_cards(tenant_id, customer_id)],
        )

    def get_pricing_profile(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> CustomerPricingProfileRead:
        self._require_customer(tenant_id, customer_id, actor)
        return CustomerPricingProfileRead(
            tenant_id=tenant_id,
            customer_id=customer_id,
            rate_cards=[CustomerRateCardRead.model_validate(row) for row in self.repository.list_rate_cards(tenant_id, customer_id)],
        )

    def upsert_billing_profile(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerBillingProfileCreate | CustomerBillingProfileUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerBillingProfileRead:
        self._require_customer(tenant_id, customer_id, actor)
        self._validate_billing_profile_path(tenant_id, customer_id, payload)
        normalized = self._normalize_billing_profile(payload)
        existing = self.repository.get_billing_profile(tenant_id, customer_id)
        if existing is None:
            self._validate_billing_profile(tenant_id, customer_id, normalized)
            if not isinstance(normalized, CustomerBillingProfileCreate):
                raise ApiException(
                    404,
                    "customers.not_found.billing_profile",
                    "errors.customers.billing_profile.not_found",
                )
            profile = self.repository.create_billing_profile(tenant_id, customer_id, normalized, actor.user_id)
            self._record_event(
                actor,
                event_type="customers.billing_profile.created",
                entity_type="crm.customer_billing_profile",
                entity_id=profile.id,
                tenant_id=tenant_id,
                after_json=self._billing_profile_audit_snapshot(profile),
                metadata_json={"customer_id": customer_id},
            )
            return CustomerBillingProfileRead.model_validate(profile)

        if not isinstance(normalized, CustomerBillingProfileUpdate):
            normalized = CustomerBillingProfileUpdate(**normalized.model_dump(), version_no=existing.version_no)
        self._validate_billing_profile(tenant_id, customer_id, self._merge_billing_profile(existing, normalized))
        before_json = self._billing_profile_audit_snapshot(existing)
        profile = self.repository.update_billing_profile(tenant_id, customer_id, normalized, actor.user_id)
        if profile is None:
            raise ApiException(404, "customers.not_found.billing_profile", "errors.customers.billing_profile.not_found")
        self._record_event(
            actor,
            event_type="customers.billing_profile.updated",
            entity_type="crm.customer_billing_profile",
            entity_id=profile.id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=self._billing_profile_audit_snapshot(profile),
            metadata_json={"customer_id": customer_id},
        )
        return CustomerBillingProfileRead.model_validate(profile)

    def list_invoice_parties(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerInvoicePartyRead]:
        self._require_customer(tenant_id, customer_id, actor)
        return [
            CustomerInvoicePartyRead.model_validate(row)
            for row in self.repository.list_invoice_parties(tenant_id, customer_id)
        ]

    def create_invoice_party(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerInvoicePartyCreate,
        actor: RequestAuthorizationContext,
    ) -> CustomerInvoicePartyRead:
        self._require_customer(tenant_id, customer_id, actor)
        self._validate_invoice_party_path(tenant_id, customer_id, payload)
        self._validate_invoice_party(tenant_id, customer_id, payload)
        party = self.repository.create_invoice_party(tenant_id, customer_id, payload, actor.user_id)
        self._record_event(
            actor,
            event_type="customers.invoice_party.created",
            entity_type="crm.customer_invoice_party",
            entity_id=party.id,
            tenant_id=tenant_id,
            after_json=self._invoice_party_snapshot(party),
            metadata_json={"customer_id": customer_id},
        )
        return CustomerInvoicePartyRead.model_validate(party)

    def update_invoice_party(
        self,
        tenant_id: str,
        customer_id: str,
        invoice_party_id: str,
        payload: CustomerInvoicePartyUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerInvoicePartyRead:
        self._require_customer(tenant_id, customer_id, actor)
        existing = self.repository.get_invoice_party(tenant_id, customer_id, invoice_party_id)
        if existing is None:
            raise ApiException(404, "customers.not_found.invoice_party", "errors.customers.invoice_party.not_found")
        if payload.version_no is None or payload.version_no != existing.version_no:
            raise ApiException(
                409,
                "customers.conflict.stale_invoice_party_version",
                "errors.customers.invoice_party.stale_version",
                {"expected_version_no": existing.version_no},
            )
        normalized = self._normalize_invoice_party(existing, payload)
        self._validate_invoice_party(tenant_id, customer_id, normalized, exclude_invoice_party_id=invoice_party_id)
        before_json = self._invoice_party_snapshot(existing)
        updated = self.repository.update_invoice_party(tenant_id, customer_id, invoice_party_id, payload, actor.user_id)
        if updated is None:
            raise ApiException(404, "customers.not_found.invoice_party", "errors.customers.invoice_party.not_found")
        self._record_event(
            actor,
            event_type="customers.invoice_party.updated",
            entity_type="crm.customer_invoice_party",
            entity_id=updated.id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=self._invoice_party_snapshot(updated),
            metadata_json={"customer_id": customer_id},
        )
        return CustomerInvoicePartyRead.model_validate(updated)

    def list_rate_cards(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerRateCardRead]:
        self._require_customer(tenant_id, customer_id, actor)
        return [CustomerRateCardRead.model_validate(row) for row in self.repository.list_rate_cards(tenant_id, customer_id)]

    def create_rate_card(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerRateCardCreate,
        actor: RequestAuthorizationContext,
    ) -> CustomerRateCardRead:
        self._require_customer(tenant_id, customer_id, actor)
        normalized = self._canonicalize_rate_card(payload)
        self._validate_rate_card_path(tenant_id, customer_id, normalized)
        self._validate_rate_card(tenant_id, customer_id, normalized)
        row = self.repository.create_rate_card(tenant_id, customer_id, normalized, actor.user_id)
        self._record_event(
            actor,
            event_type="customers.rate_card.created",
            entity_type="crm.customer_rate_card",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._rate_card_snapshot(row),
            metadata_json={"customer_id": customer_id},
        )
        return CustomerRateCardRead.model_validate(row)

    def update_rate_card(
        self,
        tenant_id: str,
        customer_id: str,
        rate_card_id: str,
        payload: CustomerRateCardUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerRateCardRead:
        self._require_customer(tenant_id, customer_id, actor)
        existing = self.repository.get_rate_card(tenant_id, customer_id, rate_card_id)
        if existing is None:
            raise ApiException(404, "customers.not_found.rate_card", "errors.customers.rate_card.not_found")
        if payload.version_no is None or payload.version_no != existing.version_no:
            raise ApiException(
                409,
                "customers.conflict.stale_rate_card_version",
                "errors.customers.rate_card.stale_version",
                {"expected_version_no": existing.version_no},
            )
        normalized = self._canonicalize_rate_card(self._normalize_rate_card(existing, payload))
        self._validate_rate_card(tenant_id, customer_id, normalized, exclude_rate_card_id=rate_card_id)
        before_json = self._rate_card_snapshot(existing)
        updated = self.repository.update_rate_card(
            tenant_id,
            customer_id,
            rate_card_id,
            CustomerRateCardUpdate(**normalized.model_dump(), version_no=payload.version_no),
            actor.user_id,
        )
        if updated is None:
            raise ApiException(404, "customers.not_found.rate_card", "errors.customers.rate_card.not_found")
        self._record_event(
            actor,
            event_type="customers.rate_card.updated",
            entity_type="crm.customer_rate_card",
            entity_id=updated.id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=self._rate_card_snapshot(updated),
            metadata_json={"customer_id": customer_id},
        )
        return CustomerRateCardRead.model_validate(updated)

    def list_rate_lines(
        self,
        tenant_id: str,
        customer_id: str,
        rate_card_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerRateLineRead]:
        self._require_rate_card(tenant_id, customer_id, rate_card_id, actor)
        return [CustomerRateLineRead.model_validate(row) for row in self.repository.list_rate_lines(tenant_id, rate_card_id)]

    def create_rate_line(
        self,
        tenant_id: str,
        customer_id: str,
        rate_card_id: str,
        payload: CustomerRateLineCreate,
        actor: RequestAuthorizationContext,
    ) -> CustomerRateLineRead:
        rate_card = self._require_rate_card(tenant_id, customer_id, rate_card_id, actor)
        normalized = self._canonicalize_rate_line(payload)
        self._validate_rate_line_path(tenant_id, rate_card_id, normalized)
        self._validate_rate_line(tenant_id, rate_card, normalized)
        row = self.repository.create_rate_line(tenant_id, rate_card_id, normalized, actor.user_id)
        self._record_event(
            actor,
            event_type="customers.rate_line.created",
            entity_type="crm.customer_rate_line",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._rate_line_snapshot(row),
            metadata_json={"customer_id": customer_id, "rate_card_id": rate_card_id},
        )
        return CustomerRateLineRead.model_validate(row)

    def update_rate_line(
        self,
        tenant_id: str,
        customer_id: str,
        rate_card_id: str,
        rate_line_id: str,
        payload: CustomerRateLineUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerRateLineRead:
        rate_card = self._require_rate_card(tenant_id, customer_id, rate_card_id, actor)
        existing = self.repository.get_rate_line(tenant_id, rate_card_id, rate_line_id)
        if existing is None:
            raise ApiException(404, "customers.not_found.rate_line", "errors.customers.rate_line.not_found")
        if payload.version_no is None or payload.version_no != existing.version_no:
            raise ApiException(
                409,
                "customers.conflict.stale_rate_line_version",
                "errors.customers.rate_line.stale_version",
                {"expected_version_no": existing.version_no},
            )
        normalized = self._canonicalize_rate_line(self._normalize_rate_line(existing, payload))
        self._validate_rate_line(tenant_id, rate_card, normalized, exclude_rate_line_id=rate_line_id)
        before_json = self._rate_line_snapshot(existing)
        updated = self.repository.update_rate_line(
            tenant_id,
            rate_card_id,
            rate_line_id,
            CustomerRateLineUpdate(**normalized.model_dump(), version_no=payload.version_no),
            actor.user_id,
        )
        if updated is None:
            raise ApiException(404, "customers.not_found.rate_line", "errors.customers.rate_line.not_found")
        self._record_event(
            actor,
            event_type="customers.rate_line.updated",
            entity_type="crm.customer_rate_line",
            entity_id=updated.id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=self._rate_line_snapshot(updated),
            metadata_json={"customer_id": customer_id, "rate_card_id": rate_card_id},
        )
        return CustomerRateLineRead.model_validate(updated)

    def list_surcharge_rules(
        self,
        tenant_id: str,
        customer_id: str,
        rate_card_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerSurchargeRuleRead]:
        self._require_rate_card(tenant_id, customer_id, rate_card_id, actor)
        return [
            CustomerSurchargeRuleRead.model_validate(row)
            for row in self.repository.list_surcharge_rules(tenant_id, rate_card_id)
        ]

    def create_surcharge_rule(
        self,
        tenant_id: str,
        customer_id: str,
        rate_card_id: str,
        payload: CustomerSurchargeRuleCreate,
        actor: RequestAuthorizationContext,
    ) -> CustomerSurchargeRuleRead:
        rate_card = self._require_rate_card(tenant_id, customer_id, rate_card_id, actor)
        normalized = self._canonicalize_surcharge_rule(payload)
        self._validate_surcharge_rule_path(tenant_id, rate_card_id, normalized)
        self._validate_surcharge_rule(rate_card, normalized)
        row = self.repository.create_surcharge_rule(tenant_id, rate_card_id, normalized, actor.user_id)
        self._record_event(
            actor,
            event_type="customers.surcharge_rule.created",
            entity_type="crm.customer_surcharge_rule",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=self._surcharge_rule_snapshot(row),
            metadata_json={"customer_id": customer_id, "rate_card_id": rate_card_id},
        )
        return CustomerSurchargeRuleRead.model_validate(row)

    def update_surcharge_rule(
        self,
        tenant_id: str,
        customer_id: str,
        rate_card_id: str,
        surcharge_rule_id: str,
        payload: CustomerSurchargeRuleUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerSurchargeRuleRead:
        rate_card = self._require_rate_card(tenant_id, customer_id, rate_card_id, actor)
        existing = self.repository.get_surcharge_rule(tenant_id, rate_card_id, surcharge_rule_id)
        if existing is None:
            raise ApiException(404, "customers.not_found.surcharge_rule", "errors.customers.surcharge_rule.not_found")
        if payload.version_no is None or payload.version_no != existing.version_no:
            raise ApiException(
                409,
                "customers.conflict.stale_surcharge_rule_version",
                "errors.customers.surcharge_rule.stale_version",
                {"expected_version_no": existing.version_no},
            )
        normalized = self._canonicalize_surcharge_rule(self._normalize_surcharge_rule(existing, payload))
        self._validate_surcharge_rule(rate_card, normalized)
        before_json = self._surcharge_rule_snapshot(existing)
        updated = self.repository.update_surcharge_rule(
            tenant_id,
            rate_card_id,
            surcharge_rule_id,
            CustomerSurchargeRuleUpdate(**normalized.model_dump(), version_no=payload.version_no),
            actor.user_id,
        )
        if updated is None:
            raise ApiException(404, "customers.not_found.surcharge_rule", "errors.customers.surcharge_rule.not_found")
        self._record_event(
            actor,
            event_type="customers.surcharge_rule.updated",
            entity_type="crm.customer_surcharge_rule",
            entity_id=updated.id,
            tenant_id=tenant_id,
            before_json=before_json,
            after_json=self._surcharge_rule_snapshot(updated),
            metadata_json={"customer_id": customer_id, "rate_card_id": rate_card_id},
        )
        return CustomerSurchargeRuleRead.model_validate(updated)

    def _require_customer(self, tenant_id: str, customer_id: str, actor: RequestAuthorizationContext) -> None:
        enforce_customer_module_access(actor, tenant_id=tenant_id)
        customer = self.repository.get_customer(tenant_id, customer_id)
        if customer is None:
            raise ApiException(404, "customers.not_found.customer", "errors.customers.customer.not_found")

    def _require_rate_card(
        self,
        tenant_id: str,
        customer_id: str,
        rate_card_id: str,
        actor: RequestAuthorizationContext,
    ) -> CustomerRateCard:
        self._require_customer(tenant_id, customer_id, actor)
        rate_card = self.repository.get_rate_card(tenant_id, customer_id, rate_card_id)
        if rate_card is None:
            raise ApiException(404, "customers.not_found.rate_card", "errors.customers.rate_card.not_found")
        return rate_card

    @staticmethod
    def _validate_billing_profile_path(
        tenant_id: str,
        customer_id: str,
        payload: CustomerBillingProfileCreate | CustomerBillingProfileUpdate,
    ) -> None:
        if isinstance(payload, CustomerBillingProfileCreate):
            if payload.tenant_id != tenant_id:
                raise ApiException(
                    400,
                    "customers.validation.billing_profile_tenant_mismatch",
                    "errors.customers.billing_profile.tenant_mismatch",
                    {"tenant_id": tenant_id},
                )
            if payload.customer_id != customer_id:
                raise ApiException(
                    400,
                    "customers.validation.billing_profile_customer_mismatch",
                    "errors.customers.billing_profile.customer_mismatch",
                    {"customer_id": customer_id},
                )

    @staticmethod
    def _validate_invoice_party_path(tenant_id: str, customer_id: str, payload: CustomerInvoicePartyCreate) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "customers.validation.invoice_party_tenant_mismatch",
                "errors.customers.invoice_party.tenant_mismatch",
                {"tenant_id": tenant_id},
            )
        if payload.customer_id != customer_id:
            raise ApiException(
                400,
                "customers.validation.invoice_party_customer_mismatch",
                "errors.customers.invoice_party.customer_mismatch",
                {"customer_id": customer_id},
            )

    @staticmethod
    def _normalize_billing_profile(payload: CustomerBillingProfileCreate | CustomerBillingProfileUpdate):
        data = payload.model_dump(exclude_unset=True)
        for field_name in (
            "invoice_email",
            "payment_terms_note",
            "tax_number",
            "vat_id",
            "tax_exemption_reason",
            "bank_account_holder",
            "bank_iban",
            "bank_bic",
            "bank_name",
            "contract_reference",
            "debtor_number",
            "leitweg_id",
            "billing_note",
        ):
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = data[field_name].strip() or None
        for field_name in ("invoice_layout_code", "shipping_method_code", "dunning_policy_code"):
            if field_name in data and isinstance(data[field_name], str):
                data[field_name] = data[field_name].strip().lower() or None
        return payload.__class__(**data)

    @staticmethod
    def _merge_billing_profile(existing: CustomerBillingProfile, payload: CustomerBillingProfileUpdate) -> CustomerBillingProfileCreate:
        return CustomerBillingProfileCreate(
            tenant_id=existing.tenant_id,
            customer_id=existing.customer_id,
            invoice_email=payload.invoice_email if "invoice_email" in payload.model_fields_set else existing.invoice_email,
            payment_terms_days=(
                payload.payment_terms_days if "payment_terms_days" in payload.model_fields_set else existing.payment_terms_days
            ),
            payment_terms_note=(
                payload.payment_terms_note if "payment_terms_note" in payload.model_fields_set else existing.payment_terms_note
            ),
            tax_number=payload.tax_number if "tax_number" in payload.model_fields_set else existing.tax_number,
            vat_id=payload.vat_id if "vat_id" in payload.model_fields_set else existing.vat_id,
            tax_exempt=payload.tax_exempt if "tax_exempt" in payload.model_fields_set else existing.tax_exempt,
            tax_exemption_reason=(
                payload.tax_exemption_reason
                if "tax_exemption_reason" in payload.model_fields_set
                else existing.tax_exemption_reason
            ),
            bank_account_holder=(
                payload.bank_account_holder
                if "bank_account_holder" in payload.model_fields_set
                else existing.bank_account_holder
            ),
            bank_iban=payload.bank_iban if "bank_iban" in payload.model_fields_set else existing.bank_iban,
            bank_bic=payload.bank_bic if "bank_bic" in payload.model_fields_set else existing.bank_bic,
            bank_name=payload.bank_name if "bank_name" in payload.model_fields_set else existing.bank_name,
            contract_reference=(
                payload.contract_reference
                if "contract_reference" in payload.model_fields_set
                else existing.contract_reference
            ),
            debtor_number=payload.debtor_number if "debtor_number" in payload.model_fields_set else existing.debtor_number,
            e_invoice_enabled=(
                payload.e_invoice_enabled if "e_invoice_enabled" in payload.model_fields_set else existing.e_invoice_enabled
            ),
            leitweg_id=payload.leitweg_id if "leitweg_id" in payload.model_fields_set else existing.leitweg_id,
            invoice_layout_code=(
                payload.invoice_layout_code
                if "invoice_layout_code" in payload.model_fields_set
                else existing.invoice_layout_code
            ),
            shipping_method_code=(
                payload.shipping_method_code
                if "shipping_method_code" in payload.model_fields_set
                else existing.shipping_method_code
            ),
            dunning_policy_code=(
                payload.dunning_policy_code
                if "dunning_policy_code" in payload.model_fields_set
                else existing.dunning_policy_code
            ),
            billing_note=payload.billing_note if "billing_note" in payload.model_fields_set else existing.billing_note,
        )

    @staticmethod
    def _normalize_invoice_party(existing: CustomerInvoiceParty, payload: CustomerInvoicePartyUpdate) -> CustomerInvoicePartyCreate:
        return CustomerInvoicePartyCreate(
            tenant_id=existing.tenant_id,
            customer_id=existing.customer_id,
            company_name=payload.company_name if "company_name" in payload.model_fields_set else existing.company_name,
            contact_name=payload.contact_name if "contact_name" in payload.model_fields_set else existing.contact_name,
            address_id=payload.address_id if "address_id" in payload.model_fields_set else existing.address_id,
            invoice_email=payload.invoice_email if "invoice_email" in payload.model_fields_set else existing.invoice_email,
            invoice_layout_lookup_id=(
                payload.invoice_layout_lookup_id
                if "invoice_layout_lookup_id" in payload.model_fields_set
                else existing.invoice_layout_lookup_id
            ),
            external_ref=payload.external_ref if "external_ref" in payload.model_fields_set else existing.external_ref,
            is_default=payload.is_default if "is_default" in payload.model_fields_set else existing.is_default,
            note=payload.note if "note" in payload.model_fields_set else existing.note,
        )

    @staticmethod
    def _validate_rate_card_path(tenant_id: str, customer_id: str, payload: CustomerRateCardCreate) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "customers.validation.rate_card_tenant_mismatch", "errors.customers.rate_card.tenant_mismatch")
        if payload.customer_id != customer_id:
            raise ApiException(400, "customers.validation.rate_card_customer_mismatch", "errors.customers.rate_card.customer_mismatch")

    @staticmethod
    def _validate_rate_line_path(tenant_id: str, rate_card_id: str, payload: CustomerRateLineCreate) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(400, "customers.validation.rate_line_tenant_mismatch", "errors.customers.rate_line.tenant_mismatch")
        if payload.rate_card_id != rate_card_id:
            raise ApiException(400, "customers.validation.rate_line_rate_card_mismatch", "errors.customers.rate_line.rate_card_mismatch")

    @staticmethod
    def _validate_surcharge_rule_path(tenant_id: str, rate_card_id: str, payload: CustomerSurchargeRuleCreate) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "customers.validation.surcharge_rule_tenant_mismatch",
                "errors.customers.surcharge_rule.tenant_mismatch",
            )
        if payload.rate_card_id != rate_card_id:
            raise ApiException(
                400,
                "customers.validation.surcharge_rule_rate_card_mismatch",
                "errors.customers.surcharge_rule.rate_card_mismatch",
            )

    @staticmethod
    def _normalize_rate_card(existing: CustomerRateCard, payload: CustomerRateCardUpdate) -> CustomerRateCardCreate:
        return CustomerRateCardCreate(
            tenant_id=existing.tenant_id,
            customer_id=existing.customer_id,
            rate_kind=payload.rate_kind if "rate_kind" in payload.model_fields_set else existing.rate_kind,
            currency_code=payload.currency_code if "currency_code" in payload.model_fields_set else existing.currency_code,
            effective_from=payload.effective_from if "effective_from" in payload.model_fields_set else existing.effective_from,
            effective_to=payload.effective_to if "effective_to" in payload.model_fields_set else existing.effective_to,
            notes=payload.notes if "notes" in payload.model_fields_set else existing.notes,
        )

    @staticmethod
    def _canonicalize_rate_card(payload: CustomerRateCardCreate) -> CustomerRateCardCreate:
        return CustomerRateCardCreate(
            tenant_id=payload.tenant_id,
            customer_id=payload.customer_id,
            rate_kind=payload.rate_kind.strip().lower(),
            currency_code=payload.currency_code.strip().upper(),
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            notes=payload.notes.strip() if payload.notes else None,
        )

    @staticmethod
    def _normalize_rate_line(existing: CustomerRateLine, payload: CustomerRateLineUpdate) -> CustomerRateLineCreate:
        return CustomerRateLineCreate(
            tenant_id=existing.tenant_id,
            rate_card_id=existing.rate_card_id,
            line_kind=payload.line_kind if "line_kind" in payload.model_fields_set else existing.line_kind,
            function_type_id=(
                payload.function_type_id if "function_type_id" in payload.model_fields_set else existing.function_type_id
            ),
            qualification_type_id=(
                payload.qualification_type_id
                if "qualification_type_id" in payload.model_fields_set
                else existing.qualification_type_id
            ),
            planning_mode_code=(
                payload.planning_mode_code if "planning_mode_code" in payload.model_fields_set else existing.planning_mode_code
            ),
            billing_unit=payload.billing_unit if "billing_unit" in payload.model_fields_set else existing.billing_unit,
            unit_price=payload.unit_price if "unit_price" in payload.model_fields_set else Decimal(str(existing.unit_price)),
            minimum_quantity=(
                payload.minimum_quantity
                if "minimum_quantity" in payload.model_fields_set
                else (Decimal(str(existing.minimum_quantity)) if existing.minimum_quantity is not None else None)
            ),
            sort_order=payload.sort_order if "sort_order" in payload.model_fields_set else existing.sort_order,
            notes=payload.notes if "notes" in payload.model_fields_set else existing.notes,
        )

    @staticmethod
    def _canonicalize_rate_line(payload: CustomerRateLineCreate) -> CustomerRateLineCreate:
        return CustomerRateLineCreate(
            tenant_id=payload.tenant_id,
            rate_card_id=payload.rate_card_id,
            line_kind=payload.line_kind.strip().lower(),
            function_type_id=payload.function_type_id.strip() if payload.function_type_id else None,
            qualification_type_id=payload.qualification_type_id.strip() if payload.qualification_type_id else None,
            planning_mode_code=payload.planning_mode_code.strip().lower() if payload.planning_mode_code else None,
            billing_unit=payload.billing_unit.strip().lower(),
            unit_price=payload.unit_price,
            minimum_quantity=payload.minimum_quantity,
            sort_order=payload.sort_order,
            notes=payload.notes.strip() if payload.notes else None,
        )

    @staticmethod
    def _normalize_surcharge_rule(
        existing: CustomerSurchargeRule,
        payload: CustomerSurchargeRuleUpdate,
    ) -> CustomerSurchargeRuleCreate:
        return CustomerSurchargeRuleCreate(
            tenant_id=existing.tenant_id,
            rate_card_id=existing.rate_card_id,
            surcharge_type=(
                payload.surcharge_type if "surcharge_type" in payload.model_fields_set else existing.surcharge_type
            ),
            effective_from=payload.effective_from if "effective_from" in payload.model_fields_set else existing.effective_from,
            effective_to=payload.effective_to if "effective_to" in payload.model_fields_set else existing.effective_to,
            weekday_mask=payload.weekday_mask if "weekday_mask" in payload.model_fields_set else existing.weekday_mask,
            time_from_minute=(
                payload.time_from_minute if "time_from_minute" in payload.model_fields_set else existing.time_from_minute
            ),
            time_to_minute=payload.time_to_minute if "time_to_minute" in payload.model_fields_set else existing.time_to_minute,
            region_code=payload.region_code if "region_code" in payload.model_fields_set else existing.region_code,
            percent_value=(
                payload.percent_value
                if "percent_value" in payload.model_fields_set
                else (Decimal(str(existing.percent_value)) if existing.percent_value is not None else None)
            ),
            fixed_amount=(
                payload.fixed_amount
                if "fixed_amount" in payload.model_fields_set
                else (Decimal(str(existing.fixed_amount)) if existing.fixed_amount is not None else None)
            ),
            currency_code=payload.currency_code if "currency_code" in payload.model_fields_set else existing.currency_code,
            sort_order=payload.sort_order if "sort_order" in payload.model_fields_set else existing.sort_order,
            notes=payload.notes if "notes" in payload.model_fields_set else existing.notes,
        )

    @staticmethod
    def _canonicalize_surcharge_rule(payload: CustomerSurchargeRuleCreate) -> CustomerSurchargeRuleCreate:
        return CustomerSurchargeRuleCreate(
            tenant_id=payload.tenant_id,
            rate_card_id=payload.rate_card_id,
            surcharge_type=payload.surcharge_type.strip().lower(),
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            weekday_mask=payload.weekday_mask,
            time_from_minute=payload.time_from_minute,
            time_to_minute=payload.time_to_minute,
            region_code=payload.region_code.strip().upper() if payload.region_code else None,
            percent_value=payload.percent_value,
            fixed_amount=payload.fixed_amount,
            currency_code=payload.currency_code.strip().upper() if payload.currency_code else None,
            sort_order=payload.sort_order,
            notes=payload.notes.strip() if payload.notes else None,
        )

    def _validate_billing_profile(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerBillingProfileCreate | CustomerBillingProfileUpdate,
    ) -> None:
        invoice_email = getattr(payload, "invoice_email", None)
        if invoice_email and "@" not in invoice_email:
            raise ApiException(400, "customers.validation.billing_profile_invoice_email", "errors.customers.billing_profile.invalid_invoice_email")
        payment_terms_days = getattr(payload, "payment_terms_days", None)
        if payment_terms_days is not None and payment_terms_days < 0:
            raise ApiException(400, "customers.validation.billing_profile_payment_terms", "errors.customers.billing_profile.invalid_payment_terms")
        tax_exempt = getattr(payload, "tax_exempt", False)
        tax_exemption_reason = getattr(payload, "tax_exemption_reason", None)
        if tax_exempt and not (tax_exemption_reason or "").strip():
            raise ApiException(400, "customers.validation.tax_exemption_reason", "errors.customers.billing_profile.tax_exemption_reason_required")
        if not tax_exempt and tax_exemption_reason:
            raise ApiException(400, "customers.validation.tax_exemption_reason", "errors.customers.billing_profile.tax_exemption_reason_forbidden")
        has_bank_data = any(
            getattr(payload, field_name, None)
            for field_name in ("bank_account_holder", "bank_iban", "bank_bic", "bank_name")
        )
        if has_bank_data:
            if not (getattr(payload, "bank_account_holder", None) or "").strip():
                raise ApiException(400, "customers.validation.bank_account_holder", "errors.customers.billing_profile.bank_account_holder_required")
            if not (getattr(payload, "bank_iban", None) or "").strip():
                raise ApiException(400, "customers.validation.bank_iban", "errors.customers.billing_profile.bank_iban_required")
        invoice_layout_code = (getattr(payload, "invoice_layout_code", None) or "").strip().lower() or None
        shipping_method_code = (getattr(payload, "shipping_method_code", None) or "").strip().lower() or None
        dunning_policy_code = (getattr(payload, "dunning_policy_code", None) or "").strip().lower() or None
        e_invoice_enabled = bool(getattr(payload, "e_invoice_enabled", False))
        leitweg_id = (getattr(payload, "leitweg_id", None) or "").strip() or None

        if invoice_layout_code is not None:
            self._require_lookup_code(tenant_id, "invoice_layout", invoice_layout_code, "billing_profile_invoice_layout")
        if shipping_method_code is not None:
            self._require_lookup_code(
                tenant_id,
                "invoice_delivery_method",
                shipping_method_code,
                "billing_profile_shipping_method",
            )
        if dunning_policy_code is not None:
            self._require_lookup_code(tenant_id, "dunning_policy", dunning_policy_code, "billing_profile_dunning_policy")

        default_invoice_party = next(
            (row for row in self.repository.list_invoice_parties(tenant_id, customer_id) if row.is_default and row.archived_at is None),
            None,
        )
        has_dispatch_email = bool((invoice_email or "").strip()) or bool(
            default_invoice_party and (default_invoice_party.invoice_email or "").strip()
        )
        invoice_party_layout_code = None
        if default_invoice_party is not None and default_invoice_party.invoice_layout_lookup_id:
            invoice_party_layout = self.repository.get_lookup_value(default_invoice_party.invoice_layout_lookup_id)
            invoice_party_layout_code = invoice_party_layout.code if invoice_party_layout is not None else None
        effective_invoice_layout_code = invoice_layout_code or invoice_party_layout_code

        if e_invoice_enabled and shipping_method_code != "e_invoice":
            raise ApiException(
                400,
                "customers.validation.billing_profile_e_invoice_dispatch_mismatch",
                "errors.customers.billing_profile.e_invoice_dispatch_mismatch",
            )
        if shipping_method_code == "e_invoice":
            if not e_invoice_enabled:
                raise ApiException(
                    400,
                    "customers.validation.billing_profile_e_invoice_required",
                    "errors.customers.billing_profile.e_invoice_required",
                )
            if not leitweg_id:
                raise ApiException(
                    400,
                    "customers.validation.billing_profile_leitweg_required",
                    "errors.customers.billing_profile.leitweg_required",
                )
        if not e_invoice_enabled and leitweg_id:
            raise ApiException(
                400,
                "customers.validation.billing_profile_leitweg_forbidden",
                "errors.customers.billing_profile.leitweg_forbidden",
            )
        if shipping_method_code == "email_pdf" and not has_dispatch_email:
            raise ApiException(
                400,
                "customers.validation.billing_profile_dispatch_email_required",
                "errors.customers.billing_profile.dispatch_email_required",
            )
        if shipping_method_code == "e_invoice" and effective_invoice_layout_code == "compact":
            raise ApiException(
                400,
                "customers.validation.billing_profile_invoice_layout_incompatible",
                "errors.customers.billing_profile.invoice_layout_incompatible",
            )

    def _validate_invoice_party(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerInvoicePartyCreate,
        *,
        exclude_invoice_party_id: str | None = None,
    ) -> None:
        if not payload.company_name.strip():
            raise ApiException(400, "customers.validation.invoice_party_company_name", "errors.customers.invoice_party.company_name_required")
        try:
            UUID(payload.address_id)
        except ValueError as exc:
            raise ApiException(
                400,
                "customers.validation.invoice_party_address_format",
                "errors.customers.invoice_party.invalid_address_format",
            ) from exc
        if self.repository.get_address(payload.address_id) is None:
            raise ApiException(400, "customers.validation.invoice_party_address", "errors.customers.invoice_party.address_not_found")
        if payload.invoice_email and "@" not in payload.invoice_email:
            raise ApiException(400, "customers.validation.invoice_party_email", "errors.customers.invoice_party.invalid_invoice_email")
        if payload.invoice_layout_lookup_id is not None:
            try:
                normalized_lookup_id = str(UUID(str(payload.invoice_layout_lookup_id).strip()))
            except (AttributeError, TypeError, ValueError) as exc:
                raise ApiException(
                    400,
                    "customers.validation.invoice_party_layout_lookup_format",
                    "errors.customers.invoice_party.invalid_layout_format",
                ) from exc
            lookup = self.repository.get_lookup_value(normalized_lookup_id)
            if lookup is None or lookup.archived_at is not None:
                raise ApiException(400, "customers.validation.invoice_party_layout_lookup", "errors.customers.lookup.not_found")
            if lookup.domain != "invoice_layout":
                raise ApiException(400, "customers.validation.invoice_party_layout_lookup", "errors.customers.lookup.invalid_domain")
            if lookup.tenant_id not in (None, tenant_id):
                raise ApiException(400, "customers.validation.invoice_party_layout_scope", "errors.customers.lookup.scope_mismatch")
        if payload.is_default and self.repository.has_default_invoice_party(
            tenant_id,
            customer_id,
            exclude_id=exclude_invoice_party_id,
        ):
            raise ApiException(409, "customers.conflict.default_invoice_party", "errors.customers.invoice_party.default_conflict")

    def _validate_rate_card(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerRateCardCreate,
        *,
        exclude_rate_card_id: str | None = None,
    ) -> None:
        if not payload.rate_kind.strip():
            raise ApiException(400, "customers.validation.rate_card_kind", "errors.customers.rate_card.rate_kind_required")
        currency_code = payload.currency_code.strip().upper()
        if len(currency_code) != 3 or not currency_code.isalpha():
            raise ApiException(400, "customers.validation.rate_card_currency", "errors.customers.rate_card.invalid_currency")
        if payload.effective_to is not None and payload.effective_to < payload.effective_from:
            raise ApiException(400, "customers.validation.rate_card_window", "errors.customers.rate_card.invalid_window")
        overlapping = self.repository.list_overlapping_rate_cards(
            tenant_id,
            customer_id,
            rate_kind=payload.rate_kind.strip().lower(),
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            exclude_id=exclude_rate_card_id,
        )
        if overlapping:
            raise ApiException(409, "customers.conflict.rate_card_overlap", "errors.customers.rate_card.overlap")

    def _validate_rate_line(
        self,
        tenant_id: str,
        rate_card: CustomerRateCard,
        payload: CustomerRateLineCreate,
        *,
        exclude_rate_line_id: str | None = None,
    ) -> None:
        if not payload.line_kind.strip():
            raise ApiException(400, "customers.validation.rate_line_kind", "errors.customers.rate_line.line_kind_required")
        if not payload.billing_unit.strip():
            raise ApiException(400, "customers.validation.rate_line_billing_unit", "errors.customers.rate_line.invalid_billing_unit")
        if payload.unit_price < 0:
            raise ApiException(400, "customers.validation.rate_line_unit_price", "errors.customers.rate_line.invalid_unit_price")
        if payload.minimum_quantity is not None and payload.minimum_quantity < 0:
            raise ApiException(
                400,
                "customers.validation.rate_line_minimum_quantity",
                "errors.customers.rate_line.invalid_minimum_quantity",
            )
        if self.repository.find_duplicate_rate_line(
            tenant_id,
            rate_card.id,
            line_kind=payload.line_kind,
            function_type_id=payload.function_type_id,
            qualification_type_id=payload.qualification_type_id,
            planning_mode_code=payload.planning_mode_code,
            billing_unit=payload.billing_unit,
            exclude_id=exclude_rate_line_id,
        ):
            raise ApiException(409, "customers.conflict.rate_line_duplicate", "errors.customers.rate_line.duplicate_dimension")

    @staticmethod
    def _validate_surcharge_rule(rate_card: CustomerRateCard, payload: CustomerSurchargeRuleCreate) -> None:
        if not payload.surcharge_type.strip():
            raise ApiException(
                400,
                "customers.validation.surcharge_rule_type",
                "errors.customers.surcharge_rule.surcharge_type_required",
            )
        if payload.effective_to is not None and payload.effective_to < payload.effective_from:
            raise ApiException(
                400,
                "customers.validation.surcharge_rule_window",
                "errors.customers.surcharge_rule.invalid_window",
            )
        if payload.effective_from < rate_card.effective_from or (
            rate_card.effective_to is not None and (payload.effective_to is None or payload.effective_to > rate_card.effective_to)
        ):
            raise ApiException(
                400,
                "customers.validation.surcharge_rule_card_window",
                "errors.customers.surcharge_rule.outside_rate_card_window",
            )
        if payload.weekday_mask is not None and any(bit not in {"0", "1"} for bit in payload.weekday_mask):
            raise ApiException(
                400,
                "customers.validation.surcharge_rule_weekday_mask",
                "errors.customers.surcharge_rule.invalid_weekday_mask",
            )
        if (payload.time_from_minute is None) != (payload.time_to_minute is None):
            raise ApiException(
                400,
                "customers.validation.surcharge_rule_time_range",
                "errors.customers.surcharge_rule.invalid_time_range",
            )
        if payload.time_from_minute is not None and payload.time_to_minute is not None:
            if payload.time_to_minute <= payload.time_from_minute:
                raise ApiException(
                    400,
                    "customers.validation.surcharge_rule_time_range",
                    "errors.customers.surcharge_rule.invalid_time_range",
                )
        has_percent = payload.percent_value is not None
        has_fixed = payload.fixed_amount is not None
        if has_percent == has_fixed:
            raise ApiException(
                400,
                "customers.validation.surcharge_rule_amount_combination",
                "errors.customers.surcharge_rule.invalid_amount_combination",
            )
        if payload.fixed_amount is not None:
            if payload.currency_code is None or len(payload.currency_code.strip().upper()) != 3:
                raise ApiException(
                    400,
                    "customers.validation.surcharge_rule_currency",
                    "errors.customers.surcharge_rule.invalid_currency",
                )
        elif payload.currency_code is not None:
            raise ApiException(
                400,
                "customers.validation.surcharge_rule_currency",
                "errors.customers.surcharge_rule.invalid_currency",
            )

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
        *,
        event_type: str,
        entity_type: str,
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

    def _require_lookup_code(self, tenant_id: str, domain: str, code: str, validation_code: str) -> None:
        lookup = self.repository.find_lookup_by_domain_code(tenant_id, domain, code)
        if lookup is None or lookup.archived_at is not None:
            raise ApiException(400, f"customers.validation.{validation_code}", "errors.customers.lookup.not_found")

    @staticmethod
    def _mask(value: str | None, *, keep_last: int = 4) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if len(stripped) <= keep_last:
            return "*" * len(stripped)
        return f"{'*' * max(4, len(stripped) - keep_last)}{stripped[-keep_last:]}"

    @classmethod
    def _billing_profile_audit_snapshot(cls, row: CustomerBillingProfile) -> dict[str, object]:
        return {
            "invoice_email": row.invoice_email,
            "payment_terms_days": row.payment_terms_days,
            "payment_terms_note": row.payment_terms_note,
            "tax_number": cls._mask(row.tax_number),
            "vat_id": cls._mask(row.vat_id),
            "tax_exempt": row.tax_exempt,
            "tax_exemption_reason": row.tax_exemption_reason,
            "bank_account_holder": row.bank_account_holder,
            "bank_iban": cls._mask(row.bank_iban),
            "bank_bic": cls._mask(row.bank_bic),
            "bank_name": row.bank_name,
            "contract_reference": row.contract_reference,
            "debtor_number": row.debtor_number,
            "e_invoice_enabled": row.e_invoice_enabled,
            "leitweg_id": row.leitweg_id,
            "invoice_layout_code": row.invoice_layout_code,
            "shipping_method_code": row.shipping_method_code,
            "dunning_policy_code": row.dunning_policy_code,
            "status": row.status,
        }

    @staticmethod
    def _invoice_party_snapshot(row: CustomerInvoiceParty) -> dict[str, object]:
        return {
            "company_name": row.company_name,
            "contact_name": row.contact_name,
            "address_id": row.address_id,
            "invoice_email": row.invoice_email,
            "invoice_layout_lookup_id": row.invoice_layout_lookup_id,
            "external_ref": row.external_ref,
            "is_default": row.is_default,
            "status": row.status,
        }

    @staticmethod
    def _rate_card_snapshot(row: CustomerRateCard) -> dict[str, object]:
        return {
            "rate_kind": row.rate_kind,
            "currency_code": row.currency_code,
            "effective_from": row.effective_from.isoformat(),
            "effective_to": row.effective_to.isoformat() if row.effective_to else None,
            "notes": row.notes,
            "status": row.status,
        }

    @staticmethod
    def _rate_line_snapshot(row: CustomerRateLine) -> dict[str, object]:
        return {
            "line_kind": row.line_kind,
            "function_type_id": row.function_type_id,
            "qualification_type_id": row.qualification_type_id,
            "planning_mode_code": row.planning_mode_code,
            "billing_unit": row.billing_unit,
            "unit_price": str(row.unit_price),
            "minimum_quantity": str(row.minimum_quantity) if row.minimum_quantity is not None else None,
            "sort_order": row.sort_order,
            "status": row.status,
        }

    @staticmethod
    def _surcharge_rule_snapshot(row: CustomerSurchargeRule) -> dict[str, object]:
        return {
            "surcharge_type": row.surcharge_type,
            "effective_from": row.effective_from.isoformat(),
            "effective_to": row.effective_to.isoformat() if row.effective_to else None,
            "weekday_mask": row.weekday_mask,
            "time_from_minute": row.time_from_minute,
            "time_to_minute": row.time_to_minute,
            "region_code": row.region_code,
            "percent_value": str(row.percent_value) if row.percent_value is not None else None,
            "fixed_amount": str(row.fixed_amount) if row.fixed_amount is not None else None,
            "currency_code": row.currency_code,
            "sort_order": row.sort_order,
            "status": row.status,
        }
