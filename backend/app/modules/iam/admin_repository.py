"""SQLAlchemy repository for tenant admin user management."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ApiException
from app.modules.core.models import Tenant
from app.modules.iam.models import PasswordResetToken, Role, UserAccount, UserRoleAssignment, UserSession
from app.modules.iam.schemas import TenantAdminUserCreate, TenantAdminUserListItem


class SqlAlchemyIamAdminRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def tenant_exists(self, tenant_id: str) -> bool:
        return self.session.get(Tenant, tenant_id) is not None

    def list_tenant_admin_users(self, tenant_id: str) -> list[TenantAdminUserListItem]:
        return [
            self._map_row_to_item(user, assignment, role)
            for user, assignment, role in self._list_user_rows(tenant_id)
        ]

    def create_tenant_admin_user(
        self,
        payload: TenantAdminUserCreate,
        password_hash: str,
        actor_user_id: str | None,
    ) -> TenantAdminUserListItem:
        role = self._require_tenant_admin_role()
        user = UserAccount(
            tenant_id=payload.tenant_id,
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            password_hash=password_hash,
            locale=payload.locale,
            timezone=payload.timezone,
            is_platform_user=False,
            is_password_login_enabled=True,
            status=payload.status,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(user)
        self.session.flush()
        assignment = UserRoleAssignment(
            tenant_id=payload.tenant_id,
            user_account_id=user.id,
            role_id=role.id,
            scope_type="tenant",
            status=payload.status,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(assignment)
        self._commit_or_raise()
        self.session.refresh(user)
        self.session.refresh(assignment)
        return self._map_row_to_item(user, assignment, role)

    def get_tenant_admin_user(self, tenant_id: str, user_id: str) -> TenantAdminUserListItem | None:
        row = self._get_user_row(tenant_id, user_id)
        if row is None:
            return None
        user, assignment, role = row
        return self._map_row_to_item(user, assignment, role)

    def update_tenant_admin_user_status(
        self,
        tenant_id: str,
        user_id: str,
        status: str,
        actor_user_id: str | None,
    ) -> TenantAdminUserListItem | None:
        row = self._get_user_row(tenant_id, user_id)
        if row is None:
            return None
        user, assignment, role = row
        user.status = status
        user.updated_by_user_id = actor_user_id
        user.archived_at = None
        user.version_no += 1
        assignment.status = status
        assignment.updated_by_user_id = actor_user_id
        assignment.archived_at = None
        assignment.version_no += 1
        self.session.add(user)
        self.session.add(assignment)
        self._commit_or_raise()
        self.session.refresh(user)
        self.session.refresh(assignment)
        return self._map_row_to_item(user, assignment, role)

    def reset_tenant_admin_password(
        self,
        tenant_id: str,
        user_id: str,
        password_hash: str,
        actor_user_id: str | None,
        at_time: datetime,
    ) -> TenantAdminUserListItem | None:
        row = self._get_user_row(tenant_id, user_id)
        if row is None:
            return None
        user, assignment, role = row
        user.password_hash = password_hash
        user.updated_by_user_id = actor_user_id
        user.version_no += 1
        self.session.add(user)
        for token in self.session.scalars(
            select(PasswordResetToken).where(
                PasswordResetToken.user_account_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
        ).all():
            token.used_at = at_time
        for session_row in self.session.scalars(
            select(UserSession).where(
                UserSession.user_account_id == user.id,
                UserSession.revoked_at.is_(None),
            )
        ).all():
            session_row.status = "revoked"
            session_row.revoked_at = at_time
            session_row.revoked_reason = "admin_password_reset"
            session_row.last_seen_at = at_time
        self._commit_or_raise()
        self.session.refresh(user)
        self.session.refresh(assignment)
        return self._map_row_to_item(user, assignment, role)

    def _list_user_rows(self, tenant_id: str):
        role = self._require_tenant_admin_role()
        statement = (
            select(UserAccount, UserRoleAssignment, Role)
            .join(UserRoleAssignment, UserRoleAssignment.user_account_id == UserAccount.id)
            .join(Role, Role.id == UserRoleAssignment.role_id)
            .where(
                UserAccount.tenant_id == tenant_id,
                UserRoleAssignment.tenant_id == tenant_id,
                Role.id == role.id,
                UserRoleAssignment.scope_type == "tenant",
            )
            .order_by(UserAccount.username)
        )
        return self.session.execute(statement).all()

    def _get_user_row(self, tenant_id: str, user_id: str):
        role = self._require_tenant_admin_role()
        statement = (
            select(UserAccount, UserRoleAssignment, Role)
            .join(UserRoleAssignment, UserRoleAssignment.user_account_id == UserAccount.id)
            .join(Role, Role.id == UserRoleAssignment.role_id)
            .where(
                UserAccount.id == user_id,
                UserAccount.tenant_id == tenant_id,
                UserRoleAssignment.tenant_id == tenant_id,
                Role.id == role.id,
                UserRoleAssignment.scope_type == "tenant",
            )
        )
        return self.session.execute(statement).one_or_none()

    def _require_tenant_admin_role(self) -> Role:
        statement = select(Role).where(Role.key == "tenant_admin")
        role = self.session.scalars(statement).one_or_none()
        if role is None:
            raise RuntimeError("tenant_admin role is missing. Run IAM catalog seeding first.")
        return role

    @staticmethod
    def _map_row_to_item(user: UserAccount, assignment: UserRoleAssignment, role: Role) -> TenantAdminUserListItem:
        return TenantAdminUserListItem(
            id=user.id,
            tenant_id=user.tenant_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            locale=user.locale,
            timezone=user.timezone,
            status=user.status,
            is_password_login_enabled=user.is_password_login_enabled,
            last_login_at=user.last_login_at,
            role_assignment_id=assignment.id,
            role_assignment_status=assignment.status,
            role_key=role.key,
            scope_type=assignment.scope_type,
            created_at=user.created_at,
            updated_at=user.updated_at,
            version_no=user.version_no,
        )

    def _commit_or_raise(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise self._translate_integrity_error(exc) from exc

    @staticmethod
    def _translate_integrity_error(exc: IntegrityError) -> ApiException:
        message = str(exc.orig)
        if "uq_iam_user_account_tenant_username" in message:
            return ApiException(409, "iam.user.duplicate_username", "errors.iam.user.duplicate_username")
        if "uq_iam_user_account_tenant_email" in message:
            return ApiException(409, "iam.user.duplicate_email", "errors.iam.user.duplicate_email")
        if "uq_iam_user_role_assignment_scope_tuple" in message:
            return ApiException(409, "iam.user.duplicate_tenant_admin_assignment", "errors.iam.user.duplicate_assignment")
        if "fk_iam_user_role_assignment_tenant_branch" in message or "fk_iam_user_role_assignment_tenant_mandate" in message:
            return ApiException(400, "iam.user.invalid_scope", "errors.iam.user.invalid_scope")
        return ApiException(409, "iam.user.integrity_conflict", "errors.iam.user.integrity_conflict")
