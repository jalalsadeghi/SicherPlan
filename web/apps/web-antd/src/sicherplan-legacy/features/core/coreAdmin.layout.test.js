import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const viewPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/views/CoreAdminView.vue",
);

const viewSource = readFileSync(viewPath, "utf8");

test("core admin keeps a master detail layout", () => {
  assert.match(viewSource, /data-testid="core-master-detail-layout"/);
  assert.match(viewSource, /data-testid="core-list-section"/);
  assert.match(viewSource, /data-testid="core-detail-workspace"/);
});

test("core admin detail workspace uses top-level tabs", () => {
  assert.match(viewSource, /data-testid="core-detail-tabs"/);
  assert.match(viewSource, /data-testid="core-tab-panel-overview"/);
  assert.match(viewSource, /data-testid="core-tab-panel-branches"/);
  assert.match(viewSource, /data-testid="core-tab-panel-mandates"/);
  assert.match(viewSource, /data-testid="core-tab-panel-settings"/);
});

test("core admin detail tabs preserve existing forms and section handlers", () => {
  assert.match(viewSource, /core-tab-panel-overview[\s\S]*submitTenantUpdate[\s\S]*ACTION_KEYS\.tenantSave/);
  assert.match(viewSource, /core-tab-panel-branches[\s\S]*submitBranch[\s\S]*ACTION_KEYS\.branchCreate/);
  assert.match(viewSource, /core-tab-panel-mandates[\s\S]*submitMandate[\s\S]*ACTION_KEYS\.mandateCreate/);
  assert.match(viewSource, /core-tab-panel-settings[\s\S]*submitSetting[\s\S]*ACTION_KEYS\.settingCreate/);
});

test("core admin settings expose the customer portal policy toggle", () => {
  assert.match(viewSource, /data-testid="core-customer-portal-policy"/);
  assert.match(viewSource, /CUSTOMER_PORTAL_POLICY_KEY = "customer_portal\.policy"/);
  assert.match(viewSource, /setCustomerPortalWatchbookEntriesEnabled\(!customerWatchbookEntriesEnabled\)/);
});

test("core admin settings expose tenant-scoped unit-of-measure catalog management", () => {
  assert.match(viewSource, /data-testid="core-unit-of-measure-settings"/);
  assert.match(viewSource, /UNIT_OF_MEASURE_DOMAIN = "unit_of_measure"/);
  assert.match(viewSource, /listLookupValues\(effectiveAccessToken\.value, tenantId, UNIT_OF_MEASURE_DOMAIN/);
  assert.match(viewSource, /submitUnitLookup/);
  assert.match(viewSource, /createLookupValue\(/);
  assert.match(viewSource, /updateLookupValue\(/);
});
