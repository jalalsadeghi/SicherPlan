import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const viewPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/views/SubcontractorAdminView.vue",
);
const workforcePath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/components/SubcontractorWorkforcePanel.vue",
);
const apiPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/sicherplan-legacy/api/subcontractors.ts",
);
const registryPath = resolve(
  process.cwd(),
  "web/apps/web-antd/src/views/sicherplan/module-registry.ts",
);
const source = readFileSync(viewPath, "utf8");
const workforceSource = readFileSync(workforcePath, "utf8");
const apiSource = readFileSync(apiPath, "utf8");
const registrySource = readFileSync(registryPath, "utf8");

test("subcontractor workspace keeps compact master detail layout with detail tabs", () => {
  assert.match(source, /class="subcontractor-admin-grid"/);
  assert.match(source, /grid-template-columns:\s*minmax\(320px, 420px\) minmax\(0, 1fr\)/);
  assert.match(source, /data-testid="subcontractor-list-section"/);
  assert.match(source, /data-testid="subcontractor-detail-workspace"/);
  assert.match(source, /data-testid="subcontractor-detail-tabs"/);
});

test("embedded subcontractor view suppresses local hero chrome", () => {
  assert.match(source, /v-if="!props\.embedded" class="module-card subcontractor-admin-hero"/);
});

test("subcontractor detail workspace shows only supported tab panels", () => {
  assert.match(source, /data-testid="subcontractor-tab-panel-overview"/);
  assert.match(source, /data-testid="subcontractor-tab-panel-contacts"/);
  assert.match(source, /data-testid="subcontractor-tab-panel-scope-release"/);
  assert.match(source, /data-testid="subcontractor-tab-panel-billing"/);
  assert.match(source, /data-testid="subcontractor-tab-panel-history"/);
  assert.match(source, /activeDetailTab === 'workforce'/);
  assert.doesNotMatch(source, /data-testid="subcontractor-tab-panel-addresses"/);
  assert.doesNotMatch(source, /data-testid="subcontractor-tab-panel-commercial"/);
  assert.doesNotMatch(source, /tabs\.addresses/);
  assert.doesNotMatch(source, /tabs\.commercial/);
});

