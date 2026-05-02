import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const source = fs.readFileSync(
  path.resolve("web/apps/web-antd/src/views/sicherplan/customers/new-plan.vue"),
  "utf8",
);

test("wizard shell keeps customer order workspace route behavior and controlled states", () => {
  assert.match(source, /import CustomerOrderWorkspacePanel from '\.\/customer-order-workspace-panel\.vue'/);
  assert.match(source, /const panelRef = ref<InstanceType<typeof CustomerOrderWorkspacePanel> \| null>\(null\)/);
  assert.match(source, /return panelRef\.value\?\.wizardState/);
  assert.match(source, /<CustomerOrderWorkspacePanel ref="panelRef" \/>/);
});

test("wizard shell uses i18n keys for breadcrumb, invalid states, and final action labels", () => {
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.title'\)/);
  assert.match(source, /\$t\('sicherplan\.customerPlansWizard\.description'\)/);
  assert.match(source, /\$t\('sicherplan\.admin\.customers'\)/);
  assert.match(source, /<ModuleWorkspacePage/);
  assert.match(source, /<SectionBlock :show-header="false" title="">/);
});
