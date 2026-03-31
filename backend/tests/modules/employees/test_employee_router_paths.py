from __future__ import annotations

import unittest

from app.main import create_app


class EmployeeRouterPathOrderTest(unittest.TestCase):
    def test_group_catalog_routes_are_registered_before_dynamic_employee_route(self) -> None:
        app = create_app()
        paths = [route.path for route in app.routes]

        group_catalog_index = paths.index("/api/employees/tenants/{tenant_id}/employees/groups/catalog")
        dynamic_employee_index = paths.index("/api/employees/tenants/{tenant_id}/employees/{employee_id}")

        self.assertLess(group_catalog_index, dynamic_employee_index)

    def test_employee_document_management_routes_are_registered(self) -> None:
        app = create_app()
        paths = {route.path for route in app.routes}

        self.assertIn("/api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/uploads", paths)
        self.assertIn("/api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/links", paths)
        self.assertIn("/api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/{document_id}/versions", paths)
