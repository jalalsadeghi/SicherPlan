from __future__ import annotations

import unittest
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Index, UniqueConstraint

from app.db import Base
from app.errors import ApiException
from app.modules.core.schemas import AddressRead
from app.modules.customers.commercial_service import CustomerCommercialService
from app.modules.customers.models import CustomerBillingProfile, CustomerInvoiceParty
from app.modules.customers.schemas import (
    CustomerBillingProfileCreate,
    CustomerBillingProfileUpdate,
    CustomerCommercialProfileRead,
    CustomerCreate,
    CustomerInvoicePartyCreate,
    CustomerInvoicePartyUpdate,
)
from app.modules.customers.service import CustomerService
from app.modules.iam.audit_service import AuditService
from tests.modules.customers.test_customer_backbone import (
    FakeAddress,
    FakeCustomerRepository,
    FakeLookup,
    _actor,
)


@dataclass
class FakeBillingProfile:
    id: str
    tenant_id: str
    customer_id: str
    invoice_email: str | None = None
    payment_terms_days: int | None = None
    payment_terms_note: str | None = None
    tax_number: str | None = None
    vat_id: str | None = None
    tax_exempt: bool = False
    tax_exemption_reason: str | None = None
    bank_account_holder: str | None = None
    bank_iban: str | None = None
    bank_bic: str | None = None
    bank_name: str | None = None
    contract_reference: str | None = None
    debtor_number: str | None = None
    e_invoice_enabled: bool = False
    leitweg_id: str | None = None
    invoice_layout_code: str | None = None
    shipping_method_code: str | None = None
    dunning_policy_code: str | None = None
    billing_note: str | None = None
    status: str = "active"
    version_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None


@dataclass
class FakeInvoiceParty:
    id: str
    tenant_id: str
    customer_id: str
    company_name: str
    address_id: str
    contact_name: str | None = None
    invoice_email: str | None = None
    invoice_layout_lookup_id: str | None = None
    external_ref: str | None = None
    is_default: bool = False
    note: str | None = None
    status: str = "active"
    version_no: int = 1
    address: AddressRead | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None


