import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const viewPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue",
);
const registryPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/views/sicherplan/module-registry.ts",
);

const viewSource = readFileSync(viewPath, "utf8");
const registrySource = readFileSync(registryPath, "utf8");

test("employees module hides the shared workspace section header", () => {
  assert.match(registrySource, /employees:\s*{[\s\S]*showWorkspaceSectionHeader:\s*false/);
});

test("employee workspace uses master detail layout and embedded scope is removed", () => {
  assert.match(viewSource, /data-testid="employee-master-detail-layout"/);
  assert.match(viewSource, /data-testid="employee-list-section"/);
  assert.match(viewSource, /data-testid="employee-detail-workspace"/);
  assert.match(viewSource, /v-if="!embedded" class="module-card employee-admin-scope"/);
  assert.match(viewSource, /\.employee-admin-grid\s*{\s*display:\s*grid;[\s\S]*grid-template-columns:\s*minmax\(320px,\s*420px\)\s*minmax\(0,\s*1fr\)/);
});

test("employee detail uses top-level tabs and isolated tab panels", () => {
  assert.match(viewSource, /data-testid="employee-detail-tabs"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-overview"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-app-access"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-profile-photo"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-notes"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-groups"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-documents"/);
});

test("employee list rows use structured text stack markup and card row styling", () => {
  assert.match(viewSource, /class="employee-admin-row__text"/);
  assert.match(viewSource, /class="employee-admin-row__title"/);
  assert.match(viewSource, /class="employee-admin-row__meta"/);
  assert.match(viewSource, /\.employee-admin-row,\s*\.employee-admin-record\s*{[\s\S]*padding:\s*1rem;[\s\S]*border-radius:\s*18px;[\s\S]*border:\s*1px solid var\(--sp-color-border-soft\);/);
});

test("non-overview employee tabs reuse the structured section pattern", () => {
  assert.match(viewSource, /employee-tab-panel-app-access[\s\S]*employee-admin-form employee-admin-form--structured[\s\S]*employeeAdmin\.access\.stateCreateEyebrow/);
  assert.match(viewSource, /employee-tab-panel-app-access[\s\S]*v-if="!hasLinkedAccess"[\s\S]*employeeAdmin\.access\.createEyebrow/);
  assert.match(viewSource, /employee-tab-panel-app-access[\s\S]*v-else[\s\S]*employeeAdmin\.access\.manageEyebrow[\s\S]*employeeAdmin\.access\.resetEyebrow[\s\S]*employeeAdmin\.access\.detachEyebrow/);
  assert.match(viewSource, /employee-tab-panel-app-access[\s\S]*employee-admin-advanced-access[\s\S]*employeeAdmin\.access\.attachEyebrow[\s\S]*employeeAdmin\.access\.reconcileEyebrow/);
  assert.match(viewSource, /employee-tab-panel-profile-photo[\s\S]*employee-admin-editor-intro[\s\S]*employeeAdmin\.photo\.manageEyebrow/);
  assert.match(viewSource, /employee-tab-panel-notes[\s\S]*employeeAdmin\.notes\.registerEyebrow[\s\S]*employeeAdmin\.notes\.editorEyebrow/);
  assert.match(viewSource, /employee-tab-panel-groups[\s\S]*employeeAdmin\.groups\.catalogEyebrow[\s\S]*employeeAdmin\.groups\.assignEyebrow[\s\S]*employeeAdmin\.groups\.currentEyebrow/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.addresses\.currentEyebrow/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.addresses\.editorEyebrow/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*submitAddress/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*createEmployeeAddress/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*updateEmployeeAddress/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.actions\.editAddress/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.actions\.markCurrentAddress/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.actions\.closeAddressValidity/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*employeeAdmin\.documents\.libraryEyebrow/);
});

test("employee addresses tab uses admin editor copy and removes released timeline wording", () => {
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.addresses\.empty/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.feedback\.addressSaved/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAddressTimeline/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*onAddressCurrentToggle/);
  assert.doesNotMatch(viewSource, /Released address timeline/);
  assert.doesNotMatch(viewSource, /No released address history is available/);
});
