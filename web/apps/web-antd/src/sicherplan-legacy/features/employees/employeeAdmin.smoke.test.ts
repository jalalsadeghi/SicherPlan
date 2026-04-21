// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { defineComponent, reactive } from "vue";

import EmployeeAdminView from "../../views/EmployeeAdminView.vue";

const routerPushMock = vi.fn();
const showFeedbackToastMock = vi.fn();

const authStoreState = reactive({
  accessToken: "token-1",
  activeRole: "tenant_admin",
  effectiveAccessToken: "token-1",
  effectiveRole: "tenant_admin",
  effectiveTenantScopeId: "tenant-1",
  tenantScopeId: "tenant-1",
  isSessionResolving: false,
  ensureSessionReady: vi.fn().mockResolvedValue(undefined),
  syncFromPrimarySession: vi.fn(),
  setTenantScopeId: vi.fn(),
});

const apiMocks = vi.hoisted(() => ({
  addEmployeeDocumentVersionMock: vi.fn(),
  attachEmployeeAccessUserMock: vi.fn(),
  createEmployeeAbsenceMock: vi.fn(),
  createEmployeeAccessUserMock: vi.fn(),
  createEmployeeAddressMock: vi.fn(),
  createEmployeeAvailabilityRuleMock: vi.fn(),
  createEmployeeCredentialMock: vi.fn(),
  createEmployeeGroupMock: vi.fn(),
  createEmployeeGroupMembershipMock: vi.fn(),
  createEmployeeMock: vi.fn(),
  createEmployeeNoteMock: vi.fn(),
  createEmployeeQualificationMock: vi.fn(),
  detachEmployeeAccessUserMock: vi.fn(),
  downloadEmployeeDocumentMock: vi.fn(),
  exportEmployeesMock: vi.fn(),
  getEmployeeAccessLinkMock: vi.fn(),
  getEmployeeMock: vi.fn(),
  getEmployeePhotoMock: vi.fn(),
  getEmployeePrivateProfileMock: vi.fn(),
  importEmployeesDryRunMock: vi.fn(),
  importEmployeesExecuteMock: vi.fn(),
  issueEmployeeCredentialBadgeOutputMock: vi.fn(),
  linkEmployeeDocumentMock: vi.fn(),
  listEmployeeAbsencesMock: vi.fn(),
  listEmployeeAddressesMock: vi.fn(),
  listEmployeeAvailabilityRulesMock: vi.fn(),
  listEmployeeCredentialsMock: vi.fn(),
  listEmployeeDocumentsMock: vi.fn(),
  listEmployeeGroupsMock: vi.fn(),
  listEmployeeNotesMock: vi.fn(),
  listEmployeePrivateProfileMaritalStatusOptionsMock: vi.fn(),
  listEmployeeQualificationProofsMock: vi.fn(),
  listEmployeeQualificationsMock: vi.fn(),
  listEmployeesMock: vi.fn(),
  listFunctionTypesMock: vi.fn(),
  listQualificationTypesMock: vi.fn(),
  reconcileEmployeeAccessUserMock: vi.fn(),
  resetEmployeeAccessUserPasswordMock: vi.fn(),
  updateEmployeeAccessUserMock: vi.fn(),
  updateEmployeeAddressMock: vi.fn(),
  updateEmployeeAvailabilityRuleMock: vi.fn(),
  updateEmployeeAbsenceMock: vi.fn(),
  updateEmployeeCredentialMock: vi.fn(),
  updateEmployeeGroupMock: vi.fn(),
  updateEmployeeGroupMembershipMock: vi.fn(),
  updateEmployeeMock: vi.fn(),
  updateEmployeeNoteMock: vi.fn(),
  updateEmployeePrivateProfileMock: vi.fn(),
  updateEmployeeQualificationMock: vi.fn(),
  uploadEmployeeDocumentMock: vi.fn(),
  uploadEmployeePhotoMock: vi.fn(),
  uploadEmployeeQualificationProofMock: vi.fn(),
  upsertEmployeePrivateProfileMock: vi.fn(),
}));

const coreAdminMocks = vi.hoisted(() => ({
  listBranchesMock: vi.fn(),
  listMandatesMock: vi.fn(),
}));

const planningStaffingMocks = vi.hoisted(() => ({
  listStaffingBoardMock: vi.fn(),
}));

