export const REPORTING_PERMISSION_MATRIX = {
  platform_admin: ["reporting.read", "reporting.export"],
  tenant_admin: ["reporting.read", "reporting.export"],
  accounting: ["reporting.read", "reporting.export"],
  controller_qm: ["reporting.read", "reporting.export"],
  dispatcher: ["reporting.read"],
  employee_user: [],
  customer_user: [],
  subcontractor_user: [],
};

export const REPORTING_REPORT_KEYS = [
  "compliance-status",
  "notice-read-stats",
  "free-sundays",
  "absence-visibility",
  "inactivity-signals",
  "security-activity",
  "employee-activity",
  "customer-revenue",
  "subcontractor-control",
  "planning-performance",
  "payroll-basis",
  "customer-profitability",
];

export const REPORTING_DELIVERY_KEYS = [
  "compliance-status",
  "notice-read-stats",
  "free-sundays",
  "absence-visibility",
  "inactivity-signals",
  "security-activity",
];

export function hasReportingPermission(role, permissionKey) {
  return (REPORTING_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function deriveReportingActionState(role, reportKey) {
  const canRead = hasReportingPermission(role, "reporting.read");
  const canExport = hasReportingPermission(role, "reporting.export");
  return {
    canRead,
    canExport,
    canRefresh: canRead && REPORTING_REPORT_KEYS.includes(reportKey),
    canDownload: canExport && REPORTING_REPORT_KEYS.includes(reportKey),
    canQueueDelivery: canExport && REPORTING_DELIVERY_KEYS.includes(reportKey),
  };
}

export function mapReportingApiMessage(messageKey) {
  const map = {
    "errors.iam.auth.invalid_access_token": "authRequired",
    "errors.iam.authorization.permission_denied": "permissionDenied",
    "errors.iam.authorization.scope_denied": "permissionDenied",
    "errors.reporting.report.not_found": "reportNotFound",
    "errors.reporting.delivery.report_not_supported": "deliveryNotSupported",
    "errors.reporting.delivery.unavailable": "deliveryUnavailable",
    "errors.integration.endpoint.not_found": "deliveryEndpointMissing",
  };
  return map[messageKey] ?? "error";
}

export function summarizeReportingRows(rows, numericField) {
  return rows.reduce(
    (summary, row) => {
      summary.total += 1;
      summary.amount += Number(row[numericField] || 0);
      return summary;
    },
    { total: 0, amount: 0 },
  );
}

export function deliveryStatusTone(status) {
  if (status === "completed" || status === "published") {
    return "good";
  }
  if (status === "failed") {
    return "bad";
  }
  return "neutral";
}
