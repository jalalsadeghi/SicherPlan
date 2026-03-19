from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from app.db import Base
from app.errors import ApiException
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.platform_services.info_models import Notice, NoticeAudience, NoticeLink, NoticeRead
from app.modules.platform_services.info_schemas import (
    NoticeAcknowledgeRequest,
    NoticeAudienceCreate,
    NoticeCreate,
    NoticeLinkCreate,
    NoticePublishRequest,
)
from app.modules.platform_services.info_service import NoticeService


@dataclass
class FakeNoticeAudience:
    id: str
    tenant_id: str
    notice_id: str
    audience_kind: str
    target_value: str | None
    target_label: str | None
    metadata_json: dict[str, object]
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeNoticeLink:
    id: str
    tenant_id: str
    notice_id: str
    label: str
    url: str
    link_type: str
    sort_order: int
    metadata_json: dict[str, object]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeNoticeRead:
    id: str
    tenant_id: str
    notice_id: str
    user_account_id: str
    first_opened_at: datetime
    last_opened_at: datetime
    acknowledged_at: datetime | None
    acknowledgement_text: str | None
    metadata_json: dict[str, object]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeNotice:
    id: str
    tenant_id: str
    title: str
    summary: str | None
    body: str
    language_code: str
    mandatory_acknowledgement: bool
    publish_from: datetime | None
    publish_until: datetime | None
    published_at: datetime | None
    unpublished_at: datetime | None
    related_entity_type: str | None
    related_entity_id: str | None
    metadata_json: dict[str, object] = field(default_factory=dict)
    status: str = "draft"
    version_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    audiences: list[FakeNoticeAudience] = field(default_factory=list)
    reads: list[FakeNoticeRead] = field(default_factory=list)
    links: list[FakeNoticeLink] = field(default_factory=list)


class FakeDocumentService:
    def __init__(self) -> None:
        self.document_ids = {"doc-1"}
        self.attachments: list[tuple[str, str, str]] = []

    def get_document(self, tenant_id: str, document_id: str, actor):  # noqa: ANN001
        if document_id not in self.document_ids:
            raise ApiException(404, "docs.document.not_found", "errors.docs.document.not_found")
        return {"id": document_id}

    def add_document_link(self, tenant_id: str, document_id: str, payload, actor):  # noqa: ANN001
        self.attachments.append((tenant_id, document_id, payload.owner_id))
        return payload


