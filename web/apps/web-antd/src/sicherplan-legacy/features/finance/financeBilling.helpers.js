export const FINANCE_BILLING_PERMISSION_MATRIX = {
  platform_admin: ["finance.billing.read", "finance.billing.write", "finance.billing.delivery"],
  tenant_admin: ["finance.billing.read", "finance.billing.write", "finance.billing.delivery"],
  dispatcher: ["finance.billing.read", "finance.billing.write"],
  accounting: ["finance.billing.read", "finance.billing.write", "finance.billing.delivery"],
  controller_qm: ["finance.billing.read"],
  employee_user: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasFinanceBillingPermission(role, permissionKey) {
  return (FINANCE_BILLING_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function deriveFinanceBillingActionState(role, selectedTimesheet, selectedInvoice) {
  const canRead = hasFinanceBillingPermission(role, "finance.billing.read");
  const canWrite = hasFinanceBillingPermission(role, "finance.billing.write");
  const canDeliver = hasFinanceBillingPermission(role, "finance.billing.delivery");
  const invoiceStage = selectedInvoice?.invoice_status_code ?? "draft";
  return {
    canRead,
    canWrite,
    canDeliver,
    canRefresh: canRead,
    canGenerateTimesheet: canWrite,
    canReleaseTimesheet: canWrite && !!selectedTimesheet && selectedTimesheet.release_state_code !== "released",
    canGenerateInvoice: canWrite && !!selectedTimesheet && selectedTimesheet.release_state_code === "released",
    canIssueInvoice: canWrite && !!selectedInvoice && invoiceStage === "draft",
    canReleaseInvoice: canWrite && !!selectedInvoice && ["issued", "queued", "released", "sent"].includes(invoiceStage),
    canQueueDispatch: canDeliver && !!selectedInvoice && ["issued", "released"].includes(invoiceStage),
  };
}

export function mapFinanceBillingApiMessage(messageKey) {
  const map = {
    "errors.iam.auth.invalid_access_token": "authRequired",
    "errors.iam.authorization.permission_denied": "permissionDenied",
    "errors.iam.authorization.scope_denied": "permissionDenied",
    "errors.finance.timesheet.not_found": "timesheetNotFound",
    "errors.finance.timesheet.no_eligible_actuals": "timesheetNoActuals",
    "errors.finance.invoice.not_found": "invoiceNotFound",
    "errors.finance.invoice.timesheet.not_released": "timesheetNotReleased",
    "errors.finance.invoice.rate_card.not_found": "rateCardMissing",
    "errors.finance.invoice.no_billable_lines": "noBillableLines",
    "errors.finance.invoice.invalid_stage": "invalidStage",
    "errors.finance.invoice.delivery.e_invoice_required": "eInvoiceRequired",
    "errors.finance.invoice.delivery.leitweg_required": "leitwegRequired",
    "errors.finance.invoice.delivery.email_required": "emailRequired",
  };
  return map[messageKey] ?? "error";
}

export function invoiceDeliveryTone(status) {
  switch (status) {
    case "sent":
      return "good";
    case "queued":
      return "warn";
    case "failed":
      return "bad";
    default:
      return "neutral";
  }
}

export function summarizeBillingInvoices(rows) {
  return rows.reduce(
    (summary, row) => {
      summary.total += 1;
      summary.gross += Number(row.total_amount || 0);
      if (row.invoice_status_code === "released" || row.invoice_status_code === "queued" || row.invoice_status_code === "sent") {
        summary.released += 1;
      }
      if (row.delivery_status_code === "queued") {
        summary.queued += 1;
      }
      if (row.e_invoice_enabled) {
        summary.eInvoice += 1;
      }
      return summary;
    },
    { total: 0, released: 0, queued: 0, eInvoice: 0, gross: 0 },
  );
}
