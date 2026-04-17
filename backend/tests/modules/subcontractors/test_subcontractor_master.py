from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint, Index

from app.db import Base
from app.errors import ApiException
from app.modules.core.models import Address, Branch, LookupValue, Mandate
from app.modules.core.schemas import AddressCreate
from app.modules.iam.audit_service import AuditService
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.iam.models import UserAccount
from app.modules.platform_services.docs_models import Document, DocumentLink, DocumentType, DocumentVersion
from app.modules.platform_services.docs_schemas import DocumentLinkCreate
from app.modules.subcontractors.models import (
    Subcontractor,
    SubcontractorContact,
    SubcontractorFinanceProfile,
    SubcontractorHistoryEntry,
    SubcontractorScope,
)
from app.modules.subcontractors.schemas import (
    SubcontractorContactCreate,
    SubcontractorContactUpdate,
    SubcontractorCreate,
    SubcontractorFilter,
    SubcontractorFinanceProfileCreate,
    SubcontractorFinanceProfileUpdate,
    SubcontractorHistoryAttachmentLinkCreate,
    SubcontractorHistoryEntryCreate,
    SubcontractorLifecycleTransitionRequest,
    SubcontractorReferenceDataRead,
    SubcontractorScopeCreate,
    SubcontractorUpdate,
)
from app.modules.subcontractors.collaboration_service import SubcontractorCollaborationService
from app.modules.subcontractors.service import SubcontractorService


def _context(
    *permissions: str,
    tenant_id: str = "tenant-1",
    role_keys: tuple[str, ...] = ("tenant_admin",),
    scopes: tuple[AuthenticatedRoleScope, ...] | None = None,
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset(role_keys),
        permission_keys=frozenset(permissions),
        scopes=scopes or (AuthenticatedRoleScope(role_key=role_keys[0], scope_type="tenant"),),
        request_id="req-1",
    )


class RecordingAuditRepository:
    def __init__(self) -> None:
        self.audit_events: list[object] = []

    def create_login_event(self, payload):  # noqa: ANN001
        return payload

    def create_audit_event(self, payload):  # noqa: ANN001
        self.audit_events.append(payload)
        return payload


