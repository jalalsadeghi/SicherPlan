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

test("create mode exposes entity-aware header, family selector, and cancel action", () => {
  assert.match(source, /tp\("newRecordHeading", \{ entity: editorEntityLabel \}\)/);
  assert.match(source, /tp\("detailCreateLead", \{ entity: editorEntityLabel \}\)/);
  assert.match(source, /<select v-model="editorEntityKey" @change="handleEditorEntityChange">/);
  assert.match(source, /isCreatingRecord \? tp\("actionsCancelCreate"\) : tp\("actionsResetRecord"\)/);
});

test("create mode blocks child entity saves without a selected parent and hides post-save child sections", () => {
  assert.match(source, /const childCreateBlockedMessage = computed\(\(\) => \{/);
  assert.match(source, /editorEntityKey\.value === "trade_fair_zone" && !createTradeFairParentId\.value/);
  assert.match(source, /editorEntityKey\.value === "patrol_checkpoint" && !createPatrolRouteParentId\.value/);
  assert.match(source, /:disabled="\(!actionState\.canCreate && !actionState\.canEdit\) \|\| !!childCreateBlockedMessage"/);
  assert.match(source, /v-if="entityKey === 'trade_fair' && selectedRecord && !isCreatingRecord"/);
  assert.match(source, /v-if="entityKey === 'patrol_route' && selectedRecord && !isCreatingRecord"/);
});

test("planning setup create form uses parent selectors for zones and checkpoints and shows top-level status", () => {
  assert.match(source, /tp\("fieldsTradeFairParent"\)/);
  assert.match(source, /tp\("fieldsPatrolRouteParent"\)/);
  assert.match(source, /tp\("parentTradeFairPlaceholder"\)/);
  assert.match(source, /tp\("parentPatrolRoutePlaceholder"\)/);
  assert.match(source, /<label v-if="visibleStatus" class="field-stack field-stack--half">/);
});

test("planning setup address picker refresh is shared across all address-backed entity families", () => {
  assert.match(source, /function usesAddressSelection\(entity = editorEntityKey\.value\)/);
  assert.match(source, /\["site", "event_venue", "trade_fair", "patrol_route"\]\.includes\(entity\)/);
  assert.match(source, /\(\) => \[editorEntityKey\.value, draft\.customer_id\]/);
});
