from __future__ import annotations

import unittest
from uuid import uuid4

from starlette.routing import Match

from app.main import create_app


def _matched_route_path(method: str, path: str) -> str | None:
    app = create_app()
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode("utf-8"),
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    for route in app.router.routes:
        match, _ = route.matches(scope)
        if match == Match.FULL:
            return getattr(route, "path", None)
    return None


class EmployeeRouterPathOrderTest(unittest.TestCase):
    def test_static_collection_routes_are_registered_before_dynamic_employee_route(self) -> None:
        app = create_app()
        paths = [route.path for route in app.routes]

        dynamic_employee_index = paths.index("/api/employees/tenants/{tenant_id}/employees/{employee_id}")

        for static_path in (
            "/api/employees/tenants/{tenant_id}/employees/groups/catalog",
            "/api/employees/tenants/{tenant_id}/employees/availability-rules",
            "/api/employees/tenants/{tenant_id}/employees/absences",
            "/api/employees/tenants/{tenant_id}/employees/leave-balances",
            "/api/employees/tenants/{tenant_id}/employees/event-applications",
            "/api/employees/tenants/{tenant_id}/employees/time-accounts",
            "/api/employees/tenants/{tenant_id}/employees/allowances",
            "/api/employees/tenants/{tenant_id}/employees/advances",
            "/api/employees/tenants/{tenant_id}/employees/credentials",
            "/api/employees/tenants/{tenant_id}/employees/qualifications",
        ):
            self.assertLess(paths.index(static_path), dynamic_employee_index, static_path)

    def test_employee_document_management_routes_are_registered(self) -> None:
        app = create_app()
        paths = {route.path for route in app.routes}

        self.assertIn("/api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/uploads", paths)
        self.assertIn("/api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/links", paths)
        self.assertIn("/api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/{document_id}/versions", paths)

    def test_readiness_collection_get_routes_match_static_handlers(self) -> None:
        tenant_id = str(uuid4())
        employee_id = str(uuid4())

        self.assertEqual(
            _matched_route_path(
                "GET",
                f"/api/employees/tenants/{tenant_id}/employees/availability-rules",
            ),
            "/api/employees/tenants/{tenant_id}/employees/availability-rules",
        )
        self.assertEqual(
            _matched_route_path(
                "GET",
                f"/api/employees/tenants/{tenant_id}/employees/qualifications",
            ),
            "/api/employees/tenants/{tenant_id}/employees/qualifications",
        )
        self.assertEqual(
            _matched_route_path(
                "GET",
                f"/api/employees/tenants/{tenant_id}/employees/credentials",
            ),
            "/api/employees/tenants/{tenant_id}/employees/credentials",
        )
        self.assertEqual(
            _matched_route_path(
                "GET",
                f"/api/employees/tenants/{tenant_id}/employees/absences",
            ),
            "/api/employees/tenants/{tenant_id}/employees/absences",
        )
        self.assertEqual(
            _matched_route_path(
                "GET",
                f"/api/employees/tenants/{tenant_id}/employees/{employee_id}",
            ),
            "/api/employees/tenants/{tenant_id}/employees/{employee_id}",
        )

    def test_readiness_collection_post_routes_match_static_handlers(self) -> None:
        tenant_id = str(uuid4())

        self.assertEqual(
            _matched_route_path(
                "POST",
                f"/api/employees/tenants/{tenant_id}/employees/availability-rules",
            ),
            "/api/employees/tenants/{tenant_id}/employees/availability-rules",
        )
        self.assertEqual(
            _matched_route_path(
                "POST",
                f"/api/employees/tenants/{tenant_id}/employees/qualifications",
            ),
            "/api/employees/tenants/{tenant_id}/employees/qualifications",
        )
        self.assertEqual(
            _matched_route_path(
                "POST",
                f"/api/employees/tenants/{tenant_id}/employees/credentials",
            ),
            "/api/employees/tenants/{tenant_id}/employees/credentials",
        )
        self.assertEqual(
            _matched_route_path(
                "POST",
                f"/api/employees/tenants/{tenant_id}/employees/absences",
            ),
            "/api/employees/tenants/{tenant_id}/employees/absences",
        )
