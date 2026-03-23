"""Watchbook application service."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from app.errors import ApiException
from app.modules.customers.schemas import CustomerPortalContextRead
from app.modules.field_execution.models import Watchbook, WatchbookEntry
from app.modules.field_execution.schemas import (
    ReleasedCustomerWatchbookRead,
    ReleasedSubcontractorWatchbookRead,
    ReleasedWatchbookDocumentRead,
    ReleasedWatchbookEntryRead,
    WatchbookEntryCreate,
    WatchbookEntryRead,
    WatchbookListFilter,
    WatchbookListItem,
    WatchbookOpenRequest,
    WatchbookPdfRead,
    WatchbookRead,
    WatchbookReviewRequest,
    WatchbookVisibilityUpdate,
)
from app.modules.iam.audit_service import AuditActor, AuditService
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_schemas import DocumentCreate, DocumentLinkCreate, DocumentVersionCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.subcontractors.schemas import SubcontractorPortalContextRead


class WatchbookRepository(Protocol):
    def list_watchbooks(self, tenant_id: str, filters): ...  # noqa: ANN001
    def get_watchbook(self, tenant_id: str, watchbook_id: str): ...  # noqa: ANN001
    def find_open_watchbook(self, tenant_id: str, *, context_type: str, log_date, site_id: str | None, order_id: str | None, planning_record_id: str | None): ...  # noqa: ANN001,E501
    def create_watchbook(self, row: Watchbook): ...  # noqa: ANN001
    def save_watchbook(self, row: Watchbook): ...  # noqa: ANN001
    def create_entry(self, row: WatchbookEntry): ...  # noqa: ANN001
    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str): ...  # noqa: ANN001
    def get_document(self, tenant_id: str, document_id: str): ...  # noqa: ANN001
    def get_site(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def get_order(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def get_planning_record(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def get_shift(self, tenant_id: str, row_id: str): ...  # noqa: ANN001
    def get_subcontractor(self, tenant_id: str, subcontractor_id: str): ...  # noqa: ANN001
    def list_customer_released_watchbooks(self, tenant_id: str, customer_id: str): ...  # noqa: ANN001
    def list_subcontractor_released_watchbooks(self, tenant_id: str, subcontractor_id: str): ...  # noqa: ANN001


INTERNAL_WATCHBOOK_ROLES = frozenset({"platform_admin", "tenant_admin", "dispatcher", "controller_qm", "employee_user"})


@dataclass(frozen=True, slots=True)
class WatchbookService:
    repository: WatchbookRepository
    document_service: DocumentService
    audit_service: AuditService

    def list_watchbooks(self, tenant_id: str, filters: WatchbookListFilter, actor: RequestAuthorizationContext) -> list[WatchbookListItem]:
        self._ensure_internal_access(actor, tenant_id)
        return [self._to_watchbook_list_item(row) for row in self.repository.list_watchbooks(tenant_id, filters)]

    def open_or_create_watchbook(
        self,
        tenant_id: str,
        payload: WatchbookOpenRequest,
        actor: RequestAuthorizationContext,
    ) -> WatchbookRead:
        self._ensure_internal_access(actor, tenant_id)
        self._validate_context(tenant_id, payload)
        existing = self.repository.find_open_watchbook(
            tenant_id,
            context_type=payload.context_type,
            log_date=payload.log_date,
            site_id=payload.site_id,
            order_id=payload.order_id,
            planning_record_id=payload.planning_record_id,
        )
        if existing is not None:
            return self._to_watchbook_read(existing)
        customer_id, subcontractor_id = self._resolve_customer_and_subcontractor(tenant_id, payload)
        row = self.repository.create_watchbook(
            Watchbook(
                tenant_id=tenant_id,
                customer_id=customer_id,
                context_type=payload.context_type,
                log_date=payload.log_date,
                site_id=payload.site_id,
                order_id=payload.order_id,
                planning_record_id=payload.planning_record_id,
                shift_id=payload.shift_id,
                headline=payload.headline,
                summary=payload.summary,
                subcontractor_id=subcontractor_id,
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            )
        )
        self._audit(actor, "field.watchbook.created", row.id, after_json=self._watchbook_snapshot(row))
        return self._to_watchbook_read(row)

    def get_watchbook(self, tenant_id: str, watchbook_id: str, actor: RequestAuthorizationContext) -> WatchbookRead:
        self._ensure_internal_access(actor, tenant_id)
        row = self._require_watchbook(tenant_id, watchbook_id)
        return self._to_watchbook_read(row)

    def create_entry(
        self,
        tenant_id: str,
        watchbook_id: str,
        payload: WatchbookEntryCreate,
        actor: RequestAuthorizationContext,
        *,
        author_actor_type: str = "internal",
    ) -> WatchbookEntryRead:
        row = self._require_watchbook(tenant_id, watchbook_id)
        if author_actor_type == "internal":
            self._ensure_internal_access(actor, tenant_id)
        if row.closure_state_code != "open":
            raise ApiException(409, "field.watchbook.closed", "errors.field.watchbook.closed")
        entry = self.repository.create_entry(
            WatchbookEntry(
                tenant_id=tenant_id,
                watchbook_id=watchbook_id,
                assignment_id=payload.assignment_id,
                occurred_at=payload.occurred_at or datetime.now(UTC),
                entry_type_code=payload.entry_type_code,
                narrative=payload.narrative,
                traffic_light_code=payload.traffic_light_code,
                author_user_id=actor.user_id,
                author_actor_type=author_actor_type,
                created_by_user_id=actor.user_id,
                metadata_json={},
            )
        )
        for document_id in payload.attachment_document_ids:
            self.document_service.add_document_link(
                tenant_id,
                document_id,
                DocumentLinkCreate(owner_type="field.watchbook_entry", owner_id=entry.id, relation_type="attachment"),
                actor,
            )
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        self.repository.save_watchbook(row)
        self._audit(
            actor,
            "field.watchbook.entry_created",
            entry.id,
            after_json={"watchbook_id": watchbook_id, "entry_type_code": entry.entry_type_code, "author_actor_type": author_actor_type},
        )
        return self._to_entry_read(tenant_id, entry)

    def review_watchbook(
        self,
        tenant_id: str,
        watchbook_id: str,
        payload: WatchbookReviewRequest,
        actor: RequestAuthorizationContext,
    ) -> WatchbookRead:
        self._ensure_review_access(actor, tenant_id)
        row = self._require_watchbook(tenant_id, watchbook_id)
        row.review_status_code = "reviewed"
        row.reviewed_at = datetime.now(UTC)
        row.supervisor_user_id = actor.user_id
        row.supervisor_note = payload.supervisor_note
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        saved = self.repository.save_watchbook(row)
        self._audit(actor, "field.watchbook.reviewed", saved.id, after_json=self._watchbook_snapshot(saved))
        return self._to_watchbook_read(saved)

    def close_watchbook(self, tenant_id: str, watchbook_id: str, actor: RequestAuthorizationContext) -> WatchbookRead:
        self._ensure_review_access(actor, tenant_id)
        row = self._require_watchbook(tenant_id, watchbook_id)
        row.closure_state_code = "closed"
        row.closed_at = datetime.now(UTC)
        row.closed_by_user_id = actor.user_id
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        saved = self.repository.save_watchbook(row)
        self._audit(actor, "field.watchbook.closed", saved.id, after_json=self._watchbook_snapshot(saved))
        return self._to_watchbook_read(saved)

    def update_visibility(
        self,
        tenant_id: str,
        watchbook_id: str,
        payload: WatchbookVisibilityUpdate,
        actor: RequestAuthorizationContext,
    ) -> WatchbookRead:
        self._ensure_review_access(actor, tenant_id)
        row = self._require_watchbook(tenant_id, watchbook_id)
        for field in payload.model_fields_set:
            setattr(row, field, getattr(payload, field))
        row.updated_by_user_id = actor.user_id
        row.version_no += 1
        saved = self.repository.save_watchbook(row)
        self._audit(actor, "field.watchbook.visibility_updated", saved.id, after_json=self._watchbook_snapshot(saved))
        return self._to_watchbook_read(saved)

    def generate_pdf(self, tenant_id: str, watchbook_id: str, actor: RequestAuthorizationContext) -> WatchbookPdfRead:
        self._ensure_review_access(actor, tenant_id)
        row = self._require_watchbook(tenant_id, watchbook_id)
        body = self._render_pdf_bytes(row)
        if row.pdf_document_id is None:
            document = self.document_service.create_document(
                tenant_id,
                DocumentCreate(
                    tenant_id=tenant_id,
                    title=f"Watchbook {row.log_date.isoformat()}",
                    source_module="field_execution",
                    source_label="watchbook_pdf",
                    metadata_json={"watchbook_id": row.id},
                ),
                actor,
            )
            row.pdf_document_id = document.id
            self.repository.save_watchbook(row)
        version = self.document_service.add_document_version(
            tenant_id,
            row.pdf_document_id,
            DocumentVersionCreate(
                file_name=f"watchbook-{row.log_date.isoformat()}.pdf",
                content_type="application/pdf",
                content_base64=base64.b64encode(body).decode("ascii"),
                is_revision_safe_pdf=True,
                metadata_json={"watchbook_id": row.id, "entry_count": len(row.entries)},
            ),
            actor,
        )
        try:
            self.document_service.add_document_link(
                tenant_id,
                row.pdf_document_id,
                DocumentLinkCreate(owner_type="field.watchbook", owner_id=row.id, relation_type="daily_pdf"),
                actor,
            )
        except ApiException as exc:
            if exc.status_code != 409:
                raise
        document = self.document_service.get_document(tenant_id, row.pdf_document_id, actor)
        self._audit(actor, "field.watchbook.pdf_generated", row.id, after_json={"pdf_document_id": row.pdf_document_id, "version_no": version.version_no})
        return WatchbookPdfRead(watchbook_id=row.id, document=document, generated_at=datetime.now(UTC))

    def list_customer_released_watchbooks(self, context: CustomerPortalContextRead) -> list[ReleasedCustomerWatchbookRead]:
        return [self._to_customer_released_read(row) for row in self.repository.list_customer_released_watchbooks(context.tenant_id, context.customer_id)]

    def list_subcontractor_released_watchbooks(self, context: SubcontractorPortalContextRead) -> list[ReleasedSubcontractorWatchbookRead]:
        return [
            self._to_subcontractor_released_read(row)
            for row in self.repository.list_subcontractor_released_watchbooks(context.tenant_id, context.subcontractor_id)
        ]

    def add_customer_portal_entry(
        self,
        context: CustomerPortalContextRead,
        watchbook_id: str,
        payload: WatchbookEntryCreate,
        actor: RequestAuthorizationContext,
    ) -> WatchbookEntryRead:
        row = self._require_watchbook(context.tenant_id, watchbook_id)
        if row.customer_id != context.customer_id or not row.customer_visibility_released or not row.customer_participation_enabled:
            raise ApiException(403, "field.watchbook.portal_write_denied", "errors.field.watchbook.portal_write_denied")
        return self.create_entry(context.tenant_id, watchbook_id, payload, actor, author_actor_type="customer")

    def add_subcontractor_portal_entry(
        self,
        context: SubcontractorPortalContextRead,
        watchbook_id: str,
        payload: WatchbookEntryCreate,
        actor: RequestAuthorizationContext,
    ) -> WatchbookEntryRead:
        row = self._require_watchbook(context.tenant_id, watchbook_id)
        if row.subcontractor_id != context.subcontractor_id or not row.subcontractor_visibility_released or not row.subcontractor_participation_enabled:
            raise ApiException(403, "field.watchbook.portal_write_denied", "errors.field.watchbook.portal_write_denied")
        return self.create_entry(context.tenant_id, watchbook_id, payload, actor, author_actor_type="subcontractor")

    def _validate_context(self, tenant_id: str, payload: WatchbookOpenRequest) -> None:
        if payload.context_type == "site":
            if payload.site_id is None:
                raise ApiException(400, "field.watchbook.context_invalid", "errors.field.watchbook.context_invalid")
            site = self.repository.get_site(tenant_id, payload.site_id)
            if site is None or not site.watchbook_enabled:
                raise ApiException(409, "field.watchbook.context_invalid", "errors.field.watchbook.context_invalid")
            return
        if payload.context_type == "order":
            if payload.order_id is None or self.repository.get_order(tenant_id, payload.order_id) is None:
                raise ApiException(400, "field.watchbook.context_invalid", "errors.field.watchbook.context_invalid")
            return
        if payload.context_type == "planning_record":
            if payload.planning_record_id is None or self.repository.get_planning_record(tenant_id, payload.planning_record_id) is None:
                raise ApiException(400, "field.watchbook.context_invalid", "errors.field.watchbook.context_invalid")
            return
        raise ApiException(400, "field.watchbook.context_invalid", "errors.field.watchbook.context_invalid")

    def _resolve_customer_and_subcontractor(self, tenant_id: str, payload: WatchbookOpenRequest) -> tuple[str, str | None]:
        if payload.context_type == "site":
            site = self.repository.get_site(tenant_id, payload.site_id or "")
            return site.customer_id, None
        if payload.context_type == "order":
            order = self.repository.get_order(tenant_id, payload.order_id or "")
            return order.customer_id, None
        planning = self.repository.get_planning_record(tenant_id, payload.planning_record_id or "")
        return planning.order.customer_id, None

    def _require_watchbook(self, tenant_id: str, watchbook_id: str) -> Watchbook:
        row = self.repository.get_watchbook(tenant_id, watchbook_id)
        if row is None:
            raise ApiException(404, "field.watchbook.not_found", "errors.field.watchbook.not_found")
        return row

    @staticmethod
    def _ensure_internal_access(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.tenant_id != tenant_id or not actor.role_keys.intersection(INTERNAL_WATCHBOOK_ROLES):
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")

    @staticmethod
    def _ensure_review_access(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.tenant_id != tenant_id or not actor.role_keys.intersection({"platform_admin", "tenant_admin", "dispatcher", "controller_qm"}):
            raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")

    def _audit(self, actor: RequestAuthorizationContext, event_type: str, entity_id: str, *, after_json: dict[str, object]) -> None:
        self.audit_service.record_business_event(
            actor=AuditActor(
                tenant_id=actor.tenant_id,
                user_id=actor.user_id,
                session_id=actor.session_id,
                request_id=actor.request_id,
            ),
            event_type=event_type,
            entity_type="field.watchbook",
            entity_id=entity_id,
            after_json=after_json,
        )

    def _to_watchbook_list_item(self, row: Watchbook) -> WatchbookListItem:
        return WatchbookListItem(
            id=row.id,
            context_type=row.context_type,
            log_date=row.log_date,
            headline=row.headline,
            review_status_code=row.review_status_code,
            closure_state_code=row.closure_state_code,
            customer_visibility_released=row.customer_visibility_released,
            subcontractor_visibility_released=row.subcontractor_visibility_released,
            customer_participation_enabled=row.customer_participation_enabled,
            subcontractor_participation_enabled=row.subcontractor_participation_enabled,
            updated_at=row.updated_at,
        )

    def _to_watchbook_read(self, row: Watchbook) -> WatchbookRead:
        return WatchbookRead(
            id=row.id,
            tenant_id=row.tenant_id,
            customer_id=row.customer_id,
            context_type=row.context_type,
            log_date=row.log_date,
            site_id=row.site_id,
            order_id=row.order_id,
            planning_record_id=row.planning_record_id,
            shift_id=row.shift_id,
            headline=row.headline,
            summary=row.summary,
            review_status_code=row.review_status_code,
            reviewed_at=row.reviewed_at,
            supervisor_user_id=row.supervisor_user_id,
            supervisor_note=row.supervisor_note,
            closure_state_code=row.closure_state_code,
            closed_at=row.closed_at,
            closed_by_user_id=row.closed_by_user_id,
            pdf_document_id=row.pdf_document_id,
            customer_visibility_released=row.customer_visibility_released,
            subcontractor_visibility_released=row.subcontractor_visibility_released,
            customer_participation_enabled=row.customer_participation_enabled,
            subcontractor_participation_enabled=row.subcontractor_participation_enabled,
            customer_personal_names_released=row.customer_personal_names_released,
            subcontractor_id=row.subcontractor_id,
            status=row.status,
            version_no=row.version_no,
            created_at=row.created_at,
            updated_at=row.updated_at,
            entries=[self._to_entry_read(row.tenant_id, item) for item in row.entries],
        )

    def _to_entry_read(self, tenant_id: str, row: WatchbookEntry) -> WatchbookEntryRead:
        return WatchbookEntryRead(
            id=row.id,
            watchbook_id=row.watchbook_id,
            assignment_id=row.assignment_id,
            occurred_at=row.occurred_at,
            entry_type_code=row.entry_type_code,
            narrative=row.narrative,
            traffic_light_code=row.traffic_light_code,
            author_user_id=row.author_user_id,
            author_actor_type=row.author_actor_type,
            created_at=row.created_at,
            attachment_document_ids=[item.id for item in self.repository.list_documents_for_owner(tenant_id, "field.watchbook_entry", row.id)],
        )

    def _to_customer_released_read(self, row: Watchbook) -> ReleasedCustomerWatchbookRead:
        return ReleasedCustomerWatchbookRead(
            id=row.id,
            customer_id=row.customer_id,
            log_date=row.log_date,
            context_type=row.context_type,
            headline=row.headline,
            summary=row.summary,
            reviewed_at=row.reviewed_at,
            closure_state_code=row.closure_state_code,
            pdf_document=self._doc_ref(row.tenant_id, row.pdf_document_id) if row.pdf_document_id is not None else None,
            entries=[
                ReleasedWatchbookEntryRead(
                    id=item.id,
                    occurred_at=item.occurred_at,
                    entry_type_code=item.entry_type_code,
                    summary=self._customer_safe_summary(row, item),
                    traffic_light_code=item.traffic_light_code,
                )
                for item in row.entries
            ],
        )

    def _to_subcontractor_released_read(self, row: Watchbook) -> ReleasedSubcontractorWatchbookRead:
        return ReleasedSubcontractorWatchbookRead(
            id=row.id,
            subcontractor_id=row.subcontractor_id or "",
            log_date=row.log_date,
            context_type=row.context_type,
            headline=row.headline,
            summary=row.summary,
            reviewed_at=row.reviewed_at,
            closure_state_code=row.closure_state_code,
            pdf_document=self._doc_ref(row.tenant_id, row.pdf_document_id) if row.pdf_document_id is not None else None,
            entries=[
                ReleasedWatchbookEntryRead(
                    id=item.id,
                    occurred_at=item.occurred_at,
                    entry_type_code=item.entry_type_code,
                    summary=item.narrative,
                    traffic_light_code=item.traffic_light_code,
                )
                for item in row.entries
            ],
        )

    def _doc_ref(self, tenant_id: str, document_id: str) -> ReleasedWatchbookDocumentRead:
        document = self.repository.get_document(tenant_id, document_id)
        if document is None:
            return ReleasedWatchbookDocumentRead(document_id=document_id, title="Watchbook PDF")
        version = next((item for item in document.versions if item.version_no == document.current_version_no), None)
        return ReleasedWatchbookDocumentRead(
            document_id=document.id,
            title=document.title,
            file_name=version.file_name if version is not None else None,
            content_type=version.content_type if version is not None else None,
            current_version_no=document.current_version_no,
        )

    @staticmethod
    def _customer_safe_summary(watchbook: Watchbook, row: WatchbookEntry) -> str:
        if watchbook.customer_personal_names_released:
            return row.narrative
        return f"{row.entry_type_code} · {row.occurred_at.strftime('%H:%M')}"

    @staticmethod
    def _watchbook_snapshot(row: Watchbook) -> dict[str, object]:
        return {
            "context_type": row.context_type,
            "log_date": row.log_date.isoformat(),
            "review_status_code": row.review_status_code,
            "closure_state_code": row.closure_state_code,
            "customer_visibility_released": row.customer_visibility_released,
            "subcontractor_visibility_released": row.subcontractor_visibility_released,
            "customer_participation_enabled": row.customer_participation_enabled,
            "subcontractor_participation_enabled": row.subcontractor_participation_enabled,
        }

    @staticmethod
    def _render_pdf_bytes(row: Watchbook) -> bytes:
        lines = [
            "%PDF-1.4",
            f"Watchbook {row.id}",
            f"Date {row.log_date.isoformat()}",
            f"Context {row.context_type}",
        ]
        for item in sorted(row.entries, key=lambda entry: (entry.occurred_at, entry.created_at, entry.id)):
            lines.append(f"{item.occurred_at.isoformat()}|{item.entry_type_code}|{item.author_actor_type}|{item.narrative}")
        lines.append("%%EOF")
        return "\n".join(lines).encode("utf-8")
