import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const apiPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/api/planningAdmin.ts",
);
const source = readFileSync(apiPath, "utf8");

test("planning admin api maps service categories to the backend CRUD catalog", () => {
  assert.match(source, /service_category:\s*"service-categories"/);
  assert.match(source, /export function listPlanningRecords\(entityKey[\s\S]*ENTITY_PATHS\[entityKey\]/);
  assert.match(source, /export function getPlanningRecord\(entityKey[\s\S]*ENTITY_PATHS\[entityKey\]/);
  assert.match(source, /export function createPlanningRecord\(entityKey[\s\S]*ENTITY_PATHS\[entityKey\]/);
  assert.match(source, /export function updatePlanningRecord\(entityKey[\s\S]*ENTITY_PATHS\[entityKey\]/);
});

test("planning admin api preserves generic setup search and status filters", () => {
  assert.match(source, /if \(params\.search\) query\.set\("search", params\.search\)/);
  assert.match(source, /if \(params\.lifecycle_status\) query\.set\("lifecycle_status", params\.lifecycle_status\)/);
  assert.match(source, /if \(params\.include_archived\) query\.set\("include_archived", "true"\)/);
});
