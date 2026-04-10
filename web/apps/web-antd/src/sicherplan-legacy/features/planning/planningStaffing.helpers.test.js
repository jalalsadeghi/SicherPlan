import test from "node:test";
import assert from "node:assert/strict";

import {
  actorLabel,
  buildStaffingMemberOptions,
  coverageTone,
  dispatchAudienceLabel,
  derivePlanningStaffingActionState,
  hasPlanningStaffingPermission,
  mapPlanningStaffingApiMessage,
  releaseTone,
  resolveSelectedDemandGroupId,
  summarizeCoverage,
  summarizeValidations,
  validationTone,
} from "./planningStaffing.helpers.js";

test("dispatcher has planning staffing read/write/override permissions", () => {
  assert.equal(hasPlanningStaffingPermission("dispatcher", "planning.staffing.read"), true);
  assert.equal(hasPlanningStaffingPermission("dispatcher", "planning.staffing.write"), true);
  assert.equal(hasPlanningStaffingPermission("dispatcher", "planning.staffing.override"), true);
});

test("action state derives override affordance from backend rule metadata", () => {
  const empty = derivePlanningStaffingActionState("dispatcher", null, null, null);
  assert.equal(empty.canInspectDetails, false);
  assert.equal(empty.canRecordOverride, false);
  assert.equal(empty.canAssign, false);

  const selected = derivePlanningStaffingActionState(
    "dispatcher",
    { shift_id: "shift-1" },
    { id: "assignment-1" },
    { rule_code: "certificate_validity", override_allowed: true },
  );
  assert.equal(selected.canInspectDetails, true);
  assert.equal(selected.canInspectAssignments, true);
  assert.equal(selected.canRecordOverride, true);
  assert.equal(selected.canManageRelease, true);
  assert.equal(selected.canDispatch, true);
  assert.equal(selected.canAssign, true);
  assert.equal(selected.canUnassign, true);
  assert.equal(selected.canSubstitute, true);
});

test("controller_qm keeps no staffing permissions in the helper layer", () => {
  assert.equal(hasPlanningStaffingPermission("controller_qm", "planning.staffing.read"), false);
  assert.equal(hasPlanningStaffingPermission("controller_qm", "planning.staffing.write"), false);
  assert.equal(hasPlanningStaffingPermission("controller_qm", "planning.staffing.override"), false);
});

test("coverage and validation tones stay derived from normalized states", () => {
  assert.equal(coverageTone("green"), "good");
  assert.equal(coverageTone("yellow"), "warn");
  assert.equal(coverageTone("red"), "bad");
  assert.equal(validationTone("block"), "bad");
  assert.equal(validationTone("warn"), "warn");
  assert.equal(validationTone("info"), "neutral");
  assert.equal(releaseTone("released"), "good");
  assert.equal(releaseTone("release_ready"), "warn");
  assert.equal(releaseTone("draft"), "neutral");
});

test("coverage and validation summaries remain thin client helpers", () => {
  assert.deepEqual(
    summarizeCoverage([{ coverage_state: "green" }, { coverage_state: "yellow" }, { coverage_state: "red" }]),
    { green: 1, red: 1, total: 3, yellow: 1 },
  );
  assert.deepEqual(
    summarizeValidations({
      issues: [
        { severity: "block", override_allowed: true },
        { severity: "warn", override_allowed: false },
        { severity: "info", override_allowed: false },
      ],
    }),
    { blocking: 1, warnings: 1, infos: 1, overrideable: 1 },
  );
});

test("api message mapping keeps auth, release, and override states explicit", () => {
  assert.equal(mapPlanningStaffingApiMessage("errors.iam.auth.invalid_access_token"), "authRequired");
  assert.equal(mapPlanningStaffingApiMessage("errors.planning.shift.blocked_by_validation"), "releaseBlocked");
  assert.equal(mapPlanningStaffingApiMessage("errors.planning.assignment_validation.override_not_allowed"), "overrideNotAllowed");
  assert.equal(mapPlanningStaffingApiMessage("errors.planning.communication.no_recipients"), "dispatchNoRecipients");
  assert.equal(mapPlanningStaffingApiMessage("errors.planning.assignment.stale_version"), "assignmentStaleVersion");
  assert.equal(mapPlanningStaffingApiMessage("errors.platform.internal"), "error");
});

test("actor labels distinguish internal and partner actors", () => {
  assert.equal(actorLabel({ employee_id: "emp-1", subcontractor_worker_id: null }), "employee:emp-1");
  assert.equal(actorLabel({ employee_id: null, subcontractor_worker_id: "worker-2" }), "worker:worker-2");
  assert.equal(dispatchAudienceLabel("assigned_employees"), "employees");
});

test("team-member options stay scoped to the selected team", () => {
  const members = [
    { id: "m-1", team_id: "team-1" },
    { id: "m-2", team_id: "team-2" },
  ];
  assert.deepEqual(buildStaffingMemberOptions(members, "team-1"), [{ id: "m-1", team_id: "team-1" }]);
});

test("selected demand group falls back safely to the first visible row", () => {
  assert.equal(
    resolveSelectedDemandGroupId(
      { demand_groups: [{ id: "dg-1" }, { id: "dg-2" }] },
      "missing",
    ),
    "dg-1",
  );
});
