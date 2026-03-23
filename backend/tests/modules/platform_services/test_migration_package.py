from __future__ import annotations

import unittest

from app.modules.platform_services.migration_package import MigrationPackageService
from app.modules.platform_services.migration_schemas import MigrationPreflightRequest, MigrationSheetPayload


class _FakeMigrationRepo:
    def __init__(self) -> None:
        self.customers = {"K-EXIST"}
        self.employees = {"P-EXIST"}
        self.subcontractors = {"SU-EXIST"}
        self.orders = {"A-EXIST"}
        self.lookups = {
            ("tenant-1", "legal_form", "gmbh"),
            ("tenant-1", "subcontractor_status", "active"),
        }
        self.requirement_types = {("tenant-1", "event_security")}
        self.document_types = {"customer_contract", "employee_personnel_file"}

    def customer_exists_by_number(self, tenant_id: str, customer_number: str) -> bool:
        return customer_number in self.customers

    def employee_exists_by_personnel_no(self, tenant_id: str, personnel_no: str) -> bool:
        return personnel_no in self.employees

    def subcontractor_exists_by_number(self, tenant_id: str, subcontractor_number: str) -> bool:
        return subcontractor_number in self.subcontractors

    def order_exists_by_number(self, tenant_id: str, order_no: str) -> bool:
        return order_no in self.orders

    def lookup_value_exists(self, tenant_id: str, domain: str, code: str) -> bool:
        return (tenant_id, domain, code) in self.lookups

    def requirement_type_exists(self, tenant_id: str, code: str) -> bool:
        return (tenant_id, code) in self.requirement_types

    def document_type_exists(self, key: str) -> bool:
        return key in self.document_types


class TestMigrationPackage(unittest.TestCase):
    def setUp(self) -> None:
        self.service = MigrationPackageService(_FakeMigrationRepo())

    def test_package_description_contains_expected_load_order(self) -> None:
        package = self.service.describe_package()
        self.assertEqual(package.package_version, "v1")
        self.assertEqual(package.load_order, ["customers", "employees", "subcontractors", "orders", "documents"])

    def test_preflight_detects_duplicate_business_key_and_missing_required_field(self) -> None:
        result = self.service.preflight(
            MigrationPreflightRequest(
                tenant_id="tenant-1",
                sheets=[
                    MigrationSheetPayload(
                        sheet_key="customers",
                        rows=[
                            {"match_action": "upsert", "customer_number": "K-1", "name": "One"},
                            {"match_action": "upsert", "customer_number": "K-1", "name": ""},
                        ],
                    )
                ],
            )
        )
        self.assertEqual(result.summary.invalid_rows, 1)
        issues = result.rows[1].issues
        self.assertTrue(any(issue.code == "duplicate_business_key" for issue in issues))
        self.assertTrue(any(issue.code == "missing_required_field" for issue in issues))

    def test_preflight_resolves_lookup_and_cross_sheet_references(self) -> None:
        result = self.service.preflight(
            MigrationPreflightRequest(
                tenant_id="tenant-1",
                sheets=[
                    MigrationSheetPayload(
                        sheet_key="customers",
                        rows=[{"match_action": "upsert", "customer_number": "K-1001", "name": "Messe", "legal_form_code": "gmbh"}],
                    ),
                    MigrationSheetPayload(
                        sheet_key="orders",
                        rows=[
                            {
                                "match_action": "upsert",
                                "order_no": "A-1001",
                                "customer_number": "K-1001",
                                "requirement_type_code": "event_security",
                                "title": "Order",
                                "service_category_code": "event",
                                "service_from": "2026-01-01",
                                "service_to": "2026-01-02",
                            }
                        ],
                    ),
                    MigrationSheetPayload(
                        sheet_key="documents",
                        rows=[
                            {
                                "manifest_row_key": "DOC-1",
                                "source_system": "legacy",
                                "legacy_document_id": "4711",
                                "source_file_name": "contract.pdf",
                                "title": "Contract",
                                "owner_sheet": "customers",
                                "owner_business_key": "K-1001",
                                "document_type_key": "customer_contract",
                                "relation_type": "attachment",
                                "checksum_sha256": "a" * 64,
                                "content_base64": "UERG",
                            }
                        ],
                    ),
                ],
            )
        )
        self.assertEqual(result.summary.invalid_rows, 0)
        self.assertEqual(result.rows[0].match_result, "create")
        self.assertEqual(result.rows[1].match_result, "create")
        self.assertEqual(result.rows[2].match_result, "create")

    def test_preflight_flags_unknown_lookup_and_orphan_document(self) -> None:
        result = self.service.preflight(
            MigrationPreflightRequest(
                tenant_id="tenant-1",
                sheets=[
                    MigrationSheetPayload(
                        sheet_key="subcontractors",
                        rows=[
                            {
                                "match_action": "upsert",
                                "subcontractor_number": "SU-1",
                                "legal_name": "Partner",
                                "legal_form_code": "unknown",
                            }
                        ],
                    ),
                    MigrationSheetPayload(
                        sheet_key="documents",
                        rows=[
                            {
                                "manifest_row_key": "DOC-1",
                                "source_system": "legacy",
                                "legacy_document_id": "1",
                                "source_file_name": "missing.pdf",
                                "title": "Missing",
                                "owner_sheet": "customers",
                                "owner_business_key": "K-404",
                                "relation_type": "attachment",
                                "checksum_sha256": "a" * 64,
                                "content_base64": "UERG",
                            }
                        ],
                    ),
                ],
            )
        )
        self.assertEqual(result.summary.invalid_rows, 2)
        self.assertTrue(any(issue.code == "unknown_lookup_value" for issue in result.rows[0].issues))
        self.assertTrue(any(issue.code == "orphan_document_link" for issue in result.rows[1].issues))

    def test_preflight_enforces_deterministic_match_rules(self) -> None:
        result = self.service.preflight(
            MigrationPreflightRequest(
                tenant_id="tenant-1",
                sheets=[
                    MigrationSheetPayload(
                        sheet_key="customers",
                        rows=[
                            {"match_action": "create_only", "customer_number": "K-EXIST", "name": "Existing"},
                            {"match_action": "update_only", "customer_number": "K-NEW", "name": "New"},
                        ],
                    )
                ],
            )
        )
        self.assertEqual(result.summary.conflict_rows, 2)
        self.assertTrue(all(row.status == "invalid" for row in result.rows))
