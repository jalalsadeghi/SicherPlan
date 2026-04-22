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

type IntersectionObserverMockInstance = {
  callback: IntersectionObserverCallback;
  disconnect: ReturnType<typeof vi.fn>;
  observe: ReturnType<typeof vi.fn>;
  observedElements: Element[];
  options?: IntersectionObserverInit;
};

function installIntersectionObserverMock() {
  const instances: IntersectionObserverMockInstance[] = [];
  const IntersectionObserverMock = vi.fn(function (
    this: IntersectionObserverMockInstance,
    callback: IntersectionObserverCallback,
    options?: IntersectionObserverInit,
  ) {
    this.callback = callback;
    this.options = options;
    this.observedElements = [];
    this.observe = vi.fn((element: Element) => {
      this.observedElements.push(element);
    });
    this.disconnect = vi.fn();
    instances.push(this);
  });

  Object.defineProperty(window, "IntersectionObserver", {
    configurable: true,
    value: IntersectionObserverMock,
  });

  function triggerIntersection(instance: IntersectionObserverMockInstance, target: Element, intersectionRatio = 1) {
    instance.callback(
      [
        {
          boundingClientRect: { top: 0 } as DOMRectReadOnly,
          intersectionRatio,
          isIntersecting: true,
          target,
        } as IntersectionObserverEntry,
      ],
      instance as unknown as IntersectionObserver,
    );
  }

  return { instances, triggerIntersection };
}

const mountedWrappers: VueWrapper[] = [];

