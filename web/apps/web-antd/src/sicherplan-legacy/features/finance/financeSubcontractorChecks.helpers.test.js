import test from "node:test";
import assert from "node:assert/strict";

import {
  deriveFinanceSubcontractorControlState,
  invoiceCheckStatusTone,
  mapFinanceSubcontractorControlApiMessage,
  summarizeInvoiceChecks,
} from "./financeSubcontractorChecks.helpers.js";

test("deriveFinanceSubcontractorControlState exposes release action only for approved checks", () => {
  const approved = deriveFinanceSubcontractorControlState("accounting", { status_code: "approved" });
  const draft = deriveFinanceSubcontractorControlState("accounting", { status_code: "draft" });
  assert.equal(approved.canRelease, true);
  assert.equal(draft.canRelease, false);
});

test("mapFinanceSubcontractorControlApiMessage maps rate and status errors", () => {
  assert.equal(mapFinanceSubcontractorControlApiMessage("errors.finance.subcontractor_invoice_check.rate.not_found"), "missingRate");
  assert.equal(mapFinanceSubcontractorControlApiMessage("errors.finance.subcontractor_invoice_check.invalid_status"), "invalidStatus");
});

test("summarizeInvoiceChecks counts release and review buckets", () => {
  const summary = summarizeInvoiceChecks([
    { status_code: "released", approved_amount_total: "10.00" },
    { status_code: "review_required", approved_amount_total: "12.50" },
    { status_code: "exception", approved_amount_total: "0.00" },
  ]);
  assert.equal(summary.total, 3);
  assert.equal(summary.released, 1);
  assert.equal(summary.reviewRequired, 1);
  assert.equal(summary.exceptions, 1);
  assert.equal(summary.approvedAmount, 22.5);
});

test("invoiceCheckStatusTone marks review and exception distinctly", () => {
  assert.equal(invoiceCheckStatusTone("review_required"), "warn");
  assert.equal(invoiceCheckStatusTone("exception"), "bad");
});
