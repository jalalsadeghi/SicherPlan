"""Customer collaboration reads and controls for history, privacy, login visibility, and blocks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from app.errors import ApiException
from app.modules.customers.models import CustomerEmployeeBlock
from app.modules.customers.policy import enforce_customer_module_access
from app.modules.customers.schemas import (
    CustomerEmployeeBlockCapabilityRead,
    CustomerEmployeeBlockCollectionRead,
    CustomerEmployeeBlockCreate,
    CustomerEmployeeBlockRead,
    CustomerEmployeeBlockUpdate,
    CustomerHistoryAttachmentLinkCreate,
    CustomerHistoryAttachmentRead,
    CustomerHistoryEntryRead,
    CustomerLoginHistoryEntryRead,
    CustomerPortalContextRead,
    CustomerPortalHistoryCollectionRead,
    CustomerPortalPrivacyRead,
    CustomerPortalPrivacyUpdate,
    CustomerPortalHistoryEntryRead,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_schemas import DocumentLinkCreate
from app.modules.platform_services.docs_service import DocumentService


class CustomerCollaborationRepository(Protocol):
    def get_customer(self, tenant_id: str, customer_id: str): ...  # noqa: ANN001
    def get_history_entry(self, tenant_id: str, customer_id: str, history_entry_id: str): ...  # noqa: ANN001
    def list_history_entries(self, tenant_id: str, customer_id: str): ...  # noqa: ANN001
    def list_employee_blocks(self, tenant_id: str, customer_id: str): ...  # noqa: ANN001
    def get_employee_block(self, tenant_id: str, customer_id: str, block_id: str): ...  # noqa: ANN001
    def find_overlapping_employee_block(self, tenant_id: str, customer_id: str, employee_id: str, effective_from, effective_to, *, exclude_id: str | None = None): ...  # noqa: ANN001,E501
    def create_employee_block(self, row: CustomerEmployeeBlock): ...  # noqa: ANN001
    def update_employee_block(self, tenant_id: str, customer_id: str, block_id: str, payload, actor_user_id: str | None): ...  # noqa: ANN001,E501
    def update_customer(self, tenant_id: str, customer_id: str, payload, actor_user_id: str | None): ...  # noqa: ANN001,E501


class LoginAuditRepository(Protocol):
    def list_login_events_for_users(self, tenant_id: str, user_ids: list[str]): ...  # noqa: ANN001


class HistoryDocumentRepository(Protocol):
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str): ...  # noqa: ANN001


@dataclass(frozen=True, slots=True)
class EmployeeBlockCapability:
    directory_available: bool = False
    employee_reference_mode: str = "employee_id_only"
    message_key: str = "customerAdmin.employeeBlocks.capability.pendingEmployees"


@dataclass(frozen=True, slots=True)
class CustomerPrivacyRepositoryUpdate:
    version_no: int
    portal_person_names_released: bool
    portal_person_names_released_at: datetime | None
    portal_person_names_released_by_user_id: str | None

    def model_dump(self, *, exclude_unset: bool = True, exclude: set[str] | None = None) -> dict[str, object]:  # noqa: ARG002
        payload = {
            "portal_person_names_released": self.portal_person_names_released,
            "portal_person_names_released_at": self.portal_person_names_released_at,
            "portal_person_names_released_by_user_id": self.portal_person_names_released_by_user_id,
        }
        if exclude:
            for key in exclude:
                payload.pop(key, None)
        return payload


class CustomerCollaborationService:
    EMPLOYEE_BLOCK_CAPABILITY = EmployeeBlockCapability()

    def __init__(
        self,
        repository: CustomerCollaborationRepository,
        *,
        login_audit_repository: LoginAuditRepository,
        document_repository: HistoryDocumentRepository,
        document_service: DocumentService,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository
        self.login_audit_repository = login_audit_repository
        self.document_repository = document_repository
        self.document_service = document_service
        self.audit_service = audit_service

    def list_history(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerHistoryEntryRead]:
        self._require_internal_customer_access(tenant_id, customer_id, actor)
        results: list[CustomerHistoryEntryRead] = []
        for row in self.repository.list_history_entries(tenant_id, customer_id):
            validated = CustomerHistoryEntryRead.model_validate(row)
            results.append(
                validated.model_copy(update={"attachments": self._history_attachments(tenant_id, row.id)})
            )
        return results

    def list_portal_history(self, context: CustomerPortalContextRead) -> CustomerPortalHistoryCollectionRead:
        customer = self._require_customer_record(context.tenant_id, context.customer_id)
        names_released = bool(customer.portal_person_names_released)
        return CustomerPortalHistoryCollectionRead(
            customer_id=context.customer_id,
            items=[
                CustomerPortalHistoryEntryRead(
                    id=row.id,
                    entry_type=row.entry_type,
                    title=self._portal_history_title(row.entry_type, names_released),
                    summary=self._portal_history_summary(row.entry_type, names_released),
                    created_at=row.created_at,
                    attachments=self._history_attachments(context.tenant_id, row.id, names_released=names_released),
                )
                for row in self.repository.list_history_entries(context.tenant_id, context.customer_id)
            ],
        )

    def link_history_attachment(
        self,
        tenant_id: str,
        customer_id: str,
        history_entry_id: str,
        payload: CustomerHistoryAttachmentLinkCreate,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerHistoryAttachmentRead]:
        self._require_internal_customer_access(tenant_id, customer_id, actor)
        history_entry = self.repository.get_history_entry(tenant_id, customer_id, history_entry_id)
        if history_entry is None:
            raise ApiException(404, "customers.history_entry.not_found", "errors.customers.history_entry.not_found")
        self.document_service.add_document_link(
            tenant_id,
            payload.document_id,
            DocumentLinkCreate(
                owner_type="crm.customer_history_entry",
                owner_id=history_entry_id,
                relation_type="attachment",
                label=payload.label,
            ),
            actor,
        )
        return self._history_attachments(tenant_id, history_entry_id)

    def get_portal_privacy(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> CustomerPortalPrivacyRead:
        customer = self._require_internal_customer_access(tenant_id, customer_id, actor)
        return CustomerPortalPrivacyRead(
            customer_id=customer.id,
            person_names_released=customer.portal_person_names_released,
            person_names_released_at=customer.portal_person_names_released_at,
            person_names_released_by_user_id=customer.portal_person_names_released_by_user_id,
        )

    def update_portal_privacy(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerPortalPrivacyUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerPortalPrivacyRead:
        customer = self._require_internal_customer_access(tenant_id, customer_id, actor)
        updated = self.repository.update_customer(
            tenant_id,
            customer_id,
            CustomerPrivacyRepositoryUpdate(
                version_no=customer.version_no,
                portal_person_names_released=payload.person_names_released,
                portal_person_names_released_at=datetime.now(UTC) if payload.person_names_released else None,
                portal_person_names_released_by_user_id=actor.user_id if payload.person_names_released else None,
            ),
            actor.user_id,
        )
        if updated is None:
            raise ApiException(404, "customers.customer.not_found", "errors.customers.customer.not_found")
        self._record_event(
            actor,
            event_type="customers.portal_privacy.person_names_released",
            entity_id=customer_id,
            tenant_id=tenant_id,
            before_json={"person_names_released": customer.portal_person_names_released},
            after_json={"person_names_released": updated.portal_person_names_released},
        )
        return CustomerPortalPrivacyRead(
            customer_id=updated.id,
            person_names_released=updated.portal_person_names_released,
            person_names_released_at=updated.portal_person_names_released_at,
            person_names_released_by_user_id=updated.portal_person_names_released_by_user_id,
        )

    def list_login_history(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> list[CustomerLoginHistoryEntryRead]:
        customer = self._require_internal_customer_access(tenant_id, customer_id, actor)
        contacts_by_user_id = {
            contact.user_id: contact
            for contact in customer.contacts
            if contact.user_id and contact.archived_at is None
        }
        rows = self.login_audit_repository.list_login_events_for_users(tenant_id, list(contacts_by_user_id))
        return [
            CustomerLoginHistoryEntryRead(
                id=row.id,
                user_account_id=row.user_account_id,
                contact_id=contact.id if contact else None,
                contact_name=None,
                identifier=self._mask_identifier(row.identifier),
                outcome=row.outcome,
                failure_reason=row.failure_reason,
                auth_method=row.auth_method,
                created_at=row.created_at,
            )
            for row in rows
            for contact in [contacts_by_user_id.get(row.user_account_id)]
        ]

    def list_employee_blocks(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ) -> CustomerEmployeeBlockCollectionRead:
        self._require_internal_customer_access(tenant_id, customer_id, actor)
        capability = CustomerEmployeeBlockCapabilityRead(
            directory_available=self.EMPLOYEE_BLOCK_CAPABILITY.directory_available,
            employee_reference_mode=self.EMPLOYEE_BLOCK_CAPABILITY.employee_reference_mode,
            message_key=self.EMPLOYEE_BLOCK_CAPABILITY.message_key,
        )
        return CustomerEmployeeBlockCollectionRead(
            customer_id=customer_id,
            capability=capability,
            items=[
                CustomerEmployeeBlockRead.model_validate(row)
                for row in self.repository.list_employee_blocks(tenant_id, customer_id)
            ],
        )

    def create_employee_block(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerEmployeeBlockCreate,
        actor: RequestAuthorizationContext,
    ) -> CustomerEmployeeBlockRead:
        self._require_internal_customer_access(tenant_id, customer_id, actor)
        self._ensure_payload_scope(tenant_id, customer_id, payload.tenant_id, payload.customer_id)
        self._validate_block_window(payload.employee_id, payload.effective_from, payload.effective_to)
        if self.repository.find_overlapping_employee_block(
            tenant_id,
            customer_id,
            payload.employee_id,
            payload.effective_from,
            payload.effective_to,
        ):
            raise ApiException(
                409,
                "customers.employee_block.overlap",
                "errors.customers.employee_block.overlap",
            )
        row = self.repository.create_employee_block(
            CustomerEmployeeBlock(
                tenant_id=tenant_id,
                customer_id=customer_id,
                employee_id=payload.employee_id,
                reason=payload.reason.strip(),
                effective_from=payload.effective_from,
                effective_to=payload.effective_to,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._record_event(
            actor,
            event_type="customers.employee_block.created",
            entity_id=row.id,
            tenant_id=tenant_id,
            after_json={
                "customer_id": customer_id,
                "employee_id": row.employee_id,
                "effective_from": str(row.effective_from),
                "effective_to": str(row.effective_to) if row.effective_to else None,
            },
        )
        return CustomerEmployeeBlockRead.model_validate(row)

    def update_employee_block(
        self,
        tenant_id: str,
        customer_id: str,
        block_id: str,
        payload: CustomerEmployeeBlockUpdate,
        actor: RequestAuthorizationContext,
    ) -> CustomerEmployeeBlockRead:
        self._require_internal_customer_access(tenant_id, customer_id, actor)
        existing = self.repository.get_employee_block(tenant_id, customer_id, block_id)
        if existing is None:
            raise ApiException(404, "customers.employee_block.not_found", "errors.customers.employee_block.not_found")
        if payload.version_no is None or payload.version_no != existing.version_no:
            raise ApiException(
                409,
                "customers.employee_block.stale_version",
                "errors.customers.employee_block.stale_version",
            )
        next_from = payload.effective_from or existing.effective_from
        next_to = payload.effective_to if "effective_to" in payload.model_fields_set else existing.effective_to
        self._validate_block_window(existing.employee_id, next_from, next_to)
        if self.repository.find_overlapping_employee_block(
            tenant_id,
            customer_id,
            existing.employee_id,
            next_from,
            next_to,
            exclude_id=block_id,
        ):
            raise ApiException(
                409,
                "customers.employee_block.overlap",
                "errors.customers.employee_block.overlap",
            )
        updated = self.repository.update_employee_block(tenant_id, customer_id, block_id, payload, actor.user_id)
        if updated is None:
            raise ApiException(404, "customers.employee_block.not_found", "errors.customers.employee_block.not_found")
        self._record_event(
            actor,
            event_type="customers.employee_block.updated",
            entity_id=updated.id,
            tenant_id=tenant_id,
            before_json={"version_no": existing.version_no, "effective_from": str(existing.effective_from)},
            after_json={"version_no": updated.version_no, "effective_from": str(updated.effective_from)},
        )
        return CustomerEmployeeBlockRead.model_validate(updated)

    def _require_internal_customer_access(
        self,
        tenant_id: str,
        customer_id: str,
        actor: RequestAuthorizationContext,
    ):
        enforce_customer_module_access(actor, tenant_id=tenant_id)
        customer = self.repository.get_customer(tenant_id, customer_id)
        if customer is None:
            raise ApiException(404, "customers.customer.not_found", "errors.customers.customer.not_found")
        return customer

    def _require_customer_record(self, tenant_id: str, customer_id: str):
        customer = self.repository.get_customer(tenant_id, customer_id)
        if customer is None:
            raise ApiException(404, "customers.customer.not_found", "errors.customers.customer.not_found")
        return customer

    def _history_attachments(
        self,
        tenant_id: str,
        history_entry_id: str,
        *,
        names_released: bool = True,
    ) -> list[CustomerHistoryAttachmentRead]:
        return [
            CustomerHistoryAttachmentRead(
                document_id=document.id,
                title=document.title if names_released else self._mask_document_title(document, index),
                document_type_key=document.document_type.key if document.document_type else None,
                file_name=(
                    document.versions[-1].file_name
                    if names_released or not document.versions
                    else self._mask_file_name(document.versions[-1].file_name, index)
                ),
                content_type=document.versions[-1].content_type if document.versions else None,
                current_version_no=document.current_version_no,
            )
            for index, document in enumerate(
                self.document_repository.list_documents_for_owner(
                tenant_id,
                "crm.customer_history_entry",
                history_entry_id,
                ),
                start=1,
            )
        ]

    @staticmethod
    def _ensure_payload_scope(
        tenant_id: str,
        customer_id: str,
        payload_tenant_id: str,
        payload_customer_id: str,
    ) -> None:
        if payload_tenant_id == tenant_id and payload_customer_id == customer_id:
            return
        raise ApiException(400, "customers.customer.tenant_mismatch", "errors.customers.customer.tenant_mismatch")

    @staticmethod
    def _validate_block_window(employee_id: str, effective_from, effective_to) -> None:  # noqa: ANN001
        if not employee_id.strip():
            raise ApiException(400, "customers.employee_block.invalid_employee_id", "errors.customers.employee_block.invalid_employee_id")
        if effective_to is not None and effective_to < effective_from:
            raise ApiException(
                400,
                "customers.employee_block.invalid_effective_range",
                "errors.customers.employee_block.invalid_effective_range",
            )

    def _record_event(
        self,
        actor: RequestAuthorizationContext,
        *,
        event_type: str,
        entity_id: str,
        tenant_id: str,
        before_json: dict[str, object] | None = None,
        after_json: dict[str, object] | None = None,
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
            entity_type="crm.customer_employee_block",
            entity_id=entity_id,
            tenant_id=tenant_id,
            before_json=before_json or {},
            after_json=after_json or {},
            metadata_json={"employee_directory_available": False},
        )

    @staticmethod
    def _portal_history_title(entry_type: str, names_released: bool) -> str:
        if names_released:
            return {
                "customer.created": "Customer created",
                "customer.updated": "Customer updated",
                "customer.status.changed": "Customer status changed",
                "customer.contact.created": "Contact created",
                "customer.contact.updated": "Contact updated",
                "customer.address.created": "Address linked",
                "customer.address.updated": "Address updated",
            }.get(entry_type, "Customer history event")
        return {
            "customer.created": "Customer record updated",
            "customer.updated": "Customer record updated",
            "customer.status.changed": "Customer status updated",
            "customer.contact.created": "Contact change recorded",
            "customer.contact.updated": "Contact change recorded",
            "customer.address.created": "Address change recorded",
            "customer.address.updated": "Address change recorded",
        }.get(entry_type, "Customer history event")

    @staticmethod
    def _portal_history_summary(entry_type: str, names_released: bool) -> str:
        if names_released:
            return {
                "customer.created": "The customer record was created.",
                "customer.updated": "Customer master data was updated.",
                "customer.status.changed": "The customer status was changed.",
                "customer.contact.created": "A customer contact was added.",
                "customer.contact.updated": "A customer contact was updated.",
                "customer.address.created": "A customer address link was added.",
                "customer.address.updated": "A customer address link was updated.",
            }.get(entry_type, "A customer history event was recorded.")
        return {
            "customer.created": "A customer record change was recorded.",
            "customer.updated": "A customer record change was recorded.",
            "customer.status.changed": "A customer status change was recorded.",
            "customer.contact.created": "A contact-related change was recorded.",
            "customer.contact.updated": "A contact-related change was recorded.",
            "customer.address.created": "An address-related change was recorded.",
            "customer.address.updated": "An address-related change was recorded.",
        }.get(entry_type, "A customer history event was recorded.")

    @staticmethod
    def _mask_identifier(identifier: str) -> str:
        value = identifier.strip()
        if "@" in value:
            local, _, domain = value.partition("@")
            if len(local) <= 1:
                return f"* @{domain}".replace(" ", "")
            return f"{local[0]}***@{domain}"
        if len(value) <= 3:
            return "***"
        return f"{value[:2]}***"

    @staticmethod
    def _mask_document_title(document, index: int) -> str:  # noqa: ANN001
        key = document.document_type.key if document.document_type else "attachment"
        return f"{key.replace('_', ' ').title()} {index}"

    @staticmethod
    def _mask_file_name(file_name: str | None, index: int) -> str | None:
        if not file_name:
            return None
        suffix = Path(file_name).suffix
        return f"attachment-{index}{suffix}"
