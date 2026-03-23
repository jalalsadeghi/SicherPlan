import test from "node:test";
import assert from "node:assert/strict";

import {
  buildPlanningImportTemplate,
  derivePlanningActionState,
  mapPlanningApiMessage,
} from "./planningAdmin.helpers.js";

test("derivePlanningActionState grants dispatcher planning write access", () => {
  const state = derivePlanningActionState("dispatcher", "site", { id: "1" });
  assert.equal(state.canRead, true);
  assert.equal(state.canWrite, true);
  assert.equal(state.canManageChildren, false);
});

test("derivePlanningActionState enables child editing for fair and route records", () => {
  assert.equal(derivePlanningActionState("tenant_admin", "trade_fair", { id: "1" }).canManageChildren, true);
  assert.equal(derivePlanningActionState("tenant_admin", "patrol_route", { id: "1" }).canManageChildren, true);
});

test("buildPlanningImportTemplate returns stable CSV headers", () => {
  assert.equal(
    buildPlanningImportTemplate("site"),
    "customer_id,site_no,name,address_id,timezone,latitude,longitude,watchbook_enabled,notes,status",
  );
});

test("mapPlanningApiMessage maps import and duplicate errors", () => {
  assert.equal(mapPlanningApiMessage("errors.planning.import.invalid_headers"), "invalidImportHeaders");
  assert.equal(mapPlanningApiMessage("errors.planning.patrol_checkpoint.duplicate_sequence"), "duplicateChild");
});
