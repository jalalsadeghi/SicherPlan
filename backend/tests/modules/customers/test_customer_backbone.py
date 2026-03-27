from __future__ import annotations

import unittest
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from app.db import Base
from app.errors import ApiException
from app.modules.core.schemas import AddressRead
from app.modules.customers.models import Customer, CustomerAddressLink, CustomerContact, CustomerHistoryEntry
from app.modules.customers.schemas import (
    CustomerAddressCreate,
    CustomerAddressUpdate,
    CustomerContactCreate,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerFilter,
    CustomerUpdate,
)
from app.modules.customers.service import CustomerService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext

PORTAL_USER_ID = "11111111-1111-4111-8111-111111111111"
FOREIGN_PORTAL_USER_ID = "22222222-2222-4222-8222-222222222222"


@dataclass
class FakeLookup:
    id: str
    domain: str
    code: str | None = None
    label: str | None = None
    description: str | None = None
    sort_order: int = 100
    tenant_id: str | None = None
    archived_at: datetime | None = None


@dataclass
class FakeBranch:
    id: str
    tenant_id: str
    code: str = "BER"
    name: str = "Berlin"


@dataclass
class FakeMandate:
    id: str
    tenant_id: str
    branch_id: str
    code: str = "M-1"
    name: str = "Nord"


@dataclass
class FakeUser:
    id: str
    tenant_id: str
    archived_at: datetime | None = None


@dataclass
class FakeAddress:
    id: str
    street_line_1: str = "Hauptstrasse 1"
    street_line_2: str | None = None
    postal_code: str = "20095"
    city: str = "Hamburg"
    state: str | None = None
    country_code: str = "DE"


@dataclass
class FakeCustomerContact:
    id: str
    tenant_id: str
    customer_id: str
    full_name: str
    title: str | None = None
    function_label: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    is_primary_contact: bool = False
    is_billing_contact: bool = False
    user_id: str | None = None
    notes: str | None = None
    status: str = "active"
    version_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None


@dataclass
class FakeCustomerAddress:
    id: str
    tenant_id: str
    customer_id: str
    address_id: str
    address_type: str
    label: str | None = None
    is_default: bool = False
    status: str = "active"
    version_no: int = 1
    address: AddressRead | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None


@dataclass
class FakeCustomer:
    id: str
    tenant_id: str
    customer_number: str
    name: str
    legal_name: str | None = None
    external_ref: str | None = None
    legal_form_lookup_id: str | None = None
    classification_lookup_id: str | None = None
    ranking_lookup_id: str | None = None
    customer_status_lookup_id: str | None = None
    default_branch_id: str | None = None
    default_mandate_id: str | None = None
    notes: str | None = None
    portal_person_names_released: bool = False
    portal_person_names_released_at: datetime | None = None
    portal_person_names_released_by_user_id: str | None = None
    status: str = "active"
    version_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None
    contacts: list[FakeCustomerContact] = field(default_factory=list)
    addresses: list[FakeCustomerAddress] = field(default_factory=list)
    history_entries: list["FakeCustomerHistoryEntry"] = field(default_factory=list)
    employee_blocks: list["FakeCustomerEmployeeBlock"] = field(default_factory=list)


@dataclass
class FakeCustomerHistoryEntry:
    id: str
    tenant_id: str
    customer_id: str
    entry_type: str
    title: str
    summary: str
    actor_user_id: str | None = None
    related_contact_id: str | None = None
    related_address_link_id: str | None = None
    integration_job_id: str | None = None
    sort_order: int = 0
    before_json: dict[str, object] = field(default_factory=dict)
    after_json: dict[str, object] = field(default_factory=dict)
    metadata_json: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeCustomerEmployeeBlock:
    id: str
    tenant_id: str
    customer_id: str
    employee_id: str
    reason: str
    effective_from: date
    effective_to: date | None = None
    status: str = "active"
    version_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    archived_at: datetime | None = None


