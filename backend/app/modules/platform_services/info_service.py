"""Notice service with audience resolution, publish windows, and durable read evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.errors import ApiException
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.docs_schemas import DocumentLinkCreate
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.info_models import Notice, NoticeAudience, NoticeLink, NoticeRead
from app.modules.platform_services.info_schemas import (
    NoticeAcknowledgeRequest,
    NoticeAudienceRead,
    NoticeCreate,
    NoticeLinkCreate as CuratedNoticeLinkCreate,
    NoticeLinkRead,
    NoticeListItem,
    NoticePublishRequest,
    NoticeRead as NoticeReadSchema,
    NoticeReadEvidenceRead,
)


SUPPORTED_NOTICE_LANGUAGES = frozenset({"de", "en"})
SUPPORTED_AUDIENCE_KINDS = frozenset(
    {
        "role",
        "employee_group",
        "qualification",
        "function",
        "all_employees",
        "all_customers",
        "all_subcontractors",
    }
)


class NoticeRepository(Protocol):
    def create_notice(self, notice: Notice, audiences: list[NoticeAudience], links: list[NoticeLink]) -> Notice: ...
    def list_notices(self, tenant_id: str) -> list[Notice]: ...
    def get_notice(self, tenant_id: str, notice_id: str) -> Notice | None: ...
    def save_notice(self, notice: Notice) -> Notice: ...
    def get_notice_read(self, notice_id: str, user_account_id: str) -> NoticeRead | None: ...
    def upsert_notice_read(self, read_row: NoticeRead) -> NoticeRead: ...
    def list_document_links_for_notice(self, tenant_id: str, notice_id: str): ...  # noqa: ANN001
    def create_notice_link(self, row: NoticeLink) -> NoticeLink: ...


class NoticeAudienceTraitProvider(Protocol):
    def employee_groups(self, actor: RequestAuthorizationContext) -> frozenset[str]: ...
    def qualifications(self, actor: RequestAuthorizationContext) -> frozenset[str]: ...
    def functions(self, actor: RequestAuthorizationContext) -> frozenset[str]: ...


class DefaultNoticeAudienceTraitProvider:
    def employee_groups(self, actor: RequestAuthorizationContext) -> frozenset[str]:
        return frozenset()

    def qualifications(self, actor: RequestAuthorizationContext) -> frozenset[str]:
        return frozenset()

    def functions(self, actor: RequestAuthorizationContext) -> frozenset[str]:
        return frozenset()


@dataclass(frozen=True, slots=True)
class NoticeAudienceResolver:
    trait_provider: NoticeAudienceTraitProvider

    def is_visible(self, notice: Notice, actor: RequestAuthorizationContext) -> bool:
        if actor.is_platform_admin:
            return True
        if actor.tenant_id != notice.tenant_id:
            return False
        if not notice.audiences:
            return False
        role_keys = actor.role_keys
        employee_groups = self.trait_provider.employee_groups(actor)
        qualifications = self.trait_provider.qualifications(actor)
        functions = self.trait_provider.functions(actor)
        is_employee = "employee_user" in role_keys
        is_customer = "customer_user" in role_keys
        is_subcontractor = "subcontractor_user" in role_keys
        for audience in notice.audiences:
            if audience.audience_kind == "role" and audience.target_value in role_keys:
                return True
            if audience.audience_kind == "employee_group" and audience.target_value in employee_groups:
                return True
            if audience.audience_kind == "qualification" and audience.target_value in qualifications:
                return True
            if audience.audience_kind == "function" and audience.target_value in functions:
                return True
            if audience.audience_kind == "all_employees" and is_employee:
                return True
            if audience.audience_kind == "all_customers" and is_customer:
                return True
            if audience.audience_kind == "all_subcontractors" and is_subcontractor:
                return True
        return False


class NoticeService:
    def __init__(
        self,
        repository: NoticeRepository,
        *,
        document_service: DocumentService,
        audience_resolver: NoticeAudienceResolver | None = None,
    ) -> None:
        self.repository = repository
        self.document_service = document_service
        self.audience_resolver = audience_resolver or NoticeAudienceResolver(DefaultNoticeAudienceTraitProvider())

    def create_notice(
        self,
        tenant_id: str,
        payload: NoticeCreate,
        actor: RequestAuthorizationContext,
    ) -> NoticeReadSchema:
        self._ensure_write_scope(actor, tenant_id)
        self._ensure_language(payload.language_code)
        notice = self.repository.create_notice(
            Notice(
                tenant_id=tenant_id,
                title=payload.title,
                summary=payload.summary,
                body=payload.body,
                language_code=payload.language_code,
                mandatory_acknowledgement=payload.mandatory_acknowledgement,
                publish_from=payload.publish_from,
                publish_until=payload.publish_until,
                related_entity_type=payload.related_entity_type,
                related_entity_id=payload.related_entity_id,
                metadata_json=payload.metadata_json,
                status="draft",
                created_by_user_id=actor.user_id,
                updated_by_user_id=actor.user_id,
            ),
            audiences=[
                NoticeAudience(
                    tenant_id=tenant_id,
                    notice_id="",
                    audience_kind=self._normalize_audience_kind(audience.audience_kind),
                    target_value=audience.target_value,
                    target_label=audience.target_label,
                    metadata_json=audience.metadata_json,
                    created_by_user_id=actor.user_id,
                    updated_by_user_id=actor.user_id,
                )
                for audience in payload.audiences
            ],
            links=[
                NoticeLink(
                    tenant_id=tenant_id,
                    notice_id="",
                    label=link.label,
                    url=link.url,
                    link_type=link.link_type,
                    sort_order=link.sort_order,
                    metadata_json=link.metadata_json,
                )
                for link in payload.curated_links
            ],
        )
        for document_id in payload.attachment_document_ids:
            self._attach_document(tenant_id, notice.id, document_id, actor)
        return self._to_notice_read(notice)

    def list_admin_notices(self, tenant_id: str, actor: RequestAuthorizationContext) -> list[NoticeListItem]:
        self._ensure_write_scope(actor, tenant_id)
        return [self._to_notice_list_item(notice, actor.user_id) for notice in self.repository.list_notices(tenant_id)]

    def get_notice_admin(self, tenant_id: str, notice_id: str, actor: RequestAuthorizationContext) -> NoticeReadSchema:
        self._ensure_write_scope(actor, tenant_id)
        notice = self._require_notice(tenant_id, notice_id)
        return self._to_notice_read(notice)

    def publish_notice(
        self,
        tenant_id: str,
        notice_id: str,
        payload: NoticePublishRequest,
        actor: RequestAuthorizationContext,
    ) -> NoticeReadSchema:
        self._ensure_write_scope(actor, tenant_id)
        notice = self._require_notice(tenant_id, notice_id)
        if not notice.audiences:
            raise ApiException(
                400,
                "info.notice.audience_missing",
                "errors.info.notice.audience_missing",
            )
        now = datetime.now(UTC)
        notice.status = "published"
        notice.publish_from = payload.publish_from or notice.publish_from or now
        notice.publish_until = payload.publish_until
        notice.published_at = now
        notice.unpublished_at = None
        notice.updated_by_user_id = actor.user_id
        notice.version_no += 1
        saved = self.repository.save_notice(notice)
        return self._to_notice_read(saved)

    def unpublish_notice(self, tenant_id: str, notice_id: str, actor: RequestAuthorizationContext) -> NoticeReadSchema:
        self._ensure_write_scope(actor, tenant_id)
        notice = self._require_notice(tenant_id, notice_id)
        notice.status = "unpublished"
        notice.unpublished_at = datetime.now(UTC)
        notice.updated_by_user_id = actor.user_id
        notice.version_no += 1
        saved = self.repository.save_notice(notice)
        return self._to_notice_read(saved)

    def list_visible_notices(self, tenant_id: str, actor: RequestAuthorizationContext) -> list[NoticeListItem]:
        self._ensure_read_scope(actor, tenant_id)
        visible = []
        for notice in self.repository.list_notices(tenant_id):
            if self._is_published_now(notice) and self.audience_resolver.is_visible(notice, actor):
                visible.append(self._to_notice_list_item(notice, actor.user_id))
        return visible

    def open_notice(self, tenant_id: str, notice_id: str, actor: RequestAuthorizationContext) -> NoticeReadEvidenceRead:
        self._ensure_read_scope(actor, tenant_id)
        notice = self._require_visible_notice(tenant_id, notice_id, actor)
        now = datetime.now(UTC)
        existing = self.repository.get_notice_read(notice.id, actor.user_id)
        saved = self.repository.upsert_notice_read(
            NoticeRead(
                tenant_id=tenant_id,
                notice_id=notice.id,
                user_account_id=actor.user_id,
                first_opened_at=existing.first_opened_at if existing is not None else now,
                last_opened_at=now,
                acknowledged_at=existing.acknowledged_at if existing is not None else None,
                acknowledgement_text=existing.acknowledgement_text if existing is not None else None,
                metadata_json={},
            )
        )
        return NoticeReadEvidenceRead.model_validate(saved)

    def acknowledge_notice(
        self,
        tenant_id: str,
        notice_id: str,
        payload: NoticeAcknowledgeRequest,
        actor: RequestAuthorizationContext,
    ) -> NoticeReadEvidenceRead:
        self._ensure_read_scope(actor, tenant_id)
        notice = self._require_visible_notice(tenant_id, notice_id, actor)
        existing = self.repository.get_notice_read(notice.id, actor.user_id)
        if existing is not None and existing.acknowledged_at is not None:
            raise ApiException(
                409,
                "info.notice_read.already_acknowledged",
                "errors.info.notice_read.already_acknowledged",
            )
        now = datetime.now(UTC)
        saved = self.repository.upsert_notice_read(
            NoticeRead(
                tenant_id=tenant_id,
                notice_id=notice.id,
                user_account_id=actor.user_id,
                first_opened_at=existing.first_opened_at if existing is not None else now,
                last_opened_at=now,
                acknowledged_at=now,
                acknowledgement_text=payload.acknowledgement_text,
                metadata_json=payload.metadata_json,
            )
        )
        return NoticeReadEvidenceRead.model_validate(saved)

    def _attach_document(
        self,
        tenant_id: str,
        notice_id: str,
        document_id: str,
        actor: RequestAuthorizationContext,
    ) -> None:
        self.document_service.get_document(tenant_id, document_id, actor)
        self.document_service.add_document_link(
            tenant_id,
            document_id,
            DocumentLinkCreate(owner_type="info.notice", owner_id=notice_id, relation_type="attachment"),
            actor,
        )

    def _require_notice(self, tenant_id: str, notice_id: str) -> Notice:
        notice = self.repository.get_notice(tenant_id, notice_id)
        if notice is None:
            raise ApiException(404, "info.notice.not_found", "errors.info.notice.not_found")
        return notice

    def _require_visible_notice(self, tenant_id: str, notice_id: str, actor: RequestAuthorizationContext) -> Notice:
        notice = self._require_notice(tenant_id, notice_id)
        if not self._is_published_now(notice) or not self.audience_resolver.is_visible(notice, actor):
            raise ApiException(
                403,
                "info.notice_read.not_visible",
                "errors.info.notice_read.not_visible",
            )
        return notice

    @staticmethod
    def _is_published_now(notice: Notice) -> bool:
        now = datetime.now(UTC)
        if notice.status != "published":
            return False
        if notice.publish_from is not None and notice.publish_from > now:
            return False
        if notice.publish_until is not None and notice.publish_until < now:
            return False
        if notice.unpublished_at is not None and notice.unpublished_at <= now:
            return False
        return True

    @staticmethod
    def _normalize_audience_kind(audience_kind: str) -> str:
        normalized = audience_kind.strip().lower()
        if normalized not in SUPPORTED_AUDIENCE_KINDS:
            raise ApiException(
                400,
                "info.notice.audience_kind_invalid",
                "errors.info.notice.audience_kind_invalid",
                {"audience_kind": audience_kind},
            )
        return normalized

    @staticmethod
    def _ensure_language(language_code: str) -> None:
        if language_code not in SUPPORTED_NOTICE_LANGUAGES:
            raise ApiException(
                400,
                "info.notice.language_not_supported",
                "errors.info.notice.language_not_supported",
                {"language_code": language_code},
            )

    @staticmethod
    def _ensure_write_scope(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.is_platform_admin or actor.tenant_id == tenant_id:
            return
        raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")

    @staticmethod
    def _ensure_read_scope(actor: RequestAuthorizationContext, tenant_id: str) -> None:
        if actor.is_platform_admin or actor.tenant_id == tenant_id:
            return
        raise ApiException(403, "iam.authorization.scope_denied", "errors.iam.authorization.scope_denied")

    def _to_notice_read(self, notice: Notice) -> NoticeReadSchema:
        attachment_ids = [link.document_id for link in self.repository.list_document_links_for_notice(notice.tenant_id, notice.id)]
        schema = NoticeReadSchema.model_validate(notice)
        return schema.model_copy(update={"attachment_document_ids": attachment_ids})

    def _to_notice_list_item(self, notice: Notice, user_account_id: str) -> NoticeListItem:
        evidence = next((row for row in notice.reads if row.user_account_id == user_account_id), None)
        attachment_ids = [link.document_id for link in self.repository.list_document_links_for_notice(notice.tenant_id, notice.id)]
        return NoticeListItem(
            id=notice.id,
            title=notice.title,
            summary=notice.summary,
            language_code=notice.language_code,
            mandatory_acknowledgement=notice.mandatory_acknowledgement,
            publish_from=notice.publish_from,
            publish_until=notice.publish_until,
            published_at=notice.published_at,
            status=notice.status,
            acknowledged_at=evidence.acknowledged_at if evidence is not None else None,
            audiences=[NoticeAudienceRead.model_validate(audience) for audience in notice.audiences],
            links=[NoticeLinkRead.model_validate(link) for link in notice.links],
            attachment_document_ids=attachment_ids,
        )
