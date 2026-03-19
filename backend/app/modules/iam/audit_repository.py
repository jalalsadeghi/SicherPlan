"""Repository for append-only audit and login events."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.iam.audit_models import AuditEvent, LoginEvent
from app.modules.iam.audit_schemas import AuditEventRead, AuditEventWrite, LoginEventRead, LoginEventWrite


class SqlAlchemyAuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_login_event(self, payload: LoginEventWrite) -> LoginEventRead:
        row = LoginEvent(**payload.model_dump())
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return LoginEventRead.model_validate(row)

    def create_audit_event(self, payload: AuditEventWrite) -> AuditEventRead:
        row = AuditEvent(**payload.model_dump())
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return AuditEventRead.model_validate(row)

    def list_login_events(self) -> list[LoginEventRead]:
        rows = self.session.scalars(select(LoginEvent).order_by(LoginEvent.created_at)).all()
        return [LoginEventRead.model_validate(row) for row in rows]

    def list_audit_events(self) -> list[AuditEventRead]:
        rows = self.session.scalars(select(AuditEvent).order_by(AuditEvent.created_at)).all()
        return [AuditEventRead.model_validate(row) for row in rows]
