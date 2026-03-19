"""SQLAlchemy repository for IAM authentication flows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.core.models import Tenant
from app.modules.iam.models import (
    PasswordResetToken,
    Permission,
    Role,
    RolePermission,
    UserAccount,
    UserRoleAssignment,
    UserSession,
)


@dataclass(frozen=True, slots=True)
class AuthRoleScopeRecord:
    role_key: str
    scope_type: str
    branch_id: str | None
    mandate_id: str | None
    customer_id: str | None
    subcontractor_id: str | None


class SqlAlchemyAuthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_user_by_tenant_and_identifier(
        self,
        tenant_code: str,
        identifier: str,
    ) -> tuple[UserAccount, Tenant] | None:
        statement = (
            select(UserAccount, Tenant)
            .join(Tenant, Tenant.id == UserAccount.tenant_id)
            .where(
                Tenant.code == tenant_code,
                or_(UserAccount.username == identifier, UserAccount.email == identifier),
            )
        )
        row = self.session.execute(statement).one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    def get_user_by_id(self, user_account_id: str) -> UserAccount | None:
        return self.session.get(UserAccount, user_account_id)

    def list_role_scopes_for_user(self, user_account_id: str, at_time: datetime | None = None) -> list[AuthRoleScopeRecord]:
        now = at_time or datetime.now(UTC)
        statement = (
            select(UserRoleAssignment, Role)
            .join(Role, Role.id == UserRoleAssignment.role_id)
            .where(
                UserRoleAssignment.user_account_id == user_account_id,
                UserRoleAssignment.status == "active",
                or_(UserRoleAssignment.valid_from.is_(None), UserRoleAssignment.valid_from <= now),
                or_(UserRoleAssignment.valid_until.is_(None), UserRoleAssignment.valid_until >= now),
            )
        )
        rows = self.session.execute(statement).all()
        return [
            AuthRoleScopeRecord(
                role_key=role.key,
                scope_type=assignment.scope_type,
                branch_id=assignment.branch_id,
                mandate_id=assignment.mandate_id,
                customer_id=assignment.customer_id,
                subcontractor_id=assignment.subcontractor_id,
            )
            for assignment, role in rows
        ]

    def list_permission_keys_for_user(self, user_account_id: str, at_time: datetime | None = None) -> list[str]:
        now = at_time or datetime.now(UTC)
        statement = (
            select(Permission.key)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
            .where(
                UserRoleAssignment.user_account_id == user_account_id,
                UserRoleAssignment.status == "active",
                Role.status == "active",
                or_(UserRoleAssignment.valid_from.is_(None), UserRoleAssignment.valid_from <= now),
                or_(UserRoleAssignment.valid_until.is_(None), UserRoleAssignment.valid_until >= now),
            )
            .distinct()
        )
        return list(self.session.scalars(statement).all())

    def create_session(self, session_row: UserSession) -> UserSession:
        self.session.add(session_row)
        self.session.commit()
        self.session.refresh(session_row)
        return session_row

    def get_session_by_id(self, session_id: str) -> UserSession | None:
        statement = (
            select(UserSession)
            .options(joinedload(UserSession.user_account))
            .where(UserSession.id == session_id)
        )
        return self.session.scalars(statement).one_or_none()

    def get_session_by_token_hash(self, token_hash: str) -> UserSession | None:
        statement = (
            select(UserSession)
            .options(joinedload(UserSession.user_account))
            .where(UserSession.session_token_hash == token_hash)
        )
        return self.session.scalars(statement).one_or_none()

    def list_sessions_for_user(self, user_account_id: str) -> list[UserSession]:
        statement = (
            select(UserSession)
            .where(UserSession.user_account_id == user_account_id)
            .order_by(UserSession.issued_at.desc())
        )
        return self.session.scalars(statement).all()

    def update_session(self, session_row: UserSession) -> UserSession:
        self.session.add(session_row)
        self.session.commit()
        self.session.refresh(session_row)
        return session_row

    def revoke_session(self, session_row: UserSession, *, reason: str, at_time: datetime) -> UserSession:
        session_row.status = "revoked"
        session_row.revoked_at = at_time
        session_row.revoked_reason = reason
        session_row.last_seen_at = at_time
        self.session.add(session_row)
        self.session.commit()
        self.session.refresh(session_row)
        return session_row

    def revoke_all_sessions_for_user(
        self,
        user_account_id: str,
        *,
        except_session_id: str | None,
        reason: str,
        at_time: datetime,
    ) -> int:
        sessions = self.list_sessions_for_user(user_account_id)
        count = 0
        for session_row in sessions:
            if session_row.id == except_session_id or session_row.revoked_at is not None:
                continue
            session_row.status = "revoked"
            session_row.revoked_at = at_time
            session_row.revoked_reason = reason
            session_row.last_seen_at = at_time
            count += 1
        if count:
            self.session.commit()
        return count

    def touch_user_login(self, user_account: UserAccount, at_time: datetime) -> UserAccount:
        user_account.last_login_at = at_time
        user_account.updated_at = at_time
        self.session.add(user_account)
        self.session.commit()
        self.session.refresh(user_account)
        return user_account

    def update_user_password(self, user_account: UserAccount, password_hash: str, at_time: datetime) -> UserAccount:
        user_account.password_hash = password_hash
        user_account.updated_at = at_time
        user_account.version_no += 1
        self.session.add(user_account)
        self.session.commit()
        self.session.refresh(user_account)
        return user_account

    def invalidate_active_reset_tokens(self, user_account_id: str, at_time: datetime) -> int:
        statement = select(PasswordResetToken).where(
            PasswordResetToken.user_account_id == user_account_id,
            PasswordResetToken.used_at.is_(None),
        )
        rows = self.session.scalars(statement).all()
        for row in rows:
            row.used_at = at_time
        if rows:
            self.session.commit()
        return len(rows)

    def create_password_reset_token(self, token_row: PasswordResetToken) -> PasswordResetToken:
        self.session.add(token_row)
        self.session.commit()
        self.session.refresh(token_row)
        return token_row

    def update_password_reset_token(self, token_row: PasswordResetToken) -> PasswordResetToken:
        self.session.add(token_row)
        self.session.commit()
        self.session.refresh(token_row)
        return token_row

    def get_password_reset_token_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        statement = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        return self.session.scalars(statement).one_or_none()

    def mark_password_reset_token_used(self, token_row: PasswordResetToken, at_time: datetime) -> PasswordResetToken:
        token_row.used_at = at_time
        self.session.add(token_row)
        self.session.commit()
        self.session.refresh(token_row)
        return token_row
