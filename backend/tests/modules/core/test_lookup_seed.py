from __future__ import annotations

import unittest

from app.modules.core.lookup_seed import (
    ALL_LOOKUP_DOMAINS,
    SYSTEM_LOOKUP_DOMAINS,
    TENANT_EXTENSIBLE_LOOKUP_DOMAINS,
    seed_lookup_values,
)
from app.modules.core.models import LookupValue


class _FakeScalarResult:
    def __init__(self, value: LookupValue | None) -> None:
        self.value = value

    def one_or_none(self) -> LookupValue | None:
        return self.value


class _FakeSession:
    def __init__(self) -> None:
        self.rows: list[LookupValue] = []

    def add(self, row: LookupValue) -> None:
        self.rows.append(row)

    def scalars(self, statement):  # noqa: ANN001
        compiled = statement.compile()
        values = list(compiled.params.values())
        if len(values) == 3:
            tenant_value, domain_value, code_value = values
        elif len(values) == 2:
            tenant_value = None
            domain_value, code_value = values
        else:
            raise AssertionError(f"Unexpected lookup query shape: {compiled.params}")

        for row in self.rows:
            if row.tenant_id == tenant_value and row.domain == domain_value and row.code == code_value:
                return _FakeScalarResult(row)
        return _FakeScalarResult(None)


class TestLookupSeed(unittest.TestCase):
    def test_domain_governance_has_no_duplicate_domain_names(self) -> None:
        names = [domain.name for domain in ALL_LOOKUP_DOMAINS]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("dunning_policy", names)

    def test_system_seed_is_idempotent(self) -> None:
        session = _FakeSession()

        first = seed_lookup_values(session)
        second = seed_lookup_values(session)

        expected = sum(len(domain.values) for domain in SYSTEM_LOOKUP_DOMAINS)
        self.assertEqual(first["inserted"], expected)
        self.assertEqual(first["updated"], 0)
        self.assertEqual(second, {"inserted": 0, "updated": 0})

    def test_tenant_seed_only_applies_tenant_extensible_domains(self) -> None:
        session = _FakeSession()

        result = seed_lookup_values(session, tenant_id="tenant-1")

        self.assertEqual(result, {"inserted": 0, "updated": 0})
        self.assertEqual(len(session.rows), 0)
        self.assertTrue(all(domain.values == () for domain in TENANT_EXTENSIBLE_LOOKUP_DOMAINS))

    def test_seed_updates_existing_labels_without_duplication(self) -> None:
        session = _FakeSession()
        row = LookupValue(
            tenant_id=None,
            domain="legal_form",
            code="gmbh",
            label="Old",
            description="Old",
            sort_order=999,
        )
        session.rows.append(row)

        result = seed_lookup_values(session)

        self.assertEqual(result["inserted"], sum(len(domain.values) for domain in SYSTEM_LOOKUP_DOMAINS) - 1)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(row.label, "GmbH")
        self.assertEqual(row.sort_order, 10)
