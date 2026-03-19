"""Contract-first customer-portal read models for released outputs."""

from __future__ import annotations

from app.modules.customers.schemas import (
    CustomerPortalCollectionSourceRead,
    CustomerPortalContextRead,
    CustomerPortalOrderCollectionRead,
    CustomerPortalReportPackageCollectionRead,
    CustomerPortalScheduleCollectionRead,
    CustomerPortalTimesheetCollectionRead,
    CustomerPortalWatchbookCollectionRead,
)


class CustomerPortalReadService:
    def list_orders(self, context: CustomerPortalContextRead) -> CustomerPortalOrderCollectionRead:
        return CustomerPortalOrderCollectionRead(
            customer_id=context.customer_id,
            source=self._build_source(
                domain_key="orders",
                source_module_key="planning",
                message_key="portalCustomer.datasets.orders.pending",
            ),
        )

    def list_schedules(self, context: CustomerPortalContextRead) -> CustomerPortalScheduleCollectionRead:
        return CustomerPortalScheduleCollectionRead(
            customer_id=context.customer_id,
            source=self._build_source(
                domain_key="schedules",
                source_module_key="planning",
                message_key="portalCustomer.datasets.schedules.pending",
            ),
        )

    def list_watchbook_entries(
        self,
        context: CustomerPortalContextRead,
    ) -> CustomerPortalWatchbookCollectionRead:
        return CustomerPortalWatchbookCollectionRead(
            customer_id=context.customer_id,
            source=self._build_source(
                domain_key="watchbooks",
                source_module_key="field_execution",
                message_key="portalCustomer.datasets.watchbooks.pending",
            ),
        )

    def list_timesheets(self, context: CustomerPortalContextRead) -> CustomerPortalTimesheetCollectionRead:
        return CustomerPortalTimesheetCollectionRead(
            customer_id=context.customer_id,
            source=self._build_source(
                domain_key="timesheets",
                source_module_key="finance",
                docs_backed_outputs=True,
                message_key="portalCustomer.datasets.timesheets.pending",
            ),
        )

    def list_report_packages(
        self,
        context: CustomerPortalContextRead,
    ) -> CustomerPortalReportPackageCollectionRead:
        return CustomerPortalReportPackageCollectionRead(
            customer_id=context.customer_id,
            source=self._build_source(
                domain_key="reports",
                source_module_key="reporting",
                docs_backed_outputs=True,
                message_key="portalCustomer.datasets.reports.pending",
            ),
        )

    def _build_source(
        self,
        *,
        domain_key: str,
        source_module_key: str,
        message_key: str,
        docs_backed_outputs: bool = False,
    ) -> CustomerPortalCollectionSourceRead:
        return CustomerPortalCollectionSourceRead(
            domain_key=domain_key,
            source_module_key=source_module_key,
            availability_status="pending_source_module",
            released_only=True,
            customer_scoped=True,
            docs_backed_outputs=docs_backed_outputs,
            message_key=message_key,
        )
