import assert from "node:assert/strict";
import test from "node:test";

import {
  buildCustomerCommercialLocation,
  buildPlanningSetupLocation,
  derivePlanningOrderSubmitBlockReason,
  derivePlanningOrderActionState,
  filterPlanningOrderOptionsByCustomer,
  formatPlanningCommercialIssueFallback,
  formatPlanningOrderReferenceOption,
  hasPlanningOrderSetupGap,
  hasPlanningOrderPermission,
  mapPlanningCommercialIssueCode,
  mapPlanningOrderApiMessage,
  normalizePlanningOrderUuidValue,
  planningModeLabel,
  validatePlanningOrderDraft,
} from "./planningOrders.helpers.js";

test("dispatcher can manage orders and planning records", () => {
  assert.equal(hasPlanningOrderPermission("dispatcher", "planning.order.write"), true);
  assert.equal(hasPlanningOrderPermission("dispatcher", "planning.record.write"), true);
  assert.equal(hasPlanningOrderPermission("accounting", "planning.order.read"), false);
});

test("action state follows selected order and planning record", () => {
  const state = derivePlanningOrderActionState("tenant_admin", { id: "order-1" }, { id: "plan-1" });
  assert.equal(state.canCreateOrder, true);
  assert.equal(state.canEditOrder, true);
  assert.equal(state.canCreatePlanning, true);
  assert.equal(state.canEditPlanning, true);
  assert.equal(state.canManagePlanningDocs, true);
});

test("api message mapping covers planning-specific errors", () => {
  assert.equal(mapPlanningOrderApiMessage("errors.planning.customer_order.duplicate_number"), "orderDuplicateNumber");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.customer_order.invalid_requirement_type_id"), "requirementTypeRequired");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.requirement_type.duplicate_code"), "planningSetupDuplicateCode");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.planning_record.detail_mismatch"), "planningDetailMismatch");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.planning_record_attachment.scope_mismatch"), "attachmentScopeMismatch");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.commercial_link.prerequisites_missing"), "commercialPrerequisitesMissing");
});

test("planning mode labels stay stable", () => {
  assert.equal(planningModeLabel("trade_fair"), "tradeFair");
  assert.equal(planningModeLabel("patrol"), "patrol");
});

test("planning-order reference options use business labels", () => {
  assert.equal(
    formatPlanningOrderReferenceOption("requirement_type", { id: "req-1", code: "REQ-1", label: "Objektschutz" }),
    "REQ-1 — Objektschutz",
  );
  assert.equal(
    formatPlanningOrderReferenceOption("patrol_route", { id: "route-1", route_no: "R-7", name: "Nachtstreife" }),
    "R-7 — Nachtstreife",
  );
});

test("planning-order reference options can be filtered by customer", () => {
  const rows = [
    { id: "req-1", customer_id: "customer-1" },
    { id: "req-2", customer_id: "customer-2" },
  ];
  assert.deepEqual(filterPlanningOrderOptionsByCustomer(rows, "customer-1"), [{ id: "req-1", customer_id: "customer-1" }]);
  assert.deepEqual(filterPlanningOrderOptionsByCustomer(rows, ""), rows);
});

test("planning-order UUID normalization turns blank values into null", () => {
  assert.equal(normalizePlanningOrderUuidValue(""), null);
  assert.equal(normalizePlanningOrderUuidValue("   "), null);
  assert.equal(normalizePlanningOrderUuidValue("route-1"), "route-1");
});

test("planning-order draft validation blocks missing required selects only", () => {
  assert.deepEqual(
    validatePlanningOrderDraft({ customer_id: "", requirement_type_id: "" }),
    { customer_id: true, requirement_type_id: true },
  );
  assert.deepEqual(
    validatePlanningOrderDraft({ customer_id: "customer-1", requirement_type_id: "" }),
    { customer_id: false, requirement_type_id: true },
  );
  assert.deepEqual(
    validatePlanningOrderDraft({ customer_id: "customer-1", requirement_type_id: "req-1", patrol_route_id: "" }),
    { customer_id: false, requirement_type_id: false },
  );
});

test("planning-order detects missing prerequisite setup data for selected customer", () => {
  assert.equal(
    hasPlanningOrderSetupGap({ customerId: "customer-1", options: [], loading: false, error: "" }),
    true,
  );
  assert.equal(
    hasPlanningOrderSetupGap({ customerId: "customer-1", options: [], loading: true, error: "" }),
    false,
  );
  assert.equal(
    hasPlanningOrderSetupGap({ customerId: "", options: [], loading: false, error: "" }),
    false,
  );
});

test("planning-order submit block reason distinguishes missing setup from missing selection", () => {
  assert.equal(
    derivePlanningOrderSubmitBlockReason(
      { customer_id: "customer-1", requirement_type_id: "" },
      { requirementTypeSetupMissing: true },
    ),
    "requirementTypeSetupBlocked",
  );
  assert.equal(
    derivePlanningOrderSubmitBlockReason(
      { customer_id: "customer-1", requirement_type_id: "" },
      { requirementTypeSetupMissing: false },
    ),
    "requirementTypeRequired",
  );
});

test("planning-order builds planning-setup deep links with customer context", () => {
  assert.deepEqual(
    buildPlanningSetupLocation("requirement_type", "customer-1"),
    { path: "/admin/planning", query: { entity: "requirement_type", customer_id: "customer-1" } },
  );
  assert.deepEqual(
    buildPlanningSetupLocation("patrol_route", ""),
    { path: "/admin/planning", query: { entity: "patrol_route" } },
  );
});

test("planning-order commercial issues map known codes and fall back cleanly", () => {
  assert.equal(mapPlanningCommercialIssueCode("missing_billing_profile"), "commercialIssueMissingBillingProfile");
  assert.equal(mapPlanningCommercialIssueCode("missing_default_invoice_party"), "commercialIssueMissingDefaultInvoiceParty");
  assert.equal(mapPlanningCommercialIssueCode("missing_active_rate_card"), "commercialIssueMissingActiveRateCard");
  assert.equal(mapPlanningCommercialIssueCode("unknown_issue_code"), null);
  assert.equal(formatPlanningCommercialIssueFallback("missing_credit_limit"), "Missing Credit Limit");
  assert.equal(formatPlanningCommercialIssueFallback(""), "");
});

test("planning-order can deep link into customer commercial settings", () => {
  assert.deepEqual(
    buildCustomerCommercialLocation("customer-1"),
    { path: "/admin/customers", query: { tab: "commercial", customer_id: "customer-1" } },
  );
  assert.deepEqual(
    buildCustomerCommercialLocation(""),
    { path: "/admin/customers", query: { tab: "commercial" } },
  );
});
