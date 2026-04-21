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
  assert.match(registrySource, /customers:\s*{[\s\S]*showPageIntro:\s*false/);
  assert.match(registrySource, /employees:\s*{[\s\S]*showPageIntro:\s*false,[\s\S]*showWorkspaceSectionHeader:\s*false/);
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

test("employee detail uses dashboard and overview top-level tabs with one-page overview sections", () => {
  assert.match(viewSource, /<SicherPlanLoadingOverlay[\s\S]*busy-testid="employee-workspace-loading-overlay"/);
  assert.match(viewSource, /:busy="employeeWorkspaceBusy"/);
  assert.match(viewSource, /:text="employeeWorkspaceLoadingText"/);
  assert.match(viewSource, /const employeeWorkspaceBusy = computed\(\(\) => isEmployeeSessionResolving\.value \|\| loading\.action\)/);
  assert.match(viewSource, /const employeeWorkspaceLoadingText = computed\(\(\) =>/);
  assert.match(viewSource, /data-testid="employee-detail-tabs"/);
  assert.match(viewSource, /EmployeeDashboardTab/);
  assert.match(viewSource, /data-testid="employee-tab-panel-dashboard"/);
  assert.match(viewSource, /data-testid="employee-tab-panel-overview"/);
  assert.match(viewSource, /data-testid="employee-overview-onepage"/);
  assert.match(viewSource, /data-testid="employee-overview-section-nav"/);
  assert.match(viewSource, /class="employee-admin-overview-nav-shell"[\s\S]*data-testid="employee-overview-section-nav"[\s\S]*<nav[\s\S]*class="employee-admin-overview-nav"/);
  assert.match(viewSource, /<aside[\s\S]*class="employee-admin-overview-nav-shell"[\s\S]*<\/aside>\s*<div class="employee-admin-overview-content">/);
  assert.match(viewSource, /employee-admin-overview-section-card/);
  assert.match(viewSource, /employee-admin-overview-section-card__header/);
  assert.match(viewSource, /employee-admin-overview-subsection/);
  assert.match(viewSource, /employee-admin-overview-subsection__header/);
  assert.match(viewSource, /IconifyIcon class="employee-admin-overview-nav__icon"/);
  assert.match(viewSource, /:icon="section\.icon"/);
  assert.match(viewSource, /aria-hidden="true"/);
  assert.match(viewSource, /import \{ IconifyIcon \} from "@vben\/icons";/);
  assert.match(viewSource, /employeeOverviewSectionObserver: IntersectionObserver \| null/);
  assert.match(viewSource, /root:\s*resolveOverviewIntersectionRoot\(\)/);
  assert.match(viewSource, /rootMargin:\s*`-\$\{Math\.round\(stickyTop\)\}px 0px -55% 0px`/);
  assert.match(viewSource, /employee-admin-overview-nav__link--active/);
  assert.match(viewSource, /ref="overviewOnePageRef"/);
  assert.match(viewSource, /ref="overviewNavShellRef"/);
  assert.match(viewSource, /overviewNavFloatingMode === 'fixed'/);
  assert.match(viewSource, /overviewNavFloatingMode === 'pinned'/);
  assert.match(viewSource, /class="employee-admin-overview-nav-shell"/);
  assert.match(viewSource, /class="employee-admin-overview-nav"/);
  assert.match(viewSource, /class="employee-admin-overview-nav__link"/);
  assert.doesNotMatch(viewSource, /class="[^"]*employee-admin-overview-nav[^"]*employee-admin-card[^"]*"/);
  assert.doesNotMatch(viewSource, /class="[^"]*employee-admin-overview-nav__link[^"]*employee-admin-tab[^"]*"/);
  assert.doesNotMatch(viewSource, /employee-admin-overview-nav__chip/);
  assert.match(viewSource, /--employee-overview-sticky-top:\s*var\(--sp-sticky-offset,\s*6\.5rem\)/);
  assert.match(viewSource, /\.employee-admin-overview-onepage\s*\{[\s\S]*grid-template-columns:\s*minmax\(190px,\s*240px\) minmax\(0,\s*1fr\)/);
  assert.match(viewSource, /\.employee-admin-overview-onepage\s*\{[\s\S]*align-items:\s*start/);
  assert.match(viewSource, /\.employee-admin-overview-onepage\s*\{[\s\S]*position:\s*relative/);
  assert.match(viewSource, /\.employee-admin-overview-content\s*\{[\s\S]*display:\s*grid/);
  assert.match(viewSource, /\.employee-admin-overview-content\s*\{[\s\S]*grid-column:\s*2/);
  assert.match(viewSource, /\.employee-admin-overview-nav-shell\s*\{[\s\S]*position:\s*sticky/);
  assert.match(viewSource, /\.employee-admin-overview-nav-shell\s*\{[\s\S]*grid-column:\s*1/);
  assert.match(viewSource, /top:\s*var\(--employee-overview-sticky-top,\s*6\.5rem\)/);
  assert.match(viewSource, /max-height:\s*calc\(100vh - var\(--employee-overview-sticky-top,\s*6\.5rem\) - 1rem\)/);
  assert.match(viewSource, /\.employee-admin-overview-nav-shell\s*\{[\s\S]*overflow-y:\s*auto/);
  assert.match(viewSource, /\.employee-admin-overview-nav-shell\s*\{[\s\S]*overscroll-behavior:\s*contain/);
  assert.match(viewSource, /function setupOverviewNavFloating\(\)/);
  assert.match(viewSource, /window\.requestAnimationFrame\(updateOverviewNavFloating\)/);
  assert.match(viewSource, /\.employee-admin-overview-nav-shell--fixed\s*\{[\s\S]*position:\s*fixed/);
  assert.match(viewSource, /\.employee-admin-overview-nav-shell--pinned\s*\{[\s\S]*position:\s*absolute/);
  assert.match(viewSource, /\.employee-admin-overview-section-card\s*\{[\s\S]*scroll-margin-top:\s*var\(--employee-overview-sticky-top,\s*6\.5rem\)/);
  assert.match(viewSource, /@media \(max-width: 1080px\)[\s\S]*\.employee-admin-overview-nav-shell\s*\{[\s\S]*position:\s*static/);
  assert.match(viewSource, /@media \(max-width: 1080px\)[\s\S]*\.employee-admin-overview-nav-shell\s*\{[\s\S]*overflow:\s*visible/);
  assert.match(viewSource, /@media \(max-width: 1080px\)[\s\S]*\.employee-admin-overview-nav\s*\{[\s\S]*overflow-x:\s*auto/);
  assert.match(viewSource, /scrollIntoView\(\{\s*behavior:\s*"smooth",\s*block:\s*"start"/);
  assert.match(viewSource, /data-testid="employee-overview-section-file"/);
  assert.match(viewSource, /data-testid="employee-overview-section-app-access"/);
  assert.doesNotMatch(viewSource, /data-testid="employee-tab-panel-profile-photo"/);
  assert.match(viewSource, /data-testid="employee-overview-section-qualifications"/);
  assert.match(viewSource, /data-testid="employee-overview-section-credentials"/);
  assert.match(viewSource, /data-testid="employee-overview-section-availability"/);
  assert.match(viewSource, /data-testid="employee-overview-section-private-profile"/);
  assert.match(viewSource, /data-testid="employee-overview-section-addresses"/);
  assert.match(viewSource, /data-testid="employee-overview-section-absences"/);
  assert.match(viewSource, /data-testid="employee-overview-section-notes"/);
  assert.match(viewSource, /data-testid="employee-overview-section-groups"/);
  assert.match(viewSource, /data-testid="employee-overview-section-documents"/);
  assert.match(
    viewSource,
    /data-testid="employee-overview-section-file"[\s\S]*data-testid="employee-overview-section-app-access"[\s\S]*data-testid="employee-overview-section-qualifications"[\s\S]*data-testid="employee-overview-section-credentials"[\s\S]*data-testid="employee-overview-section-availability"[\s\S]*data-testid="employee-overview-section-private-profile"[\s\S]*data-testid="employee-overview-section-addresses"[\s\S]*data-testid="employee-overview-section-absences"[\s\S]*data-testid="employee-overview-section-notes"[\s\S]*data-testid="employee-overview-section-groups"[\s\S]*data-testid="employee-overview-section-documents"/,
  );
  assert.match(viewSource, /async function selectEmployee\(employeeId: string, options: SelectEmployeeOptions = \{\}\)/);
  assert.match(viewSource, /preserveActiveTab = false/);
  assert.match(viewSource, /fallbackTab = "dashboard"/);
  assert.match(viewSource, /legacyEmployeeDetailTabIds\.has\(desiredTab\)[\s\S]*openEmployeeOverviewSection\(desiredTab\);/);
  assert.match(viewSource, /function openEmployeeOverviewSection\(sectionId: string\)[\s\S]*activeDetailTab\.value = "overview";[\s\S]*activeOverviewSection\.value = normalizeOverviewSectionId\(sectionId\);/);
  assert.match(viewSource, /const visibleEmployeeOverviewSections = computed\(\(\) => employeeOverviewSections\.value\.filter\(\(section\) => section\.visible\)\)/);
  assert.match(viewSource, /:aria-current="section\.id === activeOverviewSection \? 'true' : undefined"/);
  assert.match(viewSource, /testId: "employee-overview-nav-file"/);
  assert.match(viewSource, /testId: "employee-overview-nav-documents"/);
  assert.match(viewSource, /employeeAdmin\.overviewSections\.employeeFile/);
  assert.match(viewSource, /employeeAdmin\.overviewSections\.documents/);
  assert.match(viewSource, /resolveEmployeeDetailTab\(\s*desiredTab,[\s\S]*employeeDetailTabs\.value\.map\(\(tab\) => tab\.id\)/);
  assert.match(viewSource, /selectEmployee\(selectedEmployeeId\.value, \{ preserveActiveTab: true \}\)/);
});

test("employee overview moves heavy editor forms into accessible modals", () => {
  [
    "qualification",
    "qualification-proof",
    "credential",
    "availability",
    "absence",
    "note",
    "group-catalog",
    "group-assignment",
    "address",
    "document-upload",
    "document-link",
    "document-version",
  ].forEach((editorId) => {
    assert.match(viewSource, new RegExp(`data-testid="employee-overview-editor-${editorId}-modal"[\\s\\S]*role="dialog"`));
  });

  assert.match(viewSource, /type EmployeeOverviewEditorDialog =/);
  assert.match(viewSource, /const activeEmployeeOverviewEditor = ref<EmployeeOverviewEditorDialog>\(null\)/);
  assert.match(viewSource, /@click\.self="closeEmployeeOverviewEditor"/);
  assert.match(viewSource, /aria-modal="true"/);
  assert.match(viewSource, /function closeEmployeeOverviewEditor\(\)/);
  assert.doesNotMatch(viewSource, /employee-admin-inline-form/);
  assert.match(viewSource, /openNewQualificationEditor/);
  assert.match(viewSource, /openNewCredentialEditor/);
  assert.match(viewSource, /openNewAvailabilityEditor/);
  assert.match(viewSource, /openNewAddressEditor/);
  assert.match(viewSource, /openNewAbsenceEditor/);
  assert.match(viewSource, /openNewNoteEditor/);
  assert.match(viewSource, /openGroupAssignmentEditor/);
  assert.match(viewSource, /openEmployeeOverviewEditor\(['"]document_upload['"]\)/);
  assert.match(viewSource, /openEmployeeOverviewEditor\(['"]document_link['"]\)/);
  assert.match(viewSource, /openEmployeeOverviewEditor\(['"]document_version['"]\)/);
});

test("existing employee detail prepends dashboard while create mode remains overview only", () => {
  assert.match(viewSource, /const employeeDetailTabs = computed\(\(\) => \{[\s\S]*if \(isCreatingEmployee\.value\) \{[\s\S]*return \[\{ id: "overview", label: t\("employeeAdmin\.tabs\.overview"\) \}\];[\s\S]*return \[[\s\S]*\{ id: "dashboard", label: t\("employeeAdmin\.tabs\.dashboard"\) \},[\s\S]*\{ id: "overview", label: t\("employeeAdmin\.tabs\.overview"\) \},[\s\S]*\];/);
  assert.doesNotMatch(viewSource, /id: "profile_photo"/);
  assert.doesNotMatch(viewSource, /\{ id: "app_access", label: t\("employeeAdmin\.tabs\.appAccess"\) \}/);
  assert.doesNotMatch(viewSource, /\{ id: "qualifications", label: t\("employeeAdmin\.tabs\.qualifications"\) \}/);
  assert.doesNotMatch(viewSource, /\{ id: "credentials", label: t\("employeeAdmin\.tabs\.credentials"\) \}/);
  assert.doesNotMatch(viewSource, /\{ id: "availability", label: t\("employeeAdmin\.tabs\.availability"\) \}/);
  assert.doesNotMatch(viewSource, /\{ id: "private_profile", label: t\("employeeAdmin\.tabs\.privateProfile"\) \}/);
  assert.doesNotMatch(viewSource, /\{ id: "addresses", label: t\("employeeAdmin\.tabs\.addresses"\) \}/);
  assert.doesNotMatch(viewSource, /\{ id: "absences", label: t\("employeeAdmin\.tabs\.absences"\) \}/);
  assert.doesNotMatch(viewSource, /\{ id: "notes", label: t\("employeeAdmin\.tabs\.notes"\) \}/);
  assert.doesNotMatch(viewSource, /\{ id: "groups", label: t\("employeeAdmin\.tabs\.groups"\) \}/);
  assert.doesNotMatch(viewSource, /\{ id: "documents", label: t\("employeeAdmin\.tabs\.documents"\) \}/);
  assert.match(viewSource, /function startCreateEmployee\(\) \{[\s\S]*isCreatingEmployee\.value = true;[\s\S]*activeDetailTab\.value = "overview";/);
  assert.match(viewSource, /selectEmployeeFromSearchResult\(employeeId: string\)[\s\S]*selectEmployee\(employeeId, \{ fallbackTab: "dashboard" \}\);[\s\S]*activeDetailTab\.value = "dashboard";/);
  assert.match(viewSource, /selectEmployeeFromSuggestion\(employee: EmployeeListItem\)[\s\S]*selectEmployee\(employee\.id, \{ fallbackTab: "dashboard" \}\);[\s\S]*activeDetailTab\.value = "dashboard";/);
  assert.match(viewSource, /watch\(\s*\(\) => \[isCreatingEmployee\.value, !!selectedEmployee\.value, canReadPrivate\.value, activeDetailTab\.value\]/);
});

test("employee dashboard staffing data is permission-gated and uses the planning staffing board", () => {
  const componentPath = resolveWebAppPath("src/sicherplan-legacy/components/employees/EmployeeDashboardTab.vue");
  const helperPath = resolveWebAppPath("src/sicherplan-legacy/features/employees/employeeDashboard.helpers.ts");
  const componentSource = readFileSync(componentPath, "utf8");
  const helperSource = readFileSync(helperPath, "utf8");

  assert.match(viewSource, /hasPlanningStaffingPermission\(effectiveRole\.value, "planning\.staffing\.read"\)/);
  assert.match(viewSource, /:can-read-staffing="canReadStaffing"/);
  assert.match(componentSource, /import \{ listStaffingBoard, type StaffingBoardShiftItem \} from "@\/api\/planningStaffing";/);
  assert.match(componentSource, /filterShiftsForEmployee\(shifts, props\.employee\.id\)/);
  assert.match(helperSource, /export function filterShiftsForEmployee/);
  assert.match(helperSource, /shift\.assignments\.some\(\(assignment\) => assignment\.employee_id === employeeId\)/);
  assert.match(helperSource, /export function groupEmployeeProjectsFromShifts/);
  assert.match(helperSource, /export function mapEmployeeShiftsToCalendarCells/);
  assert.match(helperSource, /export function classifyEmployeeProject/);
  assert.match(componentSource, /v-if="!canReadStaffing"[\s\S]*employeeAdmin\.dashboard\.noStaffingAccess/);
  assert.match(componentSource, /<DashboardCalendarPanel[\s\S]*data-testid="employee-dashboard-calendar"/);
  assert.match(componentSource, /monthCache = new Map/);
  assert.match(componentSource, /requestVersion/);
});

test("employee dashboard owns profile photo entry point and the old photo tab is removed", () => {
  const componentPath = resolveWebAppPath("src/sicherplan-legacy/components/employees/EmployeeDashboardTab.vue");
  const componentSource = readFileSync(componentPath, "utf8");

  assert.match(viewSource, /:can-manage-photo="actionState\.canManagePhoto"/);
  assert.match(viewSource, /:photo-uploading="loading\.photo"/);
  assert.match(viewSource, /@photo-selected="submitDashboardPhoto"/);
  assert.match(viewSource, /async function submitPhotoFile\(file: File\)/);
  assert.match(componentSource, /data-testid="employee-dashboard-photo-button"/);
  assert.match(componentSource, /data-testid="employee-dashboard-photo-input"/);
  assert.match(componentSource, /data-testid="employee-dashboard-photo-uploading"/);
  assert.match(componentSource, /data-testid="employee-dashboard-photo-image"/);
  assert.match(componentSource, /data-testid="employee-dashboard-photo-placeholder"/);
  assert.match(componentSource, /accept="image\/\*"/);
  assert.doesNotMatch(componentSource, /employeeAdmin\.dashboard\.identityEyebrow/);
  assert.doesNotMatch(viewSource, /activeDetailTab === 'profile_photo'/);
  assert.doesNotMatch(viewSource, /employeeAdmin\.tabs\.profilePhoto/);
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

test("overview sections preserve the old tab business flows", () => {
  assert.match(viewSource, /employee-overview-section-private-profile[\s\S]*employeeAdmin\.privateProfile\.identityEyebrow/);
  assert.match(viewSource, /employee-overview-section-private-profile[\s\S]*employeeAdmin\.privateProfile\.contactEyebrow/);
  assert.match(viewSource, /employee-overview-section-private-profile[\s\S]*employeeAdmin\.privateProfile\.payrollEyebrow/);
  assert.match(viewSource, /employee-overview-section-private-profile[\s\S]*employeeAdmin\.privateProfile\.bankingEyebrow/);
  assert.match(viewSource, /employee-overview-section-private-profile[\s\S]*submitPrivateProfile/);
  assert.match(viewSource, /employee-overview-section-app-access[\s\S]*employeeAdmin\.access\.stateCreateEyebrow/);
  assert.match(viewSource, /employee-overview-section-app-access[\s\S]*employee-admin-advanced-access[\s\S]*employeeAdmin\.access\.attachEyebrow/);
  assert.match(viewSource, /employee-overview-section-qualifications[\s\S]*createEmployeeQualification/);
  assert.match(viewSource, /employee-overview-section-qualifications[\s\S]*uploadEmployeeQualificationProof/);
  assert.match(viewSource, /employee-overview-section-credentials[\s\S]*createEmployeeCredential/);
  assert.match(viewSource, /employee-overview-section-credentials[\s\S]*issueEmployeeCredentialBadgeOutput/);
  assert.match(viewSource, /employee-overview-section-availability[\s\S]*createEmployeeAvailabilityRule/);
  assert.match(viewSource, /employee-overview-section-availability[\s\S]*updateEmployeeAvailabilityRule/);
  assert.match(viewSource, /employee-overview-section-notes[\s\S]*employeeAdmin\.notes\.registerEyebrow[\s\S]*employeeAdmin\.notes\.editorEyebrow/);
  assert.match(viewSource, /employee-overview-section-groups[\s\S]*employeeAdmin\.groups\.catalogEyebrow[\s\S]*employeeAdmin\.groups\.assignEyebrow[\s\S]*employeeAdmin\.groups\.currentEyebrow/);
  assert.match(viewSource, /employee-overview-section-addresses[\s\S]*submitAddress/);
  assert.match(viewSource, /employee-overview-section-addresses[\s\S]*employeeAdmin\.actions\.markCurrentAddress/);
  assert.match(viewSource, /employee-overview-section-addresses[\s\S]*employeeAdmin\.actions\.closeAddressValidity/);
  assert.match(viewSource, /employee-overview-section-documents[\s\S]*uploadEmployeeDocument/);
  assert.match(viewSource, /employee-overview-section-documents[\s\S]*linkEmployeeDocument/);
  assert.match(viewSource, /employee-overview-section-documents[\s\S]*addEmployeeDocumentVersion/);
  assert.match(viewSource, /employee-overview-section-absences[\s\S]*createEmployeeAbsence/);
  assert.match(viewSource, /employee-overview-section-absences[\s\S]*updateEmployeeAbsence/);
  assert.match(viewSource, /selectedQualificationType = computed/);
  assert.match(viewSource, /validateEmployeeQualificationDraft\(qualificationDraft, selectedQualificationType\.value\)/);
  assert.match(viewSource, /EMPLOYEE_CREDENTIAL_TYPE_OPTIONS/);
  assert.match(viewSource, /EMPLOYEE_AVAILABILITY_RULE_KIND_OPTIONS/);
  assert.match(viewSource, /EMPLOYEE_DOCUMENT_TYPE_OPTIONS/);
  assert.doesNotMatch(viewSource, /employee-tab-panel-profile-photo/);
  assert.doesNotMatch(viewSource, /privateProfileDraft\.(religion|tax_class|health_insurer|child_allowance|driver_license)/);
  assert.doesNotMatch(viewSource, /addressDraft\.is_current/);
});

test("employee addresses overview section uses admin editor copy and removes released timeline wording", () => {
  assert.match(viewSource, /employee-overview-section-addresses[\s\S]*employeeAdmin\.addresses\.empty/);
  assert.match(viewSource, /employee-overview-section-addresses[\s\S]*employeeAdmin\.feedback\.addressSaved/);
  assert.match(viewSource, /employee-overview-section-addresses[\s\S]*employeeAddressTimeline/);
  assert.match(viewSource, /employee-overview-section-addresses[\s\S]*prepareAddressAsCurrent/);
  assert.match(viewSource, /employee-overview-section-addresses[\s\S]*prepareAddressValidityClose/);
  assert.match(viewSource, /employee-overview-section-addresses[\s\S]*isEmployeeAddressCurrent\(addressRow\)/);
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