class FakeNoticeRepository:
    def __init__(self) -> None:
        self.notices: dict[str, FakeNotice] = {}
        self.reads: dict[tuple[str, str], FakeNoticeRead] = {}
        self.document_links: dict[str, list[object]] = {}

    def create_notice(self, notice: Notice, audiences: list[NoticeAudience], links: list[NoticeLink]):
        stored = FakeNotice(
            id=str(uuid4()),
            tenant_id=notice.tenant_id,
            title=notice.title,
            summary=notice.summary,
            body=notice.body,
            language_code=notice.language_code,
            mandatory_acknowledgement=notice.mandatory_acknowledgement,
            publish_from=notice.publish_from,
            publish_until=notice.publish_until,
            published_at=notice.published_at,
            unpublished_at=notice.unpublished_at,
            related_entity_type=notice.related_entity_type,
            related_entity_id=notice.related_entity_id,
            metadata_json=notice.metadata_json,
            status=notice.status,
        )
        stored.audiences = [
            FakeNoticeAudience(
                id=str(uuid4()),
                tenant_id=audience.tenant_id,
                notice_id=stored.id,
                audience_kind=audience.audience_kind,
                target_value=audience.target_value,
                target_label=audience.target_label,
                metadata_json=audience.metadata_json,
            )
            for audience in audiences
        ]
        stored.links = [
            FakeNoticeLink(
                id=str(uuid4()),
                tenant_id=link.tenant_id,
                notice_id=stored.id,
                label=link.label,
                url=link.url,
                link_type=link.link_type,
                sort_order=link.sort_order,
                metadata_json=link.metadata_json,
            )
            for link in links
        ]
        self.notices[stored.id] = stored
        self.document_links[stored.id] = []
        return stored

    def list_notices(self, tenant_id: str):
        return [notice for notice in self.notices.values() if notice.tenant_id == tenant_id]

    def get_notice(self, tenant_id: str, notice_id: str):
        notice = self.notices.get(notice_id)
        if notice is None or notice.tenant_id != tenant_id:
            return None
        return notice

    def save_notice(self, notice):
        notice.updated_at = datetime.now(UTC)
        self.notices[notice.id] = notice
        return notice

    def get_notice_read(self, notice_id: str, user_account_id: str):
        return self.reads.get((notice_id, user_account_id))

    def upsert_notice_read(self, read_row):
        existing = self.reads.get((read_row.notice_id, read_row.user_account_id))
        if existing is None:
            stored = FakeNoticeRead(
                id=str(uuid4()),
                tenant_id=read_row.tenant_id,
                notice_id=read_row.notice_id,
                user_account_id=read_row.user_account_id,
                first_opened_at=read_row.first_opened_at,
                last_opened_at=read_row.last_opened_at,
                acknowledged_at=read_row.acknowledged_at,
                acknowledgement_text=read_row.acknowledgement_text,
                metadata_json=read_row.metadata_json,
            )
            self.reads[(stored.notice_id, stored.user_account_id)] = stored
            self.notices[stored.notice_id].reads.append(stored)
            return stored
        existing.last_opened_at = read_row.last_opened_at
        existing.acknowledged_at = read_row.acknowledged_at or existing.acknowledged_at
        existing.acknowledgement_text = read_row.acknowledgement_text or existing.acknowledgement_text
        existing.metadata_json = {**existing.metadata_json, **read_row.metadata_json}
        existing.updated_at = datetime.now(UTC)
        return existing

    def list_document_links_for_notice(self, tenant_id: str, notice_id: str):
        return self.document_links.get(notice_id, [])

    def create_notice_link(self, row):  # noqa: ANN001
        return row


def _actor(role: str, tenant_id: str = "tenant-1") -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id=f"user-{role}",
        tenant_id=tenant_id,
        role_keys=frozenset({role}),
        permission_keys=frozenset({"platform.info.read", "platform.info.write", "platform.docs.write"}),
        scopes=(AuthenticatedRoleScope(role_key=role, scope_type="tenant"),),
    )


