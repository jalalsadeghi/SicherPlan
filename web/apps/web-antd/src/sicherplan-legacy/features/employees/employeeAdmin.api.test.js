import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const apiPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/api/employeeAdmin.ts",
);

const apiSource = readFileSync(apiPath, "utf8");

test("employee admin api exposes readiness management bindings", () => {
  assert.match(apiSource, /export function listFunctionTypes/);
  assert.match(apiSource, /export function createFunctionType/);
  assert.match(apiSource, /export function updateFunctionType/);
  assert.match(apiSource, /\/catalog\/function-types/);
  assert.match(apiSource, /export function listQualificationTypes/);
  assert.match(apiSource, /export function createQualificationType/);
  assert.match(apiSource, /export function updateQualificationType/);
  assert.match(apiSource, /\/catalog\/qualification-types/);
  assert.match(apiSource, /export function listEmployeeQualifications/);
  assert.match(apiSource, /\/employees\/qualifications/);
  assert.match(apiSource, /export function uploadEmployeeQualificationProof/);
  assert.match(apiSource, /\/proofs\/uploads/);
  assert.match(apiSource, /export function listEmployeeCredentials/);
  assert.match(apiSource, /\/employees\/credentials/);
  assert.match(apiSource, /export function issueEmployeeCredentialBadgeOutput/);
  assert.match(apiSource, /\/badge-output/);
  assert.match(apiSource, /export function listEmployeeAvailabilityRules/);
  assert.match(apiSource, /\/employees\/availability-rules/);
  assert.match(apiSource, /export function listEmployeeAbsences/);
  assert.match(apiSource, /\/employees\/absences/);
});

test("employee admin api uses the shared legacy session request path without bespoke refresh plumbing", () => {
  assert.match(apiSource, /legacySessionRequest/);
  assert.doesNotMatch(apiSource, /refreshTokenApi/);
  assert.doesNotMatch(apiSource, /useAccessStore/);
  assert.doesNotMatch(apiSource, /performAuthorizedRequest/);
  assert.doesNotMatch(apiSource, /refreshLegacyEmployeeToken/);
  assert.doesNotMatch(apiSource, /Authorization:\s*`Bearer/);
});
