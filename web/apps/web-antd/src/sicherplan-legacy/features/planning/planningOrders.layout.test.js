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
  assert.match(source, /data-testid="planning-orders-record-list-section"/);
  assert.match(source, /data-testid="planning-orders-detail-workspace"/);
  assert.match(source, /grid-template-columns:\s*minmax\(320px, 420px\) minmax\(0, 1fr\)/);
  assert.match(source, /class="module-card planning-orders-panel planning-orders-list-panel"/);
  assert.doesNotMatch(source, /v-if="feedback\.message"/);
  assert.doesNotMatch(source, /class="planning-orders-feedback"/);
});

test("planning-orders row badges stay bound to real release states and the header badge is contextual", () => {
  assert.match(source, /<StatusBadge :status="order\.release_state" \/>/);
  assert.match(source, /<StatusBadge :status="record\.release_state" \/>/);
  assert.match(source, /const detailHeaderBadgeStatus = computed\(\(\) => \{/);
  assert.match(source, /if \(activeMainTab\.value === "planning_records"\) \{\s*return selectedPlanningRecord\.value\?\.release_state \|\| "";/s);
  assert.match(source, /return selectedOrder\.value\?\.release_state \|\| "";/);
  assert.match(source, /<StatusBadge v-if="detailHeaderBadgeStatus" :status="detailHeaderBadgeStatus" \/>/);
  assert.doesNotMatch(source, /<StatusBadge v-if="selectedOrder" :status="selectedOrder\.release_state" \/>/);
});

test("planning-orders no longer renders the local hero and scope chrome", () => {
  assert.doesNotMatch(source, /planning-orders-hero/);
  assert.doesNotMatch(source, /planning-orders-scope/);
  assert.doesNotMatch(source, /rememberScopeAndToken/);
});

test("planning-orders bootstraps legacy auth session and uses effective scope/token before loading references", () => {
  assert.match(source, /useAuthStore as usePrimaryAuthStore/);
  assert.match(source, /const primaryAuthStore = usePrimaryAuthStore\(\)/);
  assert.match(source, /const tenantScopeId = computed\(\(\) => authStore\.effectiveTenantScopeId \|\| authStore\.tenantScopeId \|\| authStore\.sessionUser\?\.tenant_id \|\| ""\)/);
  assert.match(source, /const accessToken = computed\(\(\) => authStore\.effectiveAccessToken \|\| authStore\.accessToken\)/);
  assert.match(source, /async function ensurePlanningOrdersSessionReady\(\) \{\s*authStore\.syncFromPrimarySession\(\);[\s\S]*await authStore\.ensureSessionReady\(\);/s);
  assert.match(source, /async function handleAuthExpired\(\) \{[\s\S]*primaryAuthStore\.clearSessionState\(\);[\s\S]*primaryAuthStore\.redirectToLogin\("\/admin\/planning-orders"\);/s);
  assert.match(source, /onMounted\(async \(\) => \{[\s\S]*authStore\.syncFromPrimarySession\(\);[\s\S]*ensurePlanningOrdersSessionReady\(\);/s);
  assert.match(source, /document\.addEventListener\("visibilitychange", handleVisibilityChange\)/);
  assert.match(source, /window\.addEventListener\("focus", handleWindowFocus\)/);
});

test("planning-orders detail area uses the refined card sections", () => {
  assert.match(source, /\.planning-orders-section\s*\{[\s\S]*border-radius:\s*18px/);
  assert.doesNotMatch(source, /\.planning-orders-feedback\s*\{/);
});

test("planning-orders uses the shared bottom-right toast feedback composable", () => {
  assert.match(source, /useSicherPlanFeedback/);
  assert.match(source, /const \{ showFeedbackToast \} = useSicherPlanFeedback\(\)/);
  assert.match(source, /function setFeedback\(tone: string, title: string, message: string\) \{[\s\S]*showFeedbackToast\(\{[\s\S]*key: "planning-orders-feedback"/);
  assert.doesNotMatch(source, /function clearFeedback\(/);
});

test("planning-orders detail workspace uses main tabs for order and planning records", () => {
  assert.match(source, /data-testid="planning-orders-main-tabs"/);
  assert.match(source, /:data-testid="`planning-orders-main-tab-\$\{tab\.id\}`"/);
  assert.match(source, /data-testid="planning-orders-tab-panel-order"/);
  assert.match(source, /data-testid="planning-orders-main-panel-planning_records"/);
  assert.match(source, /const activeMainTab = ref\("order"\)/);
  assert.match(source, /const mainDetailTabs = computed\(\(\) => \[/);
  assert.match(source, /tabOrder/);
  assert.match(source, /tabPlanningRecords/);
  assert.doesNotMatch(source, /data-testid="planning-orders-tab-panel-commercial"/);
  assert.doesNotMatch(source, /data-testid="planning-orders-tab-panel-release"/);
  assert.doesNotMatch(source, /data-testid="planning-orders-tab-panel-documents"/);
});

test("planning-orders order workspace uses nested tabs for all order sections", () => {
  assert.match(source, /data-testid="planning-orders-order-tabs"/);
  assert.match(source, /:aria-label="tp\('orderOverviewDetailTabsAria'\)"/);
  assert.match(source, /:data-testid="`planning-orders-order-tab-\$\{tab\.id\}`"/);
  assert.match(source, /data-testid="planning-orders-order-panel-order_details"/);
  assert.match(source, /data-testid="planning-orders-order-panel-equipment_lines"/);
  assert.match(source, /data-testid="planning-orders-order-panel-requirement_lines"/);
  assert.match(source, /data-testid="planning-orders-order-panel-commercial"/);
  assert.match(source, /data-testid="planning-orders-order-panel-release"/);
  assert.match(source, /data-testid="planning-orders-order-panel-documents"/);
  assert.match(source, /const activeOrderTab = ref\("order_details"\)/);
  assert.match(source, /const orderTabs = computed\(\(\) => \{/);
  assert.match(source, /if \(!orderHasSavedRecord\.value\) \{\s*return tabs;/);
  assert.match(source, /v-show="activeOrderTab === 'order_details'"/);
  assert.match(source, /v-show="activeOrderTab === 'equipment_lines'"/);
  assert.match(source, /v-show="activeOrderTab === 'requirement_lines'"/);
  assert.match(source, /v-show="activeOrderTab === 'commercial'"/);
  assert.match(source, /v-show="activeOrderTab === 'release'"/);
  assert.match(source, /v-show="activeOrderTab === 'documents'"/);
  assert.match(source, /async function selectOrder\(orderId: string\) \{[\s\S]*activeMainTab\.value = "order";[\s\S]*activeOrderTab\.value = "order_details";/s);
  assert.match(source, /function startCreateOrder\(\) \{[\s\S]*activeMainTab\.value = "order";[\s\S]*activeOrderTab\.value = "order_details";/s);
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
  assert.match(source, /:options="requirementTypeSelectOptions"[\s\S]*:disabled="loading\.action"/);
});

test("planning-orders requirement type and patrol route actions are not wrapped in interactive labels", () => {
  assert.match(source, /<div class="field-stack">[\s\S]*id="planning-orders-requirement-type-label"[\s\S]*@mousedown\.stop[\s\S]*@click\.stop="openRequirementTypeModal"[\s\S]*:aria-labelledby="'planning-orders-requirement-type-label'"/s);
  assert.match(source, /<div class="field-stack">[\s\S]*id="planning-orders-patrol-route-label"[\s\S]*@mousedown\.stop[\s\S]*@click\.stop="openPatrolRouteModal"[\s\S]*:aria-labelledby="'planning-orders-patrol-route-label'"/s);
  assert.doesNotMatch(source, /<label class="field-stack">\s*<div class="planning-orders-field-header">\s*<span id="planning-orders-requirement-type-label"/s);
  assert.doesNotMatch(source, /<label class="field-stack">\s*<div class="planning-orders-field-header">\s*<span id="planning-orders-patrol-route-label"/s);
});

test("planning-orders overview exposes independent order child sections", () => {
  assert.match(source, /data-testid="planning-orders-order-panel-equipment_lines"/);
  assert.match(source, /data-testid="planning-orders-order-panel-requirement_lines"/);
  assert.match(source, /submitEquipmentLine/);
  assert.match(source, /submitRequirementLine/);
  assert.match(source, /listOrderEquipmentLines/);
  assert.match(source, /listOrderRequirementLines/);
  assert.match(source, /:options="equipmentItemSelectOptions"[\s\S]*:disabled="loading\.action"/);
  assert.match(source, /:options="requirementTypeSelectOptions"[\s\S]*:disabled="loading\.action"/);
  assert.match(source, /fieldsFunctionType/);
  assert.match(source, /fieldsQualificationType/);
  assert.match(source, /:options="functionTypeSelectOptions"[\s\S]*show-search[\s\S]*allow-clear/s);
  assert.match(source, /:options="qualificationTypeSelectOptions"[\s\S]*show-search[\s\S]*allow-clear/s);
  assert.match(source, /listFunctionTypes/);
  assert.match(source, /listQualificationTypes/);
  assert.match(source, /function_type_id: requirementLineDraft\.function_type_id \|\| null/);
  assert.match(source, /qualification_type_id: requirementLineDraft\.qualification_type_id \|\| null/);
  assert.match(source, /functionTypePlaceholder/);
  assert.match(source, /qualificationTypePlaceholder/);
});

test("planning-orders requirement lines support lifecycle actions, archived toggle, and duplicate guard", () => {
  assert.match(source, /const includeArchivedRequirementLines = ref\(false\)/);
  assert.match(source, /const selectedRequirementLine = computed\(/);
  assert.match(source, /const visibleRequirementLines = computed\(\(\) =>[\s\S]*filterVisibleRequirementLines\(orderRequirementLines\.value, includeArchivedRequirementLines\.value\)/s);
  assert.match(source, /v-model="includeArchivedRequirementLines"/);
  assert.match(source, /tp\("includeArchivedRequirementLines"\)/);
  assert.match(source, /v-for="line in visibleRequirementLines"/);
  assert.match(source, /tp\("requirementLineLifecycleHint"\)/);
  assert.match(source, /tp\("actionsDeactivateRequirementLine"\)/);
  assert.match(source, /tp\("actionsArchiveRequirementLine"\)/);
  assert.match(source, /tp\("actionsRestoreRequirementLine"\)/);
  assert.match(source, /async function deactivateRequirementLine\(\)/);
  assert.match(source, /async function archiveRequirementLine\(\)/);
  assert.match(source, /async function restoreRequirementLine\(\)/);
  assert.match(source, /status: "inactive"/);
  assert.match(source, /status: "archived", archived_at: new Date\(\)\.toISOString\(\)/);
  assert.match(source, /status: "active", archived_at: null/);
  assert.match(source, /hasDuplicateActiveRequirementLine\([\s\S]*requirementLineDraft\.requirement_type_id[\s\S]*requirementLineDraft\.function_type_id[\s\S]*requirementLineDraft\.qualification_type_id[\s\S]*selectedRequirementLineId\.value/s);
  assert.match(source, /tp\("requirementLineDuplicateActive"\)/);
  assert.match(source, /function syncRequirementLineDraft\(line: OrderRequirementLineRead\) \{[\s\S]*function_type_id: line\.function_type_id \?\? ""[\s\S]*qualification_type_id: line\.qualification_type_id \?\? ""/s);
});

test("planning-orders keeps planning-record browsing in the left workspace", () => {
  assert.match(source, /v-model="planningRecordFilters\.planning_mode_code"/);
  assert.match(source, /v-model="planningRecordFilters\.planning_from"/);
  assert.match(source, /v-model="planningRecordFilters\.planning_to"/);
  assert.match(source, /planningListOrderRequired/);
  assert.match(source, /planningListEmpty/);
  assert.match(source, /@click="selectPlanningRecord\(record\.id\)"/);
});

test("planning-record detail workspace uses nested tabs inside the planning-records tab", () => {
  assert.match(source, /data-testid="planning-orders-main-panel-planning_records"/);
  assert.match(source, /data-testid="planning-records-detail-tabs"/);
  assert.match(source, /:aria-label="tp\('planningRecordDetailTabsAria'\)"/);
  assert.match(source, /:data-testid="`planning-records-tab-\$\{tab\.id\}`"/);
  assert.match(source, /data-testid="planning-records-tab-panel-overview"/);
  assert.match(source, /data-testid="planning-records-tab-panel-commercial"/);
  assert.match(source, /data-testid="planning-records-tab-panel-release"/);
  assert.match(source, /data-testid="planning-records-tab-panel-documents"/);
  assert.match(source, /const activePlanningDetailTab = ref\("overview"\)/);
  assert.match(source, /const planningDetailTabs = computed\(\(\) => \{/);
  assert.match(source, /if \(!planningHasSavedRecord\.value\) \{\s*return tabs;/);
  assert.match(source, /v-show="activePlanningDetailTab === 'overview'"/);
  assert.match(source, /v-show="activePlanningDetailTab === 'commercial'"/);
  assert.match(source, /v-show="activePlanningDetailTab === 'release'"/);
  assert.match(source, /v-show="activePlanningDetailTab === 'documents'"/);
  assert.match(source, /function startCreatePlanning\(\) \{[\s\S]*activeMainTab\.value = "planning_records";[\s\S]*activePlanningDetailTab\.value = "overview";/s);
  assert.match(source, /async function selectPlanningRecord\(planningRecordId: string\) \{[\s\S]*activeMainTab\.value = "planning_records";[\s\S]*activePlanningDetailTab\.value = "overview";/s);
});

test("planning-orders enforces read-only fieldsets for controller_qm-style access", () => {
  assert.match(source, /<fieldset class="planning-orders-fieldset" :disabled="!actionState\.canWriteOrders \|\| loading\.action">/);
  assert.match(source, /<fieldset class="planning-orders-fieldset" :disabled="!actionState\.canWritePlanning \|\| loading\.action">/);
  assert.match(source, /<fieldset class="planning-orders-fieldset" :disabled="!actionState\.canManageOrderDocs \|\| loading\.action">/);
  assert.match(source, /<fieldset class="planning-orders-fieldset" :disabled="!actionState\.canManagePlanningDocs \|\| loading\.action">/);
});

test("planning-orders detail form uses friendly labels and inline placeholders", () => {
  assert.match(source, /tp\('fieldsCustomer'\)/);
  assert.match(source, /tp\("fieldsRequirementType"\)/);
  assert.match(source, /tp\("fieldsPatrolRoute"\)/);
  assert.match(source, /tp\("fieldsServiceCategory"\)/);
  assert.match(source, /tp\("requirementTypeSetupMissing"\)/);
  assert.match(source, /tp\("patrolRouteSetupMissing"\)/);
  assert.match(source, /:options="serviceCategorySelectOptions"/);
  assert.match(source, /:placeholder="serviceCategoryPlaceholder"/);
  assert.match(source, /serviceCategoryLegacyValue/);
  assert.match(source, /tp\("serviceCategoryRequired"\)/);
  assert.match(source, /tp\("actionsOpenPlanningSetup"\)/);
  assert.match(source, /tp\("actionsAddRequirementType"\)/);
  assert.match(source, /tp\("actionsAddPatrolRoute"\)/);
  assert.match(source, /:placeholder="requirementTypePlaceholder"/);
  assert.match(source, /:placeholder="patrolRoutePlaceholder"/);
  assert.match(source, /:value="orderDraft\.requirement_type_id \|\| undefined"/);
  assert.match(source, /:value="orderDraft\.patrol_route_id \|\| undefined"/);
  assert.match(source, /:value="orderDraft\.service_category_code \|\| undefined"/);
  assert.doesNotMatch(source, /fieldsServiceCategory[\s\S]*<input v-model="orderDraft\.service_category_code"/);
  assert.doesNotMatch(source, /tp\("requirementTypeEmpty"\)\s*<\/p>/);
  assert.doesNotMatch(source, /tp\("patrolRouteEmpty"\)\s*<\/p>/);
  assert.doesNotMatch(source, /serviceCategoryManualHelp/);
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

test("planning-record create form validates the order window before submit", () => {
  assert.match(source, /validatePlanningRecordDraft\(/);
  assert.match(source, /const planningRecordValidation = computed\(\(\) =>/);
  assert.match(source, /const planningWindowHelp = computed\(\(\) =>/);
  assert.match(source, /tpf\("planningWindowAllowed", \{/);
  assert.match(source, /v-model="planningDraft\.planning_from"[\s\S]*:min="planningFromMin"[\s\S]*:max="planningFromMax"/s);
  assert.match(source, /v-model="planningDraft\.planning_to"[\s\S]*:min="planningToMin"[\s\S]*:max="planningToMax"/s);
  assert.match(source, /planningValidationState\.attempted = true;[\s\S]*planningRecordValidation\.value\.messageKey/s);
});

test("planning-record mode-specific empty states expose direct planning-setup recovery", () => {
  assert.match(source, /@click="openPlanningSetup\('event_venue'\)"/);
  assert.match(source, /@click="openPlanningSetup\('site'\)"/);
  assert.match(source, /@click="openPlanningSetup\('trade_fair'\)"/);
  assert.match(source, /@click="openPlanningSetup\('patrol_route'\)"/);
  assert.match(source, /tp\("eventVenueRequired"\)/);
  assert.match(source, /tp\("siteRequired"\)/);
  assert.match(source, /tp\("tradeFairRequired"\)/);
  assert.match(source, /tp\("patrolRouteRequired"\)/);
});

test("planning-record status is edit-only and no longer sent on create", () => {
  assert.doesNotMatch(source, /fieldsStatus[\s\S]*<input v-model="planningDraft\.status"/);
  assert.match(source, /v-if="!isCreatingPlanning && selectedPlanningRecord"[\s\S]*fieldsStatus[\s\S]*v-model="planningDraft\.status"/s);
  assert.doesNotMatch(source, /notes:\s*planningDraft\.notes \|\| null,\s*status:/);
  assert.match(source, /if \(includeVersion && selectedPlanningRecord\.value\) \{[\s\S]*payload\.version_no = selectedPlanningRecord\.value\.version_no;[\s\S]*payload\.status = planningDraft\.status \|\| selectedPlanningRecord\.value\.status \|\| "active";/s);
});

test("planning-record overview explains immutable mode and exposes explicit lifecycle actions", () => {
  assert.match(source, /<select v-model="planningDraft\.planning_mode_code" :disabled="!isCreatingPlanning">/);
  assert.match(source, /v-if="!isCreatingPlanning && selectedPlanningRecord" class="field-help">[\s\S]*tp\("planningModeImmutableHelp"\)/s);
  assert.match(source, /tp\("actionsDeactivatePlanningRecord"\)/);
  assert.match(source, /tp\("actionsReactivatePlanningRecord"\)/);
  assert.match(source, /tp\("actionsArchivePlanningRecord"\)/);
  assert.match(source, /tp\("actionsCreateReplacementPlanning"\)/);
  assert.match(source, /async function deactivatePlanningRecord\(\)/);
  assert.match(source, /async function reactivatePlanningRecord\(\)/);
  assert.match(source, /async function archivePlanningRecord\(\)/);
  assert.match(source, /status: "inactive"/);
  assert.match(source, /status: "active"/);
  assert.match(source, /archived_at: new Date\(\)\.toISOString\(\)/);
  assert.match(source, /function startReplacementPlanning\(\)/);
  assert.match(source, /function prefillReplacementPlanningDraft\(\)/);
  assert.doesNotMatch(source, /Delete planning/i);
});

test("planning-record update payload excludes unsupported mode and parent top-level fields", () => {
  assert.match(source, /function buildPlanningPayload\(includeVersion = false\) \{/);
  assert.match(source, /const payload: Record<string, unknown> = \{[\s\S]*dispatcher_user_id:[\s\S]*name:[\s\S]*planning_from:[\s\S]*planning_to:[\s\S]*notes:/s);
  assert.match(source, /if \(!includeVersion\) \{[\s\S]*payload\.order_id = selectedOrderId\.value;[\s\S]*payload\.parent_planning_record_id = planningDraft\.parent_planning_record_id \|\| null;[\s\S]*payload\.planning_mode_code = planningDraft\.planning_mode_code;/s);
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
  assert.match(source, /listPlanningRecords\(tenantScopeId\.value, accessToken\.value, \{[\s\S]*order_id: selectedOrderId\.value[\s\S]*planning_mode_code: planningRecordFilters\.planning_mode_code/);
  assert.match(source, /filterPlanningOrderOptionsByScope\("requirement_type"/);
  assert.match(source, /filterPlanningOrderOptionsByScope\([\s\S]*"equipment_item"/);
  assert.match(source, /filterPlanningOrderOptionsByScope\("event_venue"/);
  assert.match(source, /filterPlanningOrderOptionsByScope\("site"/);
  assert.match(source, /filterPlanningOrderOptionsByScope\("trade_fair"/);
  assert.match(source, /filterPlanningOrderOptionsByScope\("patrol_route"/);
});

test("planning-record dispatcher selector shows IAM guidance and defaults only for new records", () => {
  assert.match(source, /<p class="field-help">{{ tp\("dispatcherIamHint"\) }}<\/p>/);
  assert.match(source, /const currentSessionUserId = computed\(\(\) => authStore\.sessionUser\?\.id \|\| ""\);/);
  assert.match(source, /function applyDefaultDispatcherForNewPlanning\(\) \{/);
  assert.match(source, /if \(!isCreatingPlanning\.value \|\| planningDraft\.dispatcher_user_id \|\| !currentSessionUserId\.value\) \{/);
  assert.match(source, /const currentUserCandidate = dispatcherOptions\.value\.find\(\(row\) => row\.id === currentSessionUserId\.value\);/);
  assert.match(source, /planningDraft\.dispatcher_user_id = currentUserCandidate\.id;/);
  assert.match(source, /function startCreatePlanning\(\) \{[\s\S]*resetPlanningDraft\(\);[\s\S]*applyDefaultDispatcherForNewPlanning\(\);/s);
  assert.match(source, /async function refreshDispatcherOptions\(\) \{[\s\S]*catch \{[\s\S]*dispatcherOptions\.value = \[\];[\s\S]*dispatcherLookupError\.value = tp\("dispatcherLoadError"\);/s);
  assert.doesNotMatch(source, /async function refreshDispatcherOptions\(\) \{[\s\S]*catch \{[\s\S]*planningDraft\.dispatcher_user_id = ""/s);
});

test("planning-orders exposes inline setup links, add buttons, and real create modals", () => {
  assert.match(source, /@click="openPlanningSetup\('requirement_type'\)"/);
  assert.match(source, /@click="openPlanningSetup\('patrol_route'\)"/);
  assert.match(source, /@mousedown\.stop[\s\S]*@click\.stop="openRequirementTypeModal"/);
  assert.match(source, /@mousedown\.stop[\s\S]*@click\.stop="openPatrolRouteModal"/);
  assert.match(source, /v-model:open="requirementTypeModal\.open"/);
  assert.match(source, /v-model:open="patrolRouteModal\.open"/);
  assert.match(source, /@ok="submitRequirementTypeModal"/);
  assert.match(source, /@ok="submitPatrolRouteModal"/);
});

test("planning-orders groups service dates and release state into one desktop row", () => {
  assert.match(source, /class="planning-orders-form-row planning-orders-form-row--triple"/);
  assert.match(source, /\.planning-orders-form-row--triple\s*\{[\s\S]*grid-template-columns:\s*repeat\(3, minmax\(0, 1fr\)\)/);
});

test("planning-orders document tabs use selectable rows and inline action panels", () => {
  assert.match(source, /const selectedOrderDocumentId = ref\(""\)/);
  assert.match(source, /const selectedPlanningDocumentId = ref\(""\)/);
  assert.match(source, /const selectedOrderDocument = computed\(/);
  assert.match(source, /const selectedPlanningDocument = computed\(/);
  assert.match(source, /@click="selectOrderDocument\(document\.id\)"/);
  assert.match(source, /@click="selectPlanningDocument\(document\.id\)"/);
  assert.match(source, /class="planning-orders-doc-row planning-orders-doc-button"/);
  assert.match(source, /:class="\{ selected: document\.id === selectedOrderDocumentId \}"/);
  assert.match(source, /:class="\{ selected: document\.id === selectedPlanningDocumentId \}"/);
  assert.match(source, /data-testid="planning-orders-order-document-detail"/);
  assert.match(source, /data-testid="planning-orders-planning-document-detail"/);
  assert.match(source, /downloadOrderDocumentSelection/);
  assert.match(source, /downloadPlanningDocumentSelection/);
  assert.match(source, /copyOrderDocumentId/);
  assert.match(source, /copyPlanningDocumentId/);
  assert.match(source, /clearOrderDocumentSelection/);
  assert.match(source, /clearPlanningDocumentSelection/);
  assert.match(source, /tp\("actionsDownloadCurrentVersion"\)/);
  assert.match(source, /tp\("actionsCopyDocumentId"\)/);
  assert.match(source, /tp\("actionsClearDocumentSelection"\)/);
  assert.match(source, /tp\("documentSelectionEmpty"\)/);
});

test("planning-orders wrapper skips the extra workspace block but keeps the shared intro", () => {
  assert.match(
    registrySource,
    /'planning-orders':\s*\{[\s\S]*showWorkspaceSectionHeader:\s*false/,
  );
});