const translations: Record<string, string> = {
  "employeeAdmin.actions.cancel": "Cancel",
  "employeeAdmin.actions.exportEmployees": "Export employees",
  "employeeAdmin.actions.importDryRun": "Dry run",
  "employeeAdmin.actions.importExecute": "Import execute",
  "employeeAdmin.actions.loadImportFile": "Load import file",
  "employeeAdmin.actions.newEmployee": "Create employee file",
  "employeeAdmin.actions.resetImportTemplate": "Reset template",
  "employeeAdmin.actions.search": "Search",
  "employeeAdmin.detail.emptyBody": "Use search to open an employee or create a new employee file.",
  "employeeAdmin.detail.emptyTitle": "No employee selected",
  "employeeAdmin.detail.eyebrow": "Employee detail",
  "employeeAdmin.detail.newTitle": "Create employee",
  "employeeAdmin.fields.defaultBranchId": "Default branch",
  "employeeAdmin.fields.defaultMandateId": "Default mandate",
  "employeeAdmin.filters.allStatuses": "All statuses",
  "employeeAdmin.filters.includeArchived": "Include archived",
  "employeeAdmin.filters.search": "Search",
  "employeeAdmin.filters.searchPlaceholder": "Personnel number or name",
  "employeeAdmin.filters.status": "Status",
  "employeeAdmin.import.continueOnError": "Continue on error",
  "employeeAdmin.import.csvLabel": "CSV",
  "employeeAdmin.import.eyebrow": "Import / Export",
  "employeeAdmin.import.exportSummary": "Export ready",
  "employeeAdmin.import.title": "Import and export",
  "employeeAdmin.list.eyebrow": "Employees",
  "employeeAdmin.list.title": "Employee list",
  "employeeAdmin.search.suggestionsEmpty": "No matching employees",
  "employeeAdmin.search.suggestionsLoading": "Searching employees...",
  "employeeAdmin.search.selectEmployee": "Select employee",
  "employeeAdmin.permission.missingBody": "No employee read permission.",
  "employeeAdmin.permission.missingTitle": "Permission missing",
  "employeeAdmin.permission.privateRead": "Private read",
  "employeeAdmin.permission.read": "Read",
  "employeeAdmin.permission.write": "Write",
  "employeeAdmin.scope.missingBody": "Choose a tenant scope.",
  "employeeAdmin.scope.missingTitle": "Tenant scope missing",
  "employeeAdmin.searchResults.empty": "No matching employees were found.",
  "employeeAdmin.searchResults.eyebrow": "Employee search",
  "employeeAdmin.searchResults.lead": "Select a matching employee.",
  "employeeAdmin.searchResults.loading": "Searching employees...",
  "employeeAdmin.searchResults.title": "Matching employees",
  "employeeAdmin.status.active": "Active",
  "employeeAdmin.status.archived": "Archived",
  "employeeAdmin.status.inactive": "Inactive",
  "employeeAdmin.summary.none": "None",
  "employeeAdmin.tabs.dashboard": "Dashboard",
  "employeeAdmin.tabs.absences": "Absences",
  "employeeAdmin.tabs.addresses": "Addresses",
  "employeeAdmin.tabs.appAccess": "App access",
  "employeeAdmin.tabs.availability": "Availability",
  "employeeAdmin.tabs.credentials": "Credentials",
  "employeeAdmin.tabs.documents": "Documents",
  "employeeAdmin.tabs.groups": "Groups",
  "employeeAdmin.tabs.notes": "Notes",
  "employeeAdmin.tabs.overview": "Overview",
  "employeeAdmin.tabs.privateProfile": "Private profile",
  "employeeAdmin.tabs.profilePhoto": "Profile photo",
  "employeeAdmin.tabs.qualifications": "Qualifications",
  "employeeAdmin.overviewSections.employeeFile": "Employee file",
  "employeeAdmin.overviewSections.appAccess": "App access",
  "employeeAdmin.overviewSections.qualifications": "Qualifications",
  "employeeAdmin.overviewSections.credentials": "Credentials",
  "employeeAdmin.overviewSections.availability": "Availability",
  "employeeAdmin.overviewSections.privateProfile": "Private profile",
  "employeeAdmin.overviewSections.addresses": "Addresses",
  "employeeAdmin.overviewSections.absences": "Absences",
  "employeeAdmin.overviewSections.notes": "Notes",
  "employeeAdmin.overviewSections.groups": "Groups",
  "employeeAdmin.overviewSections.documents": "Documents",
  "employeeAdmin.dashboard.identityEyebrow": "Employee dashboard",
  "employeeAdmin.dashboard.projectsEyebrow": "Assignment contexts",
  "employeeAdmin.dashboard.projectsTitle": "Past, current, and future projects",
  "employeeAdmin.dashboard.projectsEmpty": "No assignments found.",
  "employeeAdmin.dashboard.noStaffingAccess": "No staffing access.",
  "employeeAdmin.dashboard.loadError": "Dashboard data could not be loaded.",
  "employeeAdmin.dashboard.projectStatus.past": "Past",
  "employeeAdmin.dashboard.projectStatus.current": "Current",
  "employeeAdmin.dashboard.projectStatus.future": "Future",
  "employeeAdmin.dashboard.projectShiftCount": "shifts",
  "employeeAdmin.dashboard.calendarTitle": "Employee calendar",
  "employeeAdmin.dashboard.calendarDescription": "Only assigned shifts.",
  "employeeAdmin.dashboard.calendarMonthHint": "Month view",
  "employeeAdmin.dashboard.calendarPrevious": "Previous",
  "employeeAdmin.dashboard.calendarNext": "Next",
  "employeeAdmin.dashboard.calendarMore": "more",
  "employeeAdmin.dashboard.calendarOrderShort": "ord.",
  "employeeAdmin.dashboard.calendarShiftShort": "sh.",
  "employeeAdmin.dashboard.calendarSummary.shifts": "Shifts",
  "employeeAdmin.dashboard.calendarSummary.orders": "Orders",
  "employeeAdmin.dashboard.calendarSummary.projects": "Projects",
  "employeeAdmin.dashboard.photo.add": "Add photo",
  "employeeAdmin.dashboard.photo.change": "Change photo",
  "employeeAdmin.dashboard.photo.uploading": "Uploading photo...",
  "employeeAdmin.dashboard.photo.alt": "Employee photo",
  "employeeAdmin.title": "Employees",
  "workspace.loading.processing": "Processing",
  "workspace.loading.reconcilingSession": "Reconciling session",
};

vi.mock("@/i18n", () => ({
  useI18n: () => ({
    locale: { value: "en-US" },
    t: (key: string, params?: Record<string, unknown>) => {
      const value = translations[key] ?? key;
      if (!params) {
        return value;
      }
      return Object.entries(params).reduce(
        (message, [paramKey, paramValue]) => message.replace(`{${paramKey}}`, String(paramValue)),
        value,
      );
    },
  }),
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({
    push: routerPushMock,
  }),
}));

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => authStoreState,
}));

