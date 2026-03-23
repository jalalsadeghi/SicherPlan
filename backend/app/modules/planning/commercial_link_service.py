"""Planning-owned read contract for CRM commercial references and release readiness."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from app.errors import ApiException
from app.modules.customers.models import CustomerBillingProfile, CustomerInvoiceParty, CustomerRateCard
from app.modules.iam.authz import RequestAuthorizationContext
from app.modules.planning.models import CustomerOrder, PlanningRecord
from app.modules.planning.schemas import PlanningCommercialIssueRead, PlanningCommercialLinkRead


class PlanningCommercialRepository(Protocol):
    def get_customer_order(self, tenant_id: str, order_id: str) -> CustomerOrder | None: ...
    def get_planning_record(self, tenant_id: str, planning_record_id: str) -> PlanningRecord | None: ...
    def get_customer_billing_profile(self, tenant_id: str, customer_id: str) -> CustomerBillingProfile | None: ...
    def list_customer_invoice_parties(self, tenant_id: str, customer_id: str) -> list[CustomerInvoiceParty]: ...
    def list_customer_rate_cards(self, tenant_id: str, customer_id: str) -> list[CustomerRateCard]: ...


class PlanningCommercialLinkService:
    def __init__(self, repository: PlanningCommercialRepository) -> None:
        self.repository = repository

    def get_order_commercial_link(
        self,
        tenant_id: str,
        order_id: str,
        _actor: RequestAuthorizationContext,
    ) -> PlanningCommercialLinkRead:
        order = self._require_order(tenant_id, order_id)
        return self._build_link(tenant_id, order.customer_id, order.id, None, order.service_from)

    def get_planning_record_commercial_link(
        self,
        tenant_id: str,
        planning_record_id: str,
        _actor: RequestAuthorizationContext,
    ) -> PlanningCommercialLinkRead:
        record = self._require_planning_record(tenant_id, planning_record_id)
        order = self._require_order(tenant_id, record.order_id)
        return self._build_link(tenant_id, order.customer_id, order.id, record.id, record.planning_from)

    def assert_order_release_ready(self, tenant_id: str, order_id: str) -> None:
        link = self._build_link_for_order(tenant_id, order_id)
        self._assert_release_ready(link)

    def assert_planning_record_release_ready(self, tenant_id: str, planning_record_id: str) -> None:
        record = self._require_planning_record(tenant_id, planning_record_id)
        order = self._require_order(tenant_id, record.order_id)
        link = self._build_link(tenant_id, order.customer_id, order.id, record.id, record.planning_from)
        self._assert_release_ready(link)

    def _build_link_for_order(self, tenant_id: str, order_id: str) -> PlanningCommercialLinkRead:
        order = self._require_order(tenant_id, order_id)
        return self._build_link(tenant_id, order.customer_id, order.id, None, order.service_from)

    def _build_link(
        self,
        tenant_id: str,
        customer_id: str,
        order_id: str,
        planning_record_id: str | None,
        effective_on: date,
    ) -> PlanningCommercialLinkRead:
        profile = self.repository.get_customer_billing_profile(tenant_id, customer_id)
        invoice_parties = self.repository.list_customer_invoice_parties(tenant_id, customer_id)
        rate_cards = self.repository.list_customer_rate_cards(tenant_id, customer_id)
        default_party = next(
            (
                row
                for row in invoice_parties
                if row.archived_at is None and row.status == "active" and row.is_default
            ),
            None,
        )
        active_rate_cards = [
            row
            for row in rate_cards
            if row.archived_at is None
            and row.status == "active"
            and row.effective_from <= effective_on
            and (row.effective_to is None or row.effective_to >= effective_on)
        ]

        blocking_issues: list[PlanningCommercialIssueRead] = []
        warning_issues: list[PlanningCommercialIssueRead] = []

        if profile is None or profile.archived_at is not None or profile.status != "active":
            blocking_issues.append(
                PlanningCommercialIssueRead(
                    code="missing_billing_profile",
                    severity="blocking",
                    message_key="errors.planning.commercial_link.missing_billing_profile",
                )
            )
        else:
            if not profile.shipping_method_code:
                blocking_issues.append(
                    PlanningCommercialIssueRead(
                        code="missing_shipping_method",
                        severity="blocking",
                        message_key="errors.planning.commercial_link.missing_shipping_method",
                    )
                )
            if not profile.invoice_layout_code:
                warning_issues.append(
                    PlanningCommercialIssueRead(
                        code="missing_invoice_layout",
                        severity="warning",
                        message_key="errors.planning.commercial_link.missing_invoice_layout",
                    )
                )

        if default_party is None:
            blocking_issues.append(
                PlanningCommercialIssueRead(
                    code="missing_default_invoice_party",
                    severity="blocking",
                    message_key="errors.planning.commercial_link.missing_default_invoice_party",
                )
            )

        if not active_rate_cards:
            warning_issues.append(
                PlanningCommercialIssueRead(
                    code="missing_active_rate_card",
                    severity="warning",
                    message_key="errors.planning.commercial_link.missing_active_rate_card",
                )
            )

        return PlanningCommercialLinkRead(
            tenant_id=tenant_id,
            customer_id=customer_id,
            order_id=order_id,
            planning_record_id=planning_record_id,
            billing_profile_id=profile.id if profile is not None else None,
            default_invoice_party_id=default_party.id if default_party is not None else None,
            shipping_method_code=profile.shipping_method_code if profile is not None else None,
            invoice_layout_code=profile.invoice_layout_code if profile is not None else None,
            dunning_policy_code=profile.dunning_policy_code if profile is not None else None,
            e_invoice_enabled=bool(profile.e_invoice_enabled) if profile is not None else False,
            rate_card_ids=[row.id for row in active_rate_cards],
            is_release_ready=not blocking_issues,
            blocking_issues=blocking_issues,
            warning_issues=warning_issues,
        )

    @staticmethod
    def _assert_release_ready(link: PlanningCommercialLinkRead) -> None:
        if link.is_release_ready:
            return
        raise ApiException(
            409,
            "planning.commercial_link.prerequisites_missing",
            "errors.planning.commercial_link.prerequisites_missing",
            {"blocking_codes": [issue.code for issue in link.blocking_issues]},
        )

    def _require_order(self, tenant_id: str, order_id: str) -> CustomerOrder:
        row = self.repository.get_customer_order(tenant_id, order_id)
        if row is None:
            raise ApiException(404, "planning.customer_order.not_found", "errors.planning.customer_order.not_found")
        return row

    def _require_planning_record(self, tenant_id: str, planning_record_id: str) -> PlanningRecord:
        row = self.repository.get_planning_record(tenant_id, planning_record_id)
        if row is None:
            raise ApiException(404, "planning.planning_record.not_found", "errors.planning.planning_record.not_found")
        return row
