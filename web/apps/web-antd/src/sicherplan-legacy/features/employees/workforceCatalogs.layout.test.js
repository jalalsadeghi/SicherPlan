import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const viewPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/views/WorkforceCatalogsAdminView.vue",
);

const viewSource = readFileSync(viewPath, "utf8");

test("workforce catalogs page renders tenant-wide master-data sections without employee selection", () => {
  assert.match(viewSource, /data-testid="workforce-catalogs-layout"/);
  assert.match(viewSource, /data-testid="workforce-function-types-section"/);
  assert.match(viewSource, /data-testid="workforce-qualification-types-section"/);
  assert.match(viewSource, /deriveEmployeeActionState\(effectiveRole\.value, null\)/);
  assert.match(viewSource, /resolvedTenantScopeId/);
  assert.doesNotMatch(viewSource, /selectedEmployeeId/);
  assert.doesNotMatch(viewSource, /selectedEmployee/);
});

test("workforce catalogs page keeps full create and edit flows for both catalogs", () => {
  assert.match(viewSource, /createFunctionType\(/);
  assert.match(viewSource, /updateFunctionType\(/);
  assert.match(viewSource, /createQualificationType\(/);
  assert.match(viewSource, /updateQualificationType\(/);
  assert.match(viewSource, /buildEmployeeFunctionTypePayload/);
  assert.match(viewSource, /buildEmployeeQualificationTypePayload/);
  assert.match(viewSource, /validateEmployeeFunctionTypeDraft/);
  assert.match(viewSource, /validateEmployeeQualificationTypeDraft/);
  assert.match(viewSource, /await refreshCatalogs\(\);[\s\S]*employeeAdmin\.feedback\.functionTypeSaved/);
  assert.match(viewSource, /await refreshCatalogs\(\);[\s\S]*employeeAdmin\.feedback\.qualificationTypeSaved/);
  assert.match(viewSource, /workforce-function-type-record-/);
  assert.match(viewSource, /workforce-qualification-type-record-/);
});
