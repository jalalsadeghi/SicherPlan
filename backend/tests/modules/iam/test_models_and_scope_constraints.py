from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from app.db import Base
from app.modules.iam.models import (
    ExternalIdentity,
    PasswordResetToken,
    Permission,
    Role,
    RolePermission,
    UserAccount,
    UserRoleAssignment,
    UserSession,
)
from app.modules.iam.schemas import UserRoleAssignmentCreate, UserSessionCreate
from app.modules.iam.security import hash_session_token


class TestIamMetadata(unittest.TestCase):
    def test_expected_tables_are_registered(self) -> None:
        self.assertIn("iam.user_account", Base.metadata.tables)
        self.assertIn("iam.external_identity", Base.metadata.tables)
        self.assertIn("iam.role", Base.metadata.tables)
        self.assertIn("iam.permission", Base.metadata.tables)
        self.assertIn("iam.role_permission", Base.metadata.tables)
        self.assertIn("iam.user_role_assignment", Base.metadata.tables)
        self.assertIn("iam.user_session", Base.metadata.tables)
        self.assertIn("iam.password_reset_token", Base.metadata.tables)

    def test_user_account_uniqueness_is_tenant_scoped(self) -> None:
        names = {
            constraint.name
            for constraint in UserAccount.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn("uq_iam_user_account_tenant_username", names)
        self.assertIn("uq_iam_user_account_tenant_email", names)

    def test_external_identity_provider_uniqueness_is_global(self) -> None:
        names = {
            constraint.name
            for constraint in ExternalIdentity.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn("uq_iam_external_identity_provider_subject", names)
        self.assertIn("uq_iam_external_identity_provider_username", names)

    def test_role_and_permission_keys_are_stable_and_unique(self) -> None:
        role_constraints = {
            constraint.name for constraint in Role.__table__.constraints if isinstance(constraint, UniqueConstraint)
        }
        permission_constraints = {
            constraint.name
            for constraint in Permission.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn("uq_iam_role_key", role_constraints)
        self.assertIn("uq_iam_permission_key", permission_constraints)

    def test_scope_constraints_cover_type_and_tuple_target(self) -> None:
        constraints = {
            constraint.name for constraint in UserRoleAssignment.__table__.constraints if isinstance(constraint, CheckConstraint)
        }
        self.assertIn("ck_user_role_assignment_scope_type_valid", constraints)
        self.assertIn("ck_user_role_assignment_scope_target_matches_type", constraints)

    def test_scope_tuple_uniqueness_is_present(self) -> None:
        names = {
            constraint.name
            for constraint in UserRoleAssignment.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn("uq_iam_user_role_assignment_scope_tuple", names)

    def test_branch_and_mandate_scopes_use_composite_tenant_fks(self) -> None:
        foreign_keys = {
            fk.constraint.name: tuple(element.parent.name for element in fk.constraint.elements)
            for fk in UserRoleAssignment.__table__.foreign_keys
        }
        self.assertEqual(
            foreign_keys["fk_iam_user_role_assignment_tenant_branch"],
            ("tenant_id", "branch_id"),
        )
        self.assertEqual(
            foreign_keys["fk_iam_user_role_assignment_tenant_mandate"],
            ("tenant_id", "mandate_id"),
        )

    def test_session_table_uses_revocation_index_and_token_hash_uniqueness(self) -> None:
        names = {index.name for index in UserSession.__table__.indexes if isinstance(index, Index)}
        constraints = {
            constraint.name for constraint in UserSession.__table__.constraints if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn("ix_iam_user_session_user_account_revoked_at", names)
        self.assertIn("uq_iam_user_session_token_hash", constraints)

    def test_password_reset_token_uses_hash_uniqueness_and_user_index(self) -> None:
        names = {index.name for index in PasswordResetToken.__table__.indexes if isinstance(index, Index)}
        constraints = {
            constraint.name
            for constraint in PasswordResetToken.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn("ix_iam_password_reset_token_user_account_used_at", names)
        self.assertIn("uq_iam_password_reset_token_hash", constraints)

    def test_postgresql_ddl_includes_scope_checks(self) -> None:
        ddl = str(CreateTable(UserRoleAssignment.__table__).compile(dialect=dialect()))
        self.assertIn("CREATE TABLE iam.user_role_assignment", ddl)
        self.assertIn("CONSTRAINT uq_iam_user_role_assignment_scope_tuple", ddl)
        self.assertIn("CONSTRAINT ck_user_role_assignment_scope_target_matches_type", ddl)


class TestIamSchemasAndSecurity(unittest.TestCase):
    def test_role_scope_schema_accepts_future_customer_scope_without_fk_dependency(self) -> None:
        payload = UserRoleAssignmentCreate(
            tenant_id="tenant-1",
            user_account_id="user-1",
            role_id="role-1",
            scope_type="customer",
            customer_id="customer-1",
        )
        self.assertEqual(payload.scope_type, "customer")
        self.assertEqual(payload.customer_id, "customer-1")
        self.assertIsNone(payload.branch_id)
        self.assertIsNone(payload.mandate_id)

    def test_session_schema_supports_revocation_ready_metadata(self) -> None:
        payload = UserSessionCreate(
            tenant_id="tenant-1",
            user_account_id="user-1",
            session_token_hash=hash_session_token("refresh-secret"),
            refresh_token_family="family-1",
            expires_at=datetime.now(UTC) + timedelta(days=7),
            device_label="Chrome on Linux",
            device_id="device-1",
            metadata_json={"mfa": False},
        )
        self.assertEqual(len(payload.session_token_hash), 64)
        self.assertEqual(payload.metadata_json["mfa"], False)

    def test_session_token_hash_rejects_empty_values(self) -> None:
        with self.assertRaises(ValueError):
            hash_session_token("   ")


if __name__ == "__main__":
    unittest.main()