vi.mock("@/composables/useSicherPlanFeedback", () => ({
  useSicherPlanFeedback: () => ({
    showFeedbackToast: showFeedbackToastMock,
  }),
}));

vi.mock("@/api/coreAdmin", () => ({
  listBranches: coreAdminMocks.listBranchesMock,
  listMandates: coreAdminMocks.listMandatesMock,
}));

vi.mock("@/api/planningStaffing", () => ({
  listStaffingBoard: planningStaffingMocks.listStaffingBoardMock,
}));

vi.mock("@/api/employeeAdmin", () => {
  class EmployeeAdminApiError extends Error {
    messageKey: string;
    statusCode: number;

    constructor(messageKey: string, statusCode = 400) {
      super(messageKey);
      this.messageKey = messageKey;
      this.statusCode = statusCode;
    }
  }

  return {
    addEmployeeDocumentVersion: apiMocks.addEmployeeDocumentVersionMock,
    attachEmployeeAccessUser: apiMocks.attachEmployeeAccessUserMock,
    createEmployee: apiMocks.createEmployeeMock,
    createEmployeeAbsence: apiMocks.createEmployeeAbsenceMock,
    createEmployeeAccessUser: apiMocks.createEmployeeAccessUserMock,
    createEmployeeAddress: apiMocks.createEmployeeAddressMock,
    createEmployeeAvailabilityRule: apiMocks.createEmployeeAvailabilityRuleMock,
    createEmployeeCredential: apiMocks.createEmployeeCredentialMock,
    createEmployeeGroup: apiMocks.createEmployeeGroupMock,
    createEmployeeGroupMembership: apiMocks.createEmployeeGroupMembershipMock,
    createEmployeeNote: apiMocks.createEmployeeNoteMock,
    createEmployeeQualification: apiMocks.createEmployeeQualificationMock,
    detachEmployeeAccessUser: apiMocks.detachEmployeeAccessUserMock,
    downloadEmployeeDocument: apiMocks.downloadEmployeeDocumentMock,
    EmployeeAdminApiError,
    exportEmployees: apiMocks.exportEmployeesMock,
    getEmployee: apiMocks.getEmployeeMock,
    getEmployeeAccessLink: apiMocks.getEmployeeAccessLinkMock,
    getEmployeePhoto: apiMocks.getEmployeePhotoMock,
    getEmployeePrivateProfile: apiMocks.getEmployeePrivateProfileMock,
    importEmployeesDryRun: apiMocks.importEmployeesDryRunMock,
    importEmployeesExecute: apiMocks.importEmployeesExecuteMock,
    issueEmployeeCredentialBadgeOutput: apiMocks.issueEmployeeCredentialBadgeOutputMock,
    linkEmployeeDocument: apiMocks.linkEmployeeDocumentMock,
    listEmployeeAbsences: apiMocks.listEmployeeAbsencesMock,
    listEmployeeAddresses: apiMocks.listEmployeeAddressesMock,
    listEmployeeAvailabilityRules: apiMocks.listEmployeeAvailabilityRulesMock,
    listEmployeeCredentials: apiMocks.listEmployeeCredentialsMock,
    listEmployeeDocuments: apiMocks.listEmployeeDocumentsMock,
    listEmployeeGroups: apiMocks.listEmployeeGroupsMock,
    listEmployeeNotes: apiMocks.listEmployeeNotesMock,
    listEmployeePrivateProfileMaritalStatusOptions: apiMocks.listEmployeePrivateProfileMaritalStatusOptionsMock,
    listEmployeeQualificationProofs: apiMocks.listEmployeeQualificationProofsMock,
    listEmployeeQualifications: apiMocks.listEmployeeQualificationsMock,
    listEmployees: apiMocks.listEmployeesMock,
    listFunctionTypes: apiMocks.listFunctionTypesMock,
    listQualificationTypes: apiMocks.listQualificationTypesMock,
    reconcileEmployeeAccessUser: apiMocks.reconcileEmployeeAccessUserMock,
    resetEmployeeAccessUserPassword: apiMocks.resetEmployeeAccessUserPasswordMock,
    updateEmployee: apiMocks.updateEmployeeMock,
    updateEmployeeAccessUser: apiMocks.updateEmployeeAccessUserMock,
    updateEmployeeAddress: apiMocks.updateEmployeeAddressMock,
    updateEmployeeAvailabilityRule: apiMocks.updateEmployeeAvailabilityRuleMock,
    updateEmployeeAbsence: apiMocks.updateEmployeeAbsenceMock,
    updateEmployeeCredential: apiMocks.updateEmployeeCredentialMock,
    updateEmployeeGroup: apiMocks.updateEmployeeGroupMock,
    updateEmployeeGroupMembership: apiMocks.updateEmployeeGroupMembershipMock,
    updateEmployeeNote: apiMocks.updateEmployeeNoteMock,
    updateEmployeePrivateProfile: apiMocks.updateEmployeePrivateProfileMock,
    updateEmployeeQualification: apiMocks.updateEmployeeQualificationMock,
    uploadEmployeeDocument: apiMocks.uploadEmployeeDocumentMock,
    uploadEmployeePhoto: apiMocks.uploadEmployeePhotoMock,
    uploadEmployeeQualificationProof: apiMocks.uploadEmployeeQualificationProofMock,
    upsertEmployeePrivateProfile: apiMocks.upsertEmployeePrivateProfileMock,
  };
});

