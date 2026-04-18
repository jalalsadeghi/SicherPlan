import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const apiPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/api/customers.ts",
);

const apiSource = readFileSync(apiPath, "utf8");

test("customer admin api uses the shared legacy session request path instead of raw bearer-token fetches", () => {
  assert.match(apiSource, /legacySessionRequest/);
  assert.doesNotMatch(apiSource, /Authorization:\s*`Bearer/);
  assert.doesNotMatch(apiSource, /fetch\(`\$\{webAppConfig\.apiBaseUrl\}\$\{path\}`/);
});

test("customer admin api exposes typed customer dashboard support", () => {
  assert.match(apiSource, /export interface CustomerDashboardRead/);
  assert.match(apiSource, /export interface CustomerDashboardPlanningSummaryRead/);
  assert.match(apiSource, /export interface CustomerDashboardFinanceSummaryRead/);
  assert.match(apiSource, /export interface CustomerDashboardCalendarItemRead/);
  assert.match(apiSource, /created_at: string;/);
  assert.match(apiSource, /export function getCustomerDashboard\(tenantId: string, customerId: string, accessToken: string\)/);
  assert.match(apiSource, /\/api\/customers\/tenants\/\$\{tenantId\}\/customers\/\$\{customerId\}\/dashboard/);
});
