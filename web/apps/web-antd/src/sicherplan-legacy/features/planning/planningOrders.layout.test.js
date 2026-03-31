import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const viewPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue",
);
const registryPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/views/sicherplan/module-registry.ts",
);
const source = readFileSync(viewPath, "utf8");
const registrySource = readFileSync(registryPath, "utf8");

test("planning-orders uses the customer-style master detail shell", () => {
  assert.match(source, /data-testid="planning-orders-master-detail-layout"/);
  assert.match(source, /data-testid="planning-orders-list-section"/);
  assert.match(source, /data-testid="planning-orders-detail-workspace"/);
  assert.match(source, /grid-template-columns:\s*minmax\(320px, 420px\) minmax\(0, 1fr\)/);
  assert.match(source, /class="module-card planning-orders-panel planning-orders-list-panel"/);
});

test("planning-orders no longer renders the local hero and scope chrome", () => {
  assert.doesNotMatch(source, /planning-orders-hero/);
  assert.doesNotMatch(source, /planning-orders-scope/);
  assert.doesNotMatch(source, /rememberScopeAndToken/);
});

test("planning-orders detail area uses the refined card sections", () => {
  assert.match(source, /\.planning-orders-section\s*\{[\s\S]*border-radius:\s*18px/);
  assert.match(source, /\.planning-orders-feedback\s*\{[\s\S]*border-radius:\s*18px/);
});

test("planning-orders detail workspace uses local customer-style tabs", () => {
  assert.match(source, /data-testid="planning-orders-detail-tabs"/);
  assert.match(source, /:data-testid="`planning-orders-tab-\$\{tab\.id\}`"/);
  assert.match(source, /data-testid="planning-orders-tab-panel-overview"/);
  assert.match(source, /data-testid="planning-orders-tab-panel-commercial"/);
  assert.match(source, /data-testid="planning-orders-tab-panel-release"/);
  assert.match(source, /data-testid="planning-orders-tab-panel-documents"/);
  assert.match(source, /data-testid="planning-orders-tab-panel-planning-records"/);
  assert.match(source, /const activeDetailTab = ref\("overview"\)/);
  assert.match(source, /const orderDetailTabs = computed\(\(\) => \{/);
  assert.match(source, /if \(!orderHasSavedRecord\.value\) \{\s*return tabs;/);
});

test("planning-orders commercial tab shows customer-specific guidance and readable issue lists", () => {
  assert.match(source, /commercialSummaryKey/);
  assert.match(source, /commercialContextKey/);
  assert.match(source, /hasCommercialBlockingIssues/);
  assert.match(source, /hasCommercialWarningIssues/);
  assert.match(source, /showCommercialFixHint/);
  assert.match(source, /showCommercialReviewHint/);
  assert.match(source, /showCommercialSettingsCta/);
  assert.match(source, /selectedOrderCustomerLabel/);
  assert.match(source, /<p v-if="showCommercialFixHint" class="field-help">/);
  assert.match(source, /<p v-else-if="showCommercialReviewHint" class="field-help">/);
  assert.match(source, /tpf\("commercialFixHint"/);
  assert.match(source, /tpf\("commercialReviewHint"/);
  assert.match(source, /<div v-if="showCommercialSettingsCta" class="cta-row">/);
  assert.match(source, /tp\("commercialActionOpenCustomerCommercial"\)/);
  assert.match(source, /resolveCommercialIssueMessage\(issue\.code\)/);
  assert.doesNotMatch(source, /<p class="field-help">\s*\{\{\s*selectedOrderCustomerLabel\s*\?\s*tpf\("commercialFixHint"/);
  assert.doesNotMatch(source, /<li v-for="issue in selectedOrderCommercial\.blocking_issues"[^>]*>{{ issue\.code }}/);
});

test("planning-orders reuses the shared customer-style CTA row pattern", () => {
  assert.doesNotMatch(source, /\.cta-row\s*\{/);
  assert.match(source, /class="cta-button"/);
  assert.match(source, /class="cta-button cta-secondary"/);
});

test("planning-orders order form uses domain-aligned controls", () => {
  assert.match(
    source,
    /<PlanningCustomerSelect[\s\S]*v-model="orderDraft\.customer_id"[\s\S]*fieldsOrderNo[\s\S]*fieldsRequirementType[\s\S]*fieldsPatrolRoute/s,
  );
  assert.match(source, /<PlanningCustomerSelect[\s\S]*v-model="orderDraft\.customer_id"[\s\S]*:invalid="customerFieldInvalid"/);
  assert.match(source, /:value="orderDraft\.requirement_type_id \|\| undefined"[\s\S]*show-search[\s\S]*:status="requirementTypeLookupError \|\| requirementTypeFieldInvalid \? 'error' : undefined"/);
  assert.match(source, /:value="orderDraft\.patrol_route_id \|\| undefined"[\s\S]*show-search/);
  assert.match(source, /v-model="orderDraft\.release_state"/);
  assert.doesNotMatch(source, /v-model="orderDraft\.status"/);
});

test("planning-orders detail form uses friendly labels and inline placeholders", () => {
  assert.match(source, /tp\('fieldsCustomer'\)/);
  assert.match(source, /tp\("fieldsRequirementType"\)/);
  assert.match(source, /tp\("fieldsPatrolRoute"\)/);
  assert.match(source, /tp\("requirementTypeSetupMissing"\)/);
  assert.match(source, /tp\("patrolRouteSetupMissing"\)/);
  assert.match(source, /tp\("serviceCategoryManualHelp"\)/);
  assert.match(source, /tp\("actionsOpenPlanningSetup"\)/);
  assert.match(source, /tp\("actionsAddRequirementType"\)/);
  assert.match(source, /tp\("actionsAddPatrolRoute"\)/);
  assert.match(source, /:placeholder="requirementTypePlaceholder"/);
  assert.match(source, /:placeholder="patrolRoutePlaceholder"/);
  assert.match(source, /:value="orderDraft\.requirement_type_id \|\| undefined"/);
  assert.match(source, /:value="orderDraft\.patrol_route_id \|\| undefined"/);
  assert.doesNotMatch(source, /tp\("requirementTypeEmpty"\)\s*<\/p>/);
  assert.doesNotMatch(source, /tp\("patrolRouteEmpty"\)\s*<\/p>/);
});

test("planning-record detail form replaces raw UUID fields with selectors", () => {
  assert.doesNotMatch(source, /fieldsDispatcherUserId[\s\S]*<input v-model="planningDraft\.dispatcher_user_id"/);
  assert.doesNotMatch(source, /fieldsParentPlanningRecordId[\s\S]*<input v-model="planningDraft\.parent_planning_record_id"/);
  assert.doesNotMatch(source, /fieldsEventVenueId[\s\S]*<input v-model="planningDraft\.event_detail\.event_venue_id"/);
  assert.doesNotMatch(source, /fieldsSiteId[\s\S]*<input v-model="planningDraft\.site_detail\.site_id"/);
  assert.doesNotMatch(source, /fieldsTradeFairId[\s\S]*<input v-model="planningDraft\.trade_fair_detail\.trade_fair_id"/);
  assert.doesNotMatch(source, /fieldsTradeFairZoneId[\s\S]*<input v-model="planningDraft\.trade_fair_detail\.trade_fair_zone_id"/);
  assert.doesNotMatch(source, /fieldsPatrolRouteDetailId[\s\S]*<input v-model="planningDraft\.patrol_detail\.patrol_route_id"/);
  assert.match(source, /fieldsDispatcherUserId[\s\S]*:value="planningDraft\.dispatcher_user_id \|\| undefined"[\s\S]*dispatcherPlaceholder/s);
  assert.match(source, /fieldsParentPlanningRecordId[\s\S]*:value="planningDraft\.parent_planning_record_id \|\| undefined"[\s\S]*parentPlanningRecordPlaceholder/s);
  assert.match(source, /fieldsEventVenueId[\s\S]*:value="planningDraft\.event_detail\.event_venue_id \|\| undefined"[\s\S]*eventVenuePlaceholder/s);
  assert.match(source, /fieldsSiteId[\s\S]*:value="planningDraft\.site_detail\.site_id \|\| undefined"[\s\S]*sitePlaceholder/s);
  assert.match(source, /fieldsTradeFairId[\s\S]*:value="planningDraft\.trade_fair_detail\.trade_fair_id \|\| undefined"[\s\S]*tradeFairPlaceholder/s);
  assert.match(source, /fieldsTradeFairZoneId[\s\S]*:value="planningDraft\.trade_fair_detail\.trade_fair_zone_id \|\| undefined"[\s\S]*tradeFairZonePlaceholder/s);
  assert.match(source, /fieldsPatrolRouteDetailId[\s\S]*:value="planningDraft\.patrol_detail\.patrol_route_id \|\| undefined"[\s\S]*patrolRouteDetailPlaceholder/s);
});

test("planning-record status is edit-only and no longer sent on create", () => {
  assert.doesNotMatch(source, /fieldsStatus[\s\S]*<input v-model="planningDraft\.status"/);
  assert.match(source, /v-if="!isCreatingPlanning && selectedPlanningRecord"[\s\S]*fieldsStatus[\s\S]*v-model="planningDraft\.status"/s);
  assert.doesNotMatch(source, /notes:\s*planningDraft\.notes \|\| null,\s*status:/);
  assert.match(source, /if \(includeVersion && selectedPlanningRecord\.value\) \{[\s\S]*payload\.version_no = selectedPlanningRecord\.value\.version_no;[\s\S]*payload\.status = planningDraft\.status \|\| selectedPlanningRecord\.value\.status \|\| "active";/s);
});

test("planning-record trade-fair zone selector depends on selected trade fair", () => {
  assert.match(source, /watch\(\s*\(\) => planningDraft\.trade_fair_detail\.trade_fair_id,/);
  assert.match(source, /await refreshTradeFairZoneOptions\(tradeFairId\);/);
  assert.match(source, /:disabled="loading\.action \|\| !planningDraft\.trade_fair_detail\.trade_fair_id"/);
});

test("planning-record selectors reuse the correct lookup sources", () => {
  assert.match(source, /await listPlanningDispatcherCandidates\(tenantScopeId\.value, accessToken\.value\)/);
  assert.match(source, /listPlanningCatalogRecords\(\s*"event_venue"/);
  assert.match(source, /listPlanningCatalogRecords\(\s*"site"/);
  assert.match(source, /listPlanningCatalogRecords\(\s*"trade_fair"/);
  assert.match(source, /listPlanningCatalogRecords\(\s*"patrol_route"/);
  assert.match(source, /await listTradeFairZones\(tenantScopeId\.value, tradeFairId, accessToken\.value\)/);
  assert.match(source, /listPlanningRecords\(tenantScopeId\.value, accessToken\.value, \{ order_id: selectedOrderId\.value \}\)/);
});

test("planning-orders exposes inline setup links, add buttons, and real create modals", () => {
  assert.match(source, /@click="openPlanningSetup\('requirement_type'\)"/);
  assert.match(source, /@click="openPlanningSetup\('patrol_route'\)"/);
  assert.match(source, /@click="openRequirementTypeModal"/);
  assert.match(source, /@click="openPatrolRouteModal"/);
  assert.match(source, /v-model:open="requirementTypeModal\.open"/);
  assert.match(source, /v-model:open="patrolRouteModal\.open"/);
  assert.match(source, /@ok="submitRequirementTypeModal"/);
  assert.match(source, /@ok="submitPatrolRouteModal"/);
});

test("planning-orders groups service dates and release state into one desktop row", () => {
  assert.match(source, /class="planning-orders-form-row planning-orders-form-row--triple"/);
  assert.match(source, /\.planning-orders-form-row--triple\s*\{[\s\S]*grid-template-columns:\s*repeat\(3, minmax\(0, 1fr\)\)/);
});

test("planning-orders wrapper skips the extra workspace block but keeps the shared intro", () => {
  assert.match(
    registrySource,
    /'planning-orders':\s*\{[\s\S]*showWorkspaceSectionHeader:\s*false/,
  );
});
