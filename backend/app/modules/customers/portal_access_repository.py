"""SQLAlchemy repository for tenant-scoped customer portal access management."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ApiException
from app.modules.core.models import Tenant
from app.modules.customers.models import Customer, CustomerContact
from app.modules.customers.schemas import CustomerPortalAccessCreate, CustomerPortalAccessListItemRead
from app.modules.iam.models import PasswordResetToken, Role, UserAccount, UserRoleAssignment, UserSession


class SqlAlchemyCustomerPortalAccessRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def tenant_exists(self, tenant_id: str) -> bool:
        return self.session.get(Tenant, tenant_id) is not None

    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None:
        statement = select(Customer).where(Customer.tenant_id == tenant_id, Customer.id == customer_id)
        return self.session.scalars(statement).one_or_none()

    def get_contact(self, tenant_id: str, contact_id: str) -> CustomerContact | None:
        statement = select(CustomerContact).where(
            CustomerContact.tenant_id == tenant_id,
            CustomerContact.id == contact_id,
        )
        return self.session.scalars(statement).one_or_none()

    def list_portal_access(self, tenant_id: str, customer_id: str) -> list[CustomerPortalAccessListItemRead]:
        return [
            self._map_row_to_item(user, assignment, role, contact)
            for user, assignment, role, contact in self._list_rows(tenant_id, customer_id)
        ]

    def get_portal_access_user(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: str,
    ) -> CustomerPortalAccessListItemRead | None:
        row = self._get_row(tenant_id, customer_id, user_id)
        if row is None:
            return None
        user, assignment, role, contact = row
        return self._map_row_to_item(user, assignment, role, contact)

    def create_portal_access_user(
        self,
        payload: CustomerPortalAccessCreate,
        password_hash: str,
        actor_user_id: str | None,
    ) -> CustomerPortalAccessListItemRead:
        role = self._require_customer_user_role()
        contact = self._require_contact(payload.tenant_id, payload.contact_id)
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
            scope_type="customer",
            customer_id=payload.customer_id,
            status=payload.status,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        contact.user_id = user.id
        contact.updated_by_user_id = actor_user_id
        contact.version_no += 1
        self.session.add(assignment)
        self.session.add(contact)
        self._commit_or_raise()
        return self.get_portal_access_user(payload.tenant_id, payload.customer_id, user.id) or self._map_row_to_item(
            user,
            assignment,
            role,
            contact,
        )

    def update_portal_access_status(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: str,
        status: str,
        actor_user_id: str | None,
    ) -> CustomerPortalAccessListItemRead | None:
        row = self._get_row(tenant_id, customer_id, user_id)
        if row is None:
            return None
        user, assignment, role, _contact = row
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
        if status == "inactive":
            self._revoke_user_security(user.id, actor_user_id=actor_user_id, reason="customer_portal_access_deactivated")
        self._commit_or_raise()
        return self.get_portal_access_user(tenant_id, customer_id, user_id)

    def reset_portal_access_password(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: str,
        password_hash: str,
        actor_user_id: str | None,
        at_time: datetime,
    ) -> CustomerPortalAccessListItemRead | None:
        row = self._get_row(tenant_id, customer_id, user_id)
        if row is None:
            return None
        user, _assignment, _role, _contact = row
        user.password_hash = password_hash
        user.updated_by_user_id = actor_user_id
        user.version_no += 1
        self.session.add(user)
        self._revoke_user_security(user.id, actor_user_id=actor_user_id, reason="customer_portal_password_reset", at_time=at_time)
        self._commit_or_raise()
        return self.get_portal_access_user(tenant_id, customer_id, user_id)

    def unlink_portal_access(
        self,
        tenant_id: str,
        customer_id: str,
        user_id: str,
        actor_user_id: str | None,
        at_time: datetime | None = None,
    ) -> bool:
        row = self._get_row(tenant_id, customer_id, user_id)
        if row is None:
            return False
        user, assignment, _role, contact = row
        event_time = at_time or datetime.now(UTC)
        contact.user_id = None
        contact.updated_by_user_id = actor_user_id
        contact.version_no += 1
        user.status = "inactive"
        user.updated_by_user_id = actor_user_id
        user.version_no += 1
        assignment.status = "inactive"
        assignment.updated_by_user_id = actor_user_id
        assignment.archived_at = event_time
        assignment.version_no += 1
        self.session.add(contact)
        self.session.add(user)
        self.session.add(assignment)
        self._revoke_user_security(user.id, actor_user_id=actor_user_id, reason="customer_portal_access_unlinked", at_time=event_time)
        self._commit_or_raise()
        return True

    def _list_rows(self, tenant_id: str, customer_id: str):
        role = self._require_customer_user_role()
        statement = (
            select(UserAccount, UserRoleAssignment, Role, CustomerContact)
            .join(CustomerContact, CustomerContact.user_id == UserAccount.id)
            .join(UserRoleAssignment, UserRoleAssignment.user_account_id == UserAccount.id)
            .join(Role, Role.id == UserRoleAssignment.role_id)
            .where(
                UserAccount.tenant_id == tenant_id,
                CustomerContact.tenant_id == tenant_id,
                CustomerContact.customer_id == customer_id,
                UserRoleAssignment.tenant_id == tenant_id,
                UserRoleAssignment.customer_id == customer_id,
                UserRoleAssignment.scope_type == "customer",
                Role.id == role.id,
            )
            .order_by(CustomerContact.full_name, UserAccount.username)
        )
        return self.session.execute(statement).all()

    def _get_row(self, tenant_id: str, customer_id: str, user_id: str):
        role = self._require_customer_user_role()
        statement = (
            select(UserAccount, UserRoleAssignment, Role, CustomerContact)
            .join(CustomerContact, CustomerContact.user_id == UserAccount.id)
            .join(UserRoleAssignment, UserRoleAssignment.user_account_id == UserAccount.id)
            .join(Role, Role.id == UserRoleAssignment.role_id)
            .where(
                UserAccount.id == user_id,
                UserAccount.tenant_id == tenant_id,
                CustomerContact.tenant_id == tenant_id,
                CustomerContact.customer_id == customer_id,
                UserRoleAssignment.tenant_id == tenant_id,
                UserRoleAssignment.customer_id == customer_id,
                UserRoleAssignment.scope_type == "customer",
                Role.id == role.id,
            )
        )
        return self.session.execute(statement).one_or_none()

    def _require_customer_user_role(self) -> Role:
        statement = select(Role).where(Role.key == "customer_user")
        role = self.session.scalars(statement).one_or_none()
        if role is None:
            raise RuntimeError("customer_user role is missing. Run IAM catalog seeding first.")
        return role

    def _require_contact(self, tenant_id: str, contact_id: str) -> CustomerContact:
        contact = self.get_contact(tenant_id, contact_id)
        if contact is None:
            raise ApiException(404, "customers.portal_access.contact.not_found", "errors.customers.contact.not_found")
        return contact

    def _revoke_user_security(
        self,
        user_id: str,
        *,
        actor_user_id: str | None,
        reason: str,
        at_time: datetime | None = None,
    ) -> None:
        event_time = at_time or datetime.now(UTC)
        for token in self.session.scalars(
            select(PasswordResetToken).where(
                PasswordResetToken.user_account_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
        ).all():
            token.used_at = event_time
        for session_row in self.session.scalars(
            select(UserSession).where(
                UserSession.user_account_id == user_id,
                UserSession.revoked_at.is_(None),
            )
        ).all():
            session_row.status = "revoked"
            session_row.revoked_at = event_time
            session_row.revoked_reason = reason
            session_row.last_seen_at = event_time
            session_row.updated_at = event_time

    @staticmethod
    def _map_row_to_item(
        user: UserAccount,
        assignment: UserRoleAssignment,
        role: Role,
        contact: CustomerContact,
    ) -> CustomerPortalAccessListItemRead:
        return CustomerPortalAccessListItemRead(
            user_id=user.id,
            contact_id=contact.id,
            contact_name=contact.full_name,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            locale=user.locale,
            role_key=role.key,
            status=user.status,
            role_assignment_status=assignment.status,
            is_password_login_enabled=user.is_password_login_enabled,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
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
            return ApiException(409, "customers.portal_access.duplicate_username", "errors.iam.user.duplicate_username")
        if "uq_iam_user_account_tenant_email" in message:
            return ApiException(409, "customers.portal_access.duplicate_email", "errors.iam.user.duplicate_email")
        if "uq_iam_user_role_assignment_scope_tuple" in message:
            return ApiException(409, "customers.portal_access.duplicate_assignment", "errors.iam.user.duplicate_assignment")
        if "uq_crm_customer_contact_tenant_user_id" in message:
            return ApiException(
                409,
                "customers.portal_access.contact_already_linked",
                "errors.customers.portal_access.contact_already_linked",
            )
        return ApiException(409, "customers.portal_access.integrity_conflict", "errors.iam.user.integrity_conflict")
