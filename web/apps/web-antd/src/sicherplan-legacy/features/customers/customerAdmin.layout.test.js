import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const viewPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue",
);
const source = readFileSync(viewPath, "utf8");

test("customer workspace keeps desktop master detail layout with detail tabs", () => {
  assert.match(source, /class="customer-admin-grid"/);
  assert.match(source, /data-testid="customer-list-section"/);
  assert.match(source, /data-testid="customer-detail-workspace"/);
  assert.match(source, /data-testid="customer-detail-tabs"/);
});

test("commercial workspace uses nested sub tabs and isolated panels", () => {
  assert.match(source, /data-testid="customer-commercial-tabs"/);
  assert.match(source, /data-testid="customer-commercial-panel-billing-profile"/);
  assert.match(source, /data-testid="customer-commercial-panel-invoice-parties"/);
  assert.match(source, /data-testid="customer-commercial-panel-pricing-rules"/);
});

test("detail forms use the denser detail-grid span classes", () => {
  assert.match(source, /customer-admin-form-grid--detail/);
  assert.match(source, /field-stack--half/);
  assert.match(source, /field-stack--third/);
});

test("non-overview customer tabs reuse the structured section pattern", () => {
  assert.match(source, /customer-tab-panel-contacts[\s\S]*customer-admin-form customer-admin-form--structured[\s\S]*customerAdmin\.contacts\.registerEyebrow[\s\S]*customerAdmin\.contacts\.editorEyebrow/);
  assert.match(source, /customer-tab-panel-addresses[\s\S]*customerAdmin\.addresses\.registerEyebrow[\s\S]*customerAdmin\.addresses\.editorEyebrow/);
  assert.match(source, /customer-tab-panel-commercial[\s\S]*customer-admin-editor-intro[\s\S]*customer-commercial-panel-billing-profile/);
  assert.match(source, /customer-tab-panel-portal[\s\S]*customerAdmin\.portal\.lead[\s\S]*customerAdmin\.loginHistory\.title/);
  assert.match(source, /customer-tab-panel-history[\s\S]*customerAdmin\.history\.registerEyebrow[\s\S]*customerAdmin\.history\.attachmentEyebrow/);
  assert.match(source, /customer-tab-panel-employee-blocks[\s\S]*customerAdmin\.employeeBlocks\.registerEyebrow[\s\S]*customerAdmin\.employeeBlocks\.editorEyebrow/);
});

test("full tab editors no longer use legacy inline-form layout", () => {
  assert.doesNotMatch(source, /customer-admin-inline-form/);
  assert.match(source, /submitHistoryAttachmentLink[\s\S]*customer-admin-form-grid customer-admin-form-grid--detail/);
  assert.match(source, /submitEmployeeBlock[\s\S]*customer-admin-form-grid customer-admin-form-grid--detail/);
});
