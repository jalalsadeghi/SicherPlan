from __future__ import annotations

import unittest

from app.modules.assistant.models import AssistantPageRouteCatalog
from app.modules.assistant.page_catalog_seed import ASSISTANT_PAGE_ROUTE_SEEDS, seed_assistant_page_route_catalog


class _FakeScalarResult:
    def __init__(self, value) -> None:  # noqa: ANN001
        self.value = value

    def one_or_none(self):  # noqa: ANN201
        return self.value


class _FakeSession:
    def __init__(self) -> None:
        self.page_routes: list[AssistantPageRouteCatalog] = []

    def add(self, row) -> None:  # noqa: ANN001
        if not isinstance(row, AssistantPageRouteCatalog):
            raise AssertionError(f"Unexpected row type: {type(row)!r}")
        self.page_routes.append(row)

    def scalars(self, statement):  # noqa: ANN001
        compiled = statement.compile()
        values = list(compiled.params.values())
        if len(values) != 2:
            raise AssertionError(f"Unexpected query shape: {compiled.params}")
        page_id, path_template = values
        for row in self.page_routes:
            if row.page_id == page_id and row.path_template == path_template:
                return _FakeScalarResult(row)
        return _FakeScalarResult(None)


class TestAssistantPageRouteCatalogSeed(unittest.TestCase):
    def test_seed_is_idempotent(self) -> None:
        session = _FakeSession()

        first = seed_assistant_page_route_catalog(session)
        second = seed_assistant_page_route_catalog(session)

        self.assertEqual(first["inserted"], len(ASSISTANT_PAGE_ROUTE_SEEDS))
        self.assertEqual(first["updated"], 0)
        self.assertEqual(second["inserted"], 0)
        self.assertEqual(second["updated"], 0)
        self.assertEqual(len(session.page_routes), len(ASSISTANT_PAGE_ROUTE_SEEDS))

    def test_seed_includes_markus_diagnostic_pages(self) -> None:
        session = _FakeSession()
        seed_assistant_page_route_catalog(session)

        page_ids = {row.page_id for row in session.page_routes}
        self.assertTrue({"P-03", "P-04", "P-05", "E-01", "ES-01"}.issubset(page_ids))

    def test_seed_uses_actual_frontend_route_names_and_safe_fallbacks(self) -> None:
        session = _FakeSession()
        seed_assistant_page_route_catalog(session)

        by_page_id = {row.page_id: row for row in session.page_routes}
        self.assertEqual(by_page_id["P-04"].route_name, "SicherPlanPlanningStaffing")
        self.assertEqual(by_page_id["P-04"].path_template, "/admin/planning-staffing")
        self.assertEqual(by_page_id["CP-01"].route_name, "SicherPlanCustomerPortalOverview")
        self.assertEqual(by_page_id["SP-01"].route_name, "SicherPlanSubcontractorPortal")
        self.assertEqual(by_page_id["ES-01"].route_name, "SicherPlanEmployees")
        self.assertEqual(by_page_id["ES-01"].path_template, "/admin/employees")