const SicherPlanLoadingOverlayStub = defineComponent({
  name: "SicherPlanLoadingOverlayStub",
  props: {
    busy: { type: Boolean, default: false },
    text: { type: String, default: "" },
  },
  template: `
    <div data-testid="employee-loading-overlay" :data-busy="busy ? 'true' : 'false'">
      <slot />
    </div>
  `,
});

const StatusBadgeStub = defineComponent({
  name: "StatusBadgeStub",
  props: {
    status: { type: String, default: "" },
  },
  template: '<span data-testid="status-badge">{{ status }}</span>',
});

function buildEmployeeListItem(id: string, personnelNo: string, firstName: string, lastName: string, overrides: Record<string, unknown> = {}) {
  return {
    id,
    tenant_id: "tenant-1",
    personnel_no: personnelNo,
    first_name: firstName,
    last_name: lastName,
    preferred_name: null,
    work_email: null,
    mobile_phone: null,
    default_branch_id: null,
    default_mandate_id: null,
    hire_date: "2026-04-01",
    termination_date: null,
    status: "active",
    created_at: "2026-04-01T08:00:00Z",
    updated_at: "2026-04-01T08:00:00Z",
    archived_at: null,
    version_no: 1,
    ...overrides,
  };
}

function buildEmployeeRead(id: string, personnelNo: string, firstName: string, lastName: string, overrides: Record<string, unknown> = {}) {
  return {
    ...buildEmployeeListItem(id, personnelNo, firstName, lastName),
    work_phone: null,
    employment_type_code: "full_time",
    target_weekly_hours: 40,
    target_monthly_hours: null,
    user_id: null,
    notes: null,
    group_memberships: [],
    ...overrides,
  };
}

const markus = buildEmployeeListItem("employee-markus", "P-2000", "Markus", "Neumann", {
  work_email: "markus.neumann@example.test",
});
const leon = buildEmployeeListItem("employee-leon", "P-2001", "Leon", "Yilmaz", {
  mobile_phone: "+49 170 2001",
  status: "inactive",
});

function buildStaffingBoardShift(
  id: string,
  employeeId: string,
  startsAt: string,
  endsAt: string,
  overrides: Record<string, unknown> = {},
) {
  return {
    id,
    tenant_id: "tenant-1",
    planning_record_id: `planning-${id}`,
    shift_plan_id: `shift-plan-${id}`,
    order_id: `order-${id}`,
    order_no: `ORD-${id}`,
    planning_record_name: `Planning ${id}`,
    planning_mode_code: "site",
    workforce_scope_code: "internal",
    starts_at: startsAt,
    ends_at: endsAt,
    shift_type_code: "regular",
    release_state: "released",
    status: "active",
    location_text: null,
    meeting_point: null,
    demand_groups: [],
    assignments: [
      {
        id: `assignment-${id}`,
        shift_id: id,
        demand_group_id: `demand-${id}`,
        team_id: null,
        employee_id: employeeId,
        subcontractor_worker_id: null,
        assignment_status_code: "assigned",
        assignment_source_code: "manual",
        confirmed_at: null,
        version_no: 1,
      },
    ],
    ...overrides,
  };
}

function dateTimeForCurrentMonth(dayOffset: number, hour: number) {
  const value = new Date();
  value.setDate(value.getDate() + dayOffset);
  value.setHours(hour, 0, 0, 0);
  return value.toISOString();
}

function createListEmployeesImplementation() {
  return vi.fn(async (_tenantId: string, _accessToken: string, params: Record<string, unknown>) => {
    const search = `${params.search ?? ""}`.trim().toLowerCase();
    const status = `${params.status ?? ""}`.trim();
    if (search === "markus") {
      return [markus];
    }
    if (search === "none") {
      return [];
    }
    let results = [markus, leon];
    if (status) {
      results = results.filter((employee) => employee.status === status);
    }
    if (search) {
      results = results.filter((employee) =>
        [
          employee.personnel_no,
          employee.first_name,
          employee.last_name,
          employee.preferred_name,
          employee.work_email,
          employee.mobile_phone,
        ].filter(Boolean).join(" ").toLowerCase().includes(search),
      );
    }
    return results;
  });
}

async function settle() {
  await flushPromises();
  await flushPromises();
}

function createDeferred<T = void>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, reject, resolve };
}

async function waitForEmployeeSearchDebounce() {
  await new Promise((resolve) => setTimeout(resolve, 350));
  await settle();
}

async function clickButtonByText(wrapper: VueWrapper<any>, label: string) {
  const button = wrapper
    .findAll("button")
    .find((candidate) => candidate.text().trim() === label);
  if (!button) {
    throw new Error(`Button not found: ${label}`);
  }
  await button.trigger("click");
}

async function clickButtonByTextWithin(wrapper: any, label: string) {
  const button = wrapper
    .findAll("button")
    .find((candidate) => candidate.text().trim() === label);
  if (!button) {
    throw new Error(`Button not found in wrapper: ${label}`);
  }
  await button.trigger("click");
}

const mountedWrappers: VueWrapper[] = [];

async function mountEmployeeAdmin() {
  const wrapper = mount(EmployeeAdminView, {
    global: {
      stubs: {
        RouterLink: defineComponent({
          name: "RouterLinkStub",
          template: "<a><slot /></a>",
        }),
        SicherPlanLoadingOverlay: SicherPlanLoadingOverlayStub,
        StatusBadge: StatusBadgeStub,
      },
    },
  });
  mountedWrappers.push(wrapper);
  await settle();
  return wrapper;
}

