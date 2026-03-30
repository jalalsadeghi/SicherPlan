from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import Request

from app.errors import ApiException
from app.modules.customers.router import get_customer_reference_data
from app.modules.customers.schemas import CustomerReferenceDataRead
from app.modules.iam.auth_schemas import AuthenticatedRoleScope
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization


def _request(tenant_id: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": f"/api/customers/tenants/{tenant_id}/customers/reference-data",
            "path_params": {"tenant_id": tenant_id},
            "headers": [],
        }
    )


def _context(
    *,
    tenant_id: str,
    permission_keys: frozenset[str] | None = None,
) -> RequestAuthorizationContext:
    return RequestAuthorizationContext(
        session_id="session-1",
        user_id="user-1",
        tenant_id=tenant_id,
        role_keys=frozenset({"tenant_admin"}),
        permission_keys=permission_keys if permission_keys is not None else frozenset({"customers.customer.read"}),
        scopes=(AuthenticatedRoleScope(role_key="tenant_admin", scope_type="tenant"),),
        request_id="req-1",
    )


def test_customer_reference_data_endpoint_uses_customer_read_scope() -> None:
    tenant_id = str(uuid4())
    dependency = require_authorization("customers.customer.read", scope="tenant")
    authorized_context = dependency(_request(tenant_id), _context(tenant_id=tenant_id))
    service = SimpleNamespace(
        get_reference_data=lambda tenant_id_arg, context: CustomerReferenceDataRead(
            legal_forms=[],
            classifications=[],
            rankings=[],
            customer_statuses=[],
            invoice_layouts=[],
            shipping_methods=[],
            dunning_policies=[],
            function_types=[],
            qualification_types=[],
            branches=[],
            mandates=[],
        )
    )

    result = get_customer_reference_data(UUID(tenant_id), authorized_context, service)  # type: ignore[arg-type]

    assert isinstance(result, CustomerReferenceDataRead)


def test_customer_reference_data_endpoint_rejects_missing_customer_read_permission() -> None:
    tenant_id = str(uuid4())
    dependency = require_authorization("customers.customer.read", scope="tenant")

    with pytest.raises(ApiException) as raised:
        dependency(_request(tenant_id), _context(tenant_id=tenant_id, permission_keys=frozenset()))

    assert raised.value.status_code == 403
    assert raised.value.code == "iam.authorization.permission_denied"
