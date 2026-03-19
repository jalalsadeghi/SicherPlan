from __future__ import annotations

import unittest

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from app.db import Base
from app.modules.core.models import Branch, LookupValue, Mandate, Tenant, TenantSetting


class TestTenantBackboneMetadata(unittest.TestCase):
    def test_expected_tables_are_registered(self) -> None:
        self.assertIn("core.tenant", Base.metadata.tables)
        self.assertIn("core.branch", Base.metadata.tables)
        self.assertIn("core.mandate", Base.metadata.tables)
        self.assertIn("core.tenant_setting", Base.metadata.tables)
        self.assertIn("core.lookup_value", Base.metadata.tables)
        self.assertIn("common.address", Base.metadata.tables)

    def test_branch_code_is_unique_within_tenant(self) -> None:
        names = {constraint.name for constraint in Branch.__table__.constraints if isinstance(constraint, UniqueConstraint)}
        self.assertIn("uq_core_branch_tenant_code", names)
        self.assertIn("uq_core_branch_tenant_id_id", names)

    def test_mandate_has_composite_branch_scope_fk(self) -> None:
        foreign_keys = {fk.constraint.name: tuple(fk.parent.name for fk in fk.constraint.elements) for fk in Mandate.__table__.foreign_keys}
        self.assertIn("fk_core_mandate_tenant_branch", foreign_keys)
        self.assertEqual(foreign_keys["fk_core_mandate_tenant_branch"], ("tenant_id", "branch_id"))

    def test_tenant_setting_key_is_unique_per_tenant(self) -> None:
        names = {constraint.name for constraint in TenantSetting.__table__.constraints if isinstance(constraint, UniqueConstraint)}
        self.assertIn("uq_core_tenant_setting_tenant_key", names)

    def test_lookup_value_has_split_system_and_tenant_uniqueness(self) -> None:
        indexes = {index.name: index for index in LookupValue.__table__.indexes if isinstance(index, Index)}
        self.assertIn("uq_core_lookup_value_system_domain_code", indexes)
        self.assertIn("uq_core_lookup_value_tenant_domain_code", indexes)

    def test_lifecycle_defaults_are_present(self) -> None:
        for table in (Tenant.__table__, Branch.__table__, Mandate.__table__, TenantSetting.__table__, LookupValue.__table__):
            self.assertIsNotNone(table.c.status.server_default)
            self.assertIsNotNone(table.c.created_at.server_default)
            self.assertIsNotNone(table.c.updated_at.server_default)
            self.assertIsNotNone(table.c.version_no.server_default)

    def test_postgresql_ddl_includes_schema_and_constraints(self) -> None:
        ddl = str(CreateTable(Mandate.__table__).compile(dialect=dialect()))
        self.assertIn("CREATE TABLE core.mandate", ddl)
        self.assertIn("CONSTRAINT uq_core_mandate_tenant_code", ddl)
        self.assertIn("CONSTRAINT fk_core_mandate_tenant_branch", ddl)


if __name__ == "__main__":
    unittest.main()
