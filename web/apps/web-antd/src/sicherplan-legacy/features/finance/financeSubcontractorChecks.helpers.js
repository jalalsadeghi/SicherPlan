export const FINANCE_SUBCONTRACTOR_CONTROL_PERMISSION_MATRIX = {
  platform_admin: ["finance.subcontractor_control.read", "finance.subcontractor_control.write"],
  tenant_admin: ["finance.subcontractor_control.read", "finance.subcontractor_control.write"],
  accounting: ["finance.subcontractor_control.read", "finance.subcontractor_control.write"],
  controller_qm: ["finance.subcontractor_control.read", "finance.subcontractor_control.write"],
  dispatcher: ["finance.subcontractor_control.read"],
  employee_user: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasFinanceSubcontractorControlPermission(role, permissionKey) {
  return (FINANCE_SUBCONTRACTOR_CONTROL_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function deriveFinanceSubcontractorControlState(role, selectedCheck) {
  const canRead = hasFinanceSubcontractorControlPermission(role, "finance.subcontractor_control.read");
  const canWrite = hasFinanceSubcontractorControlPermission(role, "finance.subcontractor_control.write");
  const status = selectedCheck?.status_code ?? "draft";
  return {
    canRead,
    canWrite,
    canRefresh: canRead,
    canGenerate: canWrite,
    canNote: canWrite && !!selectedCheck,
    canApprove: canWrite && !!selectedCheck && ["draft", "review_required", "exception"].includes(status),
    canException: canWrite && !!selectedCheck && ["draft", "review_required", "approved"].includes(status),
    canRelease: canWrite && !!selectedCheck && status === "approved",
  };
}

export function mapFinanceSubcontractorControlApiMessage(messageKey) {
  const map = {
    "errors.iam.auth.invalid_access_token": "authRequired",
    "errors.iam.authorization.permission_denied": "permissionDenied",
    "errors.iam.authorization.scope_denied": "permissionDenied",
    "errors.finance.subcontractor_invoice_check.not_found": "notFound",
    "errors.finance.subcontractor_invoice_check.invalid_status": "invalidStatus",
    "errors.finance.subcontractor_invoice_check.period.invalid": "invalidPeriod",
    "errors.finance.subcontractor_invoice_check.rate.not_found": "missingRate",
    "errors.finance.subcontractor_invoice_check.rate.ambiguous": "ambiguousRate",
  };
  return map[messageKey] ?? "error";
}

export function invoiceCheckStatusTone(status) {
  switch (status) {
    case "released":
      return "good";
    case "approved":
      return "good";
    case "exception":
      return "bad";
    case "review_required":
      return "warn";
    default:
      return "neutral";
  }
}

export function summarizeInvoiceChecks(rows) {
  return rows.reduce(
    (summary, row) => {
      summary.total += 1;
      summary.approvedAmount += Number(row.approved_amount_total || 0);
      if (row.status_code === "released") {
        summary.released += 1;
      }
      if (row.status_code === "review_required") {
        summary.reviewRequired += 1;
      }
      if (row.status_code === "exception") {
        summary.exceptions += 1;
      }
      return summary;
    },
    { total: 0, released: 0, reviewRequired: 0, exceptions: 0, approvedAmount: 0 },
  );
}
