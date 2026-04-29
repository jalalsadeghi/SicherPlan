import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const viewPath = new URL("../../views/CustomerAdminView.vue", import.meta.url);
const source = readFileSync(viewPath, "utf8");

test("customer detail workspace keeps dashboard, overview, and orders as the only main in-page tabs", () => {
  assert.match(source, /data-testid="customer-detail-tabs"/);
  assert.match(source, /:data-testid="`customer-tab-\$\{tab\.id\}`"/);
  assert.match(source, /const customerDetailTabs = computed\(/);
  assert.match(source, /buildCustomerDetailTabs\(\{/);
  assert.doesNotMatch(source, /customer-tab-contact_access/);
  assert.doesNotMatch(source, /customer-tab-commercial/);
  assert.doesNotMatch(source, /customer-tab-history/);
  assert.doesNotMatch(source, /customer-tab-employee_blocks/);
});

test("overview workspace is rendered as a grouped local-nav one-page layout", () => {
  assert.match(source, /data-testid="customer-overview-workspace"/);
  assert.match(source, /data-testid="customer-overview-section-nav"/);
  assert.match(source, /class="customer-admin-overview-layout"/);
  assert.match(source, /class="customer-admin-overview-nav-shell"/);
  assert.match(source, /class="customer-admin-overview-content"/);
  assert.match(source, /const customerOverviewSections = computed\(/);
  assert.match(source, /const customerOverviewNavGroups = computed\(/);
  assert.match(source, /const activeOverviewSection = ref\("master_data"\)/);
  assert.match(source, /const customerOverviewSectionRefs = reactive<Record<string, HTMLElement \| null>>\(\{\}\)/);
  assert.match(source, /function setCustomerOverviewSectionRef\(sectionId: string, element: Element \| null\)/);
  assert.match(source, /function resolveCustomerOverviewSectionElement\(sectionId: string\)/);
  assert.match(source, /function scrollToCustomerOverviewSection\(sectionId: CustomerOverviewSectionId\)/);
  assert.match(source, /function selectCustomerOverviewSection\(sectionId: string\)/);
  assert.match(source, /v-if="activeDetailTab === 'overview'"/);
});

test("customer overview nav styling mirrors the employee-style two-column side navigation", () => {
  assert.match(source, /\.customer-admin-overview-layout\s*\{/);
  assert.match(source, /grid-template-columns:\s*minmax\(190px,\s*240px\)\s*minmax\(0,\s*1fr\)/);
  assert.match(source, /\.customer-admin-overview-nav-shell\s*\{/);
  assert.match(source, /position:\s*sticky/);
  assert.match(source, /\.customer-admin-overview-nav__group-toggle\s*\{/);
  assert.match(source, /\.customer-admin-overview-nav__chevron\s*\{/);
  assert.match(source, /\.customer-admin-overview-nav__group-label\s*\{/);
  assert.match(source, /\.customer-admin-overview-nav__children\s*\{/);
  assert.match(source, /\.customer-admin-overview-nav__children--collapsed\s*\{/);
  assert.match(source, /\.customer-admin-overview-nav__link\s*\{/);
  assert.match(source, /\.customer-admin-overview-nav__link--child\s*\{/);
  assert.match(source, /\.customer-admin-overview-nav__link--grandchild\s*\{/);
  assert.match(source, /\.customer-admin-overview-nav__link--active\s*\{/);
  assert.match(source, /\.customer-admin-overview-nav__icon\s*\{/);
  assert.match(source, /\.customer-admin-overview-content\s*\{/);
  assert.match(source, /\.customer-admin-overview-section\s*\{/);
});

test("customer overview route normalization maps legacy tabs into local overview sections", () => {
  assert.match(source, /resolveCustomerOverviewSectionId\(detailTab/);
  assert.match(source, /syncOverviewSectionFromDetailTab\(tabId\)/);
  assert.match(source, /tab: customerOverviewRouteTabForSection\(normalizedSectionId\)/);
  assert.match(source, /syncOverviewSectionFromDetailTab\(nextContext\.detailTab \|\| activeDetailTab\.value\)/);
});

test("overview is a standalone nav item and collapsible groups are rendered separately", () => {
  assert.match(source, /sectionGroup\.testId/);
  assert.doesNotMatch(source, /customer-overview-group-overview/);
  assert.match(source, /data-testid="`customer-overview-group-\$\{sectionGroup\.id\}`"/);
  assert.match(source, /data-testid="`customer-overview-group-\$\{section\.id\}`"/);
  assert.match(source, /data-testid="`customer-overview-group-children-\$\{sectionGroup\.id\}`"/);
  assert.match(source, /data-testid="`customer-overview-group-children-\$\{section\.id\}`"/);
});

test("customer overview contains contacts, commercial, history, and employee blocks while orders stays separate", () => {
  assert.match(source, /data-testid="customer-overview-section-master-data"/);
  assert.match(source, /data-testid="customer-overview-section-contacts"/);
  assert.match(source, /data-testid="customer-overview-section-addresses"/);
  assert.match(source, /data-testid="customer-overview-section-portal-access"/);
  assert.match(source, /data-testid="customer-overview-section-billing-profile"/);
  assert.match(source, /data-testid="customer-overview-section-invoice-parties"/);
  assert.match(source, /data-testid="customer-overview-section-rate-cards"/);
  assert.match(source, /data-testid="customer-overview-section-history"/);
  assert.match(source, /data-testid="customer-overview-section-employee-blocks"/);
  assert.match(source, /v-if="selectedCustomer && !isCreatingCustomer && canReadCustomerOrders && activeDetailTab === 'orders'"/);
  assert.doesNotMatch(source, /data-testid="customer-overview-section-orders"/);
});

test("customer overview content sections use the shared overview card wrapper", () => {
  assert.match(source, /class="module-card customer-admin-tab-panel customer-admin-overview-section customer-admin-overview-section-card"[\s\S]*data-testid="customer-overview-section-master-data"/);
  assert.match(source, /class="module-card customer-admin-contact-access-section-card customer-admin-overview-section customer-admin-overview-section-card"[\s\S]*data-testid="customer-overview-section-contacts"/);
  assert.match(source, /class="module-card customer-admin-contact-access-section-card customer-admin-overview-section customer-admin-overview-section-card"[\s\S]*data-testid="customer-overview-section-addresses"/);
  assert.match(source, /class="module-card customer-admin-contact-access-section-card customer-admin-overview-section customer-admin-overview-section-card"[\s\S]*data-testid="customer-overview-section-portal-access"/);
  assert.match(source, /class="module-card customer-admin-section customer-admin-overview-section customer-admin-overview-section-card"[\s\S]*data-testid="customer-overview-section-billing-profile"/);
  assert.match(source, /class="module-card customer-admin-section customer-admin-overview-section customer-admin-overview-section-card"[\s\S]*data-testid="customer-overview-section-invoice-parties"/);
  assert.match(source, /class="module-card customer-admin-section customer-admin-overview-section customer-admin-overview-section-card"[\s\S]*data-testid="customer-overview-section-rate-cards"/);
});

test("contacts and commercial overview sections no longer use the old nested content gutter", () => {
  assert.match(source, /class="customer-admin-overview-section-group"[\s\S]*data-testid="customer-overview-section-contacts-access"/);
  assert.match(source, /class="customer-admin-overview-section-stack"/);
  assert.doesNotMatch(source, /customer-admin-contact-access-content--stacked/);
  assert.match(source, /class="customer-admin-overview-section-group"[\s\S]*data-testid="customer-overview-section-commercial"/);
  assert.match(source, /\.customer-admin-overview-section-group\s*\{/);
  assert.match(source, /\.customer-admin-overview-section-stack\s*\{/);
  assert.match(source, /\.customer-admin-overview-section-card\s*\{/);
});

test("pricing-rule section visibility still depends on rate-card availability", () => {
  assert.match(source, /customerOverviewSectionVisible\('rate_lines'\) && selectedRateCard/);
  assert.match(source, /customerOverviewSectionVisible\('surcharges'\) && selectedRateCard/);
  assert.match(source, /normalizeCustomerPricingRulesTab\(normalizedSectionId, \{/);
});

test("top-tab title and pageKey behavior remain customer-detail targeted", () => {
  assert.match(source, /function buildCustomerDetailTabTarget\(customerId: string, detailTab = activeDetailTab\.value\)/);
  assert.match(source, /await tabbarStore\.setTabTitle\(buildCustomerDetailTabTarget\(selectedCustomer\.value\.id\) as any, title\)/);
  assert.match(source, /pageKey: currentCustomerDetailPageKey\(\) \|\| buildCustomerDetailPageKey\(selectedCustomer\.value\.id\)/);
  assert.match(source, /await router\.push\(\{[\s\S]*path: CUSTOMER_ADMIN_ROUTE_PATH,[\s\S]*query: \{\},/);
});

test("dashboard and orders remain outside the overview side-navigation workspace", () => {
  assert.match(source, /v-if="selectedCustomer && !isCreatingCustomer && activeDetailTab === 'dashboard'"/);
  assert.match(source, /v-if="selectedCustomer && !isCreatingCustomer && canReadCustomerOrders && activeDetailTab === 'orders'"/);
  assert.match(source, /v-if="activeDetailTab === 'overview'"/);
});
