import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const viewPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue",
);
const source = readFileSync(viewPath, "utf8");

test("customer workspace uses a single-column list-then-detail layout with detail tabs", () => {
  assert.match(source, /<SicherPlanLoadingOverlay[\s\S]*busy-testid="customer-workspace-loading-overlay"/);
  assert.match(source, /:busy="customerWorkspaceBusy"/);
  assert.match(source, /:text="customerWorkspaceLoadingText"/);
  assert.match(source, /const customerWorkspaceBusy = computed\(/);
  assert.match(source, /loading\.customer/);
  assert.match(source, /loading\.contact/);
  assert.match(source, /loading\.address/);
  assert.match(source, /loading\.commercial/);
  assert.match(source, /loading\.rateLine/);
  assert.match(source, /loading\.surchargeRule/);
  assert.match(source, /loading\.portalAccess/);
  assert.match(source, /loading\.portalPrivacy/);
  assert.match(source, /loading\.historyAttachment/);
  assert.match(source, /loading\.employeeBlock/);
  assert.match(source, /loading\.sharedAddress/);
  assert.match(source, /loading\.hrCatalogBootstrap/);
  assert.match(source, /const customerWorkspaceLoadingText = computed\(\(\) =>/);
  assert.match(source, /class="customer-admin-grid"/);
  assert.match(source, /\.customer-admin-grid \{[\s\S]*grid-template-columns: minmax\(0, 1fr\);/);
  assert.match(source, /data-testid="customer-list-section"/);
  assert.match(source, /data-testid="customer-detail-workspace"/);
  assert.match(source, /data-testid="customer-detail-tabs"/);
  assert.match(source, /\.customer-admin-list-panel \{[\s\S]*position: static;/);
  assert.match(source, /resolveCustomerAdminRouteContext\(route\.query\)/);
});

test("customer list panel keeps filters and actions but removes inline customer rows", () => {
  const listSectionMatch = source.match(
    /<section class="module-card customer-admin-panel customer-admin-list-panel" data-testid="customer-list-section">([\s\S]*?)<\/section>/,
  );
  assert.ok(listSectionMatch, "customer list section should exist");
  const listSection = listSectionMatch[1];
  assert.match(listSection, /customerAdmin\.filters\.search/);
  assert.match(listSection, /customerAdmin\.actions\.search/);
  assert.match(listSection, /customerAdmin\.actions\.exportCustomers/);
  assert.match(listSection, /customerAdmin\.actions\.newCustomer/);
  assert.match(listSection, /class="customer-admin-filter-grid"/);
  assert.match(listSection, /class="customer-admin-filter-actions"/);
  assert.match(listSection, /class="cta-row customer-admin-filter-actions__buttons"/);
  assert.match(listSection, /data-testid="customer-search-select"/);
  assert.match(listSection, /data-testid="customer-search-select-input"/);
  assert.doesNotMatch(listSection, /customer-admin-row/);
  assert.doesNotMatch(listSection, /v-for="customer in customers"/);
  assert.doesNotMatch(listSection, /customerAdmin\.list\.sidebarNavigationHint/);

  const listSectionIndex = source.indexOf('data-testid="customer-list-section"');
  const detailSectionIndex = source.indexOf('data-testid="customer-detail-workspace"');
  assert.ok(listSectionIndex >= 0 && detailSectionIndex >= 0 && listSectionIndex < detailSectionIndex);
});

test("customer list filter layout uses a dedicated responsive grid and compact action row", () => {
  assert.match(source, /\.customer-admin-filter-grid \{[\s\S]*grid-template-columns: repeat\(4, minmax\(0, 1fr\)\);/);
  assert.match(
    source,
    /@media \(max-width: 1280px\) \{[\s\S]*\.customer-admin-filter-grid \{[\s\S]*grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/,
  );
  assert.match(source, /@media \(max-width: 720px\) \{[\s\S]*\.customer-admin-filter-grid \{[\s\S]*grid-template-columns: 1fr;/);
  assert.match(source, /\.customer-admin-filter-actions \{[\s\S]*justify-content: space-between;[\s\S]*align-items: center;/);
  assert.match(source, /\.customer-admin-filter-actions__buttons \{[\s\S]*justify-content: flex-end;/);
  assert.match(source, /@media \(max-width: 720px\) \{[\s\S]*\.customer-admin-filter-actions \{[\s\S]*flex-direction: column;/);
  assert.match(source, /@media \(max-width: 720px\) \{[\s\S]*\.customer-admin-filter-actions__buttons \{[\s\S]*justify-content: flex-start;/);
});

test("customer search uses debounced modal-backed results and dashboard selection", () => {
  assert.match(source, /customerSearchModalOpen = ref\(false\)/);
  assert.match(source, /customerSearchResults = ref<CustomerListItem\[\]>\(\[\]\)/);
  assert.match(source, /customerSearchSuggestions = ref<CustomerListItem\[\]>\(\[\]\)/);
  assert.match(source, /loading = reactive\(\{[\s\S]*customerSearch: false,/);
  assert.match(source, /setTimeout\(\(\) => \{[\s\S]*runCustomerSearch\(\{ suppressFeedback: true \}\)/);
  assert.match(source, /await listCustomers\([\s\S]*buildCustomerSearchParams/);
  assert.match(source, /data-testid="customer-search-results-modal"/);
  assert.match(source, /data-testid="customer-search-result-row"/);
  assert.match(source, /data-testid="customer-search-result-empty"/);
  assert.match(source, /data-testid="customer-search-result-close"/);
  assert.match(source, /role="dialog"/);
  assert.match(source, /window\.addEventListener\("keydown", handleCustomerSearchWindowKeydown\)/);
  assert.match(source, /event\.key === "Escape"/);
  assert.match(source, /await router\.replace\([\s\S]*customer_id: customerId,[\s\S]*tab: "dashboard"/);
});

test("customer workspace removes the manual bearer-token gate and only keeps tenant switching for platform admins", () => {
  assert.match(source, /<div v-if="isPlatformAdmin" class="module-card customer-admin-scope"/);
  assert.match(source, /<section v-if="isCustomerSessionResolving && !tenantScopeId" class="module-card customer-admin-empty">/);
  assert.match(source, /<section v-else-if="!tenantScopeId" class="module-card customer-admin-empty">/);
  assert.match(source, /const isPlatformAdmin = computed\(\(\) => authStore\.effectiveRole === "platform_admin"\)/);
  assert.match(source, /const tenantScopeId = computed\(\(\) => authStore\.effectiveTenantScopeId\)/);
  assert.match(source, /const accessToken = computed\(\(\) => authStore\.effectiveAccessToken \|\| authStore\.accessToken\)/);
  assert.match(source, /const isCustomerSessionResolving = computed\(\(\) => authStore\.isSessionResolving\)/);
  assert.match(source, /authStore\.syncFromPrimarySession\(\)/);
  assert.match(source, /await authStore\.ensureSessionReady\(\)/);
  assert.match(source, /syncCustomerSessionState\(\)/);
  assert.doesNotMatch(source, /customerAdmin\.token\.label/);
  assert.doesNotMatch(source, /customerAdmin\.token\.placeholder/);
  assert.doesNotMatch(source, /customerAdmin\.token\.help/);
  assert.doesNotMatch(source, /rememberScopeAndToken/);
  assert.doesNotMatch(source, /accessTokenInput/);
  assert.doesNotMatch(source, /readStoredAccessToken/);
  assert.doesNotMatch(source, /ACCESS_TOKEN_STORAGE_KEY/);
});

test("customer workspace keeps the draft workspace mounted during session reconciliation", () => {
  assert.match(source, /isCustomerSessionResolving\.value/);
  assert.match(source, /workspace\.loading\.reconcilingSession/);
  assert.match(source, /customerAdmin\.scope\.reconcilingTitle/);
  assert.match(source, /customerAdmin\.scope\.reconcilingBody/);
  assert.match(source, /isCustomerSessionResolving\.value\s*\|\|\s*loading\.customer/);
});

test("customer same-record reloads preserve nested tab context with safe fallbacks", () => {
  assert.match(source, /type SelectCustomerOptions = \{/);
  assert.match(source, /preserveDetailTab\?: boolean/);
  assert.match(source, /preserveCommercialTab\?: boolean/);
  assert.match(source, /preservePricingRulesTab\?: boolean/);
  assert.match(source, /preserveSelectedRateCard\?: boolean/);
  assert.match(source, /function buildPreservedCustomerSelectionOptions\(\): SelectCustomerOptions/);
  assert.match(source, /preferredDetailTab: activeDetailTab\.value/);
  assert.match(source, /preferredCommercialTab: activeCommercialTab\.value/);
  assert.match(source, /preferredPricingRulesTab: activePricingRulesTab\.value/);
  assert.match(source, /preferredRateCardId: selectedRateCardId\.value/);
  assert.match(source, /async function selectCustomer\(customerId: string, options: SelectCustomerOptions = \{\}\)/);
  assert.match(source, /activeDetailTab\.value = normalizeCustomerDetailTab\(desiredDetailTab/);
  assert.match(source, /activeCommercialTab\.value = normalizeCustomerCommercialTab\(desiredCommercialTab\)/);
  assert.match(source, /activePricingRulesTab\.value = normalizeCustomerPricingRulesTab\(desiredPricingRulesTab/);
  assert.match(source, /selectedRateCardId\.value = resolveCustomerSelectedRateCardId\(/);
  assert.match(source, /await selectCustomer\(selectedCustomer\.value\.id, buildPreservedCustomerSelectionOptions\(\)\)/);
  assert.match(source, /await refreshCustomers\(\{\s*preferredCustomerId: updated\.id,[\s\S]*selectionOptions: buildPreservedCustomerSelectionOptions\(\)/);
});

test("existing customers default to dashboard while create mode stays on overview", () => {
  assert.match(source, /import CustomerDashboardTab from "@\/components\/customers\/CustomerDashboardTab\.vue"/);
  assert.match(source, /import CustomerPlansTab from "@\/components\/customers\/CustomerPlansTab\.vue"/);
  assert.match(source, /dashboard:\s*"customerAdmin\.tabs\.dashboard"/);
  assert.match(source, /plans:\s*"customerAdmin\.tabs\.plans"/);
  assert.match(
    source,
    /<CustomerDashboardTab[\s\S]*v-if="selectedCustomer && !isCreatingCustomer && activeDetailTab === 'dashboard'"/,
  );
  assert.match(
    source,
    /<CustomerPlansTab[\s\S]*v-if="selectedCustomer && !isCreatingCustomer && canReadPlans && activeDetailTab === 'plans'"/,
  );
  assert.match(source, /customerDashboard = ref<CustomerDashboardRead \| null>\(null\)/);
  assert.match(source, /customerDashboardError = ref\(""\)/);
  assert.match(source, /loading = reactive\(\{[\s\S]*dashboard: false,/);
  assert.match(source, /getCustomerDashboard\(/);
  assert.match(source, /options\.preferredDetailTab \?\? options\.fallbackDetailTab \?\? "dashboard"/);
  assert.match(source, /options\.fallbackDetailTab \|\| "dashboard"/);
  assert.match(source, /startCreateCustomer\(\) \{[\s\S]*activeDetailTab\.value = "overview"/);
});

test("dashboard quick actions reuse existing tab and create handlers", () => {
  assert.match(source, /function handleDashboardCreateContact\(\) \{/);
  assert.match(source, /selectCustomerDetailTab\("contacts"\)/);
  assert.match(source, /startCreateContact\(\);/);
  assert.match(source, /function handleDashboardCreateInvoiceParty\(\) \{/);
  assert.match(source, /activeDetailTab\.value = "commercial"/);
  assert.match(source, /startCreateInvoiceParty\(\);/);
  assert.match(source, /:can-read-commercial="canReadCommercial"/);
  assert.match(source, /:can-write-commercial="canWriteCommercial"/);
  assert.match(source, /:can-manage-contacts="actionState\.canManageContacts"/);
  assert.match(source, /:tenant-id="tenantScopeId"/);
  assert.match(source, /:access-token="accessToken"/);
});

test("plans tab is inserted after contacts access and before history with planning-record permission gating", () => {
  assert.match(source, /const canReadPlans = computed\(\(\) => hasPlanningOrderPermission\(authStore\.activeRole, "planning\.record\.read"\)\)/);
  assert.match(source, /const canStartCustomerPlanWizard = computed\(\(\) => authStore\.effectiveRole === "tenant_admin"\)/);
  assert.match(source, /buildCustomerDetailTabs\(\{[\s\S]*canReadCommercial: canReadCommercial\.value,[\s\S]*canReadPlans: canReadPlans\.value,/);
  assert.match(source, /contact_access:\s*"customerAdmin\.tabs\.contactAccess",[\s\S]*plans:\s*"customerAdmin\.tabs\.plans",[\s\S]*history:\s*"customerAdmin\.tabs\.history"/);
  assert.match(source, /:can-start-new-plan="canStartCustomerPlanWizard"/);
  assert.match(source, /@start-new-plan="handleStartCustomerNewPlan"/);
  assert.match(source, /name: "SicherPlanCustomerNewPlan",[\s\S]*customer_id: selectedCustomer\.value\.id/);
});

test("customer detail navigation splits primary tabs from secondary link-style tabs", () => {
  assert.match(source, /class="customer-admin-tabs customer-admin-tabs--split"/);
  assert.match(source, /customer-admin-tabs__primary[\s\S]*v-for="tab in primaryCustomerDetailTabs"[\s\S]*class="customer-admin-tab"[\s\S]*@click="selectCustomerDetailTab\(tab\.id\)"/);
  assert.match(source, /customer-admin-tabs__secondary[\s\S]*v-for="tab in secondaryCustomerDetailTabs"[\s\S]*class="customer-admin-tab-link"[\s\S]*:aria-current="tab\.id === activeDetailTab \? 'page' : undefined"[\s\S]*@click="selectCustomerDetailTab\(tab\.id\)"/);
  assert.match(source, /const secondaryCustomerDetailTabIds = new Set\(\["history", "employee_blocks"\]\)/);
});

test("create-mode cancel restores the selected customer through the dashboard default path", () => {
  assert.match(source, /async function cancelCustomerEdit\(\) \{/);
  assert.match(source, /await selectCustomer\(selectedCustomer\.value\.id, \{\s*preferredDetailTab: "dashboard",\s*\}\);/);
  assert.match(source, /startCreateCustomer\(\) \{[\s\S]*activeDetailTab\.value = "overview"/);
  assert.match(source, /startCreateCustomer\(\) \{[\s\S]*customerDashboard\.value = null;/);
});

test("customer workspace uses shared toast feedback instead of a persistent inline banner", () => {
  assert.match(source, /useSicherPlanFeedback/);
  assert.match(source, /showFeedbackToast\(\{\s*key:\s*"customer-admin-feedback"/);
  assert.doesNotMatch(source, /<section v-if="feedback\.message" class="customer-admin-feedback"/);
  assert.doesNotMatch(source, /function clearFeedback\(/);
});

test("commercial workspace uses nested sub tabs and isolated panels", () => {
  assert.match(source, /data-testid="customer-commercial-tabs"/);
  assert.match(source, /data-testid="customer-commercial-panel-billing-profile"/);
  assert.match(source, /data-testid="customer-commercial-panel-invoice-parties"/);
  assert.match(source, /data-testid="customer-commercial-panel-pricing-rules"/);
  assert.match(source, /data-testid="customer-pricing-rules-tabs"/);
  assert.match(source, /data-testid="customer-pricing-rules-panel-rate-cards"/);
  assert.match(source, /data-testid="customer-pricing-rules-panel-rate-lines"/);
  assert.match(source, /data-testid="customer-pricing-rules-panel-surcharges"/);
  assert.match(source, /const activePricingRulesTab = ref\("rate_cards"\)/);
  assert.match(source, /const pricingRulesTabs = computed/);
  assert.match(source, /commercialProfile\.value\?\.rate_cards\.length/);
  assert.match(source, /activePricingRulesTab\.value = "rate_cards"/);
  assert.match(source, /activePricingRulesTab\.value = "rate_lines"/);
  assert.match(source, /activePricingRulesTab\.value = "surcharges"/);
});

test("rate cards expose explicit edit actions and a versioned pricing-window editor", () => {
  assert.match(source, /data-testid="customer-pricing-rules-panel-rate-cards"/);
  assert.match(source, /customer-rate-card-record-/);
  assert.match(source, /customer-rate-card-select-/);
  assert.match(source, /customer-rate-card-edit-/);
  assert.match(source, /@click="editRateCard\(rateCard\)"/);
  assert.match(source, /customerAdmin\.commercial\.rateCardCreateEyebrow/);
  assert.match(source, /customerAdmin\.commercial\.rateCardEditEyebrow/);
  assert.match(source, /customerAdmin\.commercial\.rateCardEditorLead/);
  assert.match(source, /customerAdmin\.commercial\.rateCardWindowHelp/);
  assert.match(source, /customerAdmin\.commercial\.rateKindPlaceholder/);
  assert.match(source, /customerAdmin\.commercial\.rateKindHelp/);
  assert.match(source, /@blur="normalizeRateKindField"/);
  assert.match(source, /customer-rate-card-archive/);
  assert.match(source, /archiveRateCard\(selectedRateCard\)/);
  assert.match(source, /await updateCustomerRateCard\([\s\S]*status: "archived",[\s\S]*archived_at: new Date\(\)\.toISOString\(\),[\s\S]*version_no: rateCard\.version_no/);
  assert.match(source, /<input[\s\S]*v-model="rateCardDraft\.rate_kind"/);
  assert.doesNotMatch(source, /<select[^>]*v-model="rateCardDraft\.rate_kind"/);
});

test("pricing-rule editors use guided select, datalist, numeric, and time controls", () => {
  assert.match(source, /<select[\s\S]*v-model="rateLineDraft\.line_kind"/);
  assert.match(source, /<select[\s\S]*v-model="rateLineDraft\.billing_unit"/);
  assert.match(source, /<select[\s\S]*v-model="rateLineDraft\.planning_mode_code"/);
  assert.match(source, /v-model="rateLineDraft\.unit_price"[\s\S]*type="number"[\s\S]*step="0\.01"[\s\S]*min="0"/);
  assert.match(source, /v-model="rateLineDraft\.minimum_quantity"[\s\S]*type="number"[\s\S]*step="0\.01"[\s\S]*min="0"/);
  assert.match(source, /<select[\s\S]*v-model="rateLineDraft\.function_type_id"/);
  assert.match(source, /<select[\s\S]*v-model="rateLineDraft\.qualification_type_id"/);
  assert.match(source, /referenceData\.value\?\.function_types/);
  assert.match(source, /referenceData\.value\?\.qualification_types/);
  assert.match(source, /rateLineFunctionTypeOptions/);
  assert.match(source, /rateLineQualificationTypeOptions/);
  assert.match(source, /formatCatalogOptionLabel\(option\)/);
  assert.match(source, /customerAdmin\.commercial\.functionTypeCatalogHint/);
  assert.match(source, /customerAdmin\.commercial\.qualificationTypeCatalogHint/);
  assert.match(source, /<select[\s\S]*v-model="surchargeRuleDraft\.surcharge_type"/);
  assert.match(source, /customer-admin-weekday-picker/);
  assert.match(source, /validateSurchargeRuleAgainstRateCardWindow/);
  assert.match(source, /surchargeRuleDraft\.effective_from[\s\S]*:min="selectedRateCard\.effective_from"[\s\S]*:max="selectedRateCard\.effective_to \|\| undefined"/);
  assert.match(source, /surchargeRuleDraft\.effective_to[\s\S]*:min="surchargeEffectiveToInputMin \|\| undefined"[\s\S]*:max="selectedRateCard\.effective_to \|\| undefined"/);
  assert.match(source, /surchargeAllowedWindowHelper/);
  assert.match(source, /customer-admin-surcharge-date-block/);
  assert.match(source, /customer-admin-surcharge-date-grid/);
  assert.match(source, /customer-admin-surcharge-date-help/);
  assert.match(source, /\.customer-admin-form-grid--detail > \.customer-admin-surcharge-date-block \{/);
  assert.match(source, /\.customer-admin-surcharge-date-grid \{/);
  assert.match(source, /\.customer-admin-surcharge-date-help \{/);
  assert.match(source, /customerAdmin\.commercial\.surchargeAllowedWindowBounded/);
  assert.match(source, /customerAdmin\.commercial\.surchargeAllowedWindowOpenEnded/);
  assert.match(source, /customerAdmin\.commercial\.surchargeEffectiveToRequiredHint/);
  assert.match(source, /customerAdmin\.feedback\.surchargeEffectiveToRequiredForRateCard/);
  assert.match(source, /surchargeRuleDraft\.effective_from = selectedRateCard\.value\?\.effective_from \?\? ""/);
  assert.match(source, /surchargeRuleDraft\.effective_to = selectedRateCard\.value\?\.effective_to \?\? ""/);
  assert.doesNotMatch(
    source,
    /<div class="field-stack field-stack--wide">\s*<small class="customer-admin-field-help">\s*\{\{\s*surchargeAllowedWindowHelper\s*\}\}/,
  );
  assert.match(source, /v-model="surchargeTimeFromInput"[\s\S]*type="time"/);
  assert.match(source, /v-model="surchargeTimeToInput"[\s\S]*type="time"/);
  assert.match(source, /setSurchargeAmountMode\('percent'\)/);
  assert.match(source, /setSurchargeAmountMode\('fixed'\)/);
  assert.match(source, /<select[\s\S]*v-model="surchargeRuleDraft\.currency_code"/);
  assert.doesNotMatch(source, /<input v-model="rateLineDraft\.line_kind"/);
  assert.doesNotMatch(source, /<input v-model="rateLineDraft\.billing_unit"/);
  assert.doesNotMatch(source, /<input v-model="rateLineDraft\.planning_mode_code"/);
  assert.doesNotMatch(source, /list="customer-rate-line-function-options"/);
  assert.doesNotMatch(source, /list="customer-rate-line-qualification-options"/);
  assert.doesNotMatch(source, /<input v-model="surchargeRuleDraft\.surcharge_type"/);
  assert.doesNotMatch(source, /<input v-model="surchargeRuleDraft\.weekday_mask"/);
  assert.doesNotMatch(source, /<input v-model\.number="surchargeRuleDraft\.time_from_minute"/);
  assert.doesNotMatch(source, /<input v-model\.number="surchargeRuleDraft\.time_to_minute"/);
  assert.doesNotMatch(source, /<input v-model="surchargeRuleDraft\.currency_code"/);
});

test("rate-line empty state offers HR bootstrap and recovery actions", () => {
  assert.match(source, /webAppConfig\.env === "development"/);
  assert.match(source, /bootstrapEmployeeCatalogSamples/);
  assert.match(source, /attemptedHrCatalogBootstrap/);
  assert.match(source, /customerAdmin\.commercial\.hrCatalogEmptyTitle/);
  assert.match(source, /customerAdmin\.commercial\.hrCatalogEmptyDevHint/);
  assert.match(source, /customerAdmin\.commercial\.hrCatalogEmptyManagedHint/);
  assert.match(source, /customerAdmin\.actions\.createHrCatalogSamples/);
  assert.match(source, /customerAdmin\.actions\.openEmployeesAdmin/);
  assert.match(source, /openEmployeesAdmin/);
  assert.match(source, /isRateLineHrCatalogEmpty/);
});

test("rate-line list resolves function and qualification labels from catalog data", () => {
  assert.match(source, /resolveRateLineCatalogLabel/);
  assert.match(source, /rateLine\.function_type/);
  assert.match(source, /rateLine\.qualification_type/);
  assert.match(source, /formatCatalogOptionLabel/);
});

test("detail forms use the denser detail-grid span classes", () => {
  assert.match(source, /customer-admin-form-grid--detail/);
  assert.match(source, /field-stack--half/);
  assert.match(source, /field-stack--third/);
});

test("overview metadata fields show seed-aware warnings when tenant lookup domains are empty", () => {
  assert.match(source, /hasCustomerMetadataCatalogGap/);
  assert.match(source, /customerAdmin\.overview\.crmMetadataWarningTitle/);
  assert.match(source, /customerAdmin\.overview\.crmMetadataWarningBody/);
  assert.match(source, /customerAdmin\.overview\.classificationEmptyHint/);
  assert.match(source, /customerAdmin\.overview\.rankingEmptyHint/);
  assert.match(source, /customerAdmin\.overview\.customerStatusEmptyHint/);
  assert.match(source, /classificationOptions\.length === 0/);
  assert.match(source, /rankingOptions\.length === 0/);
  assert.match(source, /customerStatusMetadataOptions\.length === 0/);
  assert.doesNotMatch(source, /const CUSTOMER_CLASSIFICATION_OPTIONS =/);
  assert.doesNotMatch(source, /const CUSTOMER_RANKING_OPTIONS =/);
  assert.doesNotMatch(source, /const CUSTOMER_STATUS_OPTIONS =/);
});

test("customer-facing dropdowns use label-only option formatting", () => {
  assert.match(source, /formatCustomerReferenceOptionLabel as formatCustomerReferenceOptionOnlyLabel/);
  assert.match(source, /function formatReferenceOptionLabel/);
  assert.match(source, /formatReferenceOptionLabel\(branch\)/);
  assert.match(source, /formatReferenceOptionLabel\(mandate\)/);
  assert.match(source, /formatReferenceOptionLabel\(option\)/);
  assert.doesNotMatch(source, /function formatReferenceLabel/);
});

test("non-overview customer tabs reuse the structured section pattern", () => {
  assert.match(source, /customer-tab-panel-contact-access[\s\S]*customer-tab-panel-contacts[\s\S]*customer-tab-panel-addresses[\s\S]*customer-tab-panel-portal/);
  assert.match(source, /class="customer-admin-section customer-admin-section--contact-access customer-admin-contact-access"/);
  assert.match(source, /class="customer-admin-contact-access-card customer-admin-contact-access-card--contacts"[\s\S]*data-testid="customer-contact-access-card-contacts"[\s\S]*customer-tab-panel-contacts/);
  assert.match(source, /class="customer-admin-contact-access-card customer-admin-contact-access-card--addresses"[\s\S]*data-testid="customer-contact-access-card-addresses"[\s\S]*customer-tab-panel-addresses/);
  assert.match(source, /class="customer-admin-contact-access-card customer-admin-contact-access-card--portal"[\s\S]*data-testid="customer-contact-access-card-portal"[\s\S]*customer-tab-panel-portal/);
  assert.match(source, /customer-contact-access-card-contacts[\s\S]*customerAdmin\.contactAccess\.contactsTitle[\s\S]*customerAdmin\.contactAccess\.contactsDescription[\s\S]*customer-tab-panel-contacts/);
  assert.match(source, /customer-contact-access-card-addresses[\s\S]*customerAdmin\.contactAccess\.addressesTitle[\s\S]*customerAdmin\.contactAccess\.addressesDescription[\s\S]*customer-tab-panel-addresses/);
  assert.match(source, /customer-contact-access-card-portal[\s\S]*customerAdmin\.contactAccess\.portalTitle[\s\S]*customerAdmin\.contactAccess\.portalDescription[\s\S]*customer-tab-panel-portal/);
  assert.match(source, /customer-tab-panel-contacts[\s\S]*customer-admin-form customer-admin-form--structured[\s\S]*customerAdmin\.contacts\.registerEyebrow[\s\S]*customerAdmin\.contacts\.editorEyebrow[\s\S]*customerAdmin\.fields\.notes/);
  assert.match(source, /customer-tab-panel-addresses[\s\S]*customerAdmin\.addresses\.registerEyebrow[\s\S]*customerAdmin\.addresses\.editorEyebrow/);
  assert.match(source, /customer-tab-panel-commercial[\s\S]*customer-admin-editor-intro[\s\S]*customer-commercial-panel-billing-profile/);
  assert.match(source, /customer-tab-panel-portal[\s\S]*customerAdmin\.privacy\.title[\s\S]*customer-portal-access-section[\s\S]*customerAdmin\.portalAccess\.title[\s\S]*customerAdmin\.loginHistory\.title/);
  assert.match(source, /customer-tab-panel-history[\s\S]*customerAdmin\.history\.registerEyebrow[\s\S]*customerAdmin\.history\.attachmentEyebrow/);
  assert.match(source, /customer-tab-panel-employee-blocks[\s\S]*customerAdmin\.employeeBlocks\.registerEyebrow[\s\S]*customerAdmin\.employeeBlocks\.editorEyebrow/);

  const contactAccessStart = source.indexOf('data-testid="customer-tab-panel-contact-access"');
  const commercialPanelStart = source.indexOf('data-testid="customer-tab-panel-commercial"');
  const contactAccessSource = source.slice(contactAccessStart, commercialPanelStart);
  assert.equal(contactAccessSource.includes("customer-admin-editor-intro"), false);
  assert.equal(contactAccessSource.includes("customerAdmin.contacts.title"), false);
  assert.equal(contactAccessSource.includes("customerAdmin.addresses.title"), false);
  assert.equal(contactAccessSource.includes("customerAdmin.portal.title"), false);
});

test("billing-profile form surfaces inline validation summary and field-level error hooks", () => {
  assert.match(source, /data-testid="customer-billing-profile-error-summary"/);
  assert.match(source, /billingProfileErrorState\.summaryBody/);
  assert.match(source, /billingProfileFieldError\('invoice_email'\)/);
  assert.match(source, /billingProfileFieldError\('shipping_method_code'\)/);
  assert.match(source, /billingProfileFieldError\('dunning_policy_code'\)/);
  assert.match(source, /billingProfileFieldError\('tax_exemption_reason'\)/);
  assert.match(source, /billingProfileFieldError\('leitweg_id'\)/);
  assert.match(source, /clearBillingProfileFieldErrors\(\['invoice_email'\]\)/);
  assert.match(source, /customer-admin-field-stack--error/);
  assert.match(source, /customer-admin-checkbox--error/);
});

test("billing-profile selects use lookup-backed reference data instead of hardcoded option arrays", () => {
  assert.match(source, /billingInvoiceLayoutOptions/);
  assert.match(source, /billingShippingMethodOptions/);
  assert.match(source, /billingDunningPolicyOptions/);
  assert.match(source, /billingInvoiceLayoutOptions[\s\S]*option\.label/);
  assert.match(source, /billingShippingMethodOptions[\s\S]*option\.label/);
  assert.match(source, /billingDunningPolicyOptions[\s\S]*option\.label/);
  assert.doesNotMatch(source, /const INVOICE_LAYOUT_OPTIONS =/);
  assert.doesNotMatch(source, /const SHIPPING_METHOD_OPTIONS =/);
  assert.doesNotMatch(source, /const DUNNING_POLICY_OPTIONS =/);
});

test("billing-profile rows use explicit layout helpers for bank, lookup, and note alignment", () => {
  assert.match(source, /bank_iban[\s\S]*customer-admin-billing-row-field/);
  assert.match(source, /bank_bic[\s\S]*customer-admin-billing-row-field/);
  assert.match(source, /bank_name[\s\S]*customer-admin-billing-row-field/);
  assert.match(source, /invoice_layout_code[\s\S]*customer-admin-billing-row-field/);
  assert.match(source, /shipping_method_code[\s\S]*customer-admin-billing-row-field/);
  assert.match(source, /dunning_policy_code[\s\S]*customer-admin-billing-row-field/);
  assert.match(source, /leitweg_id[\s\S]*customer-admin-billing-paired-field customer-admin-billing-paired-field--compact/);
  assert.match(source, /customer-admin-billing-paired-field customer-admin-billing-paired-field--notes[\s\S]*billing_note/);
  assert.match(source, /\.customer-admin-billing-paired-field--compact \{/);
  assert.match(source, /\.customer-admin-billing-paired-field--notes textarea \{/);
});

test("invoice-party form uses customer address selector and address-tab empty state guidance", () => {
  assert.match(source, /customerAdmin\.fields\.billingAddress/);
  assert.match(source, /invoicePartyAddressOptions/);
  assert.match(source, /invoicePartyAddressPlaceholder/);
  assert.match(source, /formatInvoicePartyAddressOption/);
  assert.match(source, /invoicePartyInvoiceLayoutOptions/);
  assert.match(source, /invoicePartyInvoiceLayoutPlaceholder/);
  assert.match(source, /invoicePartyFieldError\('invoice_layout_lookup_id'\)/);
  assert.match(source, /clearInvoicePartyErrors\(\['invoice_layout_lookup_id'\]\)/);
  assert.match(source, /option\.id" :value="option\.id"|option in invoicePartyInvoiceLayoutOptions/);
  assert.match(source, /customerAdmin\.commercial\.invoicePartyAddressMissing/);
  assert.match(source, /customerAdmin\.actions\.openAddressesTab/);
  assert.match(source, /openCustomerAddressesTab/);
  assert.doesNotMatch(source, /<input v-model="invoicePartyDraft\.address_id"/);
  assert.doesNotMatch(source, /<input v-model="invoicePartyDraft\.invoice_layout_lookup_id"/);
});

test("address-link form uses available-address selector instead of raw address uuid input", () => {
  assert.match(source, /customerAdmin\.addresses\.linkLead/);
  assert.match(source, /customerAdmin\.fields\.address/);
  assert.match(source, /availableAddressDirectory/);
  assert.match(source, /stagedAddressDirectoryByCustomer/);
  assert.match(source, /customerAddressLinkOptions/);
  assert.match(source, /customerAddressLinkPlaceholder/);
  assert.match(source, /listCustomerAvailableAddresses/);
  assert.match(source, /createCustomerAvailableAddress/);
  assert.match(source, /refreshAvailableAddresses/);
  assert.match(source, /formatAddressDirectoryOption/);
  assert.match(source, /address\.address_type === addressDraft\.address_type/);
  assert.match(source, /customer-admin-form-section__header customer-admin-form-section__header--split/);
  assert.match(source, /\.customer-admin-form-section__header--split \{/);
  assert.match(source, /customerAdmin\.addresses\.addressLinkEmpty/);
  assert.match(source, /customer-address-directory-create-modal/);
  assert.match(source, /submitAddressDirectoryEntry/);
  assert.match(source, /addressDraft\.address_id = created\.id/);
  assert.match(source, /customerAdmin\.actions\.createSharedAddress/);
  assert.match(source, /customerAdmin\.fields\.streetLine1/);
  assert.match(source, /customerAdmin\.fields\.postalCode/);
  assert.match(source, /customerAdmin\.fields\.city/);
  assert.match(source, /customerAdmin\.fields\.countryCode/);
  assert.doesNotMatch(source, /<input v-model="addressDraft\.address_id"/);
});

test("full tab editors no longer use legacy inline-form layout", () => {
  assert.doesNotMatch(source, /customer-admin-inline-form/);
  assert.doesNotMatch(source, /v-model="contactDraft\.user_id"/);
  assert.doesNotMatch(source, /user_id:\s*emptyToNull\(contactDraft\.user_id\)/);
  assert.doesNotMatch(source, /customerAdmin\.contacts\.portalAccessLabel/);
  assert.doesNotMatch(source, /customerAdmin\.contacts\.portalAccessHelp/);
  assert.match(source, /submitHistoryAttachmentLink[\s\S]*customer-admin-form-grid customer-admin-form-grid--detail/);
  assert.match(source, /submitEmployeeBlock[\s\S]*customer-admin-form-grid customer-admin-form-grid--detail/);
});