class FakeCommercialCustomerRepository(FakeCustomerRepository):
    def __init__(self) -> None:
        super().__init__()
        self.lookups["lookup-layout"] = FakeLookup("lookup-layout", "invoice_layout", code="standard")
        self.lookups["lookup-delivery-email"] = FakeLookup(
            "lookup-delivery-email",
            "invoice_delivery_method",
            code="email_pdf",
        )
        self.lookups["lookup-delivery-einvoice"] = FakeLookup(
            "lookup-delivery-einvoice",
            "invoice_delivery_method",
            code="e_invoice",
        )
        self.lookups["lookup-dunning-standard"] = FakeLookup("lookup-dunning-standard", "dunning_policy", code="standard")
        self.addresses["address-2"] = FakeAddress("address-2", street_line_1="Nebenstrasse 2")
        self.billing_profiles: dict[str, FakeBillingProfile] = {}
        self.invoice_parties: dict[str, list[FakeInvoiceParty]] = {}

    def get_billing_profile(self, tenant_id: str, customer_id: str) -> FakeBillingProfile | None:
        row = self.billing_profiles.get(customer_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def create_billing_profile(self, tenant_id: str, customer_id: str, payload: CustomerBillingProfileCreate, actor_user_id: str | None):
        row = FakeBillingProfile(
            id=str(uuid4()),
            tenant_id=tenant_id,
            customer_id=customer_id,
            invoice_email=payload.invoice_email,
            payment_terms_days=payload.payment_terms_days,
            payment_terms_note=payload.payment_terms_note,
            tax_number=payload.tax_number,
            vat_id=payload.vat_id,
            tax_exempt=payload.tax_exempt,
            tax_exemption_reason=payload.tax_exemption_reason,
            bank_account_holder=payload.bank_account_holder,
            bank_iban=payload.bank_iban,
            bank_bic=payload.bank_bic,
            bank_name=payload.bank_name,
            contract_reference=payload.contract_reference,
            debtor_number=payload.debtor_number,
            e_invoice_enabled=payload.e_invoice_enabled,
            leitweg_id=payload.leitweg_id,
            invoice_layout_code=payload.invoice_layout_code,
            shipping_method_code=payload.shipping_method_code,
            dunning_policy_code=payload.dunning_policy_code,
            billing_note=payload.billing_note,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.billing_profiles[customer_id] = row
        return row

    def update_billing_profile(self, tenant_id: str, customer_id: str, payload: CustomerBillingProfileUpdate, actor_user_id: str | None):
        row = self.get_billing_profile(tenant_id, customer_id)
        if row is None:
            return None
        updates = payload.model_dump(exclude_unset=True, exclude={"version_no"})
        next_row = replace(
            row,
            **updates,
            version_no=row.version_no + 1,
            updated_by_user_id=actor_user_id,
            updated_at=datetime.now(UTC),
        )
        self.billing_profiles[customer_id] = next_row
        return next_row

    def list_invoice_parties(self, tenant_id: str, customer_id: str) -> list[FakeInvoiceParty]:
        return [row for row in self.invoice_parties.get(customer_id, []) if row.tenant_id == tenant_id]

    def get_invoice_party(self, tenant_id: str, customer_id: str, invoice_party_id: str) -> FakeInvoiceParty | None:
        return next(
            (
                row
                for row in self.invoice_parties.get(customer_id, [])
                if row.tenant_id == tenant_id and row.id == invoice_party_id
            ),
            None,
        )

    def create_invoice_party(self, tenant_id: str, customer_id: str, payload: CustomerInvoicePartyCreate, actor_user_id: str | None):
        address = AddressRead.model_validate(self.addresses[payload.address_id])
        row = FakeInvoiceParty(
            id=str(uuid4()),
            tenant_id=tenant_id,
            customer_id=customer_id,
            company_name=payload.company_name,
            contact_name=payload.contact_name,
            address_id=payload.address_id,
            invoice_email=payload.invoice_email,
            invoice_layout_lookup_id=payload.invoice_layout_lookup_id,
            external_ref=payload.external_ref,
            is_default=payload.is_default,
            note=payload.note,
            address=address,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.invoice_parties.setdefault(customer_id, []).append(row)
        return row

    def update_invoice_party(self, tenant_id: str, customer_id: str, invoice_party_id: str, payload: CustomerInvoicePartyUpdate, actor_user_id: str | None):
        row = self.get_invoice_party(tenant_id, customer_id, invoice_party_id)
        if row is None:
            return None
        updates = payload.model_dump(exclude_unset=True, exclude={"version_no"})
        next_row = replace(
            row,
            **updates,
            version_no=row.version_no + 1,
            updated_by_user_id=actor_user_id,
            updated_at=datetime.now(UTC),
        )
        if next_row.address_id in self.addresses:
            next_row.address = AddressRead.model_validate(self.addresses[next_row.address_id])
        self.invoice_parties[customer_id] = [next_row if party.id == invoice_party_id else party for party in self.invoice_parties.get(customer_id, [])]
        return next_row

    def has_default_invoice_party(self, tenant_id: str, customer_id: str, *, exclude_id: str | None = None) -> bool:
        return any(
            row.id != exclude_id and row.tenant_id == tenant_id and row.is_default and row.archived_at is None
            for row in self.invoice_parties.get(customer_id, [])
        )

    def list_rate_cards(self, tenant_id: str, customer_id: str) -> list[object]:
        return []

    def find_lookup_by_domain_code(self, tenant_id: str | None, domain: str, code: str) -> FakeLookup | None:
        return next(
            (
                row
                for row in self.lookups.values()
                if row.domain == domain and row.tenant_id in (tenant_id, None) and row.code == code
            ),
            None,
        )


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.audit_events: list[object] = []

    def create_login_event(self, payload):  # noqa: ANN001
        return payload

    def create_audit_event(self, payload):  # noqa: ANN001
        self.audit_events.append(payload)
        return payload


class TestCustomerCommercialMetadata(unittest.TestCase):
    def test_commercial_tables_are_registered(self) -> None:
        self.assertIn("crm.customer_billing_profile", Base.metadata.tables)
        self.assertIn("crm.customer_invoice_party", Base.metadata.tables)

    def test_invoice_party_default_constraint_is_stable(self) -> None:
        invoice_indexes = {index.name for index in CustomerInvoiceParty.__table__.indexes if isinstance(index, Index)}
        profile_constraints = {
            constraint.name for constraint in CustomerBillingProfile.__table__.constraints if isinstance(constraint, UniqueConstraint)
        }

        self.assertIn("uq_crm_customer_billing_profile_customer", profile_constraints)
        self.assertIn("uq_crm_customer_billing_profile_tenant_id_id", profile_constraints)
        self.assertIn("uq_crm_customer_invoice_party_default_per_customer", invoice_indexes)


class TestCustomerCommercialService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeCommercialCustomerRepository()
        self.audit_repo = RecordingAuditRepository()
        self.customer_service = CustomerService(self.repository)
        self.service = CustomerCommercialService(self.repository, audit_service=AuditService(self.audit_repo))
        self.customer = self.customer_service.create_customer(
            "tenant-1",
            CustomerCreate(tenant_id="tenant-1", customer_number="K-1000", name="Nord Security GmbH"),
            _actor(),
        )

    def test_billing_profile_can_be_created_and_updated(self) -> None:
        created = self.service.upsert_billing_profile(
            "tenant-1",
            self.customer.id,
            CustomerBillingProfileCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                invoice_email="rechnung@example.invalid",
                payment_terms_days=14,
                tax_exempt=True,
                tax_exemption_reason="Behorde",
                bank_account_holder="Nord Security GmbH",
                bank_iban="DE1234567890",
                invoice_layout_code="standard",
                shipping_method_code="email_pdf",
                dunning_policy_code="standard",
            ),
            _actor(),
        )
        updated = self.service.upsert_billing_profile(
            "tenant-1",
            self.customer.id,
            CustomerBillingProfileUpdate(
                payment_terms_days=30,
                version_no=created.version_no,
            ),
            _actor(),
        )

        self.assertEqual(created.invoice_email, "rechnung@example.invalid")
        self.assertEqual(created.shipping_method_code, "email_pdf")
        self.assertEqual(updated.payment_terms_days, 30)
        self.assertGreaterEqual(len(self.audit_repo.audit_events), 2)

    def test_billing_profile_validates_tax_and_bank_combinations(self) -> None:
        with self.assertRaises(ApiException) as tax_context:
            self.service.upsert_billing_profile(
                "tenant-1",
                self.customer.id,
                CustomerBillingProfileCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    tax_exempt=True,
                ),
                _actor(),
            )
        with self.assertRaises(ApiException) as bank_context:
            self.service.upsert_billing_profile(
                "tenant-1",
                self.customer.id,
                CustomerBillingProfileCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    bank_name="Nord Bank",
                ),
                _actor(),
            )

        self.assertEqual(tax_context.exception.code, "customers.validation.tax_exemption_reason")
        self.assertEqual(bank_context.exception.code, "customers.validation.bank_account_holder")

    def test_billing_profile_validates_advanced_invoice_configuration_combinations(self) -> None:
        with self.assertRaises(ApiException) as e_invoice_context:
            self.service.upsert_billing_profile(
                "tenant-1",
                self.customer.id,
                CustomerBillingProfileCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    e_invoice_enabled=True,
                    shipping_method_code="email_pdf",
                ),
                _actor(),
            )
        with self.assertRaises(ApiException) as leitweg_context:
            self.service.upsert_billing_profile(
                "tenant-1",
                self.customer.id,
                CustomerBillingProfileCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    e_invoice_enabled=True,
                    shipping_method_code="e_invoice",
                ),
                _actor(),
            )
        with self.assertRaises(ApiException) as email_context:
            self.service.upsert_billing_profile(
                "tenant-1",
                self.customer.id,
                CustomerBillingProfileCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    shipping_method_code="email_pdf",
                ),
                _actor(),
            )

        self.assertEqual(e_invoice_context.exception.code, "customers.validation.billing_profile_e_invoice_dispatch_mismatch")
        self.assertEqual(leitweg_context.exception.code, "customers.validation.billing_profile_leitweg_required")
        self.assertEqual(email_context.exception.code, "customers.validation.billing_profile_dispatch_email_required")

    def test_invoice_parties_enforce_single_default_and_shared_address_linkage(self) -> None:
        first = self.service.create_invoice_party(
            "tenant-1",
            self.customer.id,
            CustomerInvoicePartyCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                company_name="Nord Billing GmbH",
                address_id="address-1",
                is_default=True,
            ),
            _actor(),
        )

        with self.assertRaises(ApiException) as conflict:
            self.service.create_invoice_party(
                "tenant-1",
                self.customer.id,
                CustomerInvoicePartyCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    company_name="Nord Billing 2 GmbH",
                    address_id="address-2",
                    is_default=True,
                ),
                _actor(),
            )

        second = self.service.create_invoice_party(
            "tenant-1",
            self.customer.id,
            CustomerInvoicePartyCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                company_name="Nord Billing 2 GmbH",
                address_id="address-2",
                invoice_layout_lookup_id="lookup-layout",
                is_default=False,
            ),
            _actor(),
        )

        self.assertEqual(first.address.street_line_1, "Hauptstrasse 1")
        self.assertEqual(second.address.street_line_1, "Nebenstrasse 2")
        self.assertEqual(conflict.exception.code, "customers.conflict.default_invoice_party")

    def test_finance_read_contract_returns_profile_and_invoice_parties(self) -> None:
        profile = self.service.upsert_billing_profile(
            "tenant-1",
            self.customer.id,
            CustomerBillingProfileCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                invoice_email="finance@example.invalid",
                bank_account_holder="Nord Security GmbH",
                bank_iban="DE4455667788",
            ),
            _actor(),
        )
        party = self.service.create_invoice_party(
            "tenant-1",
            self.customer.id,
            CustomerInvoicePartyCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                company_name="Nord Invoice Party",
                address_id="address-1",
            ),
            _actor(),
        )

        contract = self.service.get_commercial_profile("tenant-1", self.customer.id, _actor())

        self.assertIsInstance(contract, CustomerCommercialProfileRead)
        self.assertEqual(contract.billing_profile.id, profile.id)
        self.assertEqual(contract.invoice_parties[0].id, party.id)

    def test_invoice_party_update_requires_current_version(self) -> None:
        party = self.service.create_invoice_party(
            "tenant-1",
            self.customer.id,
            CustomerInvoicePartyCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                company_name="Nord Invoice Party",
                address_id="address-1",
            ),
            _actor(),
        )

        with self.assertRaises(ApiException) as context:
            self.service.update_invoice_party(
                "tenant-1",
                self.customer.id,
                party.id,
                CustomerInvoicePartyUpdate(company_name="Updated", version_no=99),
                _actor(),
            )

        self.assertEqual(context.exception.code, "customers.conflict.stale_invoice_party_version")


if __name__ == "__main__":
    unittest.main()
