import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const viewPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/views/CustomerAdminView.vue",
);
const source = readFileSync(viewPath, "utf8");

test("customer workspace splits list-only and detail-only modes with detail tabs", () => {
  assert.match(source, /<SicherPlanLoadingOverlay[\s\S]*busy-testid="customer-workspace-loading-overlay"/);
  assert.match(source, /:busy="customerWorkspaceBusy"/);
  assert.match(source, /:text="customerWorkspaceLoadingText"/);
  assert.match(source, /const customerWorkspaceBusy = computed\(/);
  assert.match(source, /const customerWorkspaceHasStableContent = computed/);
  assert.match(source, /const customerWorkspaceBlockingLoad = computed/);
  const busyBlock = source.slice(
    source.indexOf("const customerWorkspaceBusy = computed"),
    source.indexOf("const customerWorkspaceLoadingText = computed"),
  );
  assert.match(busyBlock, /customerWorkspaceBlockingLoad\.value/);
  assert.doesNotMatch(busyBlock, /loading\.customer/);
  assert.doesNotMatch(busyBlock, /loading\.contact/);
  assert.doesNotMatch(busyBlock, /loading\.address/);
  assert.doesNotMatch(busyBlock, /loading\.commercial/);
  assert.doesNotMatch(busyBlock, /loading\.rateLine/);
  assert.doesNotMatch(busyBlock, /loading\.surchargeRule/);
  assert.doesNotMatch(busyBlock, /loading\.portalAccess/);
  assert.doesNotMatch(busyBlock, /loading\.portalPrivacy/);
  assert.doesNotMatch(busyBlock, /loading\.historyAttachment/);
  assert.doesNotMatch(busyBlock, /loading\.employeeBlock/);
  assert.doesNotMatch(busyBlock, /loading\.sharedAddress/);
  assert.doesNotMatch(busyBlock, /loading\.hrCatalogBootstrap/);
  assert.match(source, /const customerWorkspaceLoadingText = computed\(\(\) =>/);
  assert.match(source, /class="customer-admin-grid"/);
  assert.match(source, /\.customer-admin-grid \{[\s\S]*grid-template-columns: minmax\(0, 1fr\);/);
  assert.match(source, /v-if="customerAdminListMode"[\s\S]*data-testid="customer-list-only-mode"/);
  assert.match(source, /v-else[\s\S]*data-testid="customer-detail-only-mode"/);
  assert.match(source, /data-testid="customer-list-section"/);
  assert.match(source, /data-testid="customer-detail-workspace"/);
  assert.match(source, /data-testid="customer-back-to-list"/);
  assert.match(source, /data-testid="customer-detail-tabs"/);
  assert.match(source, /data-testid="customer-detail-title"/);
  assert.doesNotMatch(source, /data-testid="customer-page-context-label"/);
  assert.doesNotMatch(source, /data-testid="customer-page-context-label-full-title"/);
  assert.match(source, /\.customer-admin-list-panel \{[\s\S]*position: static;/);
  assert.match(source, /resolveCustomerAdminRouteContext\(route\.query\)/);
});

test("customer detail mode updates app-shell title without rendering a duplicate in-page pill", () => {
  assert.match(source, /const customerPageContextFullTitle = computed/);
  assert.match(source, /const customerPageContextLabel = computed\(\(\) => truncateCustomerContextLabel/);
  assert.match(source, /function truncateCustomerContextLabel\(value: string, maxLength = 34\)/);
  assert.match(source, /\(route\.meta as Record<string, unknown>\)\.title = label/);
  assert.doesNotMatch(source, /class="customer-admin-context-bar"/);
  assert.doesNotMatch(source, /\.customer-admin-context-bar/);
  assert.match(source, /class="customer-admin-detail-title"/);
  assert.match(source, /class="cta-button cta-secondary customer-admin-back-button"/);
  assert.match(source, /\.customer-admin-detail-title \{[\s\S]*font-size: clamp\(1\.55rem, 2\.4vw, 2\.2rem\);/);
  assert.match(source, /\.customer-admin-detail-title \{[\s\S]*font-weight: 800;/);
  assert.match(source, /\.customer-admin-back-button \{[\s\S]*min-height: 2rem;/);
  assert.match(source, /\.customer-admin-back-button \{[\s\S]*padding: 0\.32rem 0\.68rem;/);
});

test("contacts and access nav reuses the employee-style floating shell behavior", () => {
  assert.match(source, /ref="contactAccessOnePageRef"/);
  assert.match(source, /ref="contactAccessNavShellRef"/);
  assert.match(source, /const contactAccessNavFloatingMode = ref<"fixed" \| "pinned" \| "static">\("static"\)/);
  assert.match(source, /const contactAccessNavFloatingStyle = ref<CSSProperties>\(\{\}\)/);
  assert.match(source, /const CUSTOMER_CONTACT_ACCESS_NAV_FLOATING_MIN_WIDTH = 1081/);
  assert.match(source, /let contactAccessNavScrollTargets: Array<HTMLElement \| Window> = \[\]/);
  assert.match(source, /let contactAccessNavFloatingRaf: number \| null = null/);
  assert.match(source, /'customer-admin-contact-access-nav-shell--fixed': contactAccessNavFloatingMode === 'fixed'/);
  assert.match(source, /'customer-admin-contact-access-nav-shell--pinned': contactAccessNavFloatingMode === 'pinned'/);
  assert.match(source, /:style="contactAccessNavFloatingStyle"/);
  assert.match(source, /function isCustomerContactAccessScrollableAncestor\(element: HTMLElement\)/);
  assert.match(source, /function findCustomerContactAccessScrollContainers\(\)/);
  assert.match(source, /function resolveContactAccessIntersectionRoot\(\)/);
  assert.match(source, /function resetContactAccessNavFloating\(\)/);
  assert.match(source, /function cancelContactAccessNavFloatingFrame\(\)/);
  assert.match(source, /function scrollToCustomerContactAccessSection\(sectionId: CustomerContactAccessSectionId\)/);
  assert.match(source, /sectionElement\.scrollIntoView\(\{[\s\S]*behavior: "smooth",[\s\S]*block: "start",/);
  assert.match(source, /function selectCustomerContactAccessSection\(sectionId: string\) \{[\s\S]*scrollToCustomerContactAccessSection\(activeContactAccessSection\.value\);/);
  assert.match(source, /function updateContactAccessNavFloating\(\)/);
  assert.match(source, /window\.matchMedia\(`\(min-width: \$\{CUSTOMER_CONTACT_ACCESS_NAV_FLOATING_MIN_WIDTH\}px\)`\)\.matches/);
  assert.match(source, /contactAccessNavFloatingMode\.value = "pinned"/);
  assert.match(source, /contactAccessNavFloatingMode\.value = "fixed"/);
  assert.match(source, /function scheduleContactAccessNavFloatingUpdate\(\)/);
  assert.match(source, /window\.requestAnimationFrame\(updateContactAccessNavFloating\)/);
  assert.match(source, /function teardownContactAccessNavFloating\(\)/);
  assert.match(source, /function setupContactAccessNavFloating\(\)/);
  assert.match(source, /contactAccessNavScrollTargets = \[window, \.\.\.findCustomerContactAccessScrollContainers\(\)\]/);
  assert.match(source, /target\.addEventListener\("scroll", scheduleContactAccessNavFloatingUpdate, \{ passive: true \}\)/);
  assert.match(source, /window\.addEventListener\("resize", scheduleContactAccessNavFloatingUpdate, \{ passive: true \}\)/);
  assert.match(source, /setupContactAccessNavFloating\(\);[\s\S]*setupCustomerContactAccessSectionObserver\(\);/);
  assert.match(source, /teardownContactAccessNavFloating\(\);/);
  assert.match(source, /root: resolveContactAccessIntersectionRoot\(\)/);
  assert.match(source, /\.customer-admin-contact-access-nav-shell \{[\s\S]*grid-column: 1;[\s\S]*position: sticky;[\s\S]*z-index: 2;/);
  assert.match(source, /\.customer-admin-contact-access-content \{[\s\S]*grid-column: 2;[\s\S]*display: grid;/);
  assert.match(source, /\.customer-admin-contact-access-nav-shell--fixed \{[\s\S]*position: fixed;/);
  assert.match(source, /\.customer-admin-contact-access-nav-shell--pinned \{[\s\S]*position: absolute;/);
  assert.doesNotMatch(source, /\.customer-admin-contact-access-onepage--fixed/);
  assert.doesNotMatch(source, /\.customer-admin-contact-access-content--fixed/);
  assert.match(source, /@media \(max-width: 1080px\) \{[\s\S]*\.customer-admin-contact-access-nav-shell--fixed,[\s\S]*\.customer-admin-contact-access-nav-shell--pinned \{[\s\S]*position: static;/);
  assert.match(source, /@media \(max-width: 1080px\) \{[\s\S]*\.customer-admin-contact-access-content \{[\s\S]*grid-column: 1;/);
});

test("contacts register opens the existing contact editor in a modal instead of keeping it inline", () => {
  assert.match(source, /data-testid="customer-contact-register-create"/);
  assert.match(source, /customerAdmin\.actions\.createNewContact/);
  assert.match(source, /@click="startCreateContact"/);
  assert.match(source, /v-if="contactEditorModalOpen"/);
  assert.match(source, /data-testid="customer-contact-editor-modal"/);
  assert.match(source, /aria-modal="true"/);
  assert.match(source, /role="dialog"/);
  assert.match(source, /v-if="contactEditorErrorMessage"/);
  assert.match(source, /data-testid="customer-contact-editor-error"/);
  assert.match(source, /@submit\.prevent="submitContact"/);
  assert.match(source, /@click="closeContactEditorModal"/);
  assert.match(source, /const contactEditorModalOpen = ref\(false\)/);
  assert.match(source, /const contactEditorErrorMessage = ref\(""\)/);
  assert.match(source, /function clearContactEditorError\(\)/);
  assert.match(source, /function openContactEditorModal\(\)/);
  assert.match(source, /function closeContactEditorModal\(\)/);
  assert.match(source, /function editContact\(contact: CustomerContactRead\) \{[\s\S]*openContactEditorModal\(\);/);
  assert.match(source, /function startCreateContact\(\) \{[\s\S]*openContactEditorModal\(\);/);
  assert.match(source, /contactEditorErrorMessage\.value = t\("customerAdmin\.feedback\.contactRequired"\)/);
  assert.match(source, /contactEditorModalOpen\.value = false;[\s\S]*resetContactDraft\(\);[\s\S]*await selectCustomer\(selectedCustomer\.value\.id, buildPreservedCustomerSelectionOptions\(\)\);/);
  assert.doesNotMatch(source, /<form class="customer-admin-form-section" @submit\.prevent="submitContact">[\s\S]*customer-tab-panel-contacts/);
});

test("address register opens the existing address link editor in a modal instead of keeping it inline", () => {
  assert.match(source, /data-testid="customer-address-register-create"/);
  assert.match(source, /customerAdmin\.actions\.createNewAddress/);
  assert.match(source, /@click="startCreateAddress"/);
  assert.match(source, /v-if="addressEditorModalOpen"/);
  assert.match(source, /data-testid="customer-address-editor-modal"/);
  assert.match(source, /data-testid="customer-address-editor-error"/);
  assert.match(source, /const addressEditorModalOpen = ref\(false\)/);
  assert.match(source, /const addressEditorErrorMessage = ref\(""\)/);
  assert.match(source, /function clearAddressEditorError\(\)/);
  assert.match(source, /function openAddressEditorModal\(\)/);
  assert.match(source, /function closeAddressEditorModal\(\)/);
  assert.match(source, /function editAddress\(address: CustomerAddressRead\) \{[\s\S]*openAddressEditorModal\(\);/);
  assert.match(source, /function startCreateAddress\(\) \{[\s\S]*openAddressEditorModal\(\);/);
  assert.match(source, /addressEditorErrorMessage\.value = t\("customerAdmin\.feedback\.addressRequired"\)/);
  assert.match(source, /addressEditorModalOpen\.value = false;[\s\S]*resetAddressDraft\(\);[\s\S]*await selectCustomer\(selectedCustomer\.value\.id, buildPreservedCustomerSelectionOptions\(\)\);/);
  assert.doesNotMatch(source, /<form class="customer-admin-form-section" @submit\.prevent="submitAddress">[\s\S]*customer-tab-panel-addresses/);
});

test("customer list panel keeps a compact inline search row and renders clickable customer rows", () => {
  const listSectionMatch = source.match(
    /<section class="module-card customer-admin-panel customer-admin-list-panel" data-testid="customer-list-section">([\s\S]*?)<\/section>/,
  );
  assert.ok(listSectionMatch, "customer list section should exist");
  const listSection = listSectionMatch[1];
  assert.match(listSection, /customerAdmin\.filters\.search/);
  assert.match(listSection, /customerAdmin\.actions\.advancedFilters/);
  assert.match(listSection, /customerAdmin\.actions\.exportCustomers/);
  assert.match(listSection, /customerAdmin\.actions\.newCustomer/);
  assert.match(listSection, /data-testid="customer-list-header-export"/);
  assert.match(listSection, /data-testid="customer-list-header-new-customer"/);
  assert.match(listSection, /class="customer-admin-filter-toolbar"/);
  assert.match(listSection, /class="customer-admin-filter-toolbar__actions"/);
  assert.match(listSection, /data-testid="customer-search-select"/);
  assert.match(listSection, /data-testid="customer-search-select-input"/);
  assert.match(listSection, /data-testid="customer-advanced-filters-open"/);
  assert.doesNotMatch(listSection, /data-testid="customer-search-suggestions"/);
  assert.doesNotMatch(listSection, /@keydown\.enter\.prevent="handleOpenCustomerSearchResults"/);
  assert.doesNotMatch(listSection, /customerAdmin\.actions\.search/);
  assert.doesNotMatch(listSection, /v-model="filters\.lifecycle_status"/);
  assert.doesNotMatch(listSection, /v-model="filters\.default_branch_id"/);
  assert.doesNotMatch(listSection, /v-model="filters\.default_mandate_id"/);
  assert.doesNotMatch(listSection, /v-model="filters\.include_archived"/);
  assert.match(listSection, /data-testid="customer-list-row"/);
  assert.match(listSection, /data-testid="customer-list-row-name"/);
  assert.match(listSection, /data-testid="customer-list-row-number"/);
  assert.match(listSection, /data-testid="customer-list-row-status"/);
  assert.match(listSection, /@click="openCustomerWorkspace\(customer\.id\)"/);
  assert.match(listSection, /v-for="customer in filteredCustomers"/);
  assert.doesNotMatch(listSection, /customerAdmin\.list\.sidebarNavigationHint/);

  const listSectionIndex = source.indexOf('data-testid="customer-list-section"');
  const detailSectionIndex = source.indexOf('data-testid="customer-detail-workspace"');
  assert.ok(listSectionIndex >= 0 && detailSectionIndex >= 0 && listSectionIndex < detailSectionIndex);
});

test("advanced filters use the existing modal pattern and stable controls", () => {
  assert.match(source, /advancedFiltersModalOpen = ref\(false\)/);
  assert.match(source, /data-testid="customer-advanced-filters-dialog"/);
  assert.match(source, /role="dialog"/);
  assert.match(source, /aria-modal="true"/);
  assert.match(source, /data-testid="customer-advanced-filters-search"/);
  assert.match(source, /data-testid="customer-advanced-filters-status"/);
  assert.match(source, /data-testid="customer-advanced-filters-default-branch"/);
  assert.match(source, /data-testid="customer-advanced-filters-default-mandate"/);
  assert.match(source, /data-testid="customer-advanced-filters-include-archived"/);
  assert.match(source, /data-testid="customer-advanced-filters-apply"/);
  assert.match(source, /data-testid="customer-advanced-filters-cancel"/);
  assert.match(source, /function applyAdvancedFilters\(\)/);
  assert.match(source, /await refreshCustomers\(\);[\s\S]*advancedFiltersModalOpen\.value = false/);
  assert.match(source, /event\.key === "Escape" && advancedFiltersModalOpen\.value/);
});

test("customer list compact filter layout keeps search beside actions", () => {
  assert.match(source, /\.customer-admin-filter-toolbar \{[\s\S]*grid-template-columns: minmax\(280px, 1fr\) auto;/);
  assert.match(source, /\.customer-admin-filter-toolbar__actions \{[\s\S]*justify-content: flex-end;/);
  assert.match(source, /\.customer-admin-list-header-actions \{/);
  assert.match(source, /\.customer-admin-header-action \{/);
  assert.match(source, /\.customer-admin-filter-grid--dialog \{[\s\S]*grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/);
  assert.match(source, /@media \(max-width: 720px\) \{[\s\S]*\.customer-admin-filter-toolbar \{[\s\S]*grid-template-columns: 1fr;/);
});

test("customer export downloads the generated platform document after creation", () => {
  assert.match(source, /downloadCustomerDocument/);
  assert.match(source, /const result = await exportCustomers/);
  assert.match(source, /result\.document_id/);
  assert.match(source, /result\.version_no/);
  assert.match(source, /triggerBlobDownload\(download\.blob, download\.fileName \|\| result\.file_name\)/);
  assert.match(source, /customerAdmin\.feedback\.exportDownloadStarted/);
  assert.match(source, /customerAdmin\.feedback\.exportDownloadFailed/);
  assert.match(source, /customerAdmin\.feedback\.exportDownloadFallback/);
});

test("customer search locally filters visible list rows without suggestion or modal flow", () => {
  assert.match(source, /const normalizedCustomerListSearch = computed/);
  assert.match(source, /const filteredCustomers = computed/);
  assert.match(source, /customerListSearchHaystack\(customer\)\.includes\(search\)/);
  assert.match(source, /function customerListSearchHaystack\(customer: CustomerListItem\)/);
  assert.doesNotMatch(source, /customerSearchModalOpen = ref/);
  assert.doesNotMatch(source, /customerSearchResults = ref/);
  assert.doesNotMatch(source, /customerSearchSuggestions = ref/);
  assert.doesNotMatch(source, /customerSearch: false/);
  assert.doesNotMatch(source, /runCustomerSearch/);
  assert.doesNotMatch(source, /buildCustomerSearchParams/);
  assert.doesNotMatch(source, /data-testid="customer-search-results-modal"/);
  assert.doesNotMatch(source, /data-testid="customer-search-result-row"/);
  assert.doesNotMatch(source, /data-testid="customer-search-result-empty"/);
  assert.doesNotMatch(source, /data-testid="customer-search-result-close"/);
  assert.match(source, /window\.addEventListener\("keydown", handleCustomerSearchWindowKeydown\)/);
  assert.match(source, /event\.key === "Escape"/);
  assert.match(source, /await router\.replace\([\s\S]*customer_id: customerId,[\s\S]*tab: detailTab/);
});

test("plain customers route stays list-first and customer_id query owns workspace selection", () => {
  assert.match(source, /const routeHasSelectedCustomer = computed/);
  assert.match(source, /const customerAdminDetailMode = computed/);
  assert.match(source, /const customerAdminListMode = computed\(\(\) => !customerAdminDetailMode\.value\)/);
  assert.match(source, /function openCustomerWorkspace\(customerId: string, detailTab = "dashboard"\)/);
  assert.match(source, /customer_id: customerId/);
  assert.match(source, /tab: detailTab/);
  assert.match(source, /data-testid="customer-detail-empty-state"/);
  assert.match(source, /async function returnToCustomerList\(\)/);
  assert.match(source, /delete nextQuery\.customer_id/);
  assert.match(source, /delete nextQuery\.tab/);
  assert.match(source, /routeCustomerNotFound/);
  assert.doesNotMatch(source, /else if \(customers\.value\[0\] && !isCreatingCustomer\.value\)/);
  assert.doesNotMatch(source, /await selectCustomer\(customers\.value\[0\]\.id\)/);
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
  assert.match(source, /customerWorkspaceHasStableContent/);
  assert.match(source, /!customerWorkspaceHasStableContent\.value[\s\S]*isCustomerSessionResolving\.value/);
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
  assert.match(source, /import CustomerOrdersTab from "@\/components\/customers\/CustomerOrdersTab\.vue"/);
  assert.match(source, /dashboard:\s*"customerAdmin\.tabs\.dashboard"/);
  assert.match(source, /orders:\s*"customerAdmin\.tabs\.orders"/);
  assert.match(
    source,
    /<CustomerDashboardTab[\s\S]*v-if="selectedCustomer && !isCreatingCustomer && activeDetailTab === 'dashboard'"/,
  );
  assert.match(
    source,
    /<CustomerOrdersTab[\s\S]*v-if="selectedCustomer && !isCreatingCustomer && canReadCustomerOrders && activeDetailTab === 'orders'"/,
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

test("orders tab is inserted after contacts access and before history with planning order permission gating", () => {
  assert.match(source, /const canReadCustomerOrders = computed\(\(\) => hasPlanningOrderPermission\(authStore\.activeRole, "planning\.record\.read"\)\)/);
  assert.match(source, /const canStartCustomerOrderWizard = computed\(\(\) => authStore\.effectiveRole === "tenant_admin"\)/);
  assert.match(source, /buildCustomerDetailTabs\(\{[\s\S]*canReadCommercial: canReadCommercial\.value,[\s\S]*canReadOrders: canReadCustomerOrders\.value,/);
  assert.match(source, /contact_access:\s*"customerAdmin\.tabs\.contactAccess",[\s\S]*orders:\s*"customerAdmin\.tabs\.orders",[\s\S]*history:\s*"customerAdmin\.tabs\.history"/);
  assert.match(source, /:can-start-new-order="canStartCustomerOrderWizard"/);
  assert.match(source, /@start-new-order="handleStartCustomerNewOrder"/);
  assert.match(source, /name: "SicherPlanCustomerOrderWorkspace",[\s\S]*customer_id: selectedCustomer\.value\.id/);
});

test("customer detail navigation splits primary tabs from secondary link-style tabs", () => {
  assert.match(source, /class="customer-admin-tabs customer-admin-tabs--split"/);
  assert.match(source, /customer-admin-tabs__primary[\s\S]*v-for="tab in primaryCustomerDetailTabs"[\s\S]*class="customer-admin-tab"[\s\S]*@click="selectCustomerDetailTab\(tab\.id\)"/);
  assert.match(source, /customer-admin-tabs__secondary[\s\S]*v-for="tab in secondaryCustomerDetailTabs"[\s\S]*class="customer-admin-tab-link"[\s\S]*:aria-current="tab\.id === activeDetailTab \? 'page' : undefined"[\s\S]*@click="selectCustomerDetailTab\(tab\.id\)"/);
  assert.match(source, /const secondaryCustomerDetailTabIds = new Set\(\["history", "employee_blocks"\]\)/);
});

test("create-mode cancel returns to list-first without an explicit selected customer route", () => {
  assert.match(source, /async function cancelCustomerEdit\(\) \{/);
  assert.match(source, /if \(!routeHasSelectedCustomer\.value\) \{[\s\S]*clearCustomerWorkspace\(\);[\s\S]*return;/);
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
  assert.match(source, /class="customer-admin-section customer-admin-section--contact-access"/);
  assert.match(source, /data-testid="customer-contacts-access-layout"/);
  assert.match(source, /data-testid="customer-contacts-access-nav"/);
  assert.match(source, /testId: "customer-contacts-access-nav-contacts"/);
  assert.match(source, /testId: "customer-contacts-access-nav-addresses"/);
  assert.match(source, /testId: "customer-contacts-access-nav-portal"/);
  assert.match(source, /data-testid="customer-contacts-access-section-contacts"[\s\S]*customerAdmin\.contactAccess\.contactsTitle[\s\S]*customerAdmin\.contactAccess\.contactsDescription[\s\S]*customer-tab-panel-contacts/);
  assert.match(source, /data-testid="customer-contacts-access-section-addresses"[\s\S]*customerAdmin\.contactAccess\.addressesTitle[\s\S]*customerAdmin\.contactAccess\.addressesDescription[\s\S]*customer-tab-panel-addresses/);
  assert.match(source, /data-testid="customer-contacts-access-section-portal"[\s\S]*customerAdmin\.contactAccess\.portalTitle[\s\S]*customerAdmin\.contactAccess\.portalDescription[\s\S]*customer-tab-panel-portal/);
  assert.match(source, /customer-contacts-access-section-contacts[\s\S]*customer-admin-form customer-admin-form--structured[\s\S]*customer-tab-panel-contacts[\s\S]*customerAdmin\.contacts\.registerEyebrow[\s\S]*customerAdmin\.contacts\.editorEyebrow[\s\S]*customerAdmin\.fields\.notes/);
  assert.match(source, /customer-contacts-access-section-addresses[\s\S]*customer-tab-panel-addresses[\s\S]*customerAdmin\.addresses\.registerEyebrow[\s\S]*customerAdmin\.addresses\.editorEyebrow/);
  assert.match(source, /customer-tab-panel-commercial[\s\S]*customer-admin-editor-intro[\s\S]*customer-commercial-panel-billing-profile/);
  assert.match(source, /customer-tab-panel-portal[\s\S]*customerAdmin\.privacy\.title[\s\S]*customer-portal-access-section[\s\S]*customerAdmin\.portalAccess\.title[\s\S]*customerAdmin\.loginHistory\.title/);
  assert.match(source, /customer-tab-panel-history[\s\S]*customerAdmin\.history\.registerEyebrow[\s\S]*customerAdmin\.history\.attachmentEyebrow/);
  assert.match(source, /customer-tab-panel-employee-blocks[\s\S]*customerAdmin\.employeeBlocks\.registerEyebrow[\s\S]*customerAdmin\.employeeBlocks\.editorEyebrow/);
  assert.match(source, /import \{ IconifyIcon \} from "@vben\/icons";/);
  assert.match(source, /const customerContactAccessSections = computed/);
  assert.match(source, /function selectCustomerContactAccessSection\(sectionId: string\)/);
  assert.match(source, /function setupCustomerContactAccessSectionObserver\(\)/);
  assert.match(source, /const activeContactAccessSection = ref<CustomerContactAccessSectionId>\("contacts"\)/);
  assert.match(source, /customer-admin-contact-access-onepage/);
  assert.match(source, /customer-admin-contact-access-nav-shell/);
  assert.match(source, /customer-admin-contact-access-nav__link--active/);
  assert.match(source, /customer-admin-contact-access-section-card/);
  assert.match(source, /customer-admin-contact-access-section-card__header/);
  assert.match(source, /customer-admin-contact-access-section-card \.customer-admin-form-section \+ \.customer-admin-form-section/);

  const contactAccessStart = source.indexOf('data-testid="customer-tab-panel-contact-access"');
  const commercialPanelStart = source.indexOf('data-testid="customer-tab-panel-commercial"');
  const contactAccessSource = source.slice(contactAccessStart, commercialPanelStart);
  assert.equal(contactAccessSource.includes("customer-admin-editor-intro"), false);
  assert.equal(contactAccessSource.includes("customerAdmin.contacts.title"), false);
  assert.equal(contactAccessSource.includes("customerAdmin.addresses.title"), false);
  assert.equal(contactAccessSource.includes("customerAdmin.portal.title"), false);
  assert.equal(contactAccessSource.includes("customer-admin-contact-access-card"), false);
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
