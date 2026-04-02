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
  assert.match(source, /const customerWorkspaceLoadingText = computed\(\(\) => \(customerWorkspaceBusy\.value \? t\("workspace\.loading\.processing"\) : ""\)\)/);
  assert.match(source, /class="customer-admin-grid"/);
  assert.match(source, /data-testid="customer-list-section"/);
  assert.match(source, /data-testid="customer-detail-workspace"/);
  assert.match(source, /data-testid="customer-detail-tabs"/);
  assert.match(source, /resolveCustomerAdminRouteContext\(route\.query\)/);
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
  assert.match(source, /customer-tab-panel-contacts[\s\S]*customer-admin-form customer-admin-form--structured[\s\S]*customerAdmin\.contacts\.registerEyebrow[\s\S]*customerAdmin\.contacts\.editorEyebrow[\s\S]*customerAdmin\.fields\.notes/);
  assert.match(source, /customer-tab-panel-addresses[\s\S]*customerAdmin\.addresses\.registerEyebrow[\s\S]*customerAdmin\.addresses\.editorEyebrow/);
  assert.match(source, /customer-tab-panel-commercial[\s\S]*customer-admin-editor-intro[\s\S]*customer-commercial-panel-billing-profile/);
  assert.match(source, /customer-tab-panel-portal[\s\S]*customerAdmin\.portal\.lead[\s\S]*customer-portal-access-section[\s\S]*customerAdmin\.portalAccess\.title[\s\S]*customerAdmin\.loginHistory\.title/);
  assert.match(source, /customer-tab-panel-history[\s\S]*customerAdmin\.history\.registerEyebrow[\s\S]*customerAdmin\.history\.attachmentEyebrow/);
  assert.match(source, /customer-tab-panel-employee-blocks[\s\S]*customerAdmin\.employeeBlocks\.registerEyebrow[\s\S]*customerAdmin\.employeeBlocks\.editorEyebrow/);
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
