"""Bootstrap a local system administrator with full platform permissions."""

from __future__ import annotations

from os import getenv

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.modules.core.models import Tenant
from app.modules.iam.bootstrap_admin import (
    SystemAdminBootstrapConfig,
    SystemAdminBootstrapper,
)
from app.modules.iam.models import Role, UserAccount, UserRoleAssignment
from app.modules.iam.seed_permissions import seed_iam_catalog


class SqlAlchemySystemAdminBootstrapRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_tenant_by_code(self, code: str) -> Tenant | None:
        statement = select(Tenant).where(Tenant.code == code)
        return self.session.scalars(statement).one_or_none()

    def create_tenant(self, tenant: Tenant) -> Tenant:
        self.session.add(tenant)
        self.session.flush()
        return tenant

    def get_role_by_key(self, key: str) -> Role | None:
        statement = select(Role).where(Role.key == key)
        return self.session.scalars(statement).one_or_none()

    def find_user_for_tenant(self, tenant_id: str, *, username: str, email: str) -> UserAccount | None:
        statement = select(UserAccount).where(
            UserAccount.tenant_id == tenant_id,
            or_(UserAccount.username == username, UserAccount.email == email),
        )
        return self.session.scalars(statement).one_or_none()

    def save_user(self, user: UserAccount) -> UserAccount:
        self.session.add(user)
        self.session.flush()
        return user

    def get_role_assignment(self, user_id: str, role_id: str, tenant_id: str) -> UserRoleAssignment | None:
        statement = select(UserRoleAssignment).where(
            UserRoleAssignment.user_account_id == user_id,
            UserRoleAssignment.role_id == role_id,
            UserRoleAssignment.tenant_id == tenant_id,
            UserRoleAssignment.scope_type == "tenant",
        )
        return self.session.scalars(statement).one_or_none()

    def save_role_assignment(self, assignment: UserRoleAssignment) -> UserRoleAssignment:
        self.session.add(assignment)
        self.session.flush()
        return assignment


def _load_config() -> SystemAdminBootstrapConfig:
    return SystemAdminBootstrapConfig(
        tenant_code=getenv("SP_BOOTSTRAP_SYSTEM_TENANT_CODE", "system"),
        tenant_name=getenv("SP_BOOTSTRAP_SYSTEM_TENANT_NAME", "SicherPlan System"),
        username=getenv("SP_BOOTSTRAP_SYSTEM_ADMIN_USERNAME", "sysadmin"),
        email=getenv("SP_BOOTSTRAP_SYSTEM_ADMIN_EMAIL", "sysadmin@local.sicherplan.invalid"),
        full_name=getenv("SP_BOOTSTRAP_SYSTEM_ADMIN_FULL_NAME", "System Administrator"),
        password=getenv("SP_BOOTSTRAP_SYSTEM_ADMIN_PASSWORD", "SicherPlanAdmin!123"),
        locale=getenv("SP_BOOTSTRAP_SYSTEM_ADMIN_LOCALE", "de"),
        timezone=getenv("SP_BOOTSTRAP_SYSTEM_ADMIN_TIMEZONE", "Europe/Berlin"),
    )


def main() -> None:
    from sqlalchemy import create_engine

    engine = create_engine(settings.database_url)
    config = _load_config()

    with Session(engine) as session:
        seed_iam_catalog(session)
        summary = SystemAdminBootstrapper(
            SqlAlchemySystemAdminBootstrapRepository(session)
        ).bootstrap(config)
        session.commit()

    print("SicherPlan system administrator bootstrap complete.")
    print(f"tenant_code={summary.tenant_code}")
    print(f"username={summary.username}")
    print(f"email={summary.email}")
    print(f"password={summary.password}")
    print(f"tenant_created={summary.tenant_created}")
    print(f"user_created={summary.user_created}")
    print(f"user_updated={summary.user_updated}")
    print(f"role_assignment_created={summary.role_assignment_created}")


if __name__ == "__main__":
    main()
