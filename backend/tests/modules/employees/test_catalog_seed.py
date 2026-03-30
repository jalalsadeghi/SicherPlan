from __future__ import annotations

import unittest

from app.modules.employees.catalog_seed import (
    SAMPLE_FUNCTION_TYPES,
    SAMPLE_QUALIFICATION_TYPES,
    seed_sample_employee_catalogs,
)
from app.modules.employees.models import FunctionType, QualificationType


class _FakeScalarResult:
    def __init__(self, value) -> None:  # noqa: ANN001
        self.value = value

    def one_or_none(self):  # noqa: ANN201
        return self.value


class _FakeSession:
    def __init__(self) -> None:
        self.function_types: list[FunctionType] = []
        self.qualification_types: list[QualificationType] = []

    def add(self, row) -> None:  # noqa: ANN001
        if isinstance(row, FunctionType):
            self.function_types.append(row)
            return
        if isinstance(row, QualificationType):
            self.qualification_types.append(row)
            return
        raise AssertionError(f"Unexpected row type: {type(row)!r}")

    def scalars(self, statement):  # noqa: ANN001
        compiled = statement.compile()
        values = list(compiled.params.values())
        if len(values) != 2:
            raise AssertionError(f"Unexpected query shape: {compiled.params}")
        tenant_value, code_value = values
        entity_name = statement.column_descriptions[0]["entity"].__name__
        rows = self.function_types if entity_name == "FunctionType" else self.qualification_types
        for row in rows:
            if row.tenant_id == tenant_value and row.code == code_value:
                return _FakeScalarResult(row)
        return _FakeScalarResult(None)


class TestEmployeeCatalogSeed(unittest.TestCase):
    def test_seed_creates_sample_rows_when_missing(self) -> None:
        session = _FakeSession()

        result = seed_sample_employee_catalogs(session, tenant_id="tenant-1", actor_user_id="user-1")

        self.assertEqual(result["function_types_inserted"], len(SAMPLE_FUNCTION_TYPES))
        self.assertEqual(result["qualification_types_inserted"], len(SAMPLE_QUALIFICATION_TYPES))
        self.assertTrue(all(row.is_active for row in session.function_types))
        self.assertTrue(all(row.status == "active" for row in session.function_types))
        self.assertTrue(all(row.archived_at is None for row in session.function_types))
        self.assertTrue(all(row.planning_relevant for row in session.function_types))
        self.assertTrue(all(row.is_active for row in session.qualification_types))
        self.assertTrue(all(row.status == "active" for row in session.qualification_types))
        self.assertTrue(all(row.archived_at is None for row in session.qualification_types))
        self.assertTrue(any(row.code == "SEC_GUARD" for row in session.function_types))
        self.assertTrue(any(row.code == "G34A" for row in session.qualification_types))

    def test_seed_is_idempotent_and_reactivates_existing_rows(self) -> None:
        session = _FakeSession()
        session.function_types.append(
            FunctionType(
                tenant_id="tenant-1",
                code="SEC_GUARD",
                label="Old label",
                is_active=False,
                planning_relevant=False,
                status="inactive",
                archived_at="2026-01-01T00:00:00Z",
                version_no=3,
            )
        )
        session.qualification_types.append(
            QualificationType(
                tenant_id="tenant-1",
                code="G34A",
                label="Old qualification",
                is_active=False,
                planning_relevant=False,
                compliance_relevant=False,
                expiry_required=False,
                default_validity_days=None,
                proof_required=False,
                status="inactive",
                archived_at="2026-01-01T00:00:00Z",
                version_no=4,
            )
        )

        first = seed_sample_employee_catalogs(session, tenant_id="tenant-1", actor_user_id="user-1")
        second = seed_sample_employee_catalogs(session, tenant_id="tenant-1", actor_user_id="user-1")

        self.assertEqual(first["function_types_updated"], 1)
        self.assertEqual(first["qualification_types_updated"], 1)
        self.assertEqual(second["function_types_inserted"], 0)
        self.assertEqual(second["function_types_updated"], 0)
        self.assertEqual(second["qualification_types_inserted"], 0)
        self.assertEqual(second["qualification_types_updated"], 0)
        self.assertEqual(len(session.function_types), len(SAMPLE_FUNCTION_TYPES))
        self.assertEqual(len(session.qualification_types), len(SAMPLE_QUALIFICATION_TYPES))
        guard = next(row for row in session.function_types if row.code == "SEC_GUARD")
        qualification = next(row for row in session.qualification_types if row.code == "G34A")
        self.assertEqual(guard.label, "Security agent")
        self.assertTrue(guard.is_active)
        self.assertIsNone(guard.archived_at)
        self.assertEqual(qualification.label, "34a certified")
        self.assertTrue(qualification.is_active)
        self.assertIsNone(qualification.archived_at)
