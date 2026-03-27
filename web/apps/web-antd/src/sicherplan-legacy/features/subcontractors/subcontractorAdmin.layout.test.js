import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const viewPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/views/SubcontractorAdminView.vue",
);
const registryPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/views/sicherplan/module-registry.ts",
);
const source = readFileSync(viewPath, "utf8");
const registrySource = readFileSync(registryPath, "utf8");

test("subcontractor workspace keeps compact master detail layout with detail tabs", () => {
  assert.match(source, /class="subcontractor-admin-grid"/);
  assert.match(source, /grid-template-columns:\s*minmax\(320px, 420px\) minmax\(0, 1fr\)/);
  assert.match(source, /data-testid="subcontractor-list-section"/);
  assert.match(source, /data-testid="subcontractor-detail-workspace"/);
  assert.match(source, /data-testid="subcontractor-detail-tabs"/);
});

test("embedded subcontractor view suppresses local hero chrome", () => {
  assert.match(source, /v-if="!props\.embedded" class="module-card subcontractor-admin-hero"/);
});

test("subcontractor detail workspace exposes customer-style tab panels and placeholders", () => {
  assert.match(source, /data-testid="subcontractor-tab-panel-overview"/);
  assert.match(source, /data-testid="subcontractor-tab-panel-contacts"/);
  assert.match(source, /data-testid="subcontractor-tab-panel-addresses"/);
  assert.match(source, /data-testid="subcontractor-tab-panel-commercial"/);
  assert.match(source, /data-testid="subcontractor-tab-panel-scope-release"/);
  assert.match(source, /data-testid="subcontractor-tab-panel-billing"/);
  assert.match(source, /data-testid="subcontractor-tab-panel-history"/);
  assert.match(source, /activeDetailTab === 'workforce'/);
});

test("subcontractor module wrapper skips the extra workspace block", () => {
  assert.match(
    registrySource,
    /subcontractors:\s*\{[\s\S]*showWorkspaceSectionHeader:\s*false/,
  );
});
