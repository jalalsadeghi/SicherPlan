import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test } from "vitest";

const assert = {
  match(actual, expected) {
    expect(actual).toMatch(expected);
  },
  doesNotMatch(actual, expected) {
    expect(actual).not.toMatch(expected);
  },
};

function resolveWebAppPath(relativePath) {
  const cwd = process.cwd();
  if (cwd.endsWith("web/apps/web-antd")) {
    return resolve(cwd, relativePath);
  }
  return resolve(cwd, "web/apps/web-antd", relativePath);
}

const viewPath = resolveWebAppPath("src/sicherplan-legacy/views/EmployeeAdminView.vue");
const registryPath = resolveWebAppPath("src/views/sicherplan/module-registry.ts");

const viewSource = readFileSync(viewPath, "utf8");
const registrySource = readFileSync(registryPath, "utf8");

test("employees module hides the shared workspace section header", () => {
  assert.match(registrySource, /employees:\s*{[\s\S]*showWorkspaceSectionHeader:\s*false/);
});

test("employee page does not render the top module intro hero", () => {
  assert.doesNotMatch(viewSource, /class="module-card employee-admin-hero"/);
  assert.doesNotMatch(viewSource, /class="employee-admin-meta__pill"/);
});

test("employee workspace uses stacked full-width list and detail layout with embedded scope removed", () => {
  assert.match(viewSource, /data-testid="employee-master-detail-layout"/);
  assert.match(viewSource, /data-testid="employee-list-section"/);
  assert.match(viewSource, /data-testid="employee-detail-workspace"/);
  assert.match(viewSource, /v-if="!embedded && isPlatformAdmin" class="module-card employee-admin-scope"/);
  assert.match(viewSource, /\.employee-admin-grid\s*{\s*display:\s*grid;[\s\S]*grid-template-columns:\s*minmax\(0,\s*1fr\)/);
  assert.match(viewSource, /\.employee-admin-list-panel\s*{\s*position:\s*static;[\s\S]*top:\s*auto;/);
});

test("employee workspace resolves tenant scope from session bootstrap for normal users", () => {
  assert.match(viewSource, /<section v-if="isEmployeeSessionResolving && !resolvedTenantScopeId" class="module-card employee-admin-empty">/);
  assert.match(viewSource, /<section v-else-if="!resolvedTenantScopeId" class="module-card employee-admin-empty">/);
  assert.match(viewSource, /authStore\.syncFromPrimarySession\(\)/);
  assert.match(viewSource, /await authStore\.ensureSessionReady\(\)/);
  assert.match(viewSource, /tenantScopeInput\.value = authStore\.effectiveTenantScopeId \|\| authStore\.tenantScopeId/);
  assert.match(viewSource, /watch\(\s*\(\) => \[authStore\.effectiveRole, authStore\.effectiveTenantScopeId\] as const/);
  assert.doesNotMatch(viewSource, /await authStore\.loadCurrentSession\(\)/);
});

test("employee workspace treats auth reconciliation as a loading state instead of hard missing scope", () => {
  assert.match(viewSource, /const isEmployeeSessionResolving = computed\(\(\) => authStore\.isSessionResolving\)/);
  assert.match(viewSource, /const employeeWorkspaceBusy = computed\(\(\) => isEmployeeSessionResolving\.value \|\| loading\.action\)/);
  assert.match(viewSource, /workspace\.loading\.reconcilingSession/);
  assert.match(viewSource, /employeeAdmin\.scope\.reconcilingTitle/);
  assert.match(viewSource, /employeeAdmin\.scope\.reconcilingBody/);
});

test("employee detail uses top-level tabs and isolated tab panels", () => {
  assert.match(viewSource, /<SicherPlanLoadingOverlay[\s\S]*busy-testid="employee-workspace-loading-overlay"/);
  assert.match(viewSource, /:busy="employeeWorkspaceBusy"/);
  assert.match(viewSource, /:text="employeeWorkspaceLoadingText"/);
  assert.match(viewSource, /const employeeWorkspaceBusy = computed\(\(\) => isEmployeeSessionResolving\.value \|\| loading\.action\)/);
  assert.match(viewSource, /const employeeWorkspaceLoadingText = computed\(\(\) =>/);
  assert.match(viewSource, /data-testid="employee-detail-tabs"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-overview"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-app-access"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-profile-photo"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-qualifications"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-credentials"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-availability"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-private-profile"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-absences"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-notes"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-groups"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-documents"/);
  assert.match(viewSource, /async function selectEmployee\(employeeId: string, options: SelectEmployeeOptions = \{\}\)/);
  assert.match(viewSource, /preserveActiveTab = false/);
  assert.match(viewSource, /resolveEmployeeDetailTab\(\s*desiredTab,[\s\S]*employeeDetailTabs\.value\.map\(\(tab\) => tab\.id\)/);
  assert.match(viewSource, /selectEmployee\(selectedEmployeeId\.value, \{ preserveActiveTab: true \}\)/);
});

test("employee workspace removes the redundant catalogs tab and keeps only lightweight handoff navigation", () => {
  assert.match(viewSource, /isEmployeeDetailTabDisabled\(tab\.id\)/);
  assert.match(viewSource, /data-testid="employee-open-catalogs"/);
  assert.match(viewSource, /loadEmployeeReadinessCatalogs\(\)/);
  assert.match(viewSource, /openWorkforceCatalogs\(\)/);
  assert.match(viewSource, /router\.push\("\/admin\/workforce-catalogs"\)/);
  assert.match(viewSource, /employeeFunctionTypeOptions = computed\(\(\) =>/);
  assert.match(viewSource, /employeeQualificationTypeOptions = computed\(\(\) =>/);
  assert.match(viewSource, /return true;/);
  assert.doesNotMatch(viewSource, /employeeAdmin\.tabs\.catalogs/);
  assert.doesNotMatch(viewSource, /activeDetailTab === 'catalogs'/);
  assert.doesNotMatch(viewSource, /data-testid="employee-tab-panel-catalogs"/);
  assert.doesNotMatch(viewSource, /data-testid="employee-catalog-handoff"/);
  assert.doesNotMatch(viewSource, /data-testid="employee-manage-catalogs-cta"/);
  assert.doesNotMatch(viewSource, /data-testid="employee-function-types-section"/);
  assert.doesNotMatch(viewSource, /data-testid="employee-qualification-types-section"/);
  assert.doesNotMatch(viewSource, /submitFunctionTypeCatalog/);
  assert.doesNotMatch(viewSource, /submitQualificationTypeCatalog/);
});

test("employee search results render only inside a dismissible search dialog", () => {
  assert.match(viewSource, /data-testid="employee-search-select"/);
  assert.match(viewSource, /data-testid="employee-search-select-input"/);
  assert.match(viewSource, /data-testid="employee-search-suggestions"/);
  assert.match(viewSource, /data-testid="employee-search-suggestion-row"/);
  assert.match(viewSource, /data-testid="employee-search-suggestion-empty"/);
  assert.match(viewSource, /@keydown\.escape\.stop\.prevent="closeEmployeeSearchSuggestions"/);
  assert.match(viewSource, /@keydown\.enter\.prevent="handleOpenEmployeeSearchResults"/);
  assert.match(viewSource, /data-testid="employee-search-results-modal"/);
  assert.match(viewSource, /data-testid="employee-search-result-close"/);
  assert.match(viewSource, /data-testid="employee-search-result-empty"/);
  assert.match(viewSource, /data-testid="employee-search-result-row"/);
  assert.match(viewSource, /@click="selectEmployeeFromSearchResult\(employee\.id\)"/);
  assert.doesNotMatch(viewSource, /class="employee-admin-row"/);
  assert.match(viewSource, /\.employee-admin-record\s*{[\s\S]*padding:\s*1rem;[\s\S]*border-radius:\s*18px;[\s\S]*border:\s*1px solid var\(--sp-color-border-soft\);/);
});

test("employee list panel splits search and import-export into tabs and preserves tab-panel structure", () => {
  assert.match(viewSource, /data-testid="employee-list-tabs"/);
  assert.match(viewSource, /data-testid="employee-list-tab-search"/);
  assert.match(viewSource, /data-testid="employee-list-tab-import-export"/);
  assert.match(viewSource, /data-testid="employee-list-tab-panel-search"/);
  assert.match(viewSource, /data-testid="employee-list-tab-panel-import-export"/);
  assert.match(viewSource, /v-show="listPanelTab === 'search'"/);
  assert.match(viewSource, /v-show="listPanelTab === 'import_export'"/);
  assert.match(viewSource, /employee-list-tab-panel-search[\s\S]*employeeAdmin\.actions\.search/);
  assert.match(viewSource, /employee-list-tab-panel-search[\s\S]*employeeAdmin\.actions\.newEmployee/);
  assert.match(viewSource, /employee-list-tab-panel-search[\s\S]*data-testid="employee-search-select"/);
  assert.match(viewSource, /class="employee-admin-filter-grid"/);
  assert.match(viewSource, /class="employee-admin-filter-actions"/);
  assert.match(viewSource, /class="cta-row employee-admin-filter-actions__buttons"/);
  assert.match(viewSource, /\.employee-admin-filter-grid\s*{[\s\S]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\)/);
  assert.match(viewSource, /@media \(max-width:\s*1280px\)[\s\S]*\.employee-admin-filter-grid\s*{[\s\S]*repeat\(2,\s*minmax\(0,\s*1fr\)\)/);
  assert.match(viewSource, /@media \(max-width:\s*720px\)[\s\S]*\.employee-admin-filter-grid\s*{[\s\S]*grid-template-columns:\s*1fr/);
  assert.match(viewSource, /employee-list-tab-panel-import-export[\s\S]*employeeAdmin\.actions\.loadImportFile/);
  assert.match(viewSource, /employee-list-tab-panel-import-export[\s\S]*employeeAdmin\.actions\.importExecute/);
  assert.match(viewSource, /employee-list-tab-panel-import-export[\s\S]*employeeAdmin\.actions\.exportEmployees/);
});

test("employee workspace uses shared toast feedback instead of a persistent inline banner", () => {
  assert.match(viewSource, /useSicherPlanFeedback/);
  assert.match(viewSource, /showFeedbackToast\(\{\s*key:\s*"employee-admin-feedback"/);
  assert.doesNotMatch(viewSource, /employee-feedback-banner/);
  assert.doesNotMatch(viewSource, /class="employee-admin-feedback__dismiss"/);
  assert.doesNotMatch(viewSource, /function clearFeedback\(/);
  assert.doesNotMatch(viewSource, /\.employee-admin-feedback\[data-tone='success'\]/);
});

test("non-overview employee tabs reuse the structured section pattern", () => {
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*employeeAdmin\.privateProfile\.identityEyebrow/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*employeeAdmin\.privateProfile\.contactEyebrow/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*employeeAdmin\.privateProfile\.payrollEyebrow/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*employeeAdmin\.privateProfile\.bankingEyebrow/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*employeeAdmin\.privateProfile\.emergencyEyebrow/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*employeeAdmin\.privateProfile\.notesEyebrow/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*submitPrivateProfile/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*getEmployeePrivateProfile/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*upsertEmployeePrivateProfile/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*updateEmployeePrivateProfile/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*listEmployeePrivateProfileMaritalStatusOptions/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*privateProfileDraft\.private_email/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*privateProfileDraft\.private_phone/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*privateProfileDraft\.marital_status_code/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*data-testid="employee-private-profile-marital-status-select"/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*<select[\s\S]*v-model="privateProfileDraft\.marital_status_code"/);
  assert.doesNotMatch(viewSource, /employee-tab-panel-private-profile[\s\S]*<input v-model="privateProfileDraft\.marital_status(?:_code)?"/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*employeeAdmin\.privateProfile\.maritalStatusPlaceholder/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*employeeAdmin\.privateProfile\.maritalStatusLegacyHint/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*privateProfileDraft\.tax_id/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*privateProfileDraft\.social_security_no/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*privateProfileDraft\.bank_account_holder/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*privateProfileDraft\.bank_iban/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*privateProfileDraft\.bank_bic/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*privateProfileDraft\.emergency_contact_name/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*privateProfileDraft\.emergency_contact_phone/);
  assert.match(viewSource, /employee-tab-panel-private-profile[\s\S]*privateProfileDraft\.notes/);
  assert.match(viewSource, /validateEmployeePrivateProfileDraft\(privateProfileDraft\)/);
  assert.match(viewSource, /syncPrivateProfileDraft\(profile: EmployeePrivateProfileRead \| null\)[\s\S]*privateProfileDraft\.private_email/);
  assert.match(viewSource, /resetPrivateProfileDraft\(\)[\s\S]*privateProfileDraft\.private_email/);
  assert.match(viewSource, /buildEmployeePrivateProfilePayload\(privateProfileDraft/);
  assert.doesNotMatch(viewSource, /privateProfileDraft\.(religion|tax_class|health_insurer|child_allowance|driver_license)/);
  assert.match(viewSource, /employee-tab-panel-app-access[\s\S]*employee-admin-form employee-admin-form--structured[\s\S]*employeeAdmin\.access\.stateCreateEyebrow/);
  assert.match(viewSource, /employee-tab-panel-app-access[\s\S]*v-if="!hasLinkedAccess"[\s\S]*employeeAdmin\.access\.createEyebrow/);
  assert.match(viewSource, /employee-tab-panel-app-access[\s\S]*v-else[\s\S]*employeeAdmin\.access\.manageEyebrow[\s\S]*employeeAdmin\.access\.resetEyebrow[\s\S]*employeeAdmin\.access\.detachEyebrow/);
  assert.match(viewSource, /employee-tab-panel-app-access[\s\S]*employee-admin-advanced-access[\s\S]*employeeAdmin\.access\.attachEyebrow[\s\S]*employeeAdmin\.access\.reconcileEyebrow/);
  assert.match(viewSource, /employee-tab-panel-profile-photo[\s\S]*employee-admin-editor-intro[\s\S]*employeeAdmin\.photo\.manageEyebrow/);
  assert.match(viewSource, /employee-tab-panel-qualifications[\s\S]*employeeAdmin\.qualifications\.registerEyebrow/);
  assert.match(viewSource, /employee-tab-panel-qualifications[\s\S]*createEmployeeQualification/);
  assert.match(viewSource, /employee-tab-panel-qualifications[\s\S]*updateEmployeeQualification/);
  assert.match(viewSource, /employee-tab-panel-qualifications[\s\S]*listEmployeeQualificationProofs/);
  assert.match(viewSource, /employee-tab-panel-qualifications[\s\S]*uploadEmployeeQualificationProof/);
  assert.match(viewSource, /employee-tab-panel-qualifications[\s\S]*employeeAdmin\.qualifications\.functionTypeEmptyHint/);
  assert.match(viewSource, /employee-tab-panel-qualifications[\s\S]*employeeAdmin\.qualifications\.qualificationTypeEmptyHint/);
  assert.match(viewSource, /employee-tab-panel-qualifications[\s\S]*employeeAdmin\.qualifications\.expiryRequiredHint/);
  assert.match(viewSource, /employee-tab-panel-qualifications[\s\S]*employeeAdmin\.qualifications\.expiryAutofillHint/);
  assert.match(viewSource, /selectedQualificationType = computed/);
  assert.match(viewSource, /validateEmployeeQualificationDraft\(qualificationDraft, selectedQualificationType\.value\)/);
  assert.match(viewSource, /watch\(\s*\(\) => qualificationDraft\.record_kind,[\s\S]*qualificationDraft\.qualification_type_id = ""[\s\S]*qualificationDraft\.function_type_id = ""/);
  assert.match(viewSource, /employee-tab-panel-credentials[\s\S]*employeeAdmin\.credentials\.registerEyebrow/);
  assert.match(viewSource, /employee-tab-panel-credentials[\s\S]*createEmployeeCredential/);
  assert.match(viewSource, /employee-tab-panel-credentials[\s\S]*updateEmployeeCredential/);
  assert.match(viewSource, /employee-tab-panel-credentials[\s\S]*issueEmployeeCredentialBadgeOutput/);
  assert.match(viewSource, /employee-tab-panel-credentials[\s\S]*<select v-model="credentialDraft\.credential_type"/);
  assert.doesNotMatch(viewSource, /<input v-model="credentialDraft\.credential_type"/);
  assert.match(viewSource, /employee-tab-panel-credentials[\s\S]*employeeAdmin\.credentials\.credentialTypePlaceholder/);
  assert.match(viewSource, /EMPLOYEE_CREDENTIAL_TYPE_OPTIONS/);
  assert.match(viewSource, /employeeCredentialTypeOptions = computed/);
  assert.match(viewSource, /employee-tab-panel-credentials[\s\S]*employeeAdmin\.credentials\.encodedValueHelp/);
  assert.match(viewSource, /employee-tab-panel-availability[\s\S]*employeeAdmin\.availability\.registerEyebrow/);
  assert.match(viewSource, /employee-tab-panel-availability[\s\S]*createEmployeeAvailabilityRule/);
  assert.match(viewSource, /employee-tab-panel-availability[\s\S]*updateEmployeeAvailabilityRule/);
  assert.match(viewSource, /employee-tab-panel-availability[\s\S]*<select v-model="availabilityDraft\.rule_kind"/);
  assert.doesNotMatch(viewSource, /<input v-model="availabilityDraft\.rule_kind"/);
  assert.match(viewSource, /employee-tab-panel-availability[\s\S]*employeeAdmin\.availability\.ruleKindPlaceholder/);
  assert.match(viewSource, /EMPLOYEE_AVAILABILITY_RULE_KIND_OPTIONS/);
  assert.match(viewSource, /employeeAvailabilityRuleKindOptions = computed/);
  assert.match(viewSource, /employee-tab-panel-notes[\s\S]*employeeAdmin\.notes\.registerEyebrow[\s\S]*employeeAdmin\.notes\.editorEyebrow/);
  assert.match(viewSource, /employee-tab-panel-groups[\s\S]*employeeAdmin\.groups\.catalogEyebrow[\s\S]*employeeAdmin\.groups\.assignEyebrow[\s\S]*employeeAdmin\.groups\.currentEyebrow/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.addresses\.currentEyebrow/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.addresses\.editorEyebrow/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*submitAddress/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*createEmployeeAddress/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*updateEmployeeAddress/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.actions\.editAddress/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.actions\.markCurrentAddress/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.actions\.closeAddressValidity/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*addressEditorMode/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*addressEditorEyebrowKey/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*addressEditorTitleKey/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*addressEditorLeadKey/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.addresses\.primaryLabel/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*v-if="!isEmployeeAddressCurrent\(addressRow\)"/);
  assert.doesNotMatch(viewSource, /addressDraft\.is_current/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*employeeAdmin\.documents\.libraryEyebrow/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*employeeAdmin\.documents\.uploadEyebrow/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*employeeAdmin\.documents\.linkEyebrow/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*employeeAdmin\.documents\.versionEyebrow/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*uploadEmployeeDocument/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*linkEmployeeDocument/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*addEmployeeDocumentVersion/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*employeeAdmin\.actions\.useDocumentForVersion/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*<select v-model="documentUploadDraft\.document_type_key"/);
  assert.doesNotMatch(viewSource, /employee-tab-panel-documents[\s\S]*<input v-model="documentUploadDraft\.document_type_key"/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*employeeAdmin\.documents\.documentTypePlaceholder/);
  assert.match(viewSource, /employee-tab-panel-documents[\s\S]*employeeAdmin\.documents\.documentTypeHelp/);
  assert.match(viewSource, /EMPLOYEE_DOCUMENT_TYPE_OPTIONS/);
  assert.match(viewSource, /employee-tab-panel-absences[\s\S]*employeeAdmin\.absences\.registerEyebrow/);
  assert.match(viewSource, /employee-tab-panel-absences[\s\S]*createEmployeeAbsence/);
  assert.match(viewSource, /employee-tab-panel-absences[\s\S]*updateEmployeeAbsence/);
});

test("employee addresses tab uses admin editor copy and removes released timeline wording", () => {
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.addresses\.empty/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAdmin\.feedback\.addressSaved/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*employeeAddressTimeline/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*prepareAddressAsCurrent/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*prepareAddressValidityClose/);
  assert.match(viewSource, /employee-tab-panel-addresses[\s\S]*isEmployeeAddressCurrent\(addressRow\)/);
  assert.match(viewSource, /currentEmployeeAddress[\s\S]*editAddress\(currentEmployeeAddress\)/);
  assert.match(viewSource, /currentEmployeeAddress[\s\S]*prepareAddressValidityClose\(currentEmployeeAddress\)/);
  assert.match(viewSource, /employeeAddressTimeline = computed\(\(\) =>[\s\S]*isEmployeeAddressCurrent/);
  assert.match(viewSource, /currentEmployeeAddress = computed\(\s*\(\) =>[\s\S]*isEmployeeAddressCurrent/);
  assert.match(viewSource, /addressTransitionSourceId/);
  assert.match(viewSource, /addressEditorMode\.value === "transition"/);
  assert.match(viewSource, /ignoreRowIds: \[currentSameTypeAddress\.id\]/);
  assert.match(viewSource, /employeeAdmin\.feedback\.addressTransitionEffectiveDate/);
  assert.doesNotMatch(viewSource, /Released address timeline/);
  assert.doesNotMatch(viewSource, /No released address history is available/);
  assert.doesNotMatch(viewSource, /onAddressCurrentToggle/);
});

test("employee overview exposes status and extended employment fields", () => {
  assert.match(viewSource, /employeeAdmin\.fields\.status/);
  assert.match(viewSource, /employeeAdmin\.fields\.employmentTypeCode/);
  assert.match(viewSource, /employeeAdmin\.fields\.targetWeeklyHours/);
  assert.match(viewSource, /employeeAdmin\.fields\.targetMonthlyHours/);
});
