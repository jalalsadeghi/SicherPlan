from __future__ import annotations

import unittest

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from app.db import Base
from app.modules.platform_services.integration_models import ImportExportJob


class TestIntegrationBackbone(unittest.TestCase):
    def test_import_export_job_has_composite_tenant_unique_key_for_downstream_fks(self) -> None:
        self.assertIn("integration.import_export_job", Base.metadata.tables)
        constraint_names = {
            constraint.name
            for constraint in ImportExportJob.__table__.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        self.assertIn("uq_integration_import_export_job_tenant_id_id", constraint_names)

    def test_import_export_job_ddl_contains_tenant_scoped_unique_key(self) -> None:
        ddl = str(CreateTable(ImportExportJob.__table__).compile(dialect=dialect()))
        self.assertIn("uq_integration_import_export_job_tenant_id_id", ddl)
