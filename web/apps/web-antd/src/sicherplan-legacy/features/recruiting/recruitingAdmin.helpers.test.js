import test from "node:test";
import assert from "node:assert/strict";

import {
  canAccessRecruitingAdmin,
  deriveNextActionDescriptors,
  formatApplicantLabel,
  hasRecruitingPermission,
  mapRecruitingApiMessage,
  requiresTransitionConfirmation,
} from "./recruitingAdmin.helpers.js";

test("only platform and tenant admins have recruiting permissions", () => {
  assert.equal(hasRecruitingPermission("tenant_admin", "recruiting.applicant.read"), true);
  assert.equal(hasRecruitingPermission("platform_admin", "recruiting.applicant.write"), true);
  assert.equal(hasRecruitingPermission("dispatcher", "recruiting.applicant.read"), false);
});

test("recruiting admin access requires both session and permission", () => {
  assert.equal(canAccessRecruitingAdmin("tenant_admin", true), true);
  assert.equal(canAccessRecruitingAdmin("tenant_admin", false), false);
  assert.equal(canAccessRecruitingAdmin("accounting", true), false);
});

test("next action descriptors expose required fields for sensitive transitions", () => {
  const actions = deriveNextActionDescriptors(["accepted", "interview_scheduled", "ready_for_conversion"]);

  assert.deepEqual(actions.map((item) => item.status), ["accepted", "interview_scheduled", "ready_for_conversion"]);
  assert.equal(actions[0].requiresDecisionReason, true);
  assert.equal(actions[1].requiresInterviewSchedule, true);
  assert.equal(actions[2].requiresHiringTargetDate, true);
});

test("acceptance and rejection require explicit confirmation in the UI", () => {
  assert.equal(requiresTransitionConfirmation("accepted"), true);
  assert.equal(requiresTransitionConfirmation("rejected"), true);
  assert.equal(requiresTransitionConfirmation("interview_scheduled"), false);
});

test("applicant label prefers first and last name", () => {
  assert.equal(formatApplicantLabel({ first_name: "Anna", last_name: "Wagner" }), "Anna Wagner");
});

test("api message keys map to recruiter feedback keys", () => {
  assert.equal(
    mapRecruitingApiMessage("errors.recruiting.applicant.transition_not_allowed"),
    "recruitingAdmin.feedback.transitionNotAllowed",
  );
  assert.equal(
    mapRecruitingApiMessage("errors.recruiting.applicant.converted_employee_missing"),
    "recruitingAdmin.feedback.conversionMissing",
  );
  assert.equal(mapRecruitingApiMessage("errors.platform.internal"), "recruitingAdmin.feedback.error");
});
