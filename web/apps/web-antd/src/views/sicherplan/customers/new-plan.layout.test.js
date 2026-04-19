import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const source = fs.readFileSync(
  path.resolve("web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue"),
  "utf8",
);

test("wizard shell keeps customer new-plan route behavior and controlled states", () => {
  assert.match(source, /path: '\/admin\/customers'/);
  assert.match(source, /path: '\/admin\/customers\/new-plan'/);
  assert.match(source, /contextState\.value = 'missing'/);
  assert.match(source, /contextState\.value = 'not_found'/);
  assert.match(source, /<ForbiddenView v-if="!isAuthorized" \/>/);
  assert.match(source, /window\.confirm\(\$t\('sicherplan\.customerPlansWizard\.confirmDiscard'\)\)/);
});

test("wizard shell uses i18n keys for breadcrumb, invalid states, and final action labels", () => {
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.title'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.description'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.breadcrumbCustomers'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.breadcrumbPlans'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.loadingTitle'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.missingCustomerTitle'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.unknownCustomerTitle'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.errorTitle'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.actions\.cancel'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.actions\.previous'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.actions\.next'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.actions\.generateContinue'\)/);
});