async function mountEmployeeAdmin() {
  const wrapper = mount(EmployeeAdminView, {
    attachTo: document.body,
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

function detailTabLabels(wrapper: VueWrapper<any>) {
  return wrapper.get('[data-testid="employee-detail-tabs"]').findAll("button").map((tab) => tab.text().trim());
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
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
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

  it("shows only Dashboard and Overview as existing employee top-level tabs", async () => {
    const wrapper = await mountEmployeeAdmin();

    expect(detailTabLabels(wrapper)).toEqual(["Dashboard", "Overview"]);
    expect(wrapper.get('[data-testid="employee-tab-dashboard"]').classes()).toContain("active");
    expect(wrapper.find('[data-testid="employee-tab-app_access"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-tab-profile_photo"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-tab-qualifications"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-tab-credentials"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-tab-availability"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-tab-private_profile"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-tab-addresses"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-tab-absences"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-tab-notes"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-tab-groups"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-tab-documents"]').exists()).toBe(false);
  });

  it("keeps create employee mode limited to the usable Overview form", async () => {
    const wrapper = await mountEmployeeAdmin();

    await clickButtonByText(wrapper, "Create employee file");
    await settle();

    expect(detailTabLabels(wrapper)).toEqual(["Overview"]);
    expect(wrapper.find('[data-testid="employee-tab-dashboard"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="employee-tab-overview"]').classes()).toContain("active");
    expect(wrapper.get('[data-testid="employee-overview-section-file"]').text()).toContain("employeeAdmin.form.title");
    expect(wrapper.get('[data-testid="employee-overview-section-file"]').find('input[required]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-overview-section-nav"]').exists()).toBe(false);
  });

  it("renders Overview nav and section cards with private visibility controlled by permission", async () => {
    const wrapper = await mountEmployeeAdmin();
    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();

    expect(wrapper.find('[data-testid="employee-overview-onepage"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-overview-section-nav"]').exists()).toBe(true);
    const expectedNavOrder = [
      "file",
      "app_access",
      "qualifications",
      "credentials",
      "availability",
      "private_profile",
      "addresses",
      "absences",
      "notes",
      "groups",
      "documents",
    ];
    expectedNavOrder.forEach((sectionId) => {
      expect(wrapper.find(`[data-testid="employee-overview-nav-${sectionId}"]`).exists()).toBe(true);
    });
    const expectedSectionOrder = [
      "file",
      "app-access",
      "qualifications",
      "credentials",
      "availability",
      "private-profile",
      "addresses",
      "absences",
      "notes",
      "groups",
      "documents",
    ];
    expectedSectionOrder.forEach((sectionId) => {
      const section = wrapper.get(`[data-testid="employee-overview-section-${sectionId}"]`);
      expect(section.classes()).toContain("employee-admin-overview-section-card");
      expect(section.find("h4").exists()).toBe(true);
    });
    expect(
      wrapper
        .get(".employee-admin-overview-content")
        .findAll(".employee-admin-overview-section-card")
        .map((section) => section.attributes("data-testid")?.replace("employee-overview-section-", "")),
    ).toEqual(expectedSectionOrder);

    wrapper.unmount();
    mountedWrappers.pop();
    authStoreState.effectiveRole = "dispatcher";
    authStoreState.activeRole = "dispatcher";
    const dispatcherWrapper = await mountEmployeeAdmin();
    await dispatcherWrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();

    expect(dispatcherWrapper.find('[data-testid="employee-overview-nav-private_profile"]').exists()).toBe(false);
    expect(dispatcherWrapper.find('[data-testid="employee-overview-nav-addresses"]').exists()).toBe(false);
    expect(dispatcherWrapper.find('[data-testid="employee-overview-nav-absences"]').exists()).toBe(false);
    expect(dispatcherWrapper.find('[data-testid="employee-overview-section-private-profile"]').exists()).toBe(false);
    expect(dispatcherWrapper.find('[data-testid="employee-overview-section-addresses"]').exists()).toBe(false);
    expect(dispatcherWrapper.find('[data-testid="employee-overview-section-absences"]').exists()).toBe(false);
  });

  it("renders clean link-style Overview nav items with real decorative icons", async () => {
    const wrapper = await mountEmployeeAdmin();
    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();

    const overview = wrapper.get('[data-testid="employee-overview-onepage"]');
    const navShell = wrapper.get('[data-testid="employee-overview-section-nav"]');
    const contentColumn = wrapper.get(".employee-admin-overview-content");
    expect(navShell.element.parentElement).toBe(overview.element);
    expect(contentColumn.element.parentElement).toBe(overview.element);
    expect(navShell.element.nextElementSibling).toBe(contentColumn.element);
    expect(navShell.find(".employee-admin-overview-section-card").exists()).toBe(false);
    expect(contentColumn.findAll(".employee-admin-overview-section-card")).toHaveLength(11);

    expect(navShell.classes()).toContain("employee-admin-overview-nav-shell");
    expect(navShell.classes()).not.toContain("employee-admin-card");
    expect(navShell.classes()).not.toContain("employee-admin-tab");
    expect(navShell.classes()).not.toContain("employee-admin-meta__pill");

    const nav = navShell.get(".employee-admin-overview-nav");
    const navItems = nav.findAll(".employee-admin-overview-nav__link");
    expect(navItems).toHaveLength(11);
    navItems.forEach((navItem) => {
      expect(navItem.classes()).toContain("employee-admin-overview-nav__link");
      expect(navItem.classes()).not.toContain("employee-admin-tab");
      expect(navItem.classes()).not.toContain("employee-admin-meta__pill");
      expect(navItem.classes()).not.toContain("employee-admin-overview-nav__chip");

      const icon = navItem.find(".employee-admin-overview-nav__icon");
      expect(icon.exists()).toBe(true);
      expect(icon.attributes("aria-hidden")).toBe("true");
      expect(["ID", "KEY", "AWD"]).not.toContain(icon.text().trim());
      expect(navItem.element.firstElementChild).toBe(icon.element);
    });
  });

  it("keeps Overview active, marks the nav item, and scrolls when Documents is selected", async () => {
    const scrollIntoViewMock = vi.fn();
    vi.spyOn(HTMLElement.prototype, "scrollIntoView").mockImplementation(function (this: HTMLElement, options?: boolean | ScrollIntoViewOptions) {
      scrollIntoViewMock(this, options);
    });
    const wrapper = await mountEmployeeAdmin();

    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    const section = wrapper.get('[data-testid="employee-overview-section-documents"]');
    await wrapper.get('[data-testid="employee-overview-nav-documents"]').trigger("click");
    await settle();

    expect((wrapper.vm as any).activeDetailTab).toBe("overview");
    expect((wrapper.vm as any).activeOverviewSection).toBe("documents");
    expect(wrapper.get('[data-testid="employee-overview-nav-documents"]').attributes("aria-current")).toBe("true");
    expect(scrollIntoViewMock).toHaveBeenCalledWith(
      section.element,
      expect.objectContaining({ behavior: "smooth", block: "start" }),
    );
  });

  it("switches the Overview nav shell to fixed mode while the desktop Overview container is scrolled", async () => {
    vi.spyOn(window, "matchMedia").mockImplementation(
      (query: string) =>
        ({
          addEventListener: vi.fn(),
          addListener: vi.fn(),
          dispatchEvent: vi.fn(),
          matches: true,
          media: query,
          onchange: null,
          removeEventListener: vi.fn(),
          removeListener: vi.fn(),
        }) as MediaQueryList,
    );
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback: FrameRequestCallback) => {
      callback(0);
      return 1;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    vi.spyOn(HTMLElement.prototype, "offsetWidth", "get").mockReturnValue(220);
    vi.spyOn(HTMLElement.prototype, "offsetHeight", "get").mockReturnValue(320);
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
      if (this.classList.contains("employee-admin-overview-onepage")) {
        return {
          bottom: 1800,
          height: 1800,
          left: 120,
          right: 1120,
          top: 0,
          width: 1000,
          x: 120,
          y: 0,
          toJSON: () => ({}),
        } as DOMRect;
      }
      return {
        bottom: 320,
        height: 320,
        left: 120,
        right: 340,
        top: 0,
        width: 220,
        x: 120,
        y: 0,
        toJSON: () => ({}),
      } as DOMRect;
    });

    const wrapper = await mountEmployeeAdmin();
    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();

    const navShell = wrapper.get('[data-testid="employee-overview-section-nav"]');
    expect(navShell.classes()).toContain("employee-admin-overview-nav-shell--fixed");
    expect(navShell.attributes("style")).toContain("left: 120px");
    expect(navShell.attributes("style")).toContain("top: 129px");
    expect(navShell.attributes("style")).toContain("width: 220px");
  });

  it("updates the active Overview nav item from visible section position, not stale intersection ratio", async () => {
    const { instances, triggerIntersection } = installIntersectionObserverMock();
    const wrapper = await mountEmployeeAdmin();

    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();

    const observer = instances.at(-1);
    expect(observer).toBeDefined();

    const credentialsSection = wrapper.get('[data-testid="employee-overview-section-credentials"]').element as HTMLElement;
    const availabilitySection = wrapper.get('[data-testid="employee-overview-section-availability"]').element as HTMLElement;
    const sectionTops = { availability: 129, credentials: 420 };
    const mockRect = (top: number) =>
      ({
        bottom: top + 320,
        height: 320,
        left: 0,
        right: 800,
        top,
        width: 800,
        x: 0,
        y: top,
        toJSON: () => ({}),
      }) as DOMRect;
    vi.spyOn(credentialsSection, "getBoundingClientRect").mockImplementation(() => mockRect(sectionTops.credentials));
    vi.spyOn(availabilitySection, "getBoundingClientRect").mockImplementation(() => mockRect(sectionTops.availability));

    triggerIntersection(observer!, credentialsSection, 0.9);
    triggerIntersection(observer!, availabilitySection, 0.4);
    await settle();

    expect((wrapper.vm as any).activeOverviewSection).toBe("availability");
    expect(wrapper.get('[data-testid="employee-overview-nav-availability"]').attributes("aria-current")).toBe("true");
    expect(wrapper.get('[data-testid="employee-overview-nav-availability"]').classes()).toContain(
      "employee-admin-overview-nav__link--active",
    );
    expect(wrapper.get('[data-testid="employee-overview-nav-credentials"]').attributes("aria-current")).toBeUndefined();
    expect(wrapper.get('[data-testid="employee-overview-nav-credentials"]').classes()).not.toContain(
      "employee-admin-overview-nav__link--active",
    );

    const documentsSection = wrapper.get('[data-testid="employee-overview-section-documents"]').element as HTMLElement;
    vi.spyOn(documentsSection, "getBoundingClientRect").mockImplementation(() => mockRect(129));
    sectionTops.availability = -260;
    sectionTops.credentials = -620;
    triggerIntersection(observer!, documentsSection, 0.6);
    await settle();

    expect((wrapper.vm as any).activeOverviewSection).toBe("documents");
    expect(wrapper.get('[data-testid="employee-overview-nav-documents"]').attributes("aria-current")).toBe("true");
    expect(wrapper.get('[data-testid="employee-overview-nav-documents"]').classes()).toContain(
      "employee-admin-overview-nav__link--active",
    );
    expect(wrapper.get('[data-testid="employee-overview-nav-availability"]').attributes("aria-current")).toBeUndefined();
    expect(wrapper.get('[data-testid="employee-overview-nav-availability"]').classes()).not.toContain(
      "employee-admin-overview-nav__link--active",
    );
  });

  it("observes visible Overview sections, disconnects on unmount, and reinitializes when private visibility changes", async () => {
    const { instances } = installIntersectionObserverMock();
    const wrapper = await mountEmployeeAdmin();

    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();

    const tenantAdminObserver = instances.at(-1);
    expect(tenantAdminObserver).toBeDefined();
    expect(tenantAdminObserver!.observe).toHaveBeenCalledTimes(11);
    expect(tenantAdminObserver!.observedElements.map((element) => element.id)).toContain("employee-overview-section-addresses");

    authStoreState.effectiveRole = "dispatcher";
    authStoreState.activeRole = "dispatcher";
    await settle();

    const dispatcherObserver = instances.at(-1);
    expect(dispatcherObserver).toBeDefined();
    expect(dispatcherObserver).not.toBe(tenantAdminObserver);
    expect(tenantAdminObserver!.disconnect).toHaveBeenCalled();
    expect(dispatcherObserver!.observe).toHaveBeenCalledTimes(8);
    expect(dispatcherObserver!.observedElements.map((element) => element.id)).not.toContain("employee-overview-section-addresses");

    wrapper.unmount();
    mountedWrappers.pop();
    expect(dispatcherObserver!.disconnect).toHaveBeenCalled();
  });

  it("normalizes every former tab id to its Overview section without blank panels", async () => {
    const wrapper = await mountEmployeeAdmin();
    const legacyTabIds = [
      "app_access",
      "qualifications",
      "credentials",
      "availability",
      "private_profile",
      "addresses",
      "absences",
      "notes",
      "groups",
      "documents",
    ];

    for (const legacyTabId of legacyTabIds) {
      (wrapper.vm as any).activeDetailTab = legacyTabId;
      await settle();

      expect((wrapper.vm as any).activeDetailTab).toBe("overview");
      expect((wrapper.vm as any).activeOverviewSection).toBe(legacyTabId);
      expect(wrapper.find('[data-testid="employee-tab-panel-overview"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="employee-tab-panel-dashboard"]').exists()).toBe(false);
    }
  });

  it("keeps former tab functionality reachable inside Overview section cards", async () => {
    const wrapper = await mountEmployeeAdmin();
    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();

    expect(wrapper.get('[data-testid="employee-overview-section-file"]').find("form").exists()).toBe(true);
    expect(wrapper.get('[data-testid="employee-overview-section-app-access"]').findAll("input").length).toBeGreaterThan(0);
    expect(wrapper.get('[data-testid="employee-overview-section-qualifications"]').text()).toContain("employeeAdmin.actions.createQualification");
    expect(wrapper.get('[data-testid="employee-overview-section-credentials"]').text()).toContain("employeeAdmin.actions.createCredential");
    expect(wrapper.get('[data-testid="employee-overview-section-availability"]').text()).toContain("employeeAdmin.actions.createAvailability");
    expect(wrapper.get('[data-testid="employee-overview-section-private-profile"]').find("form").exists()).toBe(true);
    expect(wrapper.get('[data-testid="employee-overview-section-addresses"]').text()).toContain("employeeAdmin.actions.addAddress");
    expect(wrapper.get('[data-testid="employee-overview-section-absences"]').text()).toContain("employeeAdmin.actions.createAbsence");
    expect(wrapper.get('[data-testid="employee-overview-section-notes"]').text()).toContain("employeeAdmin.actions.createNote");
    expect(wrapper.get('[data-testid="employee-overview-section-groups"]').text()).toContain("employeeAdmin.groups.assignTitle");
    expect(wrapper.get('[data-testid="employee-overview-section-documents"]').text()).toContain("employeeAdmin.actions.uploadDocument");

    expect(wrapper.get('[data-testid="employee-overview-section-credentials"]').find("form").exists()).toBe(false);
    await clickButtonByText(wrapper, "employeeAdmin.actions.createCredential");
    await settle();
    expect(wrapper.get('[data-testid="employee-overview-editor-credential-modal"]').text()).toContain("employeeAdmin.credentials.editorTitle");
    expect(wrapper.get('[data-testid="employee-overview-editor-credential-modal"]').text()).toContain("employeeAdmin.credentials.encodedValueHelp");
  });

  it("does not render pure intro boxes or nested card styling inside the Overview page", async () => {
    const wrapper = await mountEmployeeAdmin();
    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();

    const overview = wrapper.get('[data-testid="employee-overview-onepage"]');
    expect(overview.find(".employee-admin-editor-intro").exists()).toBe(false);
    expect(overview.findAll(".employee-admin-overview-section-card")).toHaveLength(11);
    expect(overview.findAll(".employee-admin-overview-section-card__header").length).toBeGreaterThanOrEqual(11);
  });

  it("removes static explanatory lead copy while keeping functional Overview hints", async () => {
    const wrapper = await mountEmployeeAdmin();
    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();

    const overviewText = wrapper.get('[data-testid="employee-overview-onepage"]').text();
    [
      "employeeAdmin.form.lead",
      "employeeAdmin.form.accessLead",
      "employeeAdmin.access.lead",
      "employeeAdmin.access.stateCreateLead",
      "employeeAdmin.access.createLead",
      "employeeAdmin.access.stateLinkedLead",
      "employeeAdmin.access.manageLead",
      "employeeAdmin.access.resetLead",
      "employeeAdmin.access.detachLead",
      "employeeAdmin.access.advancedLead",
      "employeeAdmin.access.attachLead",
      "employeeAdmin.access.reconcileLead",
      "employeeAdmin.qualifications.lead",
      "employeeAdmin.credentials.lead",
      "employeeAdmin.availability.lead",
      "employeeAdmin.privateProfile.lead",
      "employeeAdmin.privateProfile.payrollLead",
      "employeeAdmin.privateProfile.notesLead",
      "employeeAdmin.addresses.lead",
      "employeeAdmin.absences.lead",
      "employeeAdmin.notes.lead",
      "employeeAdmin.groups.lead",
      "employeeAdmin.documents.lead",
      "employeeAdmin.documents.uploadLead",
      "employeeAdmin.documents.linkLead",
      "employeeAdmin.documents.versionLead",
    ].forEach((removedKey) => {
      expect(overviewText).not.toContain(removedKey);
    });
    expect(overviewText).toContain("employeeAdmin.access.createHint");
    await clickButtonByText(wrapper, "employeeAdmin.actions.uploadDocument");
    await settle();
    expect(wrapper.get('[data-testid="employee-overview-editor-document-upload-modal"]').text()).toContain("employeeAdmin.documents.documentTypeHelp");
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
    expect(wrapper.get('[data-testid="employee-overview-nav-documents"]').classes()).toContain("employee-admin-overview-nav__link--active");

    await wrapper.get('[data-testid="employee-list-tab-search"]').trigger("click");
    await clickButtonByText(wrapper, "Create employee file");
    await settle();
    expect(wrapper.get('[data-testid="employee-detail-workspace"]').text()).toContain("Create employee");
    expect(wrapper.find('[data-testid="employee-tab-dashboard"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="employee-tab-overview"]').classes()).toContain("active");
    expect(wrapper.find('[data-testid="employee-overview-section-nav"]').exists()).toBe(false);
  });
});
