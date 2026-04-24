import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const componentPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/components/customers/CustomerDashboardTab.vue",
);
const source = readFileSync(componentPath, "utf8");

test("customer dashboard finance and standing KPIs expose stable tone attributes", () => {
  assert.match(source, /const financeTone = computed<CustomerDashboardFinanceTone>\(\(\) =>/);
  assert.match(source, /financeSummary\?\.visibility === "restricted"/);
  assert.match(source, /financeSummary\.visibility === "unavailable"/);
  assert.match(source, /return Number\.isFinite\(amount\) \? "good" : "warn";/);
  assert.match(source, /const standingTone = computed<CustomerDashboardStandingTone>\(\(\) =>/);
  assert.match(source, /:data-tone="financeTone"/);
  assert.match(source, /data-testid="customer-dashboard-kpi-finance"/);
  assert.match(source, /:data-tone="standingTone"/);
  assert.match(source, /data-testid="customer-dashboard-kpi-standing"/);
});

test("customer dashboard KPI tone styling uses theme tokens rather than hard-coded colors", () => {
  assert.match(source, /customer-dashboard-tab__kpi-card--tone\[data-tone="good"\]/);
  assert.match(source, /customer-dashboard-tab__kpi-card--tone\[data-tone="warn"\]/);
  assert.match(source, /customer-dashboard-tab__kpi-card--tone\[data-tone="bad"\]/);
  assert.match(source, /customer-dashboard-tab__kpi-card--tone\[data-tone="restricted"\]/);
  assert.match(source, /var\(--sp-color-success\)/);
  assert.match(source, /var\(--sp-color-warning\)/);
  assert.match(source, /var\(--sp-color-danger\)/);
  assert.match(source, /var\(--sp-color-primary-strong\)/);
  assert.match(source, /var\(--sp-color-primary-muted\)/);
});

test("customer dashboard KPI grid keeps the existing four-card desktop rhythm", () => {
  assert.match(source, /grid-template-columns: repeat\(4, minmax\(0, 1fr\)\);/);
  assert.match(source, /@media \(max-width: 1100px\) \{[\s\S]*grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/);
  assert.match(source, /@media \(max-width: 720px\) \{[\s\S]*grid-template-columns: 1fr;/);
});

test("customer dashboard latest plans use release-state status tags with stable tone hooks", () => {
  assert.match(source, /function resolveLatestPlanStatusTone\(status: string\): LatestPlanStatusTone/);
  assert.match(source, /case "released":[\s\S]*return "good";/);
  assert.match(source, /case "draft":[\s\S]*case "release_ready":[\s\S]*return "warn";/);
  assert.match(source, /return "neutral";/);
  assert.match(source, /function resolveLatestPlanTagColor\(status: string\)/);
  assert.match(source, /<Tag[\s\S]*class="customer-dashboard-tab__status-tag"/);
  assert.match(source, /:color="resolveLatestPlanTagColor\(plan\.status\)"/);
  assert.match(source, /:data-tone="resolveLatestPlanStatusTone\(plan\.status\)"/);
  assert.match(source, /:data-status="plan\.status"/);
});

test("customer dashboard second row is composed from equal-height orders and plans cards", () => {
  assert.match(source, /listCustomerOrders,/);
  assert.match(source, /const latestOrders = ref<CustomerOrderListItem\[\]>\(\[\]\);/);
  assert.match(source, /const latestFivePlans = computed\(\(\) => latestPlans\.value\.slice\(0, 5\)\);/);
  assert.match(source, /function sortOrdersByLatestWindow\(rows: CustomerOrderListItem\[\]\)/);
  assert.match(source, /async function loadLatestOrders\(\)/);
  assert.match(source, /data-testid="customer-dashboard-second-row"/);
  assert.match(source, /data-testid="customer-dashboard-orders-card"/);
  assert.match(source, /data-testid="customer-dashboard-orders-row"/);
  assert.match(source, /data-testid="customer-dashboard-orders-empty"/);
  assert.match(source, /data-testid="customer-dashboard-plans-card"/);
  assert.match(source, /data-testid="customer-dashboard-plans-row"/);
  assert.match(source, /data-testid="customer-dashboard-plans-empty"/);
  assert.match(source, /customer-dashboard-tab__row--second/);
  assert.match(source, /customer-dashboard-tab__panel--equal/);
  assert.match(source, /customer-dashboard-tab__list--stretch/);
});