class TestNoticeMetadata(unittest.TestCase):
    def test_expected_info_tables_are_registered(self) -> None:
        self.assertIn("info.notice", Base.metadata.tables)
        self.assertIn("info.notice_audience", Base.metadata.tables)
        self.assertIn("info.notice_read", Base.metadata.tables)
        self.assertIn("info.notice_link", Base.metadata.tables)

    def test_notice_read_and_audience_constraints_are_stable(self) -> None:
        notice_constraints = {
            constraint.name
            for constraint in Notice.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        audience_constraints = {
            constraint.name
            for constraint in NoticeAudience.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        read_constraints = {
            constraint.name
            for constraint in NoticeRead.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn("uq_info_notice_tenant_id_id", notice_constraints)
        self.assertIn("uq_info_notice_audience_scope", audience_constraints)
        self.assertIn("uq_info_notice_read_notice_user", read_constraints)
        index_names = {index.name for index in Notice.__table__.indexes if isinstance(index, Index)}
        self.assertIn("ix_info_notice_tenant_status_publish_from", index_names)

    def test_notice_link_schema_is_curated_url_not_attachment_blob(self) -> None:
        ddl = str(CreateTable(NoticeLink.__table__).compile(dialect=dialect()))
        self.assertIn("url", ddl)
        self.assertIn("link_type", ddl)
        self.assertNotIn("file_name", ddl)


class TestNoticeService(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = FakeNoticeRepository()
        self.docs = FakeDocumentService()
        self.service = NoticeService(self.repository, document_service=self.docs)

    def test_notice_can_be_created_published_and_listed_for_matching_role(self) -> None:
        created = self.service.create_notice(
            "tenant-1",
            NoticeCreate(
                tenant_id="tenant-1",
                title="Dienstanweisung",
                body="Bitte lesen",
                audiences=[NoticeAudienceCreate(audience_kind="role", target_value="dispatcher")],
                curated_links=[NoticeLinkCreate(label="QM", url="https://example.invalid/qm")],
                attachment_document_ids=["doc-1"],
            ),
            _actor("tenant_admin"),
        )
        published = self.service.publish_notice(
            "tenant-1",
            created.id,
            NoticePublishRequest(),
            _actor("tenant_admin"),
        )
        visible = self.service.list_visible_notices("tenant-1", _actor("dispatcher"))

        self.assertEqual(published.status, "published")
        self.assertEqual(len(visible), 1)
        self.assertEqual(visible[0].title, "Dienstanweisung")
        self.assertEqual(self.docs.attachments[0][1], "doc-1")

    def test_publish_windows_and_audience_scope_restrict_visibility(self) -> None:
        created = self.service.create_notice(
            "tenant-1",
            NoticeCreate(
                tenant_id="tenant-1",
                title="Nur spaeter",
                body="Zeitfenster",
                audiences=[NoticeAudienceCreate(audience_kind="role", target_value="dispatcher")],
            ),
            _actor("tenant_admin"),
        )
        self.service.publish_notice(
            "tenant-1",
            created.id,
            NoticePublishRequest(publish_from=datetime.now(UTC) + timedelta(days=1)),
            _actor("tenant_admin"),
        )

        self.assertEqual(self.service.list_visible_notices("tenant-1", _actor("dispatcher")), [])
        self.assertEqual(self.service.list_visible_notices("tenant-1", _actor("accounting")), [])

    def test_open_and_acknowledge_create_single_durable_read_row(self) -> None:
        created = self.service.create_notice(
            "tenant-1",
            NoticeCreate(
                tenant_id="tenant-1",
                title="Pflicht",
                body="Bitte bestaetigen",
                mandatory_acknowledgement=True,
                audiences=[NoticeAudienceCreate(audience_kind="role", target_value="dispatcher")],
            ),
            _actor("tenant_admin"),
        )
        self.service.publish_notice("tenant-1", created.id, NoticePublishRequest(), _actor("tenant_admin"))
        opened = self.service.open_notice("tenant-1", created.id, _actor("dispatcher"))
        acknowledged = self.service.acknowledge_notice(
            "tenant-1",
            created.id,
            NoticeAcknowledgeRequest(acknowledgement_text="Gelesen"),
            _actor("dispatcher"),
        )

        self.assertEqual(opened.notice_id, created.id)
        self.assertIsNotNone(acknowledged.acknowledged_at)
        self.assertEqual(len(self.repository.notices[created.id].reads), 1)

    def test_future_audience_kinds_are_persisted_without_cross_module_writes(self) -> None:
        created = self.service.create_notice(
            "tenant-1",
            NoticeCreate(
                tenant_id="tenant-1",
                title="Qualifikation",
                body="Nur fuer spaeteren Resolver",
                audiences=[NoticeAudienceCreate(audience_kind="qualification", target_value="first-aid")],
            ),
            _actor("tenant_admin"),
        )
        audience = self.repository.notices[created.id].audiences[0]
        self.assertEqual(audience.audience_kind, "qualification")
        self.assertEqual(audience.target_value, "first-aid")

    def test_ack_requires_visible_notice(self) -> None:
        created = self.service.create_notice(
            "tenant-1",
            NoticeCreate(
                tenant_id="tenant-1",
                title="Kundenhinweis",
                body="Portal",
                audiences=[NoticeAudienceCreate(audience_kind="all_customers")],
            ),
            _actor("tenant_admin"),
        )
        self.service.publish_notice("tenant-1", created.id, NoticePublishRequest(), _actor("tenant_admin"))
        with self.assertRaises(ApiException):
            self.service.acknowledge_notice(
                "tenant-1",
                created.id,
                NoticeAcknowledgeRequest(),
                _actor("dispatcher"),
            )


if __name__ == "__main__":
    unittest.main()