@dataclass
class FakeSubcontractorRepository:
    tenant_id: str = "tenant-1"
    subcontractors: dict[str, Subcontractor] = field(default_factory=dict)
    contacts: dict[str, SubcontractorContact] = field(default_factory=dict)
    scopes: dict[str, SubcontractorScope] = field(default_factory=dict)
    finance_profiles: dict[str, SubcontractorFinanceProfile] = field(default_factory=dict)
    history_entries: dict[str, SubcontractorHistoryEntry] = field(default_factory=dict)
    lookups: dict[str, LookupValue] = field(default_factory=dict)
    branches: dict[str, Branch] = field(default_factory=dict)
    mandates: dict[str, Mandate] = field(default_factory=dict)
    users: dict[str, UserAccount] = field(default_factory=dict)
    addresses: dict[str, Address] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.branches["branch-1"] = Branch(
            id="branch-1",
            tenant_id=self.tenant_id,
            code="BER",
            name="Berlin",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.mandates["mandate-1"] = Mandate(
            id="mandate-1",
            tenant_id=self.tenant_id,
            branch_id="branch-1",
            code="M-001",
            name="Mandate 1",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.users["user-portal"] = UserAccount(
            id="user-portal",
            tenant_id=self.tenant_id,
            username="partner-user",
            email="portal@example.com",
            full_name="Portal User",
            locale="de",
            timezone="Europe/Berlin",
            is_platform_user=False,
            is_password_login_enabled=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.addresses["address-1"] = Address(
            id="address-1",
            street_line_1="Hauptstrasse 1",
            street_line_2=None,
            postal_code="10115",
            city="Berlin",
            state=None,
            country_code="DE",
        )
        self.lookups["lookup-legal"] = LookupValue(
            id="lookup-legal",
            tenant_id=None,
            domain="legal_form",
            code="gmbh",
            label="GmbH",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.lookups["lookup-status"] = LookupValue(
            id="lookup-status",
            tenant_id=None,
            domain="subcontractor_status",
            code="active",
            label="Aktiv",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.lookups["lookup-delivery"] = LookupValue(
            id="lookup-delivery",
            tenant_id=None,
            domain="invoice_delivery_method",
            code="email_pdf",
            label="E-Mail PDF",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.lookups["lookup-invoice-status"] = LookupValue(
            id="lookup-invoice-status",
            tenant_id=None,
            domain="subcontractor_invoice_status_mode",
            code="manual_check",
            label="Manuelle Pruefung",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )

    @staticmethod
    def _stamp(row) -> None:  # noqa: ANN001
        now = datetime.now(UTC)
        if getattr(row, "id", None) is None:
            row.id = str(uuid4())
        if getattr(row, "created_at", None) is None:
            row.created_at = now
        row.updated_at = now
        if getattr(row, "version_no", None) is None:
            row.version_no = 1
        if getattr(row, "status", None) is None:
            row.status = "active"

    def list_subcontractors(self, tenant_id: str, filters: SubcontractorFilter) -> list[Subcontractor]:
        rows = [row for row in self.subcontractors.values() if row.tenant_id == tenant_id]
        if not filters.include_archived:
            rows = [row for row in rows if row.archived_at is None]
        if filters.status is not None:
            rows = [row for row in rows if row.status == filters.status]
        if filters.branch_id is not None:
            allowed_ids = {row.subcontractor_id for row in self.scopes.values() if row.branch_id == filters.branch_id}
            rows = [row for row in rows if row.id in allowed_ids]
        if filters.mandate_id is not None:
            allowed_ids = {row.subcontractor_id for row in self.scopes.values() if row.mandate_id == filters.mandate_id}
            rows = [row for row in rows if row.id in allowed_ids]
        if filters.search:
            term = filters.search.lower()
            rows = [row for row in rows if term in row.subcontractor_number.lower() or term in row.legal_name.lower()]
        rows.sort(key=lambda row: row.subcontractor_number)
        for row in rows:
            self._hydrate(row)
        return rows

    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None:
        row = self.subcontractors.get(subcontractor_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        self._hydrate(row)
        return row

    def create_subcontractor(self, tenant_id: str, payload: SubcontractorCreate, actor_user_id: str | None) -> Subcontractor:
        row = Subcontractor(
            tenant_id=tenant_id,
            subcontractor_number=payload.subcontractor_number,
            legal_name=payload.legal_name,
            display_name=payload.display_name,
            legal_form_lookup_id=payload.legal_form_lookup_id,
            subcontractor_status_lookup_id=payload.subcontractor_status_lookup_id,
            managing_director_name=payload.managing_director_name,
            address_id=payload.address_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.subcontractors[row.id] = row
        self._hydrate(row)
        return row

    def update_subcontractor(self, tenant_id: str, subcontractor_id: str, payload: SubcontractorUpdate, actor_user_id: str | None) -> Subcontractor | None:
        row = self.get_subcontractor(tenant_id, subcontractor_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.updated_by_user_id = actor_user_id
        row.version_no += 1
        self._stamp(row)
        self._hydrate(row)
        return row

    def save_subcontractor(self, row: Subcontractor) -> Subcontractor:
        row.updated_at = datetime.now(UTC)
        self.subcontractors[row.id] = row
        self._hydrate(row)
        return row

    def list_contacts(self, tenant_id: str, subcontractor_id: str) -> list[SubcontractorContact]:
        rows = [row for row in self.contacts.values() if row.tenant_id == tenant_id and row.subcontractor_id == subcontractor_id]
        rows.sort(key=lambda row: row.full_name)
        return rows

    def get_contact(self, tenant_id: str, subcontractor_id: str, contact_id: str) -> SubcontractorContact | None:
        row = self.contacts.get(contact_id)
        if row is None or row.tenant_id != tenant_id or row.subcontractor_id != subcontractor_id:
            return None
        return row

    def create_contact(self, tenant_id: str, subcontractor_id: str, payload: SubcontractorContactCreate, actor_user_id: str | None) -> SubcontractorContact:
        row = SubcontractorContact(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            full_name=payload.full_name,
            title=payload.title,
            function_label=payload.function_label,
            email=payload.email,
            phone=payload.phone,
            mobile=payload.mobile,
            is_primary_contact=payload.is_primary_contact,
            portal_enabled=payload.portal_enabled,
            user_id=payload.user_id,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.contacts[row.id] = row
        return row

    def update_contact(self, tenant_id: str, subcontractor_id: str, contact_id: str, payload, actor_user_id: str | None):
        row = self.get_contact(tenant_id, subcontractor_id, contact_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.updated_by_user_id = actor_user_id
        row.version_no += 1
        self._stamp(row)
        return row

    def list_scopes(self, tenant_id: str, subcontractor_id: str) -> list[SubcontractorScope]:
        rows = [row for row in self.scopes.values() if row.tenant_id == tenant_id and row.subcontractor_id == subcontractor_id]
        rows.sort(key=lambda row: row.valid_from)
        return rows

    def get_scope(self, tenant_id: str, subcontractor_id: str, scope_id: str) -> SubcontractorScope | None:
        row = self.scopes.get(scope_id)
        if row is None or row.tenant_id != tenant_id or row.subcontractor_id != subcontractor_id:
            return None
        return row

    def create_scope(self, tenant_id: str, subcontractor_id: str, payload: SubcontractorScopeCreate, actor_user_id: str | None) -> SubcontractorScope:
        row = SubcontractorScope(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            branch_id=payload.branch_id,
            mandate_id=payload.mandate_id,
            valid_from=payload.valid_from,
            valid_to=payload.valid_to,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.scopes[row.id] = row
        return row

    def update_scope(self, tenant_id: str, subcontractor_id: str, scope_id: str, payload, actor_user_id: str | None):
        row = self.get_scope(tenant_id, subcontractor_id, scope_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.updated_by_user_id = actor_user_id
        row.version_no += 1
        self._stamp(row)
        return row

    def get_finance_profile(self, tenant_id: str, subcontractor_id: str) -> SubcontractorFinanceProfile | None:
        for row in self.finance_profiles.values():
            if row.tenant_id == tenant_id and row.subcontractor_id == subcontractor_id:
                return row
        return None

    def list_history_entries(self, tenant_id: str, subcontractor_id: str) -> list[SubcontractorHistoryEntry]:
        rows = [
            row
            for row in self.history_entries.values()
            if row.tenant_id == tenant_id and row.subcontractor_id == subcontractor_id
        ]
        rows.sort(key=lambda row: (row.occurred_at, row.created_at), reverse=True)
        return rows

    def get_history_entry(self, tenant_id: str, subcontractor_id: str, history_entry_id: str) -> SubcontractorHistoryEntry | None:
        row = self.history_entries.get(history_entry_id)
        if row is None or row.tenant_id != tenant_id or row.subcontractor_id != subcontractor_id:
            return None
        return row

    def create_history_entry(self, row: SubcontractorHistoryEntry) -> SubcontractorHistoryEntry:
        if row.id is None:
            row.id = str(uuid4())
        if row.created_at is None:
            row.created_at = datetime.now(UTC)
        self.history_entries[row.id] = row
        return row

    def create_finance_profile(self, tenant_id: str, subcontractor_id: str, payload: SubcontractorFinanceProfileCreate, actor_user_id: str | None) -> SubcontractorFinanceProfile:
        row = SubcontractorFinanceProfile(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            invoice_email=payload.invoice_email,
            payment_terms_days=payload.payment_terms_days,
            payment_terms_note=payload.payment_terms_note,
            tax_number=payload.tax_number,
            vat_id=payload.vat_id,
            bank_account_holder=payload.bank_account_holder,
            bank_iban=payload.bank_iban,
            bank_bic=payload.bank_bic,
            bank_name=payload.bank_name,
            invoice_delivery_method_lookup_id=payload.invoice_delivery_method_lookup_id,
            invoice_status_mode_lookup_id=payload.invoice_status_mode_lookup_id,
            billing_note=payload.billing_note,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self._stamp(row)
        self.finance_profiles[row.id] = row
        return row

    def update_finance_profile(self, tenant_id: str, subcontractor_id: str, payload, actor_user_id: str | None):
        row = self.get_finance_profile(tenant_id, subcontractor_id)
        if row is None:
            return None
        for key, value in payload.model_dump(exclude_unset=True, exclude={"version_no"}).items():
            setattr(row, key, value)
        row.updated_by_user_id = actor_user_id
        row.version_no += 1
        self._stamp(row)
        return row

    def find_subcontractor_by_number(self, tenant_id: str, subcontractor_number: str, *, exclude_id: str | None = None) -> Subcontractor | None:
        for row in self.subcontractors.values():
            if row.tenant_id == tenant_id and row.subcontractor_number.lower() == subcontractor_number.strip().lower() and row.id != exclude_id:
                return row
        return None

    def has_primary_contact(self, tenant_id: str, subcontractor_id: str, *, exclude_id: str | None = None) -> bool:
        return any(
            row.tenant_id == tenant_id
            and row.subcontractor_id == subcontractor_id
            and row.is_primary_contact
            and row.archived_at is None
            and row.id != exclude_id
            for row in self.contacts.values()
        )

    def find_contact_by_user_id(self, tenant_id: str, user_id: str, *, exclude_id: str | None = None) -> SubcontractorContact | None:
        for row in self.contacts.values():
            if row.tenant_id == tenant_id and row.user_id == user_id and row.id != exclude_id:
                return row
        return None

    def get_portal_contact_for_user(self, tenant_id: str, user_id: str) -> tuple[Subcontractor, SubcontractorContact] | None:
        contact = self.find_contact_by_user_id(tenant_id, user_id)
        if contact is None:
            return None
        subcontractor = self.get_subcontractor(tenant_id, contact.subcontractor_id)
        if subcontractor is None:
            return None
        return subcontractor, contact

    def get_portal_subcontractor_scope_match(
        self,
        tenant_id: str,
        user_id: str,
        allowed_subcontractor_ids: list[str],
    ) -> tuple[Subcontractor, SubcontractorContact] | None:
        linked = self.get_portal_contact_for_user(tenant_id, user_id)
        if linked is None:
            return None
        subcontractor, contact = linked
        if subcontractor.id not in allowed_subcontractor_ids:
            return None
        return subcontractor, contact

    def find_overlapping_scope(self, tenant_id: str, subcontractor_id: str, branch_id: str, mandate_id: str | None, valid_from, valid_to, *, exclude_id: str | None = None):
        wanted_end = valid_to or date.max
        for row in self.scopes.values():
            if (
                row.tenant_id == tenant_id
                and row.subcontractor_id == subcontractor_id
                and row.branch_id == branch_id
                and row.mandate_id == mandate_id
                and row.archived_at is None
                and row.id != exclude_id
            ):
                row_end = row.valid_to or date.max
                if row.valid_from <= wanted_end and valid_from <= row_end:
                    return row
        return None

    def get_lookup_value(self, lookup_id: str) -> LookupValue | None:
        return self.lookups.get(lookup_id)

    def list_lookup_values(self, tenant_id: str, domain: str) -> list[LookupValue]:
        rows = [
            row
            for row in self.lookups.values()
            if row.domain == domain and (row.tenant_id is None or row.tenant_id == tenant_id)
        ]
        rows.sort(key=lambda row: ((row.label or row.code), row.code, row.id))
        return rows

    def get_branch(self, tenant_id: str, branch_id: str) -> Branch | None:
        row = self.branches.get(branch_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def get_mandate(self, tenant_id: str, mandate_id: str) -> Mandate | None:
        row = self.mandates.get(mandate_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def get_user_account(self, tenant_id: str, user_id: str) -> UserAccount | None:
        row = self.users.get(user_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    def list_contact_user_options(self, tenant_id: str, search: str = "", limit: int = 25) -> list[UserAccount]:
        if tenant_id != self.tenant_id:
            return []
        term = search.strip().lower()
        rows = [row for row in self.users.values() if row.status == "active" and row.archived_at is None]
        if term:
            rows = [
                row
                for row in rows
                if term in row.username.lower()
                or term in (row.email or "").lower()
                or term in (row.full_name or "").lower()
            ]
        rows.sort(key=lambda row: row.username)
        return rows[:limit]

    def get_address(self, address_id: str) -> Address | None:
        return self.addresses.get(address_id)

    def create_address(self, row: Address) -> Address:
        if row.id is None:
            row.id = str(uuid4())
        self.addresses[row.id] = row
        return row

    def _hydrate(self, row: Subcontractor) -> None:
        row.address = self.addresses.get(row.address_id) if row.address_id else None
        row.contacts = self.list_contacts(row.tenant_id, row.id)
        row.scopes = self.list_scopes(row.tenant_id, row.id)
        row.finance_profile = self.get_finance_profile(row.tenant_id, row.id)
        row.history_entries = self.list_history_entries(row.tenant_id, row.id)


@dataclass
class FakeHistoryDocumentRepository:
    documents_by_owner: dict[tuple[str, str, str], list[Document]] = field(default_factory=dict)

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]:
        return list(self.documents_by_owner.get((tenant_id, owner_type, owner_id), []))


@dataclass
class FakeDocumentService:
    document_repository: FakeHistoryDocumentRepository

    def add_document_link(self, tenant_id: str, document_id: str, payload: DocumentLinkCreate, actor):  # noqa: ANN001
        document = next(
            (
                row
                for rows in self.document_repository.documents_by_owner.values()
                for row in rows
                if row.id == document_id and row.tenant_id == tenant_id
            ),
            None,
        )
        if document is None:
            document = Document(
                id=document_id,
                tenant_id=tenant_id,
                title=f"Dokument {document_id}",
                source_module="subcontractors",
                source_label="history-attachment",
                current_version_no=1,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
                status="active",
            )
            document.document_type = DocumentType(
                id="doc-type-1",
                key="attachment",
                name="Attachment",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                version_no=1,
                status="active",
                is_system_type=True,
            )
            document.versions = [
                DocumentVersion(
                    id=f"{document_id}-v1",
                    tenant_id=tenant_id,
                    document_id=document_id,
                    version_no=1,
                    file_name=f"{document_id}.pdf",
                    content_type="application/pdf",
                    object_bucket="local",
                    object_key=f"{document_id}/1",
                    checksum_sha256="abc",
                    file_size_bytes=12,
                    uploaded_by_user_id=actor.user_id,
                    metadata_json={},
                    is_revision_safe_pdf=False,
                )
            ]
            document.links = []
        document.links.append(
            DocumentLink(
                id=str(uuid4()),
                tenant_id=tenant_id,
                document_id=document_id,
                owner_type=payload.owner_type,
                owner_id=payload.owner_id,
                relation_type=payload.relation_type,
                label=payload.label,
                linked_by_user_id=actor.user_id,
                metadata_json=payload.metadata_json,
            )
        )
        key = (tenant_id, payload.owner_type, payload.owner_id)
        self.document_repository.documents_by_owner.setdefault(key, [])
        if not any(existing.id == document.id for existing in self.document_repository.documents_by_owner[key]):
            self.document_repository.documents_by_owner[key].append(document)
        return document.links[-1]


class SubcontractorServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeSubcontractorRepository()
        self.audit_repository = RecordingAuditRepository()
        self.document_repository = FakeHistoryDocumentRepository()
        self.service = SubcontractorService(
            self.repository,
            audit_service=AuditService(self.audit_repository),
        )
        self.collaboration_service = SubcontractorCollaborationService(
            self.repository,
            document_repository=self.document_repository,
            document_service=FakeDocumentService(self.document_repository),
            audit_service=AuditService(self.audit_repository),
        )

    def test_create_subcontractor_with_contact_scope_and_finance_profile(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(
                tenant_id="tenant-1",
                subcontractor_number="SUB-1001",
                legal_name="Partner GmbH",
                display_name="Partner",
                legal_form_lookup_id="lookup-legal",
                subcontractor_status_lookup_id="lookup-status",
                managing_director_name="Max Muster",
                address_id="address-1",
                latitude=Decimal("52.520008"),
                longitude=Decimal("13.404954"),
                notes="Strategischer Partner",
            ),
            _context("subcontractors.company.write"),
        )
        contact = self.service.create_contact(
            "tenant-1",
            created.id,
            SubcontractorContactCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                full_name="Erika Partner",
                email="erika@example.com",
                is_primary_contact=True,
                portal_enabled=True,
                user_id="user-portal",
            ),
            _context("subcontractors.company.write"),
        )
        scope = self.service.create_scope(
            "tenant-1",
            created.id,
            SubcontractorScopeCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                branch_id="branch-1",
                mandate_id="mandate-1",
                valid_from=date(2026, 4, 1),
                valid_to=date(2026, 12, 31),
            ),
            _context("subcontractors.company.write"),
        )
        finance = self.service.upsert_finance_profile(
            "tenant-1",
            created.id,
            SubcontractorFinanceProfileCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                invoice_email="rechnung@example.com",
                payment_terms_days=14,
                vat_id="DE123456789",
                invoice_delivery_method_lookup_id="lookup-delivery",
                invoice_status_mode_lookup_id="lookup-invoice-status",
            ),
            _context("subcontractors.finance.write"),
        )

        aggregate = self.service.get_subcontractor(
            "tenant-1",
            created.id,
            _context("subcontractors.company.read", "subcontractors.finance.read"),
        )
        self.assertEqual(aggregate.subcontractor_number, "SUB-1001")
        self.assertEqual(contact.portal_enabled, True)
        self.assertEqual(scope.mandate_id, "mandate-1")
        self.assertEqual(finance.payment_terms_days, 14)
        self.assertEqual(len(aggregate.contacts), 1)
        self.assertEqual(len(aggregate.scopes), 1)
        self.assertIsNotNone(aggregate.finance_profile)
        self.assertEqual(len(self.audit_repository.audit_events), 5)

    def test_reference_data_exposes_legal_forms_for_subcontractor_overview(self) -> None:
        reference_data = self.service.get_reference_data(
            "tenant-1",
            _context("subcontractors.company.read"),
        )

        self.assertIsInstance(reference_data, SubcontractorReferenceDataRead)
        self.assertEqual(len(reference_data.legal_forms), 1)
        self.assertEqual(reference_data.legal_forms[0].id, "lookup-legal")
        self.assertEqual(reference_data.legal_forms[0].label, "GmbH")
        self.assertEqual(reference_data.legal_forms[0].code, "gmbh")

    def test_contact_user_options_and_address_options_are_exposed_for_supported_overview_fields(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(
                tenant_id="tenant-1",
                subcontractor_number="SUB-1200",
                legal_name="DomSchild Sicherheitsdienste GmbH",
                address_id="address-1",
            ),
            _context("subcontractors.company.write"),
        )

        user_options = self.service.list_contact_user_options(
            "tenant-1",
            created.id,
            _context("subcontractors.company.read"),
            search="portal",
        )
        address_options = self.service.list_address_options(
            "tenant-1",
            created.id,
            _context("subcontractors.company.read"),
        )
        created_address = self.service.create_address_option(
            "tenant-1",
            created.id,
            AddressCreate(
                street_line_1="Domplatz 1",
                postal_code="50667",
                city="Koeln",
                country_code="de",
            ),
            _context("subcontractors.company.write"),
        )

        self.assertEqual(user_options[0].id, "user-portal")
        self.assertEqual(address_options[0].id, "address-1")
        self.assertEqual(created_address.city, "Koeln")
        self.assertEqual(created_address.country_code, "DE")

    def test_duplicate_number_and_primary_contact_are_rejected(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(
                tenant_id="tenant-1",
                subcontractor_number="SUB-1001",
                legal_name="Partner GmbH",
            ),
            _context("subcontractors.company.write"),
        )

        with self.assertRaises(ApiException) as duplicate_number:
            self.service.create_subcontractor(
                "tenant-1",
                SubcontractorCreate(
                    tenant_id="tenant-1",
                    subcontractor_number="SUB-1001",
                    legal_name="Andere GmbH",
                ),
                _context("subcontractors.company.write"),
            )
        self.assertEqual(duplicate_number.exception.message_key, "errors.subcontractors.subcontractor.duplicate_number")

        self.service.create_contact(
            "tenant-1",
            created.id,
            SubcontractorContactCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                full_name="Primaer",
                is_primary_contact=True,
            ),
            _context("subcontractors.company.write"),
        )
        with self.assertRaises(ApiException) as duplicate_primary:
            self.service.create_contact(
                "tenant-1",
                created.id,
                SubcontractorContactCreate(
                    tenant_id="tenant-1",
                    subcontractor_id=created.id,
                    full_name="Zweiter",
                    is_primary_contact=True,
                ),
                _context("subcontractors.company.write"),
            )
        self.assertEqual(duplicate_primary.exception.message_key, "errors.subcontractors.contact.primary_conflict")

    def test_user_link_tenant_scope_and_portal_flag_are_validated(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _context("subcontractors.company.write"),
        )

        with self.assertRaises(ApiException) as missing_user:
            self.service.create_contact(
                "tenant-1",
                created.id,
                SubcontractorContactCreate(
                    tenant_id="tenant-1",
                    subcontractor_id=created.id,
                    full_name="Portal Kontakt",
                    portal_enabled=True,
                ),
                _context("subcontractors.company.write"),
            )
        self.assertEqual(missing_user.exception.message_key, "errors.subcontractors.contact.portal_user_required")

        self.service.create_contact(
            "tenant-1",
            created.id,
            SubcontractorContactCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                full_name="Portal Kontakt",
                portal_enabled=True,
                user_id="user-portal",
            ),
            _context("subcontractors.company.write"),
        )
        other = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1002", legal_name="Anderer Partner"),
            _context("subcontractors.company.write"),
        )
        with self.assertRaises(ApiException) as duplicate_link:
            self.service.create_contact(
                "tenant-1",
                other.id,
                SubcontractorContactCreate(
                    tenant_id="tenant-1",
                    subcontractor_id=other.id,
                    full_name="Duplikat",
                    user_id="user-portal",
                ),
                _context("subcontractors.company.write"),
            )
        self.assertEqual(duplicate_link.exception.message_key, "errors.subcontractors.contact.duplicate_user_link")

    def test_scope_overlap_and_branch_mandate_alignment_are_enforced(self) -> None:
        self.repository.branches["branch-2"] = Branch(
            id="branch-2",
            tenant_id="tenant-1",
            code="HAM",
            name="Hamburg",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _context("subcontractors.company.write"),
        )
        self.service.create_scope(
            "tenant-1",
            created.id,
            SubcontractorScopeCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                branch_id="branch-1",
                mandate_id="mandate-1",
                valid_from=date(2026, 4, 1),
                valid_to=date(2026, 12, 31),
            ),
            _context("subcontractors.company.write"),
        )

        with self.assertRaises(ApiException) as overlap:
            self.service.create_scope(
                "tenant-1",
                created.id,
                SubcontractorScopeCreate(
                    tenant_id="tenant-1",
                    subcontractor_id=created.id,
                    branch_id="branch-1",
                    mandate_id="mandate-1",
                    valid_from=date(2026, 6, 1),
                    valid_to=date(2026, 10, 1),
                ),
                _context("subcontractors.company.write"),
            )
        self.assertEqual(overlap.exception.message_key, "errors.subcontractors.scope.overlap")

        with self.assertRaises(ApiException) as mismatch:
            self.service.create_scope(
                "tenant-1",
                created.id,
                SubcontractorScopeCreate(
                    tenant_id="tenant-1",
                    subcontractor_id=created.id,
                    branch_id="branch-2",
                    mandate_id="mandate-1",
                    valid_from=date(2027, 1, 1),
                ),
                _context("subcontractors.company.write"),
            )
        self.assertEqual(mismatch.exception.message_key, "errors.subcontractors.scope.mandate_branch_mismatch")

    def test_tenant_scope_is_enforced(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _context("subcontractors.company.write"),
        )
        with self.assertRaises(ApiException) as denied:
            self.service.get_subcontractor("tenant-1", created.id, _context("subcontractors.company.read", tenant_id="tenant-2"))
        self.assertEqual(denied.exception.message_key, "errors.iam.authorization.scope_denied")

    def test_portal_roles_are_rejected_from_internal_subcontractor_api(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _context("subcontractors.company.write"),
        )

        with self.assertRaises(ApiException) as denied:
            self.service.get_subcontractor(
                "tenant-1",
                created.id,
                _context(
                    "subcontractors.company.read",
                    role_keys=("subcontractor_user",),
                    scopes=(AuthenticatedRoleScope(role_key="subcontractor_user", scope_type="subcontractor", subcontractor_id=created.id),),
                ),
            )

        self.assertEqual(denied.exception.code, "subcontractors.authorization.portal_forbidden")

    def test_branch_scoped_internal_read_is_filtered_to_matching_partner_scope(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _context("subcontractors.company.write"),
        )
        self.service.create_scope(
            "tenant-1",
            created.id,
            SubcontractorScopeCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                branch_id="branch-1",
                valid_from=date(2026, 4, 1),
            ),
            _context("subcontractors.company.write"),
        )
        other = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1002", legal_name="Anderer Partner"),
            _context("subcontractors.company.write"),
        )
        self.repository.branches["branch-2"] = Branch(
            id="branch-2",
            tenant_id="tenant-1",
            code="HAM",
            name="Hamburg",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            version_no=1,
            status="active",
        )
        self.service.create_scope(
            "tenant-1",
            other.id,
            SubcontractorScopeCreate(
                tenant_id="tenant-1",
                subcontractor_id=other.id,
                branch_id="branch-2",
                valid_from=date(2026, 4, 1),
            ),
            _context("subcontractors.company.write"),
        )

        branch_actor = _context(
            "subcontractors.company.read",
            role_keys=("dispatcher",),
            scopes=(AuthenticatedRoleScope(role_key="dispatcher", scope_type="branch", branch_id="branch-1"),),
        )
        visible = self.service.list_subcontractors("tenant-1", SubcontractorFilter(), branch_actor)
        self.assertEqual([row.id for row in visible], [created.id])

        denied_actor = _context(
            "subcontractors.company.read",
            role_keys=("dispatcher",),
            scopes=(AuthenticatedRoleScope(role_key="dispatcher", scope_type="branch", branch_id="branch-2"),),
        )
        with self.assertRaises(ApiException) as denied:
            self.service.get_subcontractor("tenant-1", created.id, denied_actor)
        self.assertEqual(denied.exception.code, "subcontractors.authorization.internal_scope_required")

    def test_company_read_masks_finance_and_portal_user_linkage(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _context("subcontractors.company.write"),
        )
        self.service.create_contact(
            "tenant-1",
            created.id,
            SubcontractorContactCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                full_name="Portal Kontakt",
                portal_enabled=True,
                user_id="user-portal",
            ),
            _context("subcontractors.company.write"),
        )
        self.service.upsert_finance_profile(
            "tenant-1",
            created.id,
            SubcontractorFinanceProfileCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                invoice_email="rechnung@example.com",
                payment_terms_days=14,
                tax_number="TAX-123",
                bank_iban="DE89370400440532013000",
                invoice_delivery_method_lookup_id="lookup-delivery",
                invoice_status_mode_lookup_id="lookup-invoice-status",
            ),
            _context("subcontractors.finance.write"),
        )

        company_read = self.service.get_subcontractor("tenant-1", created.id, _context("subcontractors.company.read", role_keys=("dispatcher",)))
        finance_read = self.service.get_finance_profile("tenant-1", created.id, _context("subcontractors.finance.read", role_keys=("accounting",)))

        self.assertIsNone(company_read.finance_profile)
        self.assertEqual(company_read.contacts[0].user_id, None)
        self.assertEqual(finance_read.tax_number, "TAX-123")

    def test_portal_link_and_finance_events_are_audited_without_raw_bank_data(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _context("subcontractors.company.write"),
        )
        contact = self.service.create_contact(
            "tenant-1",
            created.id,
            SubcontractorContactCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                full_name="Portal Kontakt",
                portal_enabled=False,
            ),
            _context("subcontractors.company.write"),
        )
        self.service.update_contact(
            "tenant-1",
            created.id,
            contact.id,
            SubcontractorContactUpdate(user_id="user-portal", portal_enabled=True, version_no=contact.version_no),
            _context("subcontractors.company.write"),
        )
        finance = self.service.upsert_finance_profile(
            "tenant-1",
            created.id,
            SubcontractorFinanceProfileCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                invoice_email="rechnung@example.com",
                payment_terms_days=14,
                tax_number="TAX-123",
                bank_iban="DE89370400440532013000",
                bank_bic="COBADEFFXXX",
                invoice_delivery_method_lookup_id="lookup-delivery",
                invoice_status_mode_lookup_id="lookup-invoice-status",
            ),
            _context("subcontractors.finance.write"),
        )
        self.service.upsert_finance_profile(
            "tenant-1",
            created.id,
            SubcontractorFinanceProfileUpdate(
                bank_iban="DE44500105175407324931",
                version_no=finance.version_no,
            ),
            _context("subcontractors.finance.write"),
        )

        event_types = [payload.event_type for payload in self.audit_repository.audit_events]
        self.assertIn("subcontractors.contact.portal_link_changed", event_types)
        self.assertIn("subcontractors.finance.updated", event_types)
        finance_event = next(payload for payload in self.audit_repository.audit_events if payload.event_type == "subcontractors.finance.updated")
        self.assertEqual(finance_event.entity_type, "partner.subcontractor_finance_profile")
        self.assertEqual(finance_event.metadata_json["subcontractor_id"], created.id)
        self.assertNotIn("bank_iban", finance_event.after_json)
        self.assertEqual(finance_event.after_json["bank_iban_last4"], "4931")
        self.assertNotIn("tax_number", finance_event.after_json)

    def test_history_entries_are_append_only_and_ordered(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _context("subcontractors.company.write"),
        )

        first = self.collaboration_service.create_history_entry(
            "tenant-1",
            created.id,
            SubcontractorHistoryEntryCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                entry_type="processing_note",
                title="Pruefung gestartet",
                body="Unterlagen zur Erstpruefung eingegangen.",
                occurred_at=datetime(2026, 3, 20, 8, 0, tzinfo=UTC),
            ),
            _context("subcontractors.company.write"),
        )
        second = self.collaboration_service.create_history_entry(
            "tenant-1",
            created.id,
            SubcontractorHistoryEntryCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                entry_type="invoice_discussion",
                title="Rechnungsrueckfrage",
                body="Abweichung in der Sammelrechnung notiert.",
                occurred_at=datetime(2026, 3, 21, 9, 30, tzinfo=UTC),
            ),
            _context("subcontractors.company.write"),
        )

        history = self.collaboration_service.list_history("tenant-1", created.id, _context("subcontractors.company.read"))
        self.assertEqual([entry.id for entry in history], [second.id, first.id])
        self.assertEqual(len(self.repository.list_history_entries("tenant-1", created.id)), 2)
        self.assertEqual(history[0].actor_user_id, "user-1")

    def test_history_attachment_links_use_docs_owner_type(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _context("subcontractors.company.write"),
        )
        history_entry = self.collaboration_service.create_history_entry(
            "tenant-1",
            created.id,
            SubcontractorHistoryEntryCreate(
                tenant_id="tenant-1",
                subcontractor_id=created.id,
                entry_type="manual_commentary",
                title="Anlage",
                body="Vertrag als Anlage hinzugefuegt.",
            ),
            _context("subcontractors.company.write"),
        )

        attachments = self.collaboration_service.link_history_attachment(
            "tenant-1",
            created.id,
            history_entry.id,
            SubcontractorHistoryAttachmentLinkCreate(document_id="doc-1", label="Rahmenvertrag"),
            _context("subcontractors.company.write"),
        )

        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].document_id, "doc-1")
        owner_docs = self.document_repository.list_documents_for_owner(
            "tenant-1",
            "partner.subcontractor_history_entry",
            history_entry.id,
        )
        self.assertEqual(len(owner_docs), 1)
        self.assertEqual(owner_docs[0].links[0].owner_type, "partner.subcontractor_history_entry")

    def test_archive_and_reactivate_create_history_and_audit_events(self) -> None:
        created = self.service.create_subcontractor(
            "tenant-1",
            SubcontractorCreate(tenant_id="tenant-1", subcontractor_number="SUB-1001", legal_name="Partner GmbH"),
            _context("subcontractors.company.write"),
        )

        archived = self.collaboration_service.archive_subcontractor(
            "tenant-1",
            created.id,
            SubcontractorLifecycleTransitionRequest(version_no=created.version_no),
            _context("subcontractors.company.write"),
        )
        self.assertEqual(archived.status, "archived")
        self.assertIsNotNone(archived.archived_at)

        history_after_archive = self.collaboration_service.list_history(
            "tenant-1",
            created.id,
            _context("subcontractors.company.read"),
        )
        self.assertEqual(history_after_archive[0].entry_type, "lifecycle_event")
        self.assertEqual(history_after_archive[0].metadata_json["lifecycle_action"], "archive")

        reactivated = self.collaboration_service.reactivate_subcontractor(
            "tenant-1",
            created.id,
            SubcontractorLifecycleTransitionRequest(version_no=archived.version_no),
            _context("subcontractors.company.write"),
        )
        self.assertEqual(reactivated.status, "active")
        self.assertIsNone(reactivated.archived_at)

        history_after_reactivate = self.collaboration_service.list_history(
            "tenant-1",
            created.id,
            _context("subcontractors.company.read"),
        )
        self.assertEqual(history_after_reactivate[0].metadata_json["lifecycle_action"], "reactivate")
        event_types = [payload.event_type for payload in self.audit_repository.audit_events]
        self.assertIn("subcontractors.company.archived", event_types)
        self.assertIn("subcontractors.company.reactivated", event_types)

    def test_metadata_exposes_expected_partner_constraints(self) -> None:
        subcontractor_table = Base.metadata.tables["partner.subcontractor"]
        contact_table = Base.metadata.tables["partner.subcontractor_contact"]
        scope_table = Base.metadata.tables["partner.subcontractor_scope"]
        finance_table = Base.metadata.tables["partner.subcontractor_finance_profile"]
        history_table = Base.metadata.tables["partner.subcontractor_history_entry"]

        subcontractor_checks = {c.name for c in subcontractor_table.constraints if isinstance(c, CheckConstraint)}
        scope_checks = {c.name for c in scope_table.constraints if isinstance(c, CheckConstraint)}
        contact_indexes = {i.name for i in contact_table.indexes if isinstance(i, Index)}
        finance_uniques = {c.name for c in finance_table.constraints if c.__class__.__name__ == "UniqueConstraint"}
        history_indexes = {i.name for i in history_table.indexes if isinstance(i, Index)}

        self.assertIn("ck_subcontractor_partner_subcontractor_coordinates_valid", subcontractor_checks)
        self.assertIn("ck_subcontractor_scope_partner_subcontractor_scope_window_valid", scope_checks)
        self.assertIn("uq_partner_subcontractor_contact_primary_per_company", contact_indexes)
        self.assertIn("uq_partner_subcontractor_finance_profile_company", finance_uniques)
        self.assertIn("ix_partner_subcontractor_history_company_occurred", history_indexes)


if __name__ == "__main__":
    unittest.main()
