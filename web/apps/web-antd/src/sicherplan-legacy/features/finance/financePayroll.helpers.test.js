import test from "node:test";
import assert from "node:assert/strict";

import {
  deriveFinancePayrollActionState,
  hasFinancePayrollPermission,
  mapFinancePayrollApiMessage,
  payrollBatchTone,
  summarizePayrollReconciliation,
} from "./financePayroll.helpers.js";

test("finance payroll permissions stay finance-only", () => {
  assert.equal(hasFinancePayrollPermission("accounting", "finance.payroll.read"), true);
  assert.equal(hasFinancePayrollPermission("dispatcher", "finance.payroll.read"), false);
  assert.deepEqual(deriveFinancePayrollActionState("accounting"), { canRead: true, canWrite: true, canExport: true });
});

test("finance payroll message mapping resolves known backend keys", () => {
  assert.equal(mapFinancePayrollApiMessage("errors.finance.payroll.tariff_table.overlap"), "tariffOverlap");
  assert.equal(mapFinancePayrollApiMessage("errors.finance.payroll.export.no_eligible_actuals"), "noEligibleActuals");
  assert.equal(mapFinancePayrollApiMessage("errors.platform.internal"), "error");
});

test("finance payroll reconciliation summary counts missing exports and payslips", () => {
  const summary = summarizePayrollReconciliation([
    { missing_export: true, missing_payslip: false, exported_amount_total: 120 },
    { missing_export: false, missing_payslip: true, exported_amount_total: 80 },
  ]);
  assert.deepEqual(summary, {
    total: 2,
    missingExport: 1,
    missingPayslip: 1,
    exportedAmountTotal: 200,
  });
  assert.equal(payrollBatchTone("queued"), "good");
  assert.equal(payrollBatchTone("failed"), "bad");
});
