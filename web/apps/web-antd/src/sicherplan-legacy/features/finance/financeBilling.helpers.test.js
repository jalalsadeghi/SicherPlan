import test from "node:test";
import assert from "node:assert/strict";

import {
  deriveFinanceBillingActionState,
  hasFinanceBillingPermission,
  invoiceDeliveryTone,
  mapFinanceBillingApiMessage,
  summarizeBillingInvoices,
} from "./financeBilling.helpers.js";

test("accounting can queue invoice dispatch after release", () => {
  const state = deriveFinanceBillingActionState(
    "accounting",
    { release_state_code: "released" },
    { invoice_status_code: "released" },
  );
  assert.equal(state.canQueueDispatch, true);
});

test("dispatcher cannot access delivery permission", () => {
  assert.equal(hasFinanceBillingPermission("dispatcher", "finance.billing.delivery"), false);
  assert.equal(hasFinanceBillingPermission("dispatcher", "finance.billing.write"), true);
});

test("message mapping keeps billing validation errors stable", () => {
  assert.equal(mapFinanceBillingApiMessage("errors.finance.invoice.delivery.leitweg_required"), "leitwegRequired");
  assert.equal(mapFinanceBillingApiMessage("errors.platform.internal"), "error");
});

test("invoice delivery tone reflects status severity", () => {
  assert.equal(invoiceDeliveryTone("sent"), "good");
  assert.equal(invoiceDeliveryTone("failed"), "bad");
  assert.equal(invoiceDeliveryTone("not_queued"), "neutral");
});

test("billing summary aggregates released, queued, and e-invoice rows", () => {
  const summary = summarizeBillingInvoices([
    { total_amount: 100, invoice_status_code: "released", delivery_status_code: "queued", e_invoice_enabled: false },
    { total_amount: 50, invoice_status_code: "draft", delivery_status_code: "not_queued", e_invoice_enabled: true },
  ]);
  assert.deepEqual(summary, {
    total: 2,
    released: 1,
    queued: 1,
    eInvoice: 1,
    gross: 150,
  });
});
