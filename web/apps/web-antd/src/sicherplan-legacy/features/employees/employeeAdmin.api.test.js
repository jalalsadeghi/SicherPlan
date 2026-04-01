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
