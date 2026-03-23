import test from "node:test";
import assert from "node:assert/strict";

import {
  REPORTING_DELIVERY_KEYS,
  REPORTING_REPORT_KEYS,
  deliveryStatusTone,
  deriveReportingActionState,
  hasReportingPermission,
  mapReportingApiMessage,
  summarizeReportingRows,
} from "./reporting.helpers.js";

test("reporting permissions expose export only to allowed roles", () => {
  assert.equal(hasReportingPermission("accounting", "reporting.export"), true);
  assert.equal(hasReportingPermission("controller_qm", "reporting.export"), true);
  assert.equal(hasReportingPermission("dispatcher", "reporting.export"), false);
});

test("reporting action state respects role and known reports", () => {
  const state = deriveReportingActionState("controller_qm", "compliance-status");
  assert.equal(state.canRead, true);
  assert.equal(state.canDownload, true);
  assert.equal(state.canRefresh, true);
  assert.equal(state.canQueueDelivery, true);
  assert.equal(REPORTING_REPORT_KEYS.includes("customer-profitability"), true);
  assert.equal(REPORTING_DELIVERY_KEYS.includes("security-activity"), true);
});

test("reporting api messages are mapped deterministically", () => {
  assert.equal(mapReportingApiMessage("errors.reporting.report.not_found"), "reportNotFound");
  assert.equal(mapReportingApiMessage("errors.reporting.delivery.report_not_supported"), "deliveryNotSupported");
  assert.equal(mapReportingApiMessage("errors.platform.internal"), "error");
});

test("reporting summaries total numeric fields", () => {
  const summary = summarizeReportingRows([{ total_amount: 10 }, { total_amount: 20 }], "total_amount");
  assert.deepEqual(summary, { total: 2, amount: 30 });
});

test("delivery status tone stays stable", () => {
  assert.equal(deliveryStatusTone("completed"), "good");
  assert.equal(deliveryStatusTone("failed"), "bad");
  assert.equal(deliveryStatusTone("requested"), "neutral");
});
