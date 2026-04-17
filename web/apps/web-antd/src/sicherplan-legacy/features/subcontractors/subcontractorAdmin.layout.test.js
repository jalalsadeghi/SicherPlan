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
  assert.match(source, /listSubcontractorAddressOptions,/);
  assert.match(source, /listSubcontractorContactUserOptions,/);
  assert.match(source, /v-if="branchOptions\.length" v-model="scopeDraft\.branch_id"/);
  assert.match(source, /v-if="mandateOptions\.length" v-model="scopeDraft\.mandate_id"/);
  assert.match(source, /v-if="legalFormOptions\.length" v-model="subcontractorDraft\.legal_form_lookup_id"/);
  assert.match(source, /v-if="subcontractorStatusOptions\.length" v-model="subcontractorDraft\.subcontractor_status_lookup_id"/);
  assert.match(source, /v-if="addressOptions\.length" v-model="subcontractorDraft\.address_id"/);
  assert.match(source, /v-if="contactUserOptions\.length" v-model="contactDraft\.user_id"/);
  assert.match(source, /v-if="invoiceDeliveryMethodOptions\.length" v-model="financeDraft\.invoice_delivery_method_lookup_id"/);
  assert.match(source, /v-if="invoiceStatusModeOptions\.length" v-model="financeDraft\.invoice_status_mode_lookup_id"/);
});

test("subcontractor overview separates lifecycle status from lookup status and uses address modal flow", () => {
  assert.match(source, /subcontractorDraft\.status/);
  assert.match(source, /fields\.lifecycleStatus/);
  assert.match(source, /fields\.statusLookupHelp/);
  assert.match(source, /data-testid="subcontractor-address-modal"/);
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
