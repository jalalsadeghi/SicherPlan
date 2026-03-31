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
  validatePlanningRecordDraft,
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
  assert.equal(mapPlanningOrderApiMessage("errors.planning.planning_record.invalid_window"), "planningInvalidWindow");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.planning_record.order_window_mismatch"), "planningOrderWindowMismatch");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.planning_record.detail_mismatch"), "planningDetailMismatch");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.event_venue.not_found"), "eventVenueNotFound");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.site.not_found"), "siteNotFound");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.trade_fair.not_found"), "tradeFairNotFound");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.trade_fair_zone.not_found"), "tradeFairZoneNotFound");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.patrol_route.not_found"), "patrolRouteNotFound");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.planning_record.parent_mismatch"), "planningParentMismatch");
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
  assert.equal(
    formatPlanningOrderReferenceOption("event_venue", { id: "venue-1", venue_no: "VEN-2", name: "Arena Nord" }),
    "VEN-2 — Arena Nord",
  );
  assert.equal(
    formatPlanningOrderReferenceOption("site", { id: "site-1", site_no: "SITE-4", name: "Werkstor" }),
    "SITE-4 — Werkstor",
  );
  assert.equal(
    formatPlanningOrderReferenceOption("trade_fair", { id: "fair-1", fair_no: "FAIR-9", name: "Expo Ost" }),
    "FAIR-9 — Expo Ost",
  );
  assert.equal(
    formatPlanningOrderReferenceOption("trade_fair_zone", { id: "zone-1", zone_code: "H2-A", label: "Halle 2 A" }),
    "H2-A — Halle 2 A",
  );
  assert.equal(
    formatPlanningOrderReferenceOption("planning_record", {
      id: "plan-1",
      name: "Objektschutz Woche 1",
      planning_from: "2026-04-01",
      planning_to: "2026-04-07",
    }),
    "Objektschutz Woche 1 · 2026-04-01 - 2026-04-07",
  );
  assert.equal(
    formatPlanningOrderReferenceOption("dispatcher_user", {
      id: "user-1",
      full_name: "Max Mustermann",
      username: "m.mustermann",
      email: "max@example.com",
    }),
    "Max Mustermann · m.mustermann",
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

test("planning-record validation enforces order window and mode-specific selectors", () => {
  assert.deepEqual(
    validatePlanningRecordDraft(
      { planning_mode_code: "event", planning_from: "", planning_to: "", event_detail: { event_venue_id: "" } },
      { orderServiceFrom: "2026-05-01", orderServiceTo: "2026-05-31", eventVenueOptions: [] },
    ),
    {
      planning_from: true,
      planning_to: false,
      planning_window: false,
      mode_detail: false,
      messageKey: "planningFromRequired",
    },
  );
  assert.deepEqual(
    validatePlanningRecordDraft(
      { planning_mode_code: "event", planning_from: "2026-05-10", planning_to: "2026-05-05", event_detail: { event_venue_id: "" } },
      { orderServiceFrom: "2026-05-01", orderServiceTo: "2026-05-31", eventVenueOptions: [] },
    ).messageKey,
    "planningInvalidWindow",
  );
  assert.deepEqual(
    validatePlanningRecordDraft(
      { planning_mode_code: "event", planning_from: "2026-04-30", planning_to: "2026-05-05", event_detail: { event_venue_id: "" } },
      { orderServiceFrom: "2026-05-01", orderServiceTo: "2026-05-31", eventVenueOptions: [] },
    ).messageKey,
    "planningOrderWindowMismatch",
  );
  assert.deepEqual(
    validatePlanningRecordDraft(
      { planning_mode_code: "event", planning_from: "2026-05-05", planning_to: "2026-05-06", event_detail: { event_venue_id: "" } },
      { orderServiceFrom: "2026-05-01", orderServiceTo: "2026-05-31", eventVenueOptions: [] },
    ).messageKey,
    "eventVenueSetupBlocked",
  );
  assert.deepEqual(
    validatePlanningRecordDraft(
      { planning_mode_code: "site", planning_from: "2026-05-05", planning_to: "2026-05-06", site_detail: { site_id: "" } },
      { orderServiceFrom: "2026-05-01", orderServiceTo: "2026-05-31", siteOptions: [{ id: "site-1" }] },
    ).messageKey,
    "siteRequired",
  );
  assert.deepEqual(
    validatePlanningRecordDraft(
      { planning_mode_code: "trade_fair", planning_from: "2026-05-05", planning_to: "2026-05-06", trade_fair_detail: { trade_fair_id: "" } },
      { orderServiceFrom: "2026-05-01", orderServiceTo: "2026-05-31", tradeFairOptions: [{ id: "fair-1" }] },
    ).messageKey,
    "tradeFairRequired",
  );
  assert.deepEqual(
    validatePlanningRecordDraft(
      { planning_mode_code: "patrol", planning_from: "2026-05-05", planning_to: "2026-05-06", patrol_detail: { patrol_route_id: "" } },
      { orderServiceFrom: "2026-05-01", orderServiceTo: "2026-05-31", patrolRouteOptions: [{ id: "route-1" }] },
    ).messageKey,
    "patrolRouteRequired",
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
