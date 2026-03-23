import test from "node:test";
import assert from "node:assert/strict";

import {
  approvalStageTone,
  deriveFinanceActualActionState,
  hasFinanceActualPermission,
  mapFinanceActualApiMessage,
  summarizeActuals,
} from "./financeActuals.helpers.js";

test("dispatcher can confirm but not finance-signoff", () => {
  const state = deriveFinanceActualActionState("dispatcher", { approval_stage_code: "operational_confirmed" });
  assert.equal(state.canApprove, true);
  assert.equal(state.canFinanceSignoff, false);
});

test("message mapping keeps explicit finance approval errors stable", () => {
  assert.equal(mapFinanceActualApiMessage("errors.finance.actual.approval.invalid_stage"), "invalidStage");
  assert.equal(mapFinanceActualApiMessage("errors.platform.internal"), "error");
});

test("summary counts actuals by approval stage", () => {
  const summary = summarizeActuals([
    { approval_stage_code: "draft" },
    { approval_stage_code: "preliminary_submitted" },
    { approval_stage_code: "operational_confirmed" },
    { approval_stage_code: "finance_signed_off" },
  ]);
  assert.deepEqual(summary, {
    draft: 1,
    financeSignedOff: 1,
    operationalConfirmed: 1,
    preliminarySubmitted: 1,
    total: 4,
  });
});

test("permission matrix exposes finance signoff only to finance-capable roles", () => {
  assert.equal(hasFinanceActualPermission("accounting", "finance.approval.signoff"), true);
  assert.equal(hasFinanceActualPermission("dispatcher", "finance.approval.signoff"), false);
});

test("approval stage tone maps to expected review severity", () => {
  assert.equal(approvalStageTone("finance_signed_off"), "good");
  assert.equal(approvalStageTone("draft"), "bad");
});
