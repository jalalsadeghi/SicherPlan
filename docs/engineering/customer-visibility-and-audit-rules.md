# Customer Visibility And Audit Rules

- Internal CRM endpoints under `/api/customers/...` are for internal tenant roles only. Platform admins are allowed platform-wide; tenant-scoped internal roles require a tenant scope and the `customers.customer.read` or `customers.customer.write` permission as applicable.
- Portal roles (`customer_user`, `subcontractor_user`, `employee_user`) are intentionally rejected by the internal customer master-data API even if a permission is misconfigured later. Customer-facing access must go through dedicated portal read models in `US-9-*`.
- Customer portal visibility must remain explicit and association-driven. Future customer-facing access must use role/user/customer scope associations, not ad hoc request parameters.
- Archived customers are hidden from list endpoints by default, remain available through detail reads for authorized internal users, and can be included explicitly with `include_archived=true`.
- Durable audit events are emitted for customer, contact, address, portal-link, lifecycle, import, export, and vCard actions. These audit events complement the customer-facing history log; they do not replace it.
- Bulk import/export audit events record actor, tenant, job/document context, and row/result summaries without persisting secrets or raw bearer material.
- Privacy boundary for later portal work: customer-facing views must hide personal names by default unless the tenant explicitly releases that disclosure.
