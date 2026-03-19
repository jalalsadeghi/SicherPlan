"""SQLAlchemy repository for notice authoring, audience targeting, and read evidence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.modules.platform_services.docs_models import DocumentLink
from app.modules.platform_services.info_models import Notice, NoticeAudience, NoticeLink, NoticeRead


class SqlAlchemyNoticeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_notice(
        self,
        notice: Notice,
        audiences: list[NoticeAudience],
        links: list[NoticeLink],
    ) -> Notice:
        self.session.add(notice)
        self.session.flush()
        for audience in audiences:
            audience.notice_id = notice.id
            self.session.add(audience)
        for link in links:
            link.notice_id = notice.id
            self.session.add(link)
        self.session.commit()
        return self.get_notice(notice.tenant_id, notice.id) or notice

    def list_notices(self, tenant_id: str) -> list[Notice]:
        statement = self._notice_query().where(Notice.tenant_id == tenant_id).order_by(Notice.created_at.desc())
        return list(self.session.scalars(statement).unique().all())

    def get_notice(self, tenant_id: str, notice_id: str) -> Notice | None:
        statement = self._notice_query().where(Notice.tenant_id == tenant_id, Notice.id == notice_id)
        return self.session.scalars(statement).unique().one_or_none()

    def save_notice(self, notice: Notice) -> Notice:
        self.session.add(notice)
        self.session.commit()
        return self.get_notice(notice.tenant_id, notice.id) or notice

    def get_notice_read(self, notice_id: str, user_account_id: str) -> NoticeRead | None:
        statement = select(NoticeRead).where(
            NoticeRead.notice_id == notice_id,
            NoticeRead.user_account_id == user_account_id,
        )
        return self.session.scalars(statement).one_or_none()

    def upsert_notice_read(self, read_row: NoticeRead) -> NoticeRead:
        existing = self.get_notice_read(read_row.notice_id, read_row.user_account_id)
        if existing is None:
            self.session.add(read_row)
            self.session.commit()
            self.session.refresh(read_row)
            return read_row
        existing.last_opened_at = read_row.last_opened_at
        existing.acknowledged_at = read_row.acknowledged_at or existing.acknowledged_at
        existing.acknowledgement_text = read_row.acknowledgement_text or existing.acknowledgement_text
        existing.metadata_json = {**existing.metadata_json, **read_row.metadata_json}
        self.session.add(existing)
        self.session.commit()
        return existing

    def list_document_links_for_notice(self, tenant_id: str, notice_id: str) -> list[DocumentLink]:
        statement = (
            select(DocumentLink)
            .where(
                DocumentLink.tenant_id == tenant_id,
                DocumentLink.owner_type == "info.notice",
                DocumentLink.owner_id == notice_id,
            )
            .order_by(DocumentLink.linked_at)
        )
        return list(self.session.scalars(statement).all())

    def create_notice_link(self, row: NoticeLink) -> NoticeLink:
        self.session.add(row)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        self.session.refresh(row)
        return row

    @staticmethod
    def _notice_query() -> Select[tuple[Notice]]:
        return (
            select(Notice)
            .options(joinedload(Notice.audiences))
            .options(joinedload(Notice.reads))
            .options(joinedload(Notice.links))
        )
