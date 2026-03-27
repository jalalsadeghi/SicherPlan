from __future__ import annotations

import unittest
from datetime import date

from app.modules.core.config_seed import (
    CUSTOMER_PORTAL_POLICY_SETTING_KEY,
    DEFAULT_NUMBERING_RULES,
    NUMBERING_RULES_SETTING_KEY,
    PRINT_TEMPLATES_SETTING_KEY,
    preview_number,
    seed_default_tenant_settings,
)
from app.modules.core.models import TenantSetting
from app.modules.platform_services.docs_models import DocumentType
from app.modules.platform_services.document_type_seed import seed_document_types


class _FakeScalarResult:
    def __init__(self, value) -> None:  # noqa: ANN001
        self.value = value

    def one_or_none(self):  # noqa: ANN001
        return self.value


class _FakeSession:
    def __init__(self) -> None:
        self.settings: list[TenantSetting] = []
        self.document_types: list[DocumentType] = []

    def add(self, row) -> None:  # noqa: ANN001
        if isinstance(row, TenantSetting):
            self.settings.append(row)
        elif isinstance(row, DocumentType):
            self.document_types.append(row)
        else:  # pragma: no cover - defensive
            raise AssertionError(type(row))

    def scalars(self, statement):  # noqa: ANN001
        compiled = statement.compile()
        values = list(compiled.params.values())
        if "tenant_setting" in str(statement):
            tenant_id, key = values
            for row in self.settings:
                if row.tenant_id == tenant_id and row.key == key:
                    return _FakeScalarResult(row)
            return _FakeScalarResult(None)
        key = values[0]
        for row in self.document_types:
            if row.key == key:
                return _FakeScalarResult(row)
        return _FakeScalarResult(None)


class TestConfigSeed(unittest.TestCase):
    def test_tenant_setting_seed_is_idempotent(self) -> None:
        session = _FakeSession()
        first = seed_default_tenant_settings(session, tenant_id="tenant-1")
        second = seed_default_tenant_settings(session, tenant_id="tenant-1")
        self.assertEqual(first, {"inserted": 3, "updated": 0})
        self.assertEqual(second, {"inserted": 0, "updated": 0})
        self.assertEqual(
            {row.key for row in session.settings},
            {
                NUMBERING_RULES_SETTING_KEY,
                PRINT_TEMPLATES_SETTING_KEY,
                CUSTOMER_PORTAL_POLICY_SETTING_KEY,
            },
        )

    def test_number_preview_uses_reset_policy(self) -> None:
        preview = preview_number(DEFAULT_NUMBERING_RULES["invoice_no"], 42, at_date=date(2026, 3, 20))
        self.assertEqual(preview, "RE-2026-00042")

    def test_document_type_seed_is_idempotent(self) -> None:
        session = _FakeSession()
        first = seed_document_types(session)
        second = seed_document_types(session)
        self.assertEqual(first["inserted"], len(session.document_types))
        self.assertEqual(second, {"inserted": 0, "updated": 0})

    def test_document_type_seed_updates_existing_name(self) -> None:
        session = _FakeSession()
        session.document_types.append(
            DocumentType(key="customer_contract", name="Old", description="Old", is_system_type=False)
        )
        result = seed_document_types(session)
        self.assertEqual(result["updated"], 1)
        self.assertEqual(session.document_types[0].name, "Kundenvertrag")
        self.assertTrue(session.document_types[0].is_system_type)
