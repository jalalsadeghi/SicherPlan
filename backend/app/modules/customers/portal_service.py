"""Customer-portal access resolution based on shared IAM session state."""

from __future__ import annotations

from typing import Protocol

from app.errors import ApiException
from app.modules.customers.schemas import (
    CustomerPortalContextRead,
    CustomerPortalScopeRead,
)
from app.modules.iam.authz import RequestAuthorizationContext, enforce_permission


class CustomerPortalRepository(Protocol):
    def get_portal_contact_for_user(self, tenant_id: str, user_id: str): ...  # noqa: ANN001
    def get_portal_customer_scope_match(
        self,
        tenant_id: str,
        user_id: str,
        allowed_customer_ids: list[str],
    ): ...  # noqa: ANN001


class CustomerPortalService:
    def __init__(self, repository: CustomerPortalRepository) -> None:
        self.repository = repository

    def get_context(self, actor: RequestAuthorizationContext) -> CustomerPortalContextRead:
        enforce_permission(actor, "portal.customer.access")

        allowed_customer_ids = sorted(
            {
                scope.customer_id
                for scope in actor.scopes
                if scope.scope_type == "customer" and scope.customer_id
            }
        )
        if not allowed_customer_ids:
            raise ApiException(
                403,
                "customers.portal.scope_not_resolved",
                "errors.customers.portal.scope_not_resolved",
            )

        linked = self.repository.get_portal_contact_for_user(actor.tenant_id, actor.user_id)
        if linked is None:
            raise ApiException(
                403,
                "customers.portal.contact_not_linked",
                "errors.customers.portal.contact_not_linked",
            )

        customer, contact = linked
        if contact.status != "active" or contact.archived_at is not None:
            raise ApiException(
                403,
                "customers.portal.contact_inactive",
                "errors.customers.portal.contact_inactive",
            )
        if customer.status != "active" or customer.archived_at is not None:
            raise ApiException(
                403,
                "customers.portal.customer_inactive",
                "errors.customers.portal.customer_inactive",
            )

        scoped = self.repository.get_portal_customer_scope_match(
            actor.tenant_id,
            actor.user_id,
            allowed_customer_ids,
        )
        if scoped is None:
            raise ApiException(
                403,
                "customers.portal.scope_not_resolved",
                "errors.customers.portal.scope_not_resolved",
            )

        resolved_customer, resolved_contact = scoped
        scopes = [
            CustomerPortalScopeRead(
                role_key=scope.role_key,
                scope_type=scope.scope_type,
                customer_id=scope.customer_id,
            )
            for scope in actor.scopes
            if scope.scope_type == "customer" and scope.customer_id
        ]
        return CustomerPortalContextRead(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            customer_id=resolved_customer.id,
            contact_id=resolved_contact.id,
            customer=resolved_customer,
            contact=resolved_contact,
            scopes=scopes,
        )