describe("EmployeeAdminView search dialog regression", () => {
  beforeEach(() => {
    authStoreState.accessToken = "token-1";
    authStoreState.activeRole = "tenant_admin";
    authStoreState.effectiveAccessToken = "token-1";
    authStoreState.effectiveRole = "tenant_admin";
    authStoreState.effectiveTenantScopeId = "tenant-1";
    authStoreState.tenantScopeId = "tenant-1";
    authStoreState.isSessionResolving = false;
    authStoreState.ensureSessionReady.mockClear();
    authStoreState.ensureSessionReady.mockResolvedValue(undefined);
    authStoreState.syncFromPrimarySession.mockClear();
    authStoreState.setTenantScopeId.mockClear();

    routerPushMock.mockReset();
    showFeedbackToastMock.mockReset();

    Object.values(apiMocks).forEach((mock) => mock.mockReset());
    Object.values(coreAdminMocks).forEach((mock) => mock.mockReset());
    Object.values(planningStaffingMocks).forEach((mock) => mock.mockReset());

    coreAdminMocks.listBranchesMock.mockResolvedValue([
      { id: "branch-1", tenant_id: "tenant-1", code: "BR-1", name: "Berlin", status: "active", archived_at: null },
    ]);
    coreAdminMocks.listMandatesMock.mockResolvedValue([
      {
        id: "mandate-1",
        tenant_id: "tenant-1",
        branch_id: "branch-1",
        code: "MAN-1",
        name: "Berlin Mitte",
        status: "active",
        archived_at: null,
      },
    ]);

    apiMocks.listEmployeesMock.mockImplementation(createListEmployeesImplementation());
    apiMocks.getEmployeeMock.mockImplementation(async (_tenantId: string, employeeId: string) => {
      if (employeeId === "employee-leon") {
        return buildEmployeeRead("employee-leon", "P-2001", "Leon", "Yilmaz", {
          mobile_phone: "+49 170 2001",
          status: "inactive",
        });
      }
      return buildEmployeeRead("employee-markus", "P-2000", "Markus", "Neumann", {
        work_email: "markus.neumann@example.test",
      });
    });
    apiMocks.getEmployeeAccessLinkMock.mockResolvedValue(null);
    apiMocks.getEmployeePhotoMock.mockResolvedValue(null);
    apiMocks.getEmployeePrivateProfileMock.mockResolvedValue(null);
    apiMocks.listEmployeeAbsencesMock.mockResolvedValue([]);
    apiMocks.listEmployeeAddressesMock.mockResolvedValue([]);
    apiMocks.listEmployeeAvailabilityRulesMock.mockResolvedValue([]);
    apiMocks.listEmployeeCredentialsMock.mockResolvedValue([]);
    apiMocks.listEmployeeDocumentsMock.mockResolvedValue([]);
    apiMocks.listEmployeeGroupsMock.mockResolvedValue([]);
    apiMocks.listEmployeeNotesMock.mockResolvedValue([]);
    apiMocks.listEmployeePrivateProfileMaritalStatusOptionsMock.mockResolvedValue([]);
    apiMocks.listEmployeeQualificationProofsMock.mockResolvedValue([]);
    apiMocks.listEmployeeQualificationsMock.mockResolvedValue([]);
    apiMocks.listFunctionTypesMock.mockResolvedValue([]);
    apiMocks.listQualificationTypesMock.mockResolvedValue([]);
    apiMocks.exportEmployeesMock.mockResolvedValue({
      row_count: 2,
      document_id: "document-export-1",
    });
    planningStaffingMocks.listStaffingBoardMock.mockResolvedValue([]);
  });

  afterEach(() => {
    while (mountedWrappers.length) {
      mountedWrappers.pop()?.unmount();
    }
  });

  it("renders a single-column full-width tools panel before the detail workspace", async () => {
    const wrapper = await mountEmployeeAdmin();

    const layout = wrapper.get('[data-testid="employee-master-detail-layout"]');
    const listSection = wrapper.get('[data-testid="employee-list-section"]');
    const detailWorkspace = wrapper.get('[data-testid="employee-detail-workspace"]');
    expect(wrapper.find(".employee-admin-hero").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("MODULE CONTROL");
    expect(layout.classes()).toContain("employee-admin-grid");
    expect(wrapper.html().indexOf('data-testid="employee-list-section"')).toBeLessThan(
      wrapper.html().indexOf('data-testid="employee-detail-workspace"'),
    );
    expect(wrapper.find(".employee-admin-row").exists()).toBe(false);
    expect(listSection.classes()).toContain("employee-admin-list-panel");
    expect(detailWorkspace.classes()).toContain("employee-admin-detail");

    const searchPanel = wrapper.get('[data-testid="employee-list-tab-panel-search"]');
    expect(wrapper.get('[data-testid="employee-list-tab-search"]').text()).toBe("Search");
    expect(wrapper.get('[data-testid="employee-list-tab-import-export"]').text()).toBe("Import / Export");
    expect(searchPanel.find('[data-testid="employee-search-select"]').exists()).toBe(true);
    expect(searchPanel.findAll("select")).toHaveLength(3);
    expect(searchPanel.find('input[type="checkbox"]').exists()).toBe(true);
    expect(searchPanel.text()).toContain("Status");
    expect(searchPanel.text()).toContain("Default branch");
    expect(searchPanel.text()).toContain("Default mandate");
    expect(searchPanel.text()).toContain("Include archived");
    expect(searchPanel.text()).toContain("Create employee file");

    await wrapper.get('[data-testid="employee-list-tab-import-export"]').trigger("click");
    const importExportPanel = wrapper.get('[data-testid="employee-list-tab-panel-import-export"]');
    expect(importExportPanel.find('input[type="file"]').exists()).toBe(true);
    expect(importExportPanel.find("textarea").exists()).toBe(true);
    expect(importExportPanel.text()).toContain("Load import file");
    expect(importExportPanel.text()).toContain("Dry run");
    expect(importExportPanel.text()).toContain("Import execute");
    expect(importExportPanel.text()).toContain("Export employees");
  });

  it("opens search results only in the dialog and passes the SearchSelect query", async () => {
    const wrapper = await mountEmployeeAdmin();
    apiMocks.listEmployeesMock.mockClear();

    const searchPanel = wrapper.get('[data-testid="employee-list-tab-panel-search"]');
    await searchPanel.get('[data-testid="employee-search-select"] input').setValue("Markus");
    await clickButtonByTextWithin(searchPanel, "Search");
    await settle();

    expect(apiMocks.listEmployeesMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({ search: "Markus" }),
    );
    expect(wrapper.find('[data-testid="employee-search-results-modal"]').exists()).toBe(true);
    expect(wrapper.findAll('[data-testid="employee-search-result-row"]')).toHaveLength(1);
    expect(wrapper.find(".employee-admin-row").exists()).toBe(false);

    const resultRow = wrapper.get('[data-testid="employee-search-result-row"]');
    expect(resultRow.text()).toContain("P-2000");
    expect(resultRow.text()).toContain("Markus Neumann");
    expect(resultRow.text()).toContain("markus.neumann@example.test");
    expect(resultRow.text()).toContain("active");
  });

  it("shows live search suggestions while typing and selects an employee without opening the modal", async () => {
    const wrapper = await mountEmployeeAdmin();
    apiMocks.listEmployeesMock.mockClear();
    apiMocks.getEmployeeMock.mockClear();

    const searchPanel = wrapper.get('[data-testid="employee-list-tab-panel-search"]');
    await searchPanel.get('[data-testid="employee-search-select-input"]').setValue("m");
    await waitForEmployeeSearchDebounce();

    expect(apiMocks.listEmployeesMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({ search: "m" }),
    );
    expect(wrapper.find('[data-testid="employee-search-suggestions"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="employee-search-suggestions"]').text()).toContain("Markus Neumann");

    await searchPanel.get('[data-testid="employee-search-select-input"]').setValue("mark");
    await waitForEmployeeSearchDebounce();
    const suggestion = wrapper.get('[data-testid="employee-search-suggestion-row"]');
    expect(suggestion.text()).toContain("P-2000");
    expect(suggestion.text()).toContain("Markus Neumann");
    expect(suggestion.text()).toContain("markus.neumann@example.test");
    expect(suggestion.text()).toContain("active");
    expect(wrapper.get('[data-testid="employee-search-suggestions"]').text()).not.toContain("Leon Yilmaz");

    await suggestion.trigger("click");
    await settle();

    expect(wrapper.find('[data-testid="employee-search-suggestions"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-search-results-modal"]').exists()).toBe(false);
    expect((searchPanel.get('[data-testid="employee-search-select-input"]').element as HTMLInputElement).value).toBe(
      "P-2000 · Markus Neumann",
    );
    expect(apiMocks.getEmployeeMock).toHaveBeenCalledWith("tenant-1", "employee-markus", "token-1");
    expect(wrapper.get('[data-testid="employee-detail-workspace"]').text()).toContain("Markus Neumann");
    expect(wrapper.get('[data-testid="employee-tab-dashboard"]').classes()).toContain("active");
  });

  it("matches employee suggestions by personnel number and work email fragments", async () => {
    const wrapper = await mountEmployeeAdmin();
    const searchPanel = wrapper.get('[data-testid="employee-list-tab-panel-search"]');

    await searchPanel.get('[data-testid="employee-search-select-input"]').setValue("P-2001");
    await waitForEmployeeSearchDebounce();
    expect(wrapper.get('[data-testid="employee-search-suggestions"]').text()).toContain("Leon Yilmaz");
    expect(wrapper.get('[data-testid="employee-search-suggestions"]').text()).not.toContain("Markus Neumann");

    await searchPanel.get('[data-testid="employee-search-select-input"]').setValue("example.test");
    await waitForEmployeeSearchDebounce();
    expect(wrapper.get('[data-testid="employee-search-suggestions"]').text()).toContain("Markus Neumann");
    expect(wrapper.get('[data-testid="employee-search-suggestions"]').text()).not.toContain("Leon Yilmaz");
  });

  it("shows a compact empty suggestion state while keeping Search modal behavior separate", async () => {
    const wrapper = await mountEmployeeAdmin();

    const searchPanel = wrapper.get('[data-testid="employee-list-tab-panel-search"]');
    await searchPanel.get('[data-testid="employee-search-select-input"]').setValue("none");
    await waitForEmployeeSearchDebounce();

    expect(wrapper.find('[data-testid="employee-search-suggestions"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-search-suggestion-empty"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-search-suggestion-empty"]').text()).toContain("No matching employees");
    expect(wrapper.find('[data-testid="employee-search-results-modal"]').exists()).toBe(false);

    await clickButtonByTextWithin(searchPanel, "Search");
    await settle();
    expect(wrapper.find('[data-testid="employee-search-results-modal"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-search-result-empty"]').exists()).toBe(true);
  });

  it("sends include-archived, status, branch, and mandate filters to employee search", async () => {
    const wrapper = await mountEmployeeAdmin();

    const searchPanel = wrapper.get('[data-testid="employee-list-tab-panel-search"]');
    const selects = searchPanel.findAll("select");
    const [statusSelect, branchSelect, mandateSelect] = selects;
    expect(statusSelect).toBeDefined();
    expect(branchSelect).toBeDefined();
    expect(mandateSelect).toBeDefined();
    await statusSelect!.setValue("active");
    await branchSelect!.setValue("branch-1");
    await settle();
    await mandateSelect!.setValue("mandate-1");
    await searchPanel.get('input[type="checkbox"]').setValue(true);
    apiMocks.listEmployeesMock.mockClear();
    await searchPanel.get('[data-testid="employee-search-select-input"]').setValue("m");
    await waitForEmployeeSearchDebounce();

    expect(apiMocks.listEmployeesMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        default_branch_id: "branch-1",
        default_mandate_id: "mandate-1",
        include_archived: true,
        search: "m",
        status: "active",
      }),
    );
    expect(wrapper.get('[data-testid="employee-search-suggestions"]').text()).toContain("Markus Neumann");
    expect(wrapper.get('[data-testid="employee-search-suggestions"]').text()).not.toContain("Leon Yilmaz");
  });

  it("selects a search result, closes the modal, and loads the dashboard detail", async () => {
    const wrapper = await mountEmployeeAdmin();
    apiMocks.getEmployeeMock.mockClear();

    const searchPanel = wrapper.get('[data-testid="employee-list-tab-panel-search"]');
    await searchPanel.get('[data-testid="employee-search-select"] input').setValue("Markus");
    await clickButtonByTextWithin(searchPanel, "Search");
    await settle();
    await wrapper.get('[data-testid="employee-search-result-row"]').trigger("click");
    await settle();

    expect(wrapper.find('[data-testid="employee-search-results-modal"]').exists()).toBe(false);
    expect(apiMocks.getEmployeeMock).toHaveBeenCalledWith("tenant-1", "employee-markus", "token-1");
    expect(wrapper.get('[data-testid="employee-detail-workspace"]').text()).toContain("Markus Neumann");
    expect(wrapper.get('[data-testid="employee-tab-dashboard"]').classes()).toContain("active");
  });

  it("renders dashboard projects and calendar from shifts assigned to the selected employee only", async () => {
    planningStaffingMocks.listStaffingBoardMock.mockResolvedValue([
      buildStaffingBoardShift(
        "markus-current",
        "employee-markus",
        dateTimeForCurrentMonth(-1, 8),
        dateTimeForCurrentMonth(1, 16),
        {
          order_no: "ORD-100",
          planning_record_name: "City Center Patrol",
        },
      ),
      buildStaffingBoardShift(
        "leon-current",
        "employee-leon",
        dateTimeForCurrentMonth(0, 9),
        dateTimeForCurrentMonth(0, 17),
        {
          order_no: "ORD-200",
          planning_record_name: "Unrelated Site",
        },
      ),
    ]);

    const wrapper = await mountEmployeeAdmin();
    await settle();

    const projects = wrapper.get('[data-testid="employee-dashboard-projects"]');
    expect(projects.text()).toContain("City Center Patrol");
    expect(projects.text()).toContain("ORD-100");
    expect(projects.text()).not.toContain("Unrelated Site");
    expect(projects.text()).not.toContain("ORD-200");

    const calendar = wrapper.get('[data-testid="employee-dashboard-calendar"]');
    expect(calendar.text()).toContain("ORD-100");
    expect(calendar.text()).not.toContain("ORD-200");
    expect(planningStaffingMocks.listStaffingBoardMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        date_from: expect.any(String),
        date_to: expect.any(String),
      }),
    );
  });

  it("uploads a dashboard photo from the clickable avatar and keeps profile photo out of the tabs", async () => {
    const wrapper = await mountEmployeeAdmin();
    await settle();

    expect(wrapper.find('[data-testid="employee-tab-profile_photo"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-tab-panel-profile-photo"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="employee-dashboard-hero"]').text()).not.toContain("Employee dashboard");

    const photoButton = wrapper.get('[data-testid="employee-dashboard-photo-button"]');
    expect(photoButton.attributes("aria-label")).toBe("Add photo");
    expect(photoButton.attributes("disabled")).toBeUndefined();
    const photoInput = wrapper.get('[data-testid="employee-dashboard-photo-input"]');
    expect(photoInput.attributes("accept")).toBe("image/*");
    expect(wrapper.find('[data-testid="employee-dashboard-photo-placeholder"]').exists()).toBe(true);
    const inputClickSpy = vi.spyOn(photoInput.element as HTMLInputElement, "click");
    await photoButton.trigger("click");
    expect(inputClickSpy).toHaveBeenCalled();

    const photoFile = new File(["photo-bytes"], "markus.png", { type: "image/png" });
    await (wrapper.vm as any).submitDashboardPhoto(photoFile);
    await settle();

    expect(apiMocks.uploadEmployeePhotoMock).toHaveBeenCalledWith(
      "tenant-1",
      "employee-markus",
      "token-1",
      expect.objectContaining({
        content_type: "image/png",
        file_name: "markus.png",
        title: "markus.png",
      }),
    );
    expect(apiMocks.uploadEmployeePhotoMock.mock.calls[0]?.[3].content_base64).toBeTruthy();
    expect(showFeedbackToastMock).toHaveBeenCalledWith(expect.objectContaining({ tone: "success" }));
  });

  it("keeps dashboard photo upload loading local while the upload is pending", async () => {
    const upload = createDeferred();
    apiMocks.uploadEmployeePhotoMock.mockReturnValue(upload.promise);

    const wrapper = await mountEmployeeAdmin();
    await settle();

    const uploadPromise = (wrapper.vm as any).submitDashboardPhoto(
      new File(["photo-bytes"], "pending.png", { type: "image/png" }),
    );
    await settle();

    expect(wrapper.find('[data-testid="employee-dashboard-photo-uploading"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-tab-panel-dashboard"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="employee-loading-overlay"]').attributes("data-busy")).toBe("false");

    upload.resolve();
    await uploadPromise;
    await settle();

    expect(wrapper.find('[data-testid="employee-dashboard-photo-uploading"]').exists()).toBe(false);
  });

  it("shows an empty dialog state without stale result rows", async () => {
    const wrapper = await mountEmployeeAdmin();

    const searchPanel = wrapper.get('[data-testid="employee-list-tab-panel-search"]');
    await searchPanel.get('[data-testid="employee-search-select"] input').setValue("Markus");
    await clickButtonByTextWithin(searchPanel, "Search");
    await settle();
    expect(wrapper.findAll('[data-testid="employee-search-result-row"]')).toHaveLength(1);

    await wrapper.get('[data-testid="employee-search-result-close"]').trigger("click");
    await searchPanel.get('[data-testid="employee-search-select"] input').setValue("none");
    await clickButtonByTextWithin(searchPanel, "Search");
    await settle();

    expect(wrapper.find('[data-testid="employee-search-results-modal"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-search-result-empty"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-search-result-empty"]').text()).toContain("No matching employees");
    expect(wrapper.findAll('[data-testid="employee-search-result-row"]')).toHaveLength(0);
  });

  it("does not fetch search results without a token or read permission", async () => {
    authStoreState.accessToken = "";
    authStoreState.effectiveAccessToken = "";
    const missingTokenWrapper = await mountEmployeeAdmin();
    apiMocks.listEmployeesMock.mockClear();

    await missingTokenWrapper.get('[data-testid="employee-search-select-input"]').setValue("mark");
    await waitForEmployeeSearchDebounce();
    expect(apiMocks.listEmployeesMock).not.toHaveBeenCalled();
    expect(missingTokenWrapper.find('[data-testid="employee-search-suggestions"]').exists()).toBe(false);

    await clickButtonByTextWithin(missingTokenWrapper.get('[data-testid="employee-list-tab-panel-search"]'), "Search");
    await settle();
    expect(apiMocks.listEmployeesMock).not.toHaveBeenCalled();
    expect(missingTokenWrapper.find('[data-testid="employee-search-results-modal"]').exists()).toBe(false);

    missingTokenWrapper.unmount();
    mountedWrappers.pop();
    authStoreState.accessToken = "token-1";
    authStoreState.effectiveAccessToken = "token-1";
    authStoreState.effectiveRole = "employee_user";

    const noPermissionWrapper = await mountEmployeeAdmin();
    expect(noPermissionWrapper.text()).toContain("No employee read permission.");
    expect(noPermissionWrapper.find('[data-testid="employee-list-section"]').exists()).toBe(false);
    expect(apiMocks.listEmployeesMock).not.toHaveBeenCalled();
  });

  it("preserves initial load, create flow, import/export, and detail tab switching", async () => {
    const wrapper = await mountEmployeeAdmin();

    expect(apiMocks.listEmployeesMock).toHaveBeenCalledWith("tenant-1", "token-1", expect.any(Object));
    expect(apiMocks.getEmployeeMock).toHaveBeenCalledWith("tenant-1", "employee-markus", "token-1");
    expect(wrapper.get('[data-testid="employee-detail-workspace"]').text()).toContain("Markus Neumann");
    expect(wrapper.get('[data-testid="employee-detail-tabs"]').text()).toMatch(/Dashboard[\s\S]*Overview/);
    expect(wrapper.get('[data-testid="employee-detail-tabs"]').text()).not.toContain("Profile photo");
    expect(wrapper.get('[data-testid="employee-detail-tabs"]').text()).not.toContain("Documents");
    expect(wrapper.get('[data-testid="employee-detail-tabs"]').text()).not.toContain("Qualifications");
    expect(wrapper.get('[data-testid="employee-tab-dashboard"]').classes()).toContain("active");
    expect(wrapper.get('[data-testid="employee-dashboard-hero"]').text()).toContain("Markus Neumann");
    expect(wrapper.find('[data-testid="employee-dashboard-calendar"]').exists()).toBe(true);

    await wrapper.get('[data-testid="employee-list-tab-import-export"]').trigger("click");
    await clickButtonByText(wrapper, "Export employees");
    await settle();
    expect(apiMocks.exportEmployeesMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        include_archived: false,
        tenant_id: "tenant-1",
      }),
    );

    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();
    expect(wrapper.get('[data-testid="employee-tab-overview"]').classes()).toContain("active");
    expect(wrapper.find('[data-testid="employee-overview-section-nav"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-overview-section-app-access"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-overview-section-documents"]').exists()).toBe(true);
    await wrapper.get('[data-testid="employee-overview-nav-documents"]').trigger("click");
    await settle();
    expect(wrapper.get('[data-testid="employee-overview-nav-documents"]').classes()).toContain("active");

    await wrapper.get('[data-testid="employee-list-tab-search"]').trigger("click");
    await clickButtonByText(wrapper, "Create employee file");
    await settle();
    expect(wrapper.get('[data-testid="employee-detail-workspace"]').text()).toContain("Create employee");
    expect(wrapper.find('[data-testid="employee-tab-dashboard"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="employee-tab-overview"]').classes()).toContain("active");
    expect(wrapper.find('[data-testid="employee-overview-section-nav"]').exists()).toBe(false);
  });
});
