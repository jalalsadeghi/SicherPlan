from __future__ import annotations

import unittest
from unittest.mock import patch
from datetime import UTC, datetime
from uuid import uuid4

from app.modules.core.admin_repository import SqlAlchemyCoreAdminRepository
from app.modules.core.schemas import BranchCreate, MandateCreate, TenantCreate, TenantOnboardingCreate, TenantSettingCreate


class _FakeSession:
    def __init__(self) -> None:
        self.rows: list[object] = []
        self.commit_calls = 0
        self.rollback_calls = 0

    def add(self, row: object) -> None:
        self.rows.append(row)

    def add_all(self, rows: list[object]) -> None:
        self.rows.extend(rows)

    def flush(self) -> None:
        for row in self.rows:
            if getattr(row, "id", None) is None:
                row.id = str(uuid4())
            if getattr(row, "status", None) is None:
                row.status = "active"
            if getattr(row, "version_no", None) is None:
                row.version_no = 1
            now = datetime.now(UTC)
            if getattr(row, "created_at", None) is None:
                row.created_at = now
            if getattr(row, "updated_at", None) is None:
                row.updated_at = now

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1

    def refresh(self, row: object) -> None:
        if getattr(row, "id", None) is None:
            row.id = str(uuid4())
        if getattr(row, "status", None) is None:
            row.status = "active"
        if getattr(row, "version_no", None) is None:
            row.version_no = 1
        now = datetime.now(UTC)
        if getattr(row, "created_at", None) is None:
            row.created_at = now
        if getattr(row, "updated_at", None) is None:
            row.updated_at = now


class CoreAdminRepositoryHrBaselineTest(unittest.TestCase):
    @patch("app.modules.core.admin_repository.seed_baseline_employee_catalogs")
    @patch("app.modules.core.admin_repository.seed_lookup_values")
    @patch("app.modules.core.admin_repository.seed_default_tenant_settings")
    def test_onboard_tenant_runs_hr_catalog_baseline_seed(
        self,
        seed_default_tenant_settings_mock,
        seed_lookup_values_mock,
        seed_baseline_employee_catalogs_mock,
    ) -> None:
        session = _FakeSession()
        repository = SqlAlchemyCoreAdminRepository(session)  # type: ignore[arg-type]

        result = repository.onboard_tenant(
            TenantOnboardingCreate(
                tenant=TenantCreate(code="north", name="SicherPlan North"),
                initial_branch=BranchCreate(tenant_id="placeholder", code="hq", name="Hamburg"),
                initial_mandate=MandateCreate(tenant_id="placeholder", branch_id="placeholder", code="main", name="Main"),
                initial_settings=[
                    TenantSettingCreate(
                        tenant_id="placeholder",
                        key="ui.theme",
                        value_json={"mode": "light"},
                    ),
                ],
            ),
            actor_user_id="user-1",
        )

        self.assertEqual(session.commit_calls, 1)
        seed_default_tenant_settings_mock.assert_called_once_with(
            session,
            tenant_id=result.tenant.id,
            actor_user_id="user-1",
        )
        seed_lookup_values_mock.assert_called_once_with(
            session,
            tenant_id=result.tenant.id,
            actor_user_id="user-1",
        )
        seed_baseline_employee_catalogs_mock.assert_called_once_with(
            session,
            tenant_id=result.tenant.id,
            actor_user_id="user-1",
        )


if __name__ == "__main__":
    unittest.main()
