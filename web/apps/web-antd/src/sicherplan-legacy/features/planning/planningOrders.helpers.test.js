import assert from "node:assert/strict";
import test from "node:test";

import {
  derivePlanningOrderActionState,
  hasPlanningOrderPermission,
  mapPlanningOrderApiMessage,
  planningModeLabel,
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
  assert.equal(mapPlanningOrderApiMessage("errors.planning.planning_record.detail_mismatch"), "planningDetailMismatch");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.planning_record_attachment.scope_mismatch"), "attachmentScopeMismatch");
  assert.equal(mapPlanningOrderApiMessage("errors.planning.commercial_link.prerequisites_missing"), "commercialPrerequisitesMissing");
});

test("planning mode labels stay stable", () => {
  assert.equal(planningModeLabel("trade_fair"), "tradeFair");
  assert.equal(planningModeLabel("patrol"), "patrol");
});
