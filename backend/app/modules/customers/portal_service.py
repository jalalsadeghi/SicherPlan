"""Customer-portal access resolution based on shared IAM session state."""

from __future__ import annotations

from typing import Protocol

from app.errors import ApiException
from app.modules.customers.schemas import (
    CustomerPortalCapabilitiesRead,
    CustomerPortalContextRead,
    CustomerPortalDatasetCapabilityRead,
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
    def get_customer_portal_policy(self, tenant_id: str) -> dict[str, object]: ...  # noqa: ANN001


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
        watchbook_entries_enabled = bool(
            self.repository.get_customer_portal_policy(actor.tenant_id).get("customer_watchbook_entries_enabled", False)
        )
        scopes = [
            CustomerPortalScopeRead(
                role_key=scope.role_key,
                scope_type=scope.scope_type,
                customer_id=scope.customer_id,
            )
            for scope in actor.scopes
            if scope.scope_type == "customer" and scope.customer_id
        ]
        capabilities = CustomerPortalCapabilitiesRead(
            can_view_orders=True,
            can_view_schedules=True,
            can_view_watchbooks=True,
            can_add_watchbook_entries=watchbook_entries_enabled,
            can_view_timesheets=True,
            can_download_timesheet_documents=True,
            can_view_invoices=True,
            can_download_invoice_documents=True,
            can_view_reports=True,
            can_view_history=True,
            personal_names_visible=bool(resolved_customer.portal_person_names_released),
            released_only=True,
            customer_scoped_only=True,
            datasets=self._build_dataset_capabilities(watchbook_entries_enabled),
        )
        return CustomerPortalContextRead(
            tenant_id=actor.tenant_id,
            user_id=actor.user_id,
            customer_id=resolved_customer.id,
            contact_id=resolved_contact.id,
            customer=resolved_customer,
            contact=resolved_contact,
            scopes=scopes,
            capabilities=capabilities,
        )

    @staticmethod
    def _build_dataset_capabilities(watchbook_entries_enabled: bool) -> list[CustomerPortalDatasetCapabilityRead]:
        return [
            CustomerPortalDatasetCapabilityRead(
                domain_key="orders",
                availability_status="pending_source_module",
                reason_message_key="portalCustomer.datasets.orders.pending",
                interaction_mode="read_only",
            ),
            CustomerPortalDatasetCapabilityRead(
                domain_key="schedules",
                availability_status="pending_source_module",
                reason_message_key="portalCustomer.datasets.schedules.pending",
                interaction_mode="read_only",
            ),
            CustomerPortalDatasetCapabilityRead(
                domain_key="watchbooks",
                availability_status="ready",
                reason_message_key=(
                    "portalCustomer.capabilities.watchbooks.writeEnabled"
                    if watchbook_entries_enabled
                    else "portalCustomer.capabilities.watchbooks.writeDisabled"
                ),
                interaction_mode="write_optional",
                can_write=watchbook_entries_enabled,
            ),
            CustomerPortalDatasetCapabilityRead(
                domain_key="timesheets",
                availability_status="ready",
                reason_message_key="portalCustomer.capabilities.timesheets.download",
                interaction_mode="download",
                can_download_documents=True,
            ),
            CustomerPortalDatasetCapabilityRead(
                domain_key="invoices",
                availability_status="ready",
                reason_message_key="portalCustomer.capabilities.invoices.download",
                interaction_mode="download",
                can_download_documents=True,
            ),
            CustomerPortalDatasetCapabilityRead(
                domain_key="reports",
                availability_status="pending_source_module",
                reason_message_key="portalCustomer.datasets.reports.pending",
                interaction_mode="read_only",
            ),
            CustomerPortalDatasetCapabilityRead(
                domain_key="history",
                availability_status="ready",
                reason_message_key="portalCustomer.capabilities.history.visible",
                interaction_mode="read_only",
            ),
        ]
