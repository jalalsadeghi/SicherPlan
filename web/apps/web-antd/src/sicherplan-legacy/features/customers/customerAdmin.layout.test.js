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
  assert.match(source, /resolveCustomerAdminRouteContext\(route\.query\)/);
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
  assert.match(source, /customerAdmin\.commercial\.invoicePartyAddressMissing/);
  assert.match(source, /customerAdmin\.actions\.openAddressesTab/);
  assert.match(source, /openCustomerAddressesTab/);
  assert.doesNotMatch(source, /<input v-model="invoicePartyDraft\.address_id"/);
});

test("address-link form uses available-address selector instead of raw address uuid input", () => {
  assert.match(source, /customerAdmin\.addresses\.linkLead/);
  assert.match(source, /customerAdmin\.fields\.address/);
  assert.match(source, /availableAddressDirectory/);
  assert.match(source, /customerAddressLinkOptions/);
  assert.match(source, /customerAddressLinkPlaceholder/);
  assert.match(source, /listCustomerAvailableAddresses/);
  assert.match(source, /refreshAvailableAddresses/);
  assert.match(source, /formatAddressDirectoryOption/);
  assert.match(source, /customerAdmin\.addresses\.addressLinkEmpty/);
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