class FakeCustomerRepository:
    def __init__(self) -> None:
        self.lookups = {
            "lookup-legal": FakeLookup("lookup-legal", "legal_form", "gmbh", "GmbH"),
            "lookup-category": FakeLookup("lookup-category", "customer_category", "standard", "Standardkunde", tenant_id="tenant-1"),
            "lookup-ranking": FakeLookup("lookup-ranking", "customer_ranking", "a", "A-Kunde", tenant_id="tenant-1"),
            "lookup-status": FakeLookup("lookup-status", "customer_status", "qualified", "Qualifiziert"),
        }
        self.branches = {"branch-1": FakeBranch("branch-1", "tenant-1")}
        self.mandates = {"mandate-1": FakeMandate("mandate-1", "tenant-1", "branch-1")}
        self.users = {PORTAL_USER_ID: FakeUser(PORTAL_USER_ID, "tenant-1")}
        self.addresses = {"address-1": FakeAddress("address-1")}
        self.customers: dict[str, FakeCustomer] = {}
        self.customer_portal_policy = {
            "version": "v1",
            "customer_watchbook_entries_enabled": False,
        }

    def list_customers(self, tenant_id: str, filters: CustomerFilter) -> list[FakeCustomer]:
        rows = [row for row in self.customers.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.search:
            term = filters.search.lower()
            rows = [row for row in rows if term in row.customer_number.lower() or term in row.name.lower()]
        return sorted(rows, key=lambda row: row.customer_number)

    def get_customer(self, tenant_id: str, customer_id: str) -> FakeCustomer | None:
        customer = self.customers.get(customer_id)
        if customer is None or customer.tenant_id != tenant_id:
            return None
        return customer

    def get_customer_portal_policy(self, tenant_id: str) -> dict[str, object]:
        return dict(self.customer_portal_policy)

    def get_portal_contact_for_user(self, tenant_id: str, user_id: str):
        for customer in self.customers.values():
            if customer.tenant_id != tenant_id:
                continue
            for contact in customer.contacts:
                if contact.user_id == user_id and contact.archived_at is None:
                    return customer, contact
        return None

    def get_portal_customer_scope_match(self, tenant_id: str, user_id: str, allowed_customer_ids: list[str]):
        for customer in self.customers.values():
            if customer.tenant_id != tenant_id or customer.id not in allowed_customer_ids:
                continue
            for contact in customer.contacts:
                if contact.user_id == user_id and contact.archived_at is None:
                    return customer, contact
        return None

    def list_history_entries(self, tenant_id: str, customer_id: str) -> list[FakeCustomerHistoryEntry]:
        customer = self.get_customer(tenant_id, customer_id)
        if customer is None:
            return []
        return sorted(customer.history_entries, key=lambda row: (row.created_at, row.sort_order), reverse=True)

    def create_history_entry(self, row: CustomerHistoryEntry) -> FakeCustomerHistoryEntry:
        history_row = FakeCustomerHistoryEntry(
            id=getattr(row, "id", None) or str(uuid4()),
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            entry_type=row.entry_type,
            title=row.title,
            summary=row.summary,
            actor_user_id=row.actor_user_id,
            related_contact_id=row.related_contact_id,
            related_address_link_id=row.related_address_link_id,
            integration_job_id=row.integration_job_id,
            sort_order=row.sort_order or 0,
            before_json=dict(row.before_json),
            after_json=dict(row.after_json),
            metadata_json=dict(row.metadata_json),
            created_at=row.created_at or datetime.now(UTC),
        )
        customer = self.customers[history_row.customer_id]
        customer.history_entries.insert(0, history_row)
        return history_row

    def get_history_entry(self, tenant_id: str, customer_id: str, history_entry_id: str):
        customer = self.get_customer(tenant_id, customer_id)
        if customer is None:
            return None
        return next((row for row in customer.history_entries if row.id == history_entry_id), None)

    def list_employee_blocks(self, tenant_id: str, customer_id: str) -> list[FakeCustomerEmployeeBlock]:
        customer = self.get_customer(tenant_id, customer_id)
        if customer is None:
            return []
        return sorted(customer.employee_blocks, key=lambda row: (row.effective_from, row.created_at), reverse=True)

    def get_employee_block(self, tenant_id: str, customer_id: str, block_id: str):
        customer = self.get_customer(tenant_id, customer_id)
        if customer is None:
            return None
        return next((row for row in customer.employee_blocks if row.id == block_id), None)

    def find_overlapping_employee_block(
        self,
        tenant_id: str,
        customer_id: str,
        employee_id: str,
        effective_from,
        effective_to,
        *,
        exclude_id: str | None = None,
    ):
        candidate_end = effective_to or effective_from
        for row in self.list_employee_blocks(tenant_id, customer_id):
            if row.employee_id != employee_id or row.archived_at is not None:
                continue
            if exclude_id and row.id == exclude_id:
                continue
            row_end = row.effective_to or row.effective_from
            if row.effective_from <= candidate_end and row_end >= effective_from:
                return row
        return None

    def create_employee_block(self, row) -> FakeCustomerEmployeeBlock:  # noqa: ANN001
        block = FakeCustomerEmployeeBlock(
            id=getattr(row, "id", None) or str(uuid4()),
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            employee_id=row.employee_id,
            reason=row.reason,
            effective_from=row.effective_from,
            effective_to=row.effective_to,
            created_by_user_id=row.created_by_user_id,
            updated_by_user_id=row.updated_by_user_id,
        )
        customer = self.customers[block.customer_id]
        customer.employee_blocks.insert(0, block)
        return block

    def update_employee_block(self, tenant_id: str, customer_id: str, block_id: str, payload, actor_user_id: str | None):
        row = self.get_employee_block(tenant_id, customer_id, block_id)
        if row is None:
            return None
        updates = payload.model_dump(exclude_unset=True, exclude={"version_no"})
        next_row = replace(
            row,
            reason=updates.get("reason", row.reason),
            effective_from=updates.get("effective_from", row.effective_from),
            effective_to=updates.get("effective_to", row.effective_to),
            status=updates.get("status", row.status),
            archived_at=updates.get("archived_at", row.archived_at),
            updated_by_user_id=actor_user_id,
            updated_at=datetime.now(UTC),
            version_no=row.version_no + 1,
        )
        customer = self.customers[row.customer_id]
        customer.employee_blocks = [next_row if item.id == row.id else item for item in customer.employee_blocks]
        return next_row

    def create_customer(self, tenant_id: str, payload: CustomerCreate, actor_user_id: str | None) -> FakeCustomer:
        row = FakeCustomer(
            id=str(uuid4()),
            tenant_id=tenant_id,
            customer_number=payload.customer_number,
            name=payload.name,
            status=payload.status or "active",
            legal_name=payload.legal_name,
            external_ref=payload.external_ref,
            legal_form_lookup_id=payload.legal_form_lookup_id,
            classification_lookup_id=payload.classification_lookup_id,
            ranking_lookup_id=payload.ranking_lookup_id,
            customer_status_lookup_id=payload.customer_status_lookup_id,
            default_branch_id=payload.default_branch_id,
            default_mandate_id=payload.default_mandate_id,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.customers[row.id] = row
        return row

    def update_customer(self, tenant_id: str, customer_id: str, payload: CustomerUpdate, actor_user_id: str | None):
        row = self.get_customer(tenant_id, customer_id)
        if row is None:
            return None
        updates = payload.model_dump(exclude_unset=True, exclude={"version_no"})
        next_row = replace(
            row,
            **updates,
            updated_by_user_id=actor_user_id,
            version_no=row.version_no + 1,
            updated_at=datetime.now(UTC),
        )
        self.customers[row.id] = next_row
        return next_row

    def list_contacts(self, tenant_id: str, customer_id: str) -> list[FakeCustomerContact]:
        customer = self.get_customer(tenant_id, customer_id)
        return list(customer.contacts if customer else [])

    def get_contact(self, tenant_id: str, customer_id: str, contact_id: str) -> FakeCustomerContact | None:
        customer = self.get_customer(tenant_id, customer_id)
        if customer is None:
            return None
        return next((row for row in customer.contacts if row.id == contact_id), None)

    def create_contact(self, tenant_id: str, customer_id: str, payload: CustomerContactCreate, actor_user_id: str | None):
        customer = self.customers[customer_id]
        row = FakeCustomerContact(
            id=str(uuid4()),
            tenant_id=tenant_id,
            customer_id=customer_id,
            full_name=payload.full_name,
            title=payload.title,
            function_label=payload.function_label,
            email=payload.email,
            phone=payload.phone,
            mobile=payload.mobile,
            is_primary_contact=payload.is_primary_contact,
            is_billing_contact=payload.is_billing_contact,
            user_id=payload.user_id,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        customer.contacts.append(row)
        return row

    def update_contact(self, tenant_id: str, customer_id: str, contact_id: str, payload: CustomerContactUpdate, actor_user_id: str | None):
        row = self.get_contact(tenant_id, customer_id, contact_id)
        if row is None:
            return None
        customer = self.customers[customer_id]
        updates = payload.model_dump(exclude_unset=True, exclude={"version_no"})
        next_row = replace(
            row,
            **updates,
            updated_by_user_id=actor_user_id,
            version_no=row.version_no + 1,
            updated_at=datetime.now(UTC),
        )
        customer.contacts = [next_row if contact.id == contact_id else contact for contact in customer.contacts]
        return next_row

    def list_customer_addresses(self, tenant_id: str, customer_id: str) -> list[FakeCustomerAddress]:
        customer = self.get_customer(tenant_id, customer_id)
        return list(customer.addresses if customer else [])

    def get_customer_address(self, tenant_id: str, customer_id: str, link_id: str) -> FakeCustomerAddress | None:
        customer = self.get_customer(tenant_id, customer_id)
        if customer is None:
            return None
        return next((row for row in customer.addresses if row.id == link_id), None)

    def create_customer_address(self, tenant_id: str, customer_id: str, payload: CustomerAddressCreate, actor_user_id: str | None):
        customer = self.customers[customer_id]
        address = self.addresses[payload.address_id]
        row = FakeCustomerAddress(
            id=str(uuid4()),
            tenant_id=tenant_id,
            customer_id=customer_id,
            address_id=payload.address_id,
            address_type=payload.address_type,
            label=payload.label,
            is_default=payload.is_default,
            address=AddressRead.model_validate(address),
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        customer.addresses.append(row)
        return row

    def update_customer_address(self, tenant_id: str, customer_id: str, link_id: str, payload: CustomerAddressUpdate, actor_user_id: str | None):
        row = self.get_customer_address(tenant_id, customer_id, link_id)
        if row is None:
            return None
        customer = self.customers[customer_id]
        updates = payload.model_dump(exclude_unset=True, exclude={"version_no"})
        next_row = replace(
            row,
            **updates,
            updated_by_user_id=actor_user_id,
            version_no=row.version_no + 1,
            updated_at=datetime.now(UTC),
        )
        if next_row.address_id in self.addresses:
            next_row.address = AddressRead.model_validate(self.addresses[next_row.address_id])
        customer.addresses = [next_row if address.id == link_id else address for address in customer.addresses]
        return next_row

    def find_customer_by_number(self, tenant_id: str, customer_number: str, *, exclude_id: str | None = None):
        for row in self.customers.values():
            if row.tenant_id == tenant_id and row.customer_number == customer_number and row.id != exclude_id:
                return row
        return None

    def find_contact_by_email(self, tenant_id: str, customer_id: str, email: str, *, exclude_id: str | None = None):
        customer = self.get_customer(tenant_id, customer_id)
        if customer is None:
            return None
        for row in customer.contacts:
            if row.id != exclude_id and row.archived_at is None and row.email and row.email.lower() == email.lower():
                return row
        return None

    def has_primary_contact(self, tenant_id: str, customer_id: str, *, exclude_id: str | None = None) -> bool:
        return any(
            row.id != exclude_id and row.archived_at is None and row.is_primary_contact
            for row in self.list_contacts(tenant_id, customer_id)
        )

    def has_default_address(self, tenant_id: str, customer_id: str, address_type: str, *, exclude_id: str | None = None) -> bool:
        return any(
            row.id != exclude_id and row.archived_at is None and row.address_type == address_type and row.is_default
            for row in self.list_customer_addresses(tenant_id, customer_id)
        )

    def find_duplicate_address_link(self, tenant_id: str, customer_id: str, address_id: str, address_type: str, *, exclude_id: str | None = None):
        for row in self.list_customer_addresses(tenant_id, customer_id):
            if row.id != exclude_id and row.address_id == address_id and row.address_type == address_type:
                return row
        return None

    def get_lookup_value(self, lookup_id: str):
        return self.lookups.get(lookup_id)

    def list_lookup_values(self, tenant_id: str, domain: str):
        return [
            row
            for row in self.lookups.values()
            if row.domain == domain and row.archived_at is None and row.tenant_id in (None, tenant_id)
        ]

    def get_branch(self, tenant_id: str, branch_id: str):
        row = self.branches.get(branch_id)
        if row and row.tenant_id == tenant_id:
            return row
        return None

    def list_branches(self, tenant_id: str):
        return [row for row in self.branches.values() if row.tenant_id == tenant_id]

    def get_mandate(self, tenant_id: str, mandate_id: str):
        row = self.mandates.get(mandate_id)
        if row and row.tenant_id == tenant_id:
            return row
        return None

    def list_mandates(self, tenant_id: str):
        return [row for row in self.mandates.values() if row.tenant_id == tenant_id]

    def get_user_account(self, tenant_id: str, user_id: str):
        row = self.users.get(user_id)
        if row and row.tenant_id == tenant_id:
            return row
        return None

    def get_address(self, address_id: str):
        return self.addresses.get(address_id)


def _actor(tenant_id: str = "tenant-1", *, platform: bool = False) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-admin",
        tenant_id=tenant_id,
        role_keys=frozenset({"platform_admin"} if platform else {"tenant_admin"}),
        permission_keys=frozenset({"customers.customer.read", "customers.customer.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
    )


class TestCustomerMetadata(unittest.TestCase):
    def test_expected_crm_tables_are_registered(self) -> None:
        self.assertIn("crm.customer", Base.metadata.tables)
        self.assertIn("crm.customer_contact", Base.metadata.tables)
        self.assertIn("crm.customer_address", Base.metadata.tables)
        self.assertIn("crm.customer_history_entry", Base.metadata.tables)

    def test_customer_contact_and_address_constraints_are_stable(self) -> None:
        contact_indexes = {index.name for index in CustomerContact.__table__.indexes if isinstance(index, Index)}
        address_indexes = {index.name for index in CustomerAddressLink.__table__.indexes if isinstance(index, Index)}
        customer_constraints = {
            constraint.name for constraint in Customer.__table__.constraints if isinstance(constraint, UniqueConstraint)
        }

        self.assertIn("uq_crm_customer_tenant_customer_number", customer_constraints)
        self.assertIn("uq_crm_customer_contact_primary_per_customer", contact_indexes)
        self.assertIn("uq_crm_customer_contact_tenant_user_id", contact_indexes)
        self.assertIn("uq_crm_customer_address_default_per_type", address_indexes)

    def test_customer_address_schema_links_to_reusable_address(self) -> None:
        ddl = str(CreateTable(CustomerAddressLink.__table__).compile(dialect=dialect()))
        self.assertIn("address_id", ddl)
        self.assertIn("address_type", ddl)
        self.assertNotIn("postal_code", ddl)


class TestCustomerService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeCustomerRepository()
        self.service = CustomerService(self.repository)
        self.customer = self.service.create_customer(
            "tenant-1",
            CustomerCreate(
                tenant_id="tenant-1",
                customer_number="K-1000",
                name="Nord Security GmbH",
                legal_form_lookup_id="lookup-legal",
                classification_lookup_id="lookup-category",
                customer_status_lookup_id="lookup-status",
                default_branch_id="branch-1",
                default_mandate_id="mandate-1",
            ),
            _actor(),
        )

    def test_customer_can_be_created_updated_and_searched(self) -> None:
        updated = self.service.update_customer(
            "tenant-1",
            self.customer.id,
            CustomerUpdate(name="Nord Security AG", version_no=self.customer.version_no),
            _actor(),
        )
        listed = self.service.list_customers("tenant-1", CustomerFilter(search="K-1000"), _actor())

        self.assertEqual(updated.name, "Nord Security AG")
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].customer_number, "K-1000")

    def test_customer_reference_data_returns_lookup_and_structure_options(self) -> None:
        reference_data = self.service.get_reference_data("tenant-1", _actor())

        self.assertTrue(any(item.id == "lookup-legal" for item in reference_data.legal_forms))
        self.assertTrue(any(item.id == "lookup-category" for item in reference_data.classifications))
        self.assertTrue(any(item.id == "lookup-ranking" for item in reference_data.rankings))
        self.assertTrue(any(item.id == "lookup-status" for item in reference_data.customer_statuses))
        self.assertEqual(reference_data.branches[0].id, "branch-1")
        self.assertEqual(reference_data.mandates[0].branch_id, "branch-1")

    def test_customer_create_accepts_explicit_initial_status(self) -> None:
        customer = self.service.create_customer(
            "tenant-1",
            CustomerCreate(
                tenant_id="tenant-1",
                customer_number="K-1001",
                name="Musterkunde",
                status="inactive",
            ),
            _actor(),
        )

        self.assertEqual(customer.status, "inactive")

    def test_customer_create_rejects_invalid_initial_status(self) -> None:
        with self.assertRaises(ApiException) as context:
            self.service.create_customer(
                "tenant-1",
                CustomerCreate(
                    tenant_id="tenant-1",
                    customer_number="K-1002",
                    name="Fehlstatus GmbH",
                    status="archived",
                ),
                _actor(),
            )

        self.assertEqual(context.exception.code, "customers.validation.initial_status")

    def test_contact_and_address_link_can_be_added_with_portal_user(self) -> None:
        contact = self.service.create_contact(
            "tenant-1",
            self.customer.id,
            CustomerContactCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                full_name="Alex Kunde",
                email="alex@example.invalid",
                is_primary_contact=True,
                user_id=PORTAL_USER_ID,
            ),
            _actor(),
        )
        address = self.service.create_customer_address(
            "tenant-1",
            self.customer.id,
            CustomerAddressCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                address_id="address-1",
                address_type="billing",
                is_default=True,
            ),
            _actor(),
        )
        detail = self.service.get_customer("tenant-1", self.customer.id, _actor())

        self.assertEqual(contact.user_id, PORTAL_USER_ID)
        self.assertTrue(address.is_default)
        self.assertEqual(len(detail.contacts), 1)
        self.assertEqual(len(detail.addresses), 1)

    def test_contact_create_without_portal_user_id_succeeds(self) -> None:
        contact = self.service.create_contact(
            "tenant-1",
            self.customer.id,
            CustomerContactCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                full_name="Kontakt Ohne Portal",
                email="kontakt@example.invalid",
            ),
            _actor(),
        )

        self.assertIsNone(contact.user_id)

    def test_non_uuid_portal_user_id_is_rejected_on_create(self) -> None:
        with self.assertRaises(ApiException) as context:
            self.service.create_contact(
                "tenant-1",
                self.customer.id,
                CustomerContactCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    full_name="Ungueltige Verknuepfung",
                    user_id="Customer001",
                ),
                _actor(),
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.code, "customers.validation.portal_user_id_format")
        self.assertEqual(context.exception.message_key, "errors.customers.contact.invalid_user_id_format")

    def test_non_uuid_portal_user_id_is_rejected_on_update(self) -> None:
        contact = self.service.create_contact(
            "tenant-1",
            self.customer.id,
            CustomerContactCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                full_name="Bestehender Kontakt",
                user_id=PORTAL_USER_ID,
            ),
            _actor(),
        )

        with self.assertRaises(ApiException) as context:
            self.service.update_contact(
                "tenant-1",
                self.customer.id,
                contact.id,
                CustomerContactUpdate(user_id="Customer001", version_no=contact.version_no),
                _actor(),
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.code, "customers.validation.portal_user_id_format")
        self.assertEqual(context.exception.message_key, "errors.customers.contact.invalid_user_id_format")

    def test_duplicate_customer_number_is_rejected(self) -> None:
        with self.assertRaises(ApiException) as context:
            self.service.create_customer(
                "tenant-1",
                CustomerCreate(
                    tenant_id="tenant-1",
                    customer_number="K-1000",
                    name="Duplikat GmbH",
                ),
                _actor(),
            )

        self.assertEqual(context.exception.code, "customers.conflict.customer_number")

    def test_primary_contact_and_duplicate_email_rules_are_enforced(self) -> None:
        self.service.create_contact(
            "tenant-1",
            self.customer.id,
            CustomerContactCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                full_name="Alex Kunde",
                email="alex@example.invalid",
                is_primary_contact=True,
            ),
            _actor(),
        )

        with self.assertRaises(ApiException) as email_context:
            self.service.create_contact(
                "tenant-1",
                self.customer.id,
                CustomerContactCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    full_name="Bea Kunde",
                    email="Alex@Example.Invalid",
                ),
                _actor(),
            )
        with self.assertRaises(ApiException) as primary_context:
            self.service.create_contact(
                "tenant-1",
                self.customer.id,
                CustomerContactCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    full_name="Chris Kunde",
                    is_primary_contact=True,
                ),
                _actor(),
            )

        self.assertEqual(email_context.exception.code, "customers.conflict.contact_email")
        self.assertEqual(primary_context.exception.code, "customers.conflict.primary_contact")

    def test_default_address_per_type_is_enforced(self) -> None:
        self.service.create_customer_address(
            "tenant-1",
            self.customer.id,
            CustomerAddressCreate(
                tenant_id="tenant-1",
                customer_id=self.customer.id,
                address_id="address-1",
                address_type="mailing",
                is_default=True,
            ),
            _actor(),
        )
        self.repository.addresses["address-2"] = FakeAddress("address-2", street_line_1="Nebenstrasse 2")

        with self.assertRaises(ApiException) as context:
            self.service.create_customer_address(
                "tenant-1",
                self.customer.id,
                CustomerAddressCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    address_id="address-2",
                    address_type="mailing",
                    is_default=True,
                ),
                _actor(),
            )

        self.assertEqual(context.exception.code, "customers.conflict.default_address")

    def test_portal_user_link_must_match_tenant_scope(self) -> None:
        self.repository.users[FOREIGN_PORTAL_USER_ID] = FakeUser(FOREIGN_PORTAL_USER_ID, "tenant-2")

        with self.assertRaises(ApiException) as context:
            self.service.create_contact(
                "tenant-1",
                self.customer.id,
                CustomerContactCreate(
                    tenant_id="tenant-1",
                    customer_id=self.customer.id,
                    full_name="Fremd Nutzer",
                    user_id=FOREIGN_PORTAL_USER_ID,
                ),
                _actor(),
            )

        self.assertEqual(context.exception.code, "customers.validation.portal_user_scope")

    def test_tenant_scope_and_stale_versions_are_enforced(self) -> None:
        with self.assertRaises(ApiException) as scope_context:
            self.service.get_customer("tenant-1", self.customer.id, _actor("tenant-2"))
        with self.assertRaises(ApiException) as version_context:
            self.service.update_customer(
                "tenant-1",
                self.customer.id,
                CustomerUpdate(name="Stale", version_no=99),
                _actor(),
            )

        self.assertEqual(scope_context.exception.code, "iam.authorization.scope_denied")
        self.assertEqual(version_context.exception.code, "customers.conflict.stale_customer_version")

    def test_invalid_mandate_for_branch_is_rejected(self) -> None:
        self.repository.branches["branch-2"] = FakeBranch("branch-2", "tenant-1")
        self.repository.mandates["mandate-2"] = FakeMandate("mandate-2", "tenant-1", "branch-2")

        with self.assertRaises(ApiException) as context:
            self.service.create_customer(
                "tenant-1",
                CustomerCreate(
                    tenant_id="tenant-1",
                    customer_number="K-1003",
                    name="Scopefehler AG",
                    default_branch_id="branch-1",
                    default_mandate_id="mandate-2",
                ),
                _actor(),
            )

        self.assertEqual(context.exception.code, "customers.validation.mandate_branch_scope")

    def test_meaningful_history_entries_are_created(self) -> None:
        created_titles = [row.title for row in self.repository.list_history_entries("tenant-1", self.customer.id)]
        self.assertIn("Customer created", created_titles)

        updated = self.service.update_customer(
            "tenant-1",
            self.customer.id,
            CustomerUpdate(status="inactive", version_no=self.customer.version_no),
            _actor(),
        )
        history_rows = self.repository.list_history_entries("tenant-1", self.customer.id)

        self.assertEqual(updated.status, "inactive")
        self.assertTrue(any(row.entry_type == "customer.status.changed" for row in history_rows))
        latest_status_entry = next(row for row in history_rows if row.entry_type == "customer.status.changed")
        self.assertEqual(latest_status_entry.after_json["status"], "inactive")


if __name__ == "__main__":
    unittest.main()
