export const FINANCE_PAYROLL_PERMISSION_MATRIX = {
  platform_admin: ["finance.payroll.read", "finance.payroll.write", "finance.payroll.export"],
  tenant_admin: ["finance.payroll.read", "finance.payroll.write", "finance.payroll.export"],
  accounting: ["finance.payroll.read", "finance.payroll.write", "finance.payroll.export"],
  dispatcher: [],
  controller_qm: [],
  employee_user: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasFinancePayrollPermission(role, permissionKey) {
  return (FINANCE_PAYROLL_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function deriveFinancePayrollActionState(role) {
  const canRead = hasFinancePayrollPermission(role, "finance.payroll.read");
  const canWrite = hasFinancePayrollPermission(role, "finance.payroll.write");
  const canExport = hasFinancePayrollPermission(role, "finance.payroll.export");
  return {
    canRead,
    canWrite,
    canExport,
  };
}

export function mapFinancePayrollApiMessage(messageKey) {
  const map = {
    "errors.iam.auth.invalid_access_token": "authRequired",
    "errors.iam.authorization.permission_denied": "permissionDenied",
    "errors.iam.authorization.scope_denied": "permissionDenied",
    "errors.finance.payroll.tariff_table.not_found": "notFound",
    "errors.finance.payroll.tariff_table.overlap": "tariffOverlap",
    "errors.finance.payroll.tariff_rate.duplicate": "duplicateRate",
    "errors.finance.payroll.surcharge_rule.duplicate": "duplicateSurcharge",
    "errors.finance.payroll.surcharge_rule.window_invalid": "invalidWindow",
    "errors.finance.payroll.surcharge_rule.amount_required": "amountRequired",
    "errors.finance.payroll.pay_profile.overlap": "profileOverlap",
    "errors.finance.payroll.export.no_eligible_actuals": "noEligibleActuals",
    "errors.finance.payroll.export_batch.not_found": "notFound",
  };
  return map[messageKey] ?? "error";
}

export function payrollBatchTone(status) {
  switch (status) {
    case "queued":
    case "dispatched":
      return "good";
    case "generated":
      return "warn";
    case "failed":
      return "bad";
    default:
      return "neutral";
  }
}

export function summarizePayrollReconciliation(rows) {
  return rows.reduce(
    (summary, row) => {
      summary.total += 1;
      if (row.missing_export) {
        summary.missingExport += 1;
      }
      if (row.missing_payslip) {
        summary.missingPayslip += 1;
      }
      summary.exportedAmountTotal += Number(row.exported_amount_total || 0);
      return summary;
    },
    { total: 0, missingExport: 0, missingPayslip: 0, exportedAmountTotal: 0 },
  );
}
