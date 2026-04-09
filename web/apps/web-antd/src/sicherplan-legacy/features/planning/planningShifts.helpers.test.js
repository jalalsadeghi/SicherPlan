import test from "node:test";
import assert from "node:assert/strict";

import {
  buildShiftTypeOptions,
  addDaysToIsoDate,
  buildShiftCopyPayload,
  DEFAULT_SHIFT_TYPE_OPTIONS,
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
  assert.equal(mapPlanningShiftApiMessage("errors.planning.shift.visibility_requires_release"), "visibilityRequiresRelease");
  assert.equal(recurrenceLabel("weekly"), "weekly");
  assert.deepEqual(
    visibilitySummary({ customer_visible_flag: true, subcontractor_visible_flag: false, stealth_mode_flag: true }),
    { customer: true, subcontractor: false, stealth: true },
  );
});

test("copy payload spans full requested range", () => {
  assert.equal(addDaysToIsoDate("2026-04-10", 6), "2026-04-16");
  assert.deepEqual(buildShiftCopyPayload("2026-04-10", 7), {
    source_from: "2026-04-10",
    source_to: "2026-04-16",
    target_from: "2026-04-17",
    duplicate_mode: "skip_existing",
  });
});

test("shift type options keep legacy values editable and fall back to defaults", () => {
  assert.deepEqual(buildShiftTypeOptions([], "", "(legacy)"), DEFAULT_SHIFT_TYPE_OPTIONS);
  assert.deepEqual(buildShiftTypeOptions([{ code: "site_day", label: "Site Day" }], "legacy_code", "(legacy)"), [
    { code: "site_day", label: "Site Day" },
    { code: "legacy_code", label: "legacy_code (legacy)" },
  ]);
});
