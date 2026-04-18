import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const componentPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/components/customers/CustomerPlansTab.vue",
);
const source = readFileSync(componentPath, "utf8");

test("customer plans tab keeps stable test hooks and subtle tone attributes", () => {
  assert.match(source, /data-testid="customer-tab-panel-plans"/);
  assert.match(source, /data-testid="customer-plans-toolbar"/);
  assert.match(source, /data-testid="customer-plans-search"/);
  assert.match(source, /data-testid="customer-plans-sort"/);
  assert.match(source, /data-testid="customer-plans-loading"/);
  assert.match(source, /data-testid="customer-plans-error"/);
  assert.match(source, /class="customer-plans-tab__panel"/);
  assert.match(source, /class="customer-plans-tab__header"/);
  assert.match(source, /class="customer-plans-tab__toolbar"/);
  assert.match(source, /customer-plans-tab__field customer-plans-tab__field--search/);
  assert.match(source, /customer-plans-tab__field customer-plans-tab__field--sort/);
  assert.match(source, /class="customer-plans-tab__row"/);
  assert.match(source, /:data-tone="plan\.displayTone"/);
  assert.match(source, /:data-state="plan\.displayStateKey"/);
});

test("customer plans tab reuses customer-admin-style control treatment with responsive toolbar stacking", () => {
  assert.match(source, /\.customer-plans-tab__toolbar \{/);
  assert.match(source, /grid-template-columns: minmax\(0, 1fr\) minmax\(16rem, 22rem\);/);
  assert.match(source, /align-items: end;/);
  assert.match(source, /padding: 1rem 1\.1rem;/);
  assert.match(source, /border-radius: 1rem;/);
  assert.match(source, /\.customer-plans-tab__field input,/);
  assert.match(source, /\.customer-plans-tab__field select \{/);
  assert.match(source, /border-radius: 14px;/);
  assert.match(source, /background: var\(--sp-color-surface-card\);/);
  assert.match(source, /\.customer-plans-tab__field input:focus,/);
  assert.match(source, /\.customer-plans-tab__field select:focus \{/);
  assert.match(source, /@media \(max-width: 900px\) \{/);
  assert.match(source, /\.customer-plans-tab__toolbar \{\s*grid-template-columns: 1fr;/);
  assert.match(source, /\.customer-plans-tab__field--sort \{\s*justify-self: stretch;/);
});

test("customer plans tab uses date-aware display-state logic and long-title overflow protection", () => {
  assert.match(source, /parseDateBoundary/);
  assert.match(source, /parseDateBoundary\(record\.planning_from, "start"\)/);
  assert.match(source, /parseDateBoundary\(record\.planning_to, "end"\)/);
  assert.match(source, /\.customer-plans-tab__row-main > div:first-child \{/);
  assert.match(source, /min-width: 0;/);
  assert.match(source, /\.customer-plans-tab__row strong \{/);
  assert.match(source, /overflow-wrap: anywhere;/);
});
