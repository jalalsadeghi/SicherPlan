from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.errors import ApiException
from app.main import create_app
from app.modules.employees.router import get_employee_file_service
from app.modules.employees.schemas import EmployeeDocumentListItemRead
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext, get_request_authorization_context


def _context(tenant_id: str) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=frozenset({"employees.employee.read", "employees.employee.write"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-test-1",
    )


@dataclass
class RecordingEmployeeFileService:
    tenant_id: str
    employee_id: str
    documents: list[EmployeeDocumentListItemRead] = field(default_factory=list)

    def list_documents(self, tenant_id: str, employee_id: str, context: RequestAuthorizationContext) -> list[EmployeeDocumentListItemRead]:
        self._require_employee(tenant_id, employee_id)
        return list(self.documents)

    def upload_employee_document(self, tenant_id: str, employee_id: str, payload, context: RequestAuthorizationContext) -> EmployeeDocumentListItemRead:  # noqa: ANN001
        self._require_employee(tenant_id, employee_id)
        row = EmployeeDocumentListItemRead(
            document_id=str(uuid4()),
            relation_type=payload.relation_type,
            label=payload.label,
            title=payload.title,
            document_type_key=payload.document_type_key,
            file_name=payload.file_name,
            content_type=payload.content_type,
            current_version_no=1,
            linked_at=datetime.now(UTC),
        )
        self.documents.append(row)
        return row

    def _require_employee(self, tenant_id: str, employee_id: str) -> None:
        if tenant_id != self.tenant_id or employee_id != self.employee_id:
            raise ApiException(404, "employees.employee.not_found", "errors.employees.employee.not_found")


def test_employee_document_upload_request_returns_created_and_listable_metadata() -> None:
    tenant_id = str(uuid4())
    employee_id = str(uuid4())
    service = RecordingEmployeeFileService(tenant_id=tenant_id, employee_id=employee_id)
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(tenant_id)
    app.dependency_overrides[get_employee_file_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            f"/api/employees/tenants/{tenant_id}/employees/{employee_id}/documents/uploads",
            json={
                "title": "Arbeitsvertrag",
                "relation_type": "contract",
                "label": "Vertrag 2026",
                "document_type_key": None,
                "file_name": "contract.pdf",
                "content_type": "application/pdf",
                "content_base64": "YQ==",
            },
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["title"] == "Arbeitsvertrag"
        assert payload["relation_type"] == "contract"
        assert payload["label"] == "Vertrag 2026"
        assert payload["file_name"] == "contract.pdf"
        assert payload["content_type"] == "application/pdf"
        assert payload["current_version_no"] == 1
        assert payload["document_id"]

        list_response = client.get(
            f"/api/employees/tenants/{tenant_id}/employees/{employee_id}/documents",
            headers={"Authorization": "Bearer test-access"},
        )
        assert list_response.status_code == 200
        items = list_response.json()
        assert len(items) == 1
        assert items[0]["document_id"] == payload["document_id"]

    app.dependency_overrides.clear()


def test_employee_document_upload_missing_employee_returns_structured_404() -> None:
    tenant_id = str(uuid4())
    existing_employee_id = str(uuid4())
    missing_employee_id = str(uuid4())
    service = RecordingEmployeeFileService(tenant_id=tenant_id, employee_id=existing_employee_id)
    app = create_app()
    app.dependency_overrides[get_request_authorization_context] = lambda: _context(tenant_id)
    app.dependency_overrides[get_employee_file_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            f"/api/employees/tenants/{tenant_id}/employees/{missing_employee_id}/documents/uploads",
            json={
                "title": "Arbeitsvertrag",
                "relation_type": "contract",
                "label": "Vertrag 2026",
                "document_type_key": None,
                "file_name": "contract.pdf",
                "content_type": "application/pdf",
                "content_base64": "YQ==",
            },
            headers={"Authorization": "Bearer test-access"},
        )

        assert response.status_code == 404
        payload = response.json()
        assert payload["error"]["code"] == "employees.employee.not_found"
        assert payload["error"]["message_key"] == "errors.employees.employee.not_found"
        assert payload["error"]["request_id"]

    app.dependency_overrides.clear()
