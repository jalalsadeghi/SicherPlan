import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const apiPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/api/planningOrders.ts",
);
const source = readFileSync(apiPath, "utf8");

test("planningOrders api exposes all documented order endpoint groups", () => {
  assert.match(source, /export function listCustomerOrders/);
  assert.match(source, /export function listServiceCategoryOptions/);
  assert.match(source, /export function createCustomerOrder/);
  assert.match(source, /export function updateCustomerOrder/);
  assert.match(source, /export function setCustomerOrderReleaseState/);
  assert.match(source, /export function listOrderEquipmentLines/);
  assert.match(source, /export function createOrderEquipmentLine/);
  assert.match(source, /export function updateOrderEquipmentLine/);
  assert.match(source, /export function listOrderRequirementLines/);
  assert.match(source, /export function createOrderRequirementLine/);
  assert.match(source, /export function updateOrderRequirementLine/);
  assert.match(source, /export function listOrderAttachments/);
  assert.match(source, /export function createOrderAttachment/);
  assert.match(source, /export function linkOrderAttachment/);
  assert.match(source, /export async function downloadPlanningDocument/);
  assert.match(source, /export function getOrderCommercialLink/);
});

test("planningOrders api exposes all documented planning-record endpoint groups", () => {
  assert.match(source, /export function listPlanningRecords/);
  assert.match(source, /export function getPlanningRecord/);
  assert.match(source, /export function listPlanningDispatcherCandidates/);
  assert.match(source, /export function createPlanningRecord/);
  assert.match(source, /export function updatePlanningRecord/);
  assert.match(source, /export function setPlanningRecordReleaseState/);
  assert.match(source, /export function listPlanningRecordAttachments/);
  assert.match(source, /export function createPlanningRecordAttachment/);
  assert.match(source, /export function linkPlanningRecordAttachment/);
  assert.match(source, /export function getPlanningRecordCommercialLink/);
});
