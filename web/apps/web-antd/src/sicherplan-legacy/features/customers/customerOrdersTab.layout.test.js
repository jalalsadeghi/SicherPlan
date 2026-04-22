import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const componentPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/components/customers/CustomerOrdersTab.vue",
);
const source = readFileSync(componentPath, "utf8");

test("customer orders tab keeps stable order-centric test hooks and subtle tone attributes", () => {
  assert.match(source, /data-testid="customer-tab-panel-orders"/);
  assert.match(source, /data-testid="customer-orders-toolbar"/);
  assert.match(source, /data-testid="customer-orders-search"/);
  assert.match(source, /data-testid="customer-orders-sort"/);
  assert.match(source, /data-testid="customer-orders-loading"/);
  assert.match(source, /data-testid="customer-orders-error"/);
  assert.match(source, /data-testid="customer-orders-card-open"/);
  assert.match(source, /data-testid="customer-orders-card-edit"/);
  assert.match(source, /data-testid="customer-orders-detail-modal"/);
  assert.match(source, /data-testid="customer-orders-detail-loading"/);
  assert.match(source, /data-testid="customer-orders-detail-error"/);
  assert.match(source, /data-testid="customer-orders-detail-close"/);
  assert.match(source, /class="customer-orders-tab__panel"/);
  assert.match(source, /class="customer-orders-tab__header"/);
  assert.match(source, /class="customer-orders-tab__toolbar"/);
  assert.match(source, /customer-orders-tab__field customer-orders-tab__field--search/);
  assert.match(source, /customer-orders-tab__field customer-orders-tab__field--sort/);
  assert.match(source, /class="customer-orders-tab__row"/);
  assert.match(source, /:data-tone="order\.displayTone"/);
  assert.match(source, /:data-state="order\.displayStateKey"/);
});

test("customer orders tab reuses customer-admin-style control treatment with responsive toolbar stacking", () => {
  assert.match(source, /\.customer-orders-tab__toolbar \{/);
  assert.match(source, /grid-template-columns: minmax\(0, 1fr\) minmax\(16rem, 22rem\);/);
  assert.match(source, /align-items: end;/);
  assert.match(source, /padding: 1rem 1\.1rem;/);
  assert.match(source, /border-radius: 1rem;/);
  assert.match(source, /\.customer-orders-tab__field input,/);
  assert.match(source, /\.customer-orders-tab__field select \{/);
  assert.match(source, /border-radius: 14px;/);
  assert.match(source, /background: var\(--sp-color-surface-card\);/);
  assert.match(source, /\.customer-orders-tab__field input:focus,/);
  assert.match(source, /\.customer-orders-tab__field select:focus \{/);
  assert.match(source, /@media \(max-width: 900px\) \{/);
  assert.match(source, /\.customer-orders-tab__toolbar \{\s*grid-template-columns: 1fr;/);
  assert.match(source, /\.customer-orders-tab__field--sort \{\s*justify-self: stretch;/);
});

test("customer orders tab uses order date-aware display-state logic and long-title overflow protection", () => {
  assert.match(source, /parseDateBoundary/);
  assert.match(source, /parseDateBoundary\(order\.service_from, "start"\)/);
  assert.match(source, /parseDateBoundary\(order\.service_to, "end"\)/);
  assert.match(source, /\.customer-orders-tab__row-main > div:first-child \{/);
  assert.match(source, /min-width: 0;/);
  assert.match(source, /\.customer-orders-tab__row strong \{/);
  assert.match(source, /overflow-wrap: anywhere;/);
  assert.doesNotMatch(source, /listPlanningRecords/);
  assert.doesNotMatch(source, /planning_from/);
  assert.doesNotMatch(source, /planning_to/);
});
