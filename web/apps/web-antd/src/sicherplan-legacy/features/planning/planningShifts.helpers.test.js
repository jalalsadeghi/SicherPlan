import test from "node:test";
import assert from "node:assert/strict";

import {
  derivePlanningShiftActionState,
  hasPlanningShiftPermission,
  mapPlanningShiftApiMessage,
  recurrenceLabel,
  visibilitySummary,
} from "./planningShifts.helpers.js";

test("dispatcher has planning shift write access", () => {
  assert.equal(hasPlanningShiftPermission("dispatcher", "planning.shift.write"), true);
  assert.equal(hasPlanningShiftPermission("accounting", "planning.shift.read"), false);
});

test("action state depends on selected entities", () => {
  const state = derivePlanningShiftActionState("dispatcher", { id: "plan-1" }, { id: "series-1" }, { id: "shift-1" });
  assert.equal(state.canCreateSeries, true);
  assert.equal(state.canGenerateSeries, true);
  assert.equal(state.canEditShift, true);
});

test("message mapping and labels are stable", () => {
  assert.equal(mapPlanningShiftApiMessage("errors.planning.shift.copy.duplicate_conflict"), "copyDuplicateConflict");
  assert.equal(recurrenceLabel("weekly"), "weekly");
  assert.deepEqual(
    visibilitySummary({ customer_visible_flag: true, subcontractor_visible_flag: false, stealth_mode_flag: true }),
    { customer: true, subcontractor: false, stealth: true },
  );
});
