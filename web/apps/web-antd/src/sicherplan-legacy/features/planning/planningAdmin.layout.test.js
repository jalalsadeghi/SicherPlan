import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync(
  new URL("../../views/PlanningOpsAdminView.vue", import.meta.url),
  "utf8",
);

test("browse records card uses internal tabs and keeps area shared above them", () => {
  assert.match(source, /<InternalCardTabs[\s\S]*test-id="planning-browse-tabs"/);
  assert.match(source, /<div class="planning-admin-shared-context">[\s\S]*<span>\{\{ tp\("entityLabel"\) \}\}<\/span>/);
  assert.doesNotMatch(source, /<p class="eyebrow">\{\{ tp\("filtersTitle"\) \}\}<\/p>/);
  assert.doesNotMatch(source, /<p class="eyebrow">\{\{ tp\("importTitle"\) \}\}<\/p>/);
});

test("browse records keeps both panels mounted with v-show and leaves results below the tabs", () => {
  assert.match(source, /id="planning-browse-panel-filters"[\s\S]*v-show="browsePanelTab === 'filters'"/);
  assert.match(source, /id="planning-browse-panel-import"[\s\S]*v-show="browsePanelTab === 'import'"/);
  assert.match(
    source,
    /id="planning-browse-panel-import"[\s\S]*<\/section>[\s\S]*<\/section>[\s\S]*<div v-if="records\.length" class="planning-admin-list">/,
  );
});

test("site address field is clearly labeled as an optional address record id", () => {
  assert.match(source, /<PlanningAddressSelect[\s\S]*tp\('fieldsAddressId'\)/);
  assert.match(source, /tp\('fieldsAddressSearchPlaceholder'\)/);
  assert.match(source, /tp\('fieldsAddressCustomerRequired'\)/);
});

test("site number and name use the same explicit field wrapper class", () => {
  assert.match(source, /planning-admin-site-primary-field field-stack field-stack--half"><span>\{\{ tp\("fieldsSiteNo"\) \}\}<\/span><input v-model="draft\.site_no"/);
  assert.match(source, /planning-admin-site-primary-field field-stack field-stack--half"><span>\{\{ tp\("fieldsName"\) \}\}<\/span><input v-model="draft\.name"/);
});

test("planning setup accepts deep-link entity and customer query context", () => {
  assert.match(source, /useRoute/);
  assert.match(source, /resolvePlanningRouteContext\(route\.query\)/);
  assert.match(source, /filters\.customer_id = customerId/);
  assert.match(source, /entityKey\.value = entity/);
});
