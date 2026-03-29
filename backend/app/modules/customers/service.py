"""Service layer for CRM customer aggregate maintenance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from app.errors import ApiException
from app.modules.core.models import Address
from app.modules.core.schemas import AddressCreate, AddressRead
from app.modules.customers.models import (
    CUSTOMER_ADDRESS_TYPES,
    Customer,
    CustomerAddressLink,
    CustomerContact,
    CustomerHistoryEntry,
)
from app.modules.customers.policy import enforce_customer_module_access
from app.modules.customers.schemas import (
    CustomerAddressCreate,
    CustomerAddressRead,
    CustomerAddressUpdate,
    CustomerContactCreate,
    CustomerContactRead,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerFilter,
    CustomerHistoryEntryRead,
    CustomerReferenceDataRead,
    CustomerReferenceOptionRead,
    CustomerBranchOptionRead,
    CustomerMandateOptionRead,
    CustomerListItem,
    CustomerRead,
    CustomerUpdate,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext


@dataclass(frozen=True, slots=True)
class CustomerAuditContext:
    actor_user_id: str | None
    request_id: str | None


class CustomerRepository(Protocol):
    def list_customers(self, tenant_id: str, filters: CustomerFilter) -> list[Customer]: ...
    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None: ...
    def create_customer(self, tenant_id: str, payload: CustomerCreate, actor_user_id: str | None) -> Customer: ...
    def update_customer(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerUpdate,
        actor_user_id: str | None,
    ) -> Customer | None: ...
    def list_contacts(self, tenant_id: str, customer_id: str) -> list[CustomerContact]: ...
    def get_contact(self, tenant_id: str, customer_id: str, contact_id: str) -> CustomerContact | None: ...
    def create_contact(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerContactCreate,
        actor_user_id: str | None,
    ) -> CustomerContact: ...
    def update_contact(
        self,
        tenant_id: str,
        customer_id: str,
        contact_id: str,
        payload: CustomerContactUpdate,
        actor_user_id: str | None,
    ) -> CustomerContact | None: ...
    def list_customer_addresses(self, tenant_id: str, customer_id: str) -> list[CustomerAddressLink]: ...
    def get_customer_address(self, tenant_id: str, customer_id: str, link_id: str) -> CustomerAddressLink | None: ...
    def create_customer_address(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerAddressCreate,
        actor_user_id: str | None,
    ) -> CustomerAddressLink: ...
    def update_customer_address(
        self,
        tenant_id: str,
        customer_id: str,
        link_id: str,
        payload: CustomerAddressUpdate,
        actor_user_id: str | None,
    ) -> CustomerAddressLink | None: ...
    def find_customer_by_number(self, tenant_id: str, customer_number: str, *, exclude_id: str | None = None) -> Customer | None: ...
    def find_contact_by_email(
        self,
        tenant_id: str,
        customer_id: str,
        email: str,
        *,
        exclude_id: str | None = None,
    ) -> CustomerContact | None: ...
    def find_contact_by_name(
        self,
        tenant_id: str,
        customer_id: str,
        full_name: str,
        *,
        exclude_id: str | None = None,
    ) -> CustomerContact | None: ...
    def has_primary_contact(self, tenant_id: str, customer_id: str, *, exclude_id: str | None = None) -> bool: ...
    def has_default_address(
        self,
        tenant_id: str,
        customer_id: str,
        address_type: str,
        *,
        exclude_id: str | None = None,
    ) -> bool: ...
    def find_duplicate_address_link(
        self,
        tenant_id: str,
        customer_id: str,
        address_id: str,
        address_type: str,
        *,
        exclude_id: str | None = None,
    ) -> CustomerAddressLink | None: ...
    def find_address_link_by_type(
        self,
        tenant_id: str,
        customer_id: str,
        address_type: str,
        *,
        exclude_id: str | None = None,
    ) -> CustomerAddressLink | None: ...
    def list_history_entries(self, tenant_id: str, customer_id: str) -> list[CustomerHistoryEntry]: ...
    def create_history_entry(self, row: CustomerHistoryEntry) -> CustomerHistoryEntry: ...
    def get_lookup_value(self, lookup_id: str): ...  # noqa: ANN001
    def list_lookup_values(self, tenant_id: str, domain: str): ...  # noqa: ANN001
    def get_branch(self, tenant_id: str, branch_id: str): ...  # noqa: ANN001
    def list_branches(self, tenant_id: str): ...  # noqa: ANN001
    def get_mandate(self, tenant_id: str, mandate_id: str): ...  # noqa: ANN001
    def list_mandates(self, tenant_id: str): ...  # noqa: ANN001
    def get_user_account(self, tenant_id: str, user_id: str): ...  # noqa: ANN001
    def get_address(self, address_id: str): ...  # noqa: ANN001
    def list_available_addresses(
        self,
        tenant_id: str,
        customer_id: str,
        search: str = "",
        limit: int = 25,
    ): ...  # noqa: ANN001
    def create_address(self, row: Address): ...  # noqa: ANN001


class CustomerService:
    LOOKUP_DOMAINS = {
        "legal_form_lookup_id": "legal_form",
        "classification_lookup_id": "customer_category",
        "ranking_lookup_id": "customer_ranking",
        "customer_status_lookup_id": "customer_status",
    }

    def __init__(self, repository: CustomerRepository, audit_service: AuditService | None = None) -> None:
        self.repository = repository
        self.audit_service = audit_service

    def list_customers(
        self,
        tenant_id: str,
        filters: CustomerFilter,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerListItem]:
        self._ensure_tenant_scope(actor, tenant_id)
        return [CustomerListItem.model_validate(row) for row in self.repository.list_customers(tenant_id, filters)]

    def get_customer(self, tenant_id: str, customer_id: str, actor: RequestAuthorizationContext) -> CustomerRead:
        customer = self._require_customer(tenant_id, customer_id, actor)
        return CustomerRead.model_validate(customer)

    def get_reference_data(self, tenant_id: str, actor: RequestAuthorizationContext) -> CustomerReferenceDataRead:
        self._ensure_tenant_scope(actor, tenant_id)
        return CustomerReferenceDataRead(
            legal_forms=[
                CustomerReferenceOptionRead.model_validate(lookup)
                for lookup in self.repository.list_lookup_values(tenant_id, "legal_form")
            ],
            classifications=[
                CustomerReferenceOptionRead.model_validate(lookup)
                for lookup in self.repository.list_lookup_values(tenant_id, "customer_category")
            ],
            rankings=[
                CustomerReferenceOptionRead.model_validate(lookup)
                for lookup in self.repository.list_lookup_values(tenant_id, "customer_ranking")
            ],
            customer_statuses=[
                CustomerReferenceOptionRead.model_validate(lookup)
                for lookup in self.repository.list_lookup_values(tenant_id, "customer_status")
            ],
            invoice_layouts=[
                CustomerReferenceOptionRead.model_validate(lookup)
                for lookup in self.repository.list_lookup_values(None, "invoice_layout")
            ],
            shipping_methods=[
                CustomerReferenceOptionRead.model_validate(lookup)
                for lookup in self.repository.list_lookup_values(None, "invoice_delivery_method")
            ],
            dunning_policies=[
                CustomerReferenceOptionRead.model_validate(lookup)
                for lookup in self.repository.list_lookup_values(None, "dunning_policy")
            ],
            branches=[
                CustomerBranchOptionRead.model_validate(branch)
                for branch in self.repository.list_branches(tenant_id)
            ],
            mandates=[
                CustomerMandateOptionRead.model_validate(mandate)
                for mandate in self.repository.list_mandates(tenant_id)
            ],
        )

    def create_customer(
        self,
        tenant_id: str,
        payload: CustomerCreate,
        actor: RequestAuthorizationContext,
    ) -> CustomerRead:
        self._ensure_tenant_scope(actor, tenant_id)
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "customers.validation.customer_tenant_mismatch",
                "errors.customers.customer.tenant_mismatch",
                {"tenant_id": tenant_id},
            )
        normalized_payload = self._normalize_customer_create(payload)
        self._validate_customer_payload(tenant_id, normalized_payload)
        if self.repository.find_customer_by_number(tenant_id, normalized_payload.customer_number) is not None:
            raise ApiException(409, "customers.conflict.customer_number", "errors.customers.customer.duplicate_number")
        customer = self.repository.create_customer(tenant_id, normalized_payload, actor.user_id)
        after_json = self._customer_snapshot(customer)
        self._record_history(
            tenant_id,
            customer.id,
            actor,
            entry_type="customer.created",
            title="Customer created",
            summary=f"Created customer {customer.customer_number} ({customer.name}).",
            after_json=after_json,
        )
        self._record_event(
            actor,
            event_type="customers.customer.created",
            entity_type="crm.customer",
            entity_id=customer.id,
            tenant_id=tenant_id,
            after_json=after_json,
        )
        return CustomerRead.model_validate(customer)

    def update_customer(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerRead:
        customer = self._require_customer(tenant_id, customer_id, actor)
        self._require_version(customer.version_no, payload.version_no, "customer")
        normalized = self._normalize_lifecycle(payload, current_archived_at=customer.archived_at)
        next_number = self._effective_value(normalized, customer, "customer_number")
        if self.repository.find_customer_by_number(tenant_id, next_number, exclude_id=customer_id) is not None:
            raise ApiException(409, "customers.conflict.customer_number", "errors.customers.customer.duplicate_number")
        self._validate_customer_payload(
            tenant_id,
            CustomerCreate(
                tenant_id=tenant_id,
                customer_number=next_number,
                name=self._effective_value(normalized, customer, "name"),
                legal_name=self._effective_value(normalized, customer, "legal_name"),
                external_ref=self._effective_value(normalized, customer, "external_ref"),
                legal_form_lookup_id=self._effective_value(normalized, customer, "legal_form_lookup_id"),
                classification_lookup_id=self._effective_value(normalized, customer, "classification_lookup_id"),
                ranking_lookup_id=self._effective_value(normalized, customer, "ranking_lookup_id"),
                customer_status_lookup_id=self._effective_value(normalized, customer, "customer_status_lookup_id"),
                default_branch_id=self._effective_value(normalized, customer, "default_branch_id"),
                default_mandate_id=self._effective_value(normalized, customer, "default_mandate_id"),
                notes=self._effective_value(normalized, customer, "notes"),
            ),
        )
        updated = self.repository.update_customer(tenant_id, customer_id, normalized, actor.user_id)
        if updated is None:
            raise self._not_found("customer")
        history = self._build_customer_history(customer, updated)
        if history is not None:
            self._record_history(
                tenant_id,
                updated.id,
                actor,
                entry_type=history["entry_type"],
                title=history["title"],
                summary=history["summary"],
                before_json=history["before_json"],
                after_json=history["after_json"],
                metadata_json=history["metadata_json"],
            )
            self._record_event(
                actor,
                event_type=self._customer_audit_event_type(history["entry_type"]),
                entity_type="crm.customer",
                entity_id=updated.id,
                tenant_id=tenant_id,
                before_json=history["before_json"],
                after_json=history["after_json"],
                metadata_json=history["metadata_json"],
            )
        return CustomerRead.model_validate(updated)

    def list_contacts(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerContactRead]:
        self._require_customer(tenant_id, customer_id, actor)
        return [CustomerContactRead.model_validate(row) for row in self.repository.list_contacts(tenant_id, customer_id)]

    def create_contact(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerContactCreate,
        actor: RequestAuthorizationContext,
    ) -> CustomerContactRead:
        self._require_customer(tenant_id, customer_id, actor)
        self._validate_contact_path(tenant_id, customer_id, payload)
        self._validate_contact_constraints(tenant_id, customer_id, payload)
        contact = self.repository.create_contact(tenant_id, customer_id, payload, actor.user_id)
        after_json = self._contact_snapshot(contact)
        self._record_history(
            tenant_id,
            customer_id,
            actor,
            entry_type="customer.contact.created",
            title="Customer contact created",
            summary=f"Added contact {contact.full_name}.",
            related_contact_id=contact.id,
            after_json=after_json,
        )
        self._record_event(
            actor,
            event_type="customers.contact.created",
            entity_type="crm.customer_contact",
            entity_id=contact.id,
            tenant_id=tenant_id,
            after_json=after_json,
            metadata_json={"customer_id": customer_id},
        )
        return CustomerContactRead.model_validate(contact)

    def update_contact(
        self,
        tenant_id: str,
        customer_id: str,
        contact_id: str,
        payload: CustomerContactUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerContactRead:
        self._require_customer(tenant_id, customer_id, actor)
        existing = self.repository.get_contact(tenant_id, customer_id, contact_id)
        if existing is None:
            raise self._not_found("contact")
        self._require_version(existing.version_no, payload.version_no, "contact")
        normalized = self._normalize_lifecycle(payload, current_archived_at=existing.archived_at)
        self._validate_contact_constraints(
            tenant_id,
            customer_id,
            CustomerContactCreate(
                tenant_id=tenant_id,
                customer_id=customer_id,
                full_name=self._effective_value(normalized, existing, "full_name"),
                title=self._effective_value(normalized, existing, "title"),
                function_label=self._effective_value(normalized, existing, "function_label"),
                email=self._effective_value(normalized, existing, "email"),
                phone=self._effective_value(normalized, existing, "phone"),
                mobile=self._effective_value(normalized, existing, "mobile"),
                is_primary_contact=self._effective_value(normalized, existing, "is_primary_contact"),
                is_billing_contact=self._effective_value(normalized, existing, "is_billing_contact"),
                user_id=self._effective_value(normalized, existing, "user_id"),
                notes=self._effective_value(normalized, existing, "notes"),
            ),
            exclude_contact_id=contact_id,
        )
        updated = self.repository.update_contact(tenant_id, customer_id, contact_id, normalized, actor.user_id)
        if updated is None:
            raise self._not_found("contact")
        history = self._build_contact_history(existing, updated)
        if history is not None:
            self._record_history(
                tenant_id,
                customer_id,
                actor,
                entry_type=history["entry_type"],
                title=history["title"],
                summary=history["summary"],
                related_contact_id=updated.id,
                before_json=history["before_json"],
                after_json=history["after_json"],
                metadata_json=history["metadata_json"],
            )
            self._record_event(
                actor,
                event_type=self._contact_audit_event_type(history["entry_type"]),
                entity_type="crm.customer_contact",
                entity_id=updated.id,
                tenant_id=tenant_id,
                before_json=history["before_json"],
                after_json=history["after_json"],
                metadata_json={"customer_id": customer_id, **history["metadata_json"]},
            )
        return CustomerContactRead.model_validate(updated)

    def list_customer_addresses(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerAddressRead]:
        self._require_customer(tenant_id, customer_id, actor)
        return [
            CustomerAddressRead.model_validate(row) for row in self.repository.list_customer_addresses(tenant_id, customer_id)
        ]

    def list_available_addresses(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
        *,
        search: str = "",
        limit: int = 25,
    ) -> list[AddressRead]:
        self._require_customer(tenant_id, customer_id, actor)
        return [
            AddressRead.model_validate(row)
            for row in self.repository.list_available_addresses(
                tenant_id,
                customer_id,
                search=search,
                limit=limit,
            )
        ]

    def create_available_address(
        self,
        tenant_id: str,
        customer_id: str,
        payload: AddressCreate,
        actor: RequestAuthorizationContext,
    ) -> AddressRead:
        self._require_customer(tenant_id, customer_id, actor)
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
        self._record_event(
            actor,
            event_type="customers.address_directory.created",
            entity_type="common.address",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json=AddressRead.model_validate(row).model_dump(),
            metadata_json={"customer_id": customer_id},
        )
        return AddressRead.model_validate(row)

    def create_customer_address(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerAddressCreate,
        actor: RequestAuthorizationContext,
    ) -> CustomerAddressRead:
        self._require_customer(tenant_id, customer_id, actor)
        self._validate_address_path(tenant_id, customer_id, payload)
        self._validate_address_constraints(tenant_id, customer_id, payload)
        link = self.repository.create_customer_address(tenant_id, customer_id, payload, actor.user_id)
        after_json = self._address_snapshot(link)
        self._record_history(
            tenant_id,
            customer_id,
            actor,
            entry_type="customer.address.created",
            title="Customer address linked",
            summary=f"Linked {payload.address_type} address {payload.address_id}.",
            related_address_link_id=link.id,
            after_json=after_json,
        )
        self._record_event(
            actor,
            event_type="customers.address.created",
            entity_type="crm.customer_address",
            entity_id=link.id,
            tenant_id=tenant_id,
            after_json=after_json,
            metadata_json={"customer_id": customer_id},
        )
        return CustomerAddressRead.model_validate(link)

    def update_customer_address(
        self,
        tenant_id: str,
        customer_id: str,
        link_id: str,
        payload: CustomerAddressUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerAddressRead:
        self._require_customer(tenant_id, customer_id, actor)
        existing = self.repository.get_customer_address(tenant_id, customer_id, link_id)
        if existing is None:
            raise self._not_found("customer_address")
        self._require_version(existing.version_no, payload.version_no, "address_link")
        normalized = self._normalize_lifecycle(payload, current_archived_at=existing.archived_at)
        self._validate_address_constraints(
            tenant_id,
            customer_id,
            CustomerAddressCreate(
                tenant_id=tenant_id,
                customer_id=customer_id,
                address_id=self._effective_value(normalized, existing, "address_id"),
                address_type=self._effective_value(normalized, existing, "address_type"),
                label=self._effective_value(normalized, existing, "label"),
                is_default=self._effective_value(normalized, existing, "is_default"),
            ),
            exclude_link_id=link_id,
        )
        updated = self.repository.update_customer_address(tenant_id, customer_id, link_id, normalized, actor.user_id)
        if updated is None:
            raise self._not_found("customer_address")
        history = self._build_address_history(existing, updated)
        if history is not None:
            self._record_history(
                tenant_id,
                customer_id,
                actor,
                entry_type=history["entry_type"],
                title=history["title"],
                summary=history["summary"],
                related_address_link_id=updated.id,
                before_json=history["before_json"],
                after_json=history["after_json"],
                metadata_json=history["metadata_json"],
            )
            self._record_event(
                actor,
                event_type="customers.address.updated",
                entity_type="crm.customer_address",
                entity_id=updated.id,
                tenant_id=tenant_id,
                before_json=history["before_json"],
                after_json=history["after_json"],
                metadata_json={"customer_id": customer_id, **history["metadata_json"]},
            )
        return CustomerAddressRead.model_validate(updated)

    def list_history(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerHistoryEntryRead]:
        self._require_customer(tenant_id, customer_id, actor)
        return [
            CustomerHistoryEntryRead.model_validate(row)
            for row in self.repository.list_history_entries(tenant_id, customer_id)
        ]

    def _validate_customer_payload(self, tenant_id: str, payload: CustomerCreate) -> None:
        if payload.status not in (None, "active", "inactive"):
            raise ApiException(
                400,
                "customers.validation.initial_status",
                "errors.customers.customer.invalid_initial_status",
            )
        for field_name, expected_domain in self.LOOKUP_DOMAINS.items():
            lookup_id = getattr(payload, field_name)
            if lookup_id is None:
                continue
            lookup = self.repository.get_lookup_value(lookup_id)
            if lookup is None or lookup.archived_at is not None:
                raise ApiException(
                    400,
                    "customers.validation.lookup_not_found",
                    "errors.customers.lookup.not_found",
                    {"field": field_name, "lookup_id": lookup_id},
                )
            if lookup.domain != expected_domain:
                raise ApiException(
                    400,
                    "customers.validation.lookup_domain",
                    "errors.customers.lookup.invalid_domain",
                    {"field": field_name, "expected_domain": expected_domain, "actual_domain": lookup.domain},
                )
            if lookup.tenant_id not in (None, tenant_id):
                raise ApiException(
                    400,
                    "customers.validation.lookup_scope",
                    "errors.customers.lookup.scope_mismatch",
                    {"field": field_name},
                )

        if payload.default_branch_id is not None and self.repository.get_branch(tenant_id, payload.default_branch_id) is None:
            raise ApiException(
                400,
                "customers.validation.branch_scope",
                "errors.customers.customer.invalid_branch_scope",
            )

        if payload.default_mandate_id is not None:
            mandate = self.repository.get_mandate(tenant_id, payload.default_mandate_id)
            if mandate is None:
                raise ApiException(
                    400,
                    "customers.validation.mandate_scope",
                    "errors.customers.customer.invalid_mandate_scope",
                )
            if payload.default_branch_id is not None and mandate.branch_id != payload.default_branch_id:
                raise ApiException(
                    400,
                    "customers.validation.mandate_branch_scope",
                    "errors.customers.customer.mandate_branch_mismatch",
                )

    @staticmethod
    def _normalize_customer_create(payload: CustomerCreate) -> CustomerCreate:
        status = payload.status.strip() if isinstance(payload.status, str) else payload.status
        return CustomerCreate(
            tenant_id=payload.tenant_id,
            customer_number=payload.customer_number.strip(),
            name=payload.name.strip(),
            status=status or "active",
            legal_name=payload.legal_name.strip() if isinstance(payload.legal_name, str) and payload.legal_name.strip() else None,
            external_ref=payload.external_ref.strip() if isinstance(payload.external_ref, str) and payload.external_ref.strip() else None,
            legal_form_lookup_id=payload.legal_form_lookup_id.strip() if isinstance(payload.legal_form_lookup_id, str) and payload.legal_form_lookup_id.strip() else None,
            classification_lookup_id=payload.classification_lookup_id.strip() if isinstance(payload.classification_lookup_id, str) and payload.classification_lookup_id.strip() else None,
            ranking_lookup_id=payload.ranking_lookup_id.strip() if isinstance(payload.ranking_lookup_id, str) and payload.ranking_lookup_id.strip() else None,
            customer_status_lookup_id=payload.customer_status_lookup_id.strip() if isinstance(payload.customer_status_lookup_id, str) and payload.customer_status_lookup_id.strip() else None,
            default_branch_id=payload.default_branch_id.strip() if isinstance(payload.default_branch_id, str) and payload.default_branch_id.strip() else None,
            default_mandate_id=payload.default_mandate_id.strip() if isinstance(payload.default_mandate_id, str) and payload.default_mandate_id.strip() else None,
            notes=payload.notes.strip() if isinstance(payload.notes, str) and payload.notes.strip() else None,
        )

    def _validate_contact_constraints(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerContactCreate,
        *,
        exclude_contact_id: str | None = None,
    ) -> None:
        if payload.email:
            duplicate = self.repository.find_contact_by_email(
                tenant_id,
                customer_id,
                payload.email,
                exclude_id=exclude_contact_id,
            )
            if duplicate is not None:
                raise ApiException(
                    409,
                    "customers.conflict.contact_email",
                    "errors.customers.contact.duplicate_email",
                )
        if payload.is_primary_contact and self.repository.has_primary_contact(
            tenant_id,
            customer_id,
            exclude_id=exclude_contact_id,
        ):
            raise ApiException(
                409,
                "customers.conflict.primary_contact",
                "errors.customers.contact.primary_conflict",
            )
        if payload.user_id is not None:
            user_id = self._normalize_portal_user_id(payload.user_id)
            user = self.repository.get_user_account(tenant_id, user_id)
            if user is None or user.archived_at is not None:
                raise ApiException(
                    400,
                    "customers.validation.portal_user_scope",
                    "errors.customers.contact.invalid_user_scope",
                )

    @staticmethod
    def _normalize_portal_user_id(user_id: str) -> str:
        try:
            return str(UUID(str(user_id).strip()))
        except (AttributeError, TypeError, ValueError) as exc:
            raise ApiException(
                400,
                "customers.validation.portal_user_id_format",
                "errors.customers.contact.invalid_user_id_format",
            ) from exc

    @staticmethod
    def _normalize_address_id(address_id: str) -> str:
        try:
            return str(UUID(str(address_id).strip()))
        except (AttributeError, TypeError, ValueError) as exc:
            raise ApiException(
                400,
                "customers.validation.address_format",
                "errors.customers.customer_address.invalid_address_format",
            ) from exc

    def _validate_address_constraints(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerAddressCreate,
        *,
        exclude_link_id: str | None = None,
    ) -> None:
        if payload.address_type not in CUSTOMER_ADDRESS_TYPES:
            raise ApiException(
                400,
                "customers.validation.address_type",
                "errors.customers.customer_address.invalid_type",
            )
        normalized_address_id = self._normalize_address_id(payload.address_id)
        if self.repository.get_address(normalized_address_id) is None:
            raise ApiException(
                400,
                "customers.validation.address_missing",
                "errors.customers.customer_address.address_not_found",
            )
        if self.repository.find_duplicate_address_link(
            tenant_id,
            customer_id,
            normalized_address_id,
            payload.address_type,
            exclude_id=exclude_link_id,
        ):
            raise ApiException(
                409,
                "customers.conflict.customer_address_duplicate",
                "errors.customers.customer_address.duplicate_link",
            )
        if payload.is_default and self.repository.has_default_address(
            tenant_id,
            customer_id,
            payload.address_type,
            exclude_id=exclude_link_id,
        ):
            raise ApiException(
                409,
                "customers.conflict.default_address",
                "errors.customers.customer_address.default_conflict",
            )

    @staticmethod
    def _validate_contact_path(tenant_id: str, customer_id: str, payload: CustomerContactCreate) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "customers.validation.contact_tenant_mismatch",
                "errors.customers.contact.tenant_mismatch",
                {"tenant_id": tenant_id},
            )
        if payload.customer_id != customer_id:
            raise ApiException(
                400,
                "customers.validation.contact_customer_mismatch",
                "errors.customers.contact.customer_mismatch",
                {"customer_id": customer_id},
            )

    @staticmethod
    def _validate_address_path(tenant_id: str, customer_id: str, payload: CustomerAddressCreate) -> None:
        if payload.tenant_id != tenant_id:
            raise ApiException(
                400,
                "customers.validation.address_tenant_mismatch",
                "errors.customers.customer_address.tenant_mismatch",
                {"tenant_id": tenant_id},
            )
        if payload.customer_id != customer_id:
            raise ApiException(
                400,
                "customers.validation.address_customer_mismatch",
                "errors.customers.customer_address.customer_mismatch",
                {"customer_id": customer_id},
            )

    def _require_customer(self, tenant_id: str, customer_id: str, actor: RequestAuthorizationContext) -> Customer:
        self._ensure_tenant_scope(actor, tenant_id)
        customer = self.repository.get_customer(tenant_id, customer_id)
        if customer is None:
            raise self._not_found("customer")
        return customer

    @staticmethod
    def _ensure_tenant_scope(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        enforce_customer_module_access(actor, tenant_id=tenant_id)

    @staticmethod
    def _not_found(entity: str) -> ApiException:
        return ApiException(
            404,
            f"customers.not_found.{entity}",
            f"errors.customers.{entity}.not_found",
        )

    @staticmethod
    def _require_version(expected: int, provided: int | None, entity: str) -> None:
        if provided is None or provided != expected:
            raise ApiException(
                409,
                f"customers.conflict.stale_{entity}_version",
                f"errors.customers.{entity}.stale_version",
                {"expected_version_no": expected},
            )

    @staticmethod
    def _normalize_lifecycle(payload, *, current_archived_at: datetime | None):  # noqa: ANN001, ANN205
        data = payload.model_dump(exclude_unset=True)
        status = data.get("status")
        archived_at = data.get("archived_at")
        if current_archived_at is not None and status is not None and status != "archived":
            raise ApiException(
                409,
                "customers.conflict.archived_record",
                "errors.customers.lifecycle.archived_record",
            )
        if status == "archived" and archived_at is None:
            data["archived_at"] = datetime.now(UTC)
        if archived_at is not None and status is None:
            data["status"] = "archived"
        if archived_at is not None and data.get("status") not in (None, "archived"):
            raise ApiException(
                400,
                "customers.validation.lifecycle_mismatch",
                "errors.customers.lifecycle.invalid_archive_state",
            )
        return payload.__class__(**data)

    @staticmethod
    def _effective_value(payload, current, field_name: str):  # noqa: ANN001, ANN205
        if field_name in payload.model_fields_set:
            return getattr(payload, field_name)
        return getattr(current, field_name)

    def _record_history(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
        *,
        entry_type: str,
        title: str,
        summary: str,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
        metadata_json: dict[str, object] | None = None,
        related_contact_id: str | None = None,
        related_address_link_id: str | None = None,
        integration_job_id: str | None = None,
    ) -> None:
        self.repository.create_history_entry(
            CustomerHistoryEntry(
                tenant_id=tenant_id,
                customer_id=customer_id,
                entry_type=entry_type,
                title=title,
                summary=summary,
                actor_user_id=actor.user_id,
                related_contact_id=related_contact_id,
                related_address_link_id=related_address_link_id,
                integration_job_id=integration_job_id,
                before_json=before_json or {},
                after_json=after_json or {},
                metadata_json=metadata_json or {},
            )
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

    @staticmethod
    def _customer_snapshot(customer) -> dict[str, object]:  # noqa: ANN001
        return {
            "customer_number": customer.customer_number,
            "name": customer.name,
            "legal_name": customer.legal_name,
            "status": customer.status,
            "default_branch_id": customer.default_branch_id,
            "default_mandate_id": customer.default_mandate_id,
            "classification_lookup_id": customer.classification_lookup_id,
            "ranking_lookup_id": customer.ranking_lookup_id,
            "customer_status_lookup_id": customer.customer_status_lookup_id,
        }

    @staticmethod
    def _contact_snapshot(contact) -> dict[str, object]:  # noqa: ANN001
        return {
            "full_name": contact.full_name,
            "email": contact.email,
            "phone": contact.phone,
            "mobile": contact.mobile,
            "is_primary_contact": contact.is_primary_contact,
            "is_billing_contact": contact.is_billing_contact,
            "user_id": contact.user_id,
            "status": contact.status,
        }

    @staticmethod
    def _address_snapshot(address) -> dict[str, object]:  # noqa: ANN001
        return {
            "address_id": address.address_id,
            "address_type": address.address_type,
            "label": address.label,
            "is_default": address.is_default,
            "status": address.status,
        }

    def _build_customer_history(self, before, after):  # noqa: ANN001, ANN205
        before_json = self._customer_snapshot(before)
        after_json = self._customer_snapshot(after)
        changes = [key for key, value in after_json.items() if before_json.get(key) != value]
        if not changes:
            return None
        if "status" in changes:
            return {
                "entry_type": "customer.status.changed",
                "title": "Customer status changed",
                "summary": f"Changed customer status from {before.status} to {after.status}.",
                "before_json": before_json,
                "after_json": after_json,
                "metadata_json": {"changed_fields": changes},
            }
        return {
            "entry_type": "customer.updated",
            "title": "Customer master data updated",
            "summary": f"Updated customer fields: {', '.join(changes)}.",
            "before_json": before_json,
            "after_json": after_json,
            "metadata_json": {"changed_fields": changes},
        }

    def _build_contact_history(self, before, after):  # noqa: ANN001, ANN205
        before_json = self._contact_snapshot(before)
        after_json = self._contact_snapshot(after)
        changes = [key for key, value in after_json.items() if before_json.get(key) != value]
        if not changes:
            return None
        if "user_id" in changes:
            return {
                "entry_type": "customer.portal_link.changed",
                "title": "Customer portal link changed",
                "summary": f"Updated portal linkage for contact {after.full_name}.",
                "before_json": before_json,
                "after_json": after_json,
                "metadata_json": {"changed_fields": changes},
            }
        if "is_primary_contact" in changes:
            return {
                "entry_type": "customer.primary_contact.changed",
                "title": "Primary contact changed",
                "summary": f"Updated primary-contact flag for {after.full_name}.",
                "before_json": before_json,
                "after_json": after_json,
                "metadata_json": {"changed_fields": changes},
            }
        return {
            "entry_type": "customer.contact.updated",
            "title": "Customer contact updated",
            "summary": f"Updated contact fields for {after.full_name}: {', '.join(changes)}.",
            "before_json": before_json,
            "after_json": after_json,
            "metadata_json": {"changed_fields": changes},
        }

    def _build_address_history(self, before, after):  # noqa: ANN001, ANN205
        before_json = self._address_snapshot(before)
        after_json = self._address_snapshot(after)
        changes = [key for key, value in after_json.items() if before_json.get(key) != value]
        if not changes:
            return None
        return {
            "entry_type": "customer.address.updated",
            "title": "Customer address updated",
            "summary": f"Updated {after.address_type} address linkage: {', '.join(changes)}.",
            "before_json": before_json,
            "after_json": after_json,
            "metadata_json": {"changed_fields": changes},
        }

    @staticmethod
    def _customer_audit_event_type(entry_type: str) -> str:
        if entry_type == "customer.status.changed":
            return "customers.customer.lifecycle_changed"
        return "customers.customer.updated"

    @staticmethod
    def _contact_audit_event_type(entry_type: str) -> str:
        if entry_type == "customer.portal_link.changed":
            return "customers.contact.portal_link_changed"
        if entry_type == "customer.primary_contact.changed":
            return "customers.contact.primary_changed"
        return "customers.contact.updated"