test("subcontractor admin uses controlled selectors where real option sources exist", () => {
  assert.match(source, /listBranches,/);
  assert.match(source, /listMandates,/);
  assert.match(source, /listLookupValues,/);
  assert.match(source, /getSubcontractorReferenceData,/);
  assert.match(source, /listSubcontractorAddressOptions,/);
  assert.match(source, /listSubcontractorContactUserOptions,/);
  assert.match(source, /data-testid="subcontractor-scope-branch"/);
  assert.match(source, /scopeBranchSelectEnabled/);
  assert.match(source, /data-testid="subcontractor-scope-mandate"/);
  assert.match(source, /scopeMandateSelectEnabled/);
  assert.match(source, /scopeMandateOptionsWithDraft/);
  assert.doesNotMatch(source, /<input v-else v-model="scopeDraft\.branch_id"/);
  assert.doesNotMatch(source, /<input v-else v-model="scopeDraft\.mandate_id"/);
  assert.match(source, /data-testid="subcontractor-legal-form"/);
  assert.match(source, /v-model="subcontractorDraft\.legal_form_lookup_id"/);
  assert.match(source, /legalFormOptionsWithDraft/);
  assert.match(source, /legalFormSelectEnabled/);
  assert.match(source, /getSubcontractorReferenceData\(/);
  assert.doesNotMatch(source, /<input v-else v-model="subcontractorDraft\.legal_form_lookup_id"/);
  assert.match(source, /v-if="subcontractorStatusOptions\.length" v-model="subcontractorDraft\.subcontractor_status_lookup_id"/);
  assert.match(source, /v-if="addressOptions\.length" v-model="subcontractorDraft\.address_id"/);
  assert.match(source, /v-if="contactUserOptions\.length" v-model="contactDraft\.user_id"/);
  assert.match(source, /v-if="invoiceDeliveryMethodOptions\.length" v-model="financeDraft\.invoice_delivery_method_lookup_id"/);
  assert.match(source, /v-if="invoiceStatusModeOptions\.length" v-model="financeDraft\.invoice_status_mode_lookup_id"/);
});

test("subcontractor scope filters mandates by branch and clears stale mandate selections", () => {
  assert.match(source, /const scopeMandateOptions = computed\(\(\) => \{/);
  assert.match(source, /return mandateOptions\.value\.filter\(\(row\) => row\.branchId === scopeDraft\.branch_id\)/);
  assert.match(source, /watch\(\s*\(\) => scopeDraft\.branch_id,/);
  assert.match(source, /const mandateStillValid = scopeMandateOptions\.value\.some\(\(mandate\) => mandate\.id === scopeDraft\.mandate_id\)/);
  assert.match(source, /scopeDraft\.mandate_id = ""/);
});

test("subcontractor scope uses distinct loading, ready, empty, and error placeholder states", () => {
  assert.match(source, /const structureOptionState = reactive\(\{/);
  assert.match(source, /loading: false/);
  assert.match(source, /error: false/);
  assert.match(source, /const scopeBranchPlaceholderKey = computed\(\(\) => \{/);
  assert.match(source, /fields\.branchLoadingPlaceholder/);
  assert.match(source, /fields\.branchPlaceholder/);
  assert.match(source, /fields\.branchEmptyPlaceholder/);
  assert.match(source, /fields\.branchUnavailablePlaceholder/);
  assert.match(source, /const scopeMandatePlaceholderKey = computed\(\(\) => \{/);
  assert.match(source, /fields\.mandateLoadingPlaceholder/);
  assert.match(source, /fields\.mandatePlaceholder/);
  assert.match(source, /fields\.mandateEmptyPlaceholder/);
  assert.match(source, /fields\.mandateEmptyForBranchPlaceholder/);
  assert.match(source, /fields\.mandateUnavailablePlaceholder/);
  assert.match(source, /structureOptionState\.loading = true/);
  assert.match(source, /structureOptionState\.error = true/);
  assert.match(source, /structureOptionState\.loading = false/);
});

test("subcontractor detail loading keeps finance-profile fetch out of the core loader and defers it to Billing", () => {
  const loadSelectedStart = source.indexOf("async function loadSelectedSubcontractor");
  const loadSelectedEnd = source.indexOf("async function loadFinanceProfile");
  assert.notEqual(loadSelectedStart, -1);
  assert.notEqual(loadSelectedEnd, -1);
  const loadSelectedSource = source.slice(loadSelectedStart, loadSelectedEnd);

  assert.match(source, /async function loadFinanceProfile\(force = false\)/);
  assert.match(source, /getSubcontractorFinanceProfile\(/);
  assert.match(source, /isMissingFinanceProfileError/);
  assert.match(source, /error instanceof SubcontractorAdminApiError && error\.statusCode === 404/);
  assert.match(source, /tabId !== "billing"/);
  assert.doesNotMatch(loadSelectedSource, /getSubcontractorFinanceProfile\(/);
});

test("subcontractor overview removes the extra legal-form and map helper copy while keeping controls", () => {
  assert.match(source, /v-if="legalFormHelpKey" class="field-help"/);
  assert.doesNotMatch(source, /fields\.legalFormHelp"/);
  assert.match(source, /data-testid="subcontractor-pick-location"/);
  assert.doesNotMatch(source, /fields\.locationPicker"/);
  assert.doesNotMatch(source, /fields\.locationPickerHelp"/);
});

test("subcontractor overview separates lifecycle status from lookup status and uses address modal flow", () => {
  assert.match(source, /subcontractorDraft\.status/);
  assert.match(source, /fields\.lifecycleStatus/);
  assert.match(source, /fields\.statusLookupHelp/);
  assert.match(source, /data-testid="subcontractor-address-modal"/);
  assert.match(source, /@click="openAddressCreateModal"/);
  assert.match(source, /@submit\.prevent="submitAddressOption"/);
  assert.match(source, /createSubcontractorAddressOption/);
  assert.match(source, /subcontractorDraft\.address_id = created\.id/);
  assert.match(source, /class="subcontractor-admin-address-row field-stack--wide"/);
  assert.match(source, /subcontractor-admin-address-row__field/);
  assert.match(source, /subcontractor-admin-address-row__action/);
});

test("subcontractor overview reuses the shared planning map picker for latitude and longitude", () => {
  assert.match(source, /import PlanningLocationPickerModal from "@\/components\/planning\/PlanningLocationPickerModal\.vue"/);
  assert.match(source, /resolveInitialMapCenter/);
  assert.match(source, /actions\.pickLocationOnMap/);
  assert.match(source, /v-model:open="locationPickerOpen"/);
  assert.match(source, /:latitude="subcontractorDraft\.latitude"/);
  assert.match(source, /:longitude="subcontractorDraft\.longitude"/);
  assert.match(source, /subcontractorDraft\.latitude = payload\.latitude/);
  assert.match(source, /subcontractorDraft\.longitude = payload\.longitude/);
  assert.match(source, /resolvedCenter\.source === "existing-record"/);
});

test("subcontractor workforce uses qualification and credential selectors instead of free-text IDs", () => {
  assert.match(workforceSource, /listQualificationTypes/);
  assert.match(workforceSource, /EMPLOYEE_CREDENTIAL_TYPE_OPTIONS/);
  assert.match(workforceSource, /<select v-if="qualificationTypeOptions\.length" v-model="qualificationDraft\.qualification_type_id" required>/);
  assert.match(workforceSource, /<select v-model="credentialDraft\.credential_type" required>/);
  assert.doesNotMatch(workforceSource, /<input v-model="credentialDraft\.credential_type" required \/>/);
});

test("subcontractor scope stays aligned with current branch and mandate contract only", () => {
  assert.match(apiSource, /export interface SubcontractorScopeRead \{[\s\S]*branch_id: string;[\s\S]*mandate_id: string \| null;/);
  assert.doesNotMatch(apiSource, /site_id/);
  assert.doesNotMatch(source, /scopeDraft\.site_id/);
});

test("subcontractor module wrapper skips the extra workspace block", () => {
  assert.match(
    registrySource,
    /subcontractors:\s*\{[\s\S]*showWorkspaceSectionHeader:\s*false/,
  );
});
