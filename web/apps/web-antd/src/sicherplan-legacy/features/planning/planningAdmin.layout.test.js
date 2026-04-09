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

test("planning workspace no longer renders the fixed inline feedback banner", () => {
  assert.doesNotMatch(source, /v-if="feedback\.message"/);
  assert.doesNotMatch(source, /class="planning-admin-feedback"/);
  assert.doesNotMatch(source, /actionsClearFeedback/);
  assert.doesNotMatch(source, /function clearFeedback\(/);
});

test("browse records keeps both panels mounted with v-show and leaves results below the tabs", () => {
  assert.match(source, /id="planning-browse-panel-filters"[\s\S]*v-show="browsePanelTab === 'filters'"/);
  assert.match(source, /id="planning-browse-panel-import"[\s\S]*v-show="browsePanelTab === 'import'"/);
  assert.match(
    source,
    /id="planning-browse-panel-import"[\s\S]*<\/section>[\s\S]*<\/section>[\s\S]*<div v-if="records\.length" class="planning-admin-list">/,
  );
});

test("planning master-detail layout pins panels and list content to the top when detail height grows", () => {
  assert.match(source, /\.planning-admin-grid \{[\s\S]*align-items: start;/);
  assert.match(source, /\.planning-admin-panel,\n\.planning-admin-list-panel,\n\.planning-admin-detail \{[\s\S]*align-content: start;/);
  assert.match(source, /\.planning-admin-list \{[\s\S]*align-content: start;[\s\S]*grid-auto-rows: max-content;/);
});

test("site address field is clearly labeled as an optional address record id", () => {
  assert.match(source, /<PlanningAddressSelect[\s\S]*tp\('fieldsAddressId'\)/);
  assert.match(source, /tp\('fieldsAddressSearchPlaceholder'\)/);
  assert.match(source, /tp\('fieldsAddressCustomerRequired'\)/);
  assert.match(source, /planning-admin-form-section__header--split/);
  assert.match(source, /<div v-if="showAddressCreateAction" class="planning-admin-form-section__actions">/);
  assert.match(source, /@click="openAddressCreateModal\(currentAddressFieldKey\)"/);
  assert.match(source, /:disabled="!draft\.customer_id \|\| loading\.sharedAddress"/);
  assert.doesNotMatch(source, /planning-admin-address-actions/);
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
  assert.doesNotMatch(source, /tp\("createModeLabel"\)/);
  assert.doesNotMatch(source, /tp\('createModeValue'/);
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

test("planning setup uses explicit customer scope instead of treating every non-child entity as customer-linked", () => {
  assert.match(source, /isPlanningCustomerScopedEntity/);
  assert.match(source, /const editorUsesCustomer = computed\(\(\) => isPlanningCustomerScopedEntity\(editorEntityKey\.value\)\)/);
  assert.doesNotMatch(source, /const editorUsesCustomer = computed\(\(\) => !isPlanningChildEntity\(editorEntityKey\.value\)\)/);
});

test("planning setup address picker refresh is shared across all address-backed entity families", () => {
  assert.match(source, /function usesAddressSelection\(entity = editorEntityKey\.value\)/);
  assert.match(source, /\["site", "event_venue", "trade_fair", "patrol_route"\]\.includes\(entity\)/);
  assert.match(source, /\(\) => \[editorEntityKey\.value, draft\.customer_id\]/);
});

test("planning checkpoint forms reuse the shared map picker with a checkpoint target", () => {
  assert.match(source, /openLocationPicker\('checkpoint'\)/);
  assert.match(source, /const locationPickerTarget = ref\("record"\)/);
  assert.match(source, /const locationPickerLatitude = computed\(\(\) =>\s*locationPickerTarget\.value === "checkpoint" \? checkpointDraft\.latitude : draft\.latitude/s);
  assert.match(source, /const locationPickerLongitude = computed\(\(\) =>\s*locationPickerTarget\.value === "checkpoint" \? checkpointDraft\.longitude : draft\.longitude/s);
  assert.match(source, /async function openLocationPicker\(target = "record"\) \{\s*locationPickerTarget\.value = target/s);
  assert.match(source, /currentLatitude: locationPickerLatitude\.value/);
  assert.match(source, /currentLongitude: locationPickerLongitude\.value/);
  assert.match(source, /if \(locationPickerTarget\.value === "checkpoint"\) \{\s*checkpointDraft\.latitude = payload\.latitude;\s*checkpointDraft\.longitude = payload\.longitude;/s);
  assert.match(source, /:latitude="locationPickerLatitude"/);
  assert.match(source, /:longitude="locationPickerLongitude"/);
});

test("planning checkpoint forms align label full-width and keep latitude/longitude on the same row", () => {
  assert.match(source, /editorEntityKey === 'patrol_checkpoint'[\s\S]*field-stack field-stack--third"><span>\{\{ tp\("fieldsSequenceNo"\) \}\}<\/span><input v-model="checkpointDraft\.sequence_no"/);
  assert.match(source, /editorEntityKey === 'patrol_checkpoint'[\s\S]*field-stack field-stack--third"><span>\{\{ tp\("fieldsCheckpointCode"\) \}\}<\/span><input v-model="checkpointDraft\.checkpoint_code"/);
  assert.match(source, /editorEntityKey === 'patrol_checkpoint'[\s\S]*field-stack field-stack--wide"><span>\{\{ tp\("fieldsLabel"\) \}\}<\/span><input v-model="checkpointDraft\.label"/);
  assert.match(source, /editorEntityKey === 'patrol_checkpoint'[\s\S]*field-stack field-stack--half"><span>\{\{ tp\("fieldsLatitude"\) \}\}<\/span><input v-model="checkpointDraft\.latitude"/);
  assert.match(source, /editorEntityKey === 'patrol_checkpoint'[\s\S]*field-stack field-stack--half"><span>\{\{ tp\("fieldsLongitude"\) \}\}<\/span><input v-model="checkpointDraft\.longitude"/);
  assert.match(source, /entityKey === 'patrol_route' && selectedRecord && !isCreatingRecord[\s\S]*field-stack field-stack--wide"><span>\{\{ tp\("fieldsLabel"\) \}\}<\/span><input v-model="checkpointDraft\.label"/);
  assert.match(source, /entityKey === 'patrol_route' && selectedRecord && !isCreatingRecord[\s\S]*field-stack field-stack--half"><span>\{\{ tp\("fieldsLatitude"\) \}\}<\/span><input v-model="checkpointDraft\.latitude"/);
  assert.match(source, /entityKey === 'patrol_route' && selectedRecord && !isCreatingRecord[\s\S]*field-stack field-stack--half"><span>\{\{ tp\("fieldsLongitude"\) \}\}<\/span><input v-model="checkpointDraft\.longitude"/);
});

test("planning setup supports inline shared-address creation modal for all address-backed entities", () => {
  assert.match(source, /<Modal[\s\S]*v-model:open="addressCreateModalOpen"[\s\S]*tp\('addressCreateModalTitle'\)/);
  assert.match(source, /v-model="addressDirectoryDraft\.street_line_1"/);
  assert.match(source, /v-model="addressDirectoryDraft\.postal_code"/);
  assert.match(source, /v-model="addressDirectoryDraft\.city"/);
  assert.match(source, /v-model="addressDirectoryDraft\.country_code"/);
  assert.match(source, /@click="submitAddressDirectoryEntry"/);
  assert.match(source, /@click="closeAddressCreateModal"/);
  assert.match(source, /const currentAddressFieldKey = computed\(\(\) => \{/);
  assert.match(source, /\["site", "event_venue", "trade_fair"\]\.includes\(editorEntityKey\.value\)/);
  assert.match(source, /editorEntityKey\.value === "patrol_route"/);
  assert.match(source, /const showAddressCreateAction = computed\(\(\) => !!currentAddressFieldKey\.value\)/);
});

test("planning list loading state drives the header badge and action disabling", () => {
  assert.match(source, /<StatusBadge :status="loading\.list \? 'inactive' : 'active'"/);
  assert.match(source, /:disabled="loading\.list \|\| loading\.action \|\| !canRead" @click="refreshRecords"/);
  assert.match(source, /:disabled="!actionState\.canCreate \|\| loading\.list \|\| loading\.action"/);
  assert.match(source, /:disabled="!actionState\.canImport \|\| loading\.list \|\| loading\.action"/);
});

test("planning failures and successful saves use unified feedback instead of browser alerts", () => {
  assert.match(source, /useSicherPlanFeedback/);
  assert.match(source, /const \{ showFeedbackToast \} = useSicherPlanFeedback\(\)/);
  assert.match(source, /function setFeedback\(tone, title, message\) \{[\s\S]*showFeedbackToast\(\{[\s\S]*key: "planning-admin-feedback"/);
  assert.match(source, /await createCustomerAvailableAddress\(/);
  assert.match(source, /await refreshSiteAddressOptions\(\);[\s\S]*draft\[addressCreateTargetField\.value\] = created\.id/s);
  assert.match(source, /closeAddressCreateModal\(\);[\s\S]*setFeedback\("success", tp\("successTitle"\), tp\("addressCreated"\)\)/s);
  assert.match(source, /setFeedback\("error", tp\("errorTitle"\), tp\(key\)\)/);
  assert.match(source, /setFeedback\("success", tp\("successTitle"\), tp\("recordSaved"\)\)/);
  assert.doesNotMatch(source, /alert\(/);
});
