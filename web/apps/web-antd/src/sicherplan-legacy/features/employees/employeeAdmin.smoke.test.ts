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
  "employeeAdmin.actions.advancedFilters": "Advanced filters",
  "employeeAdmin.actions.backToEmployeeList": "Back to employee list",
  "employeeAdmin.actions.cancel": "Cancel",
  "employeeAdmin.actions.closeFilters": "Close filters",
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
  "employeeAdmin.filters.additionalTitle": "Additional filters",
  "employeeAdmin.filters.includeArchived": "Include archived",
  "employeeAdmin.filters.search": "Search",
  "employeeAdmin.filters.searchEmployees": "Search employees",
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

function stubEmployeePhotoObjectUrls(urlByBlob = "blob:employee-photo") {
  const createObjectURLMock = vi.fn(() => urlByBlob);
  const revokeObjectURLMock = vi.fn();
  const NativeUrl = globalThis.URL;
  class UrlWithObjectUrls extends NativeUrl {
    static createObjectURL = createObjectURLMock;
    static revokeObjectURL = revokeObjectURLMock;
  }
  vi.stubGlobal("URL", UrlWithObjectUrls as unknown as typeof URL);
  return { createObjectURLMock, revokeObjectURLMock };
}

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

async function openFirstEmployeeWorkspace(wrapper: VueWrapper<any>) {
  await wrapper.get('[data-testid="employee-list-row"]').trigger("click");
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

  it("renders a customer-style employee list card with header actions and a simple live-search toolbar", async () => {
    const wrapper = await mountEmployeeAdmin();

    const layout = wrapper.get('[data-testid="employee-master-detail-layout"]');
    const listSection = wrapper.get('[data-testid="employee-list-section"]');
    const filterToolbar = wrapper.get('[data-testid="employee-list-filter-toolbar"]');

    expect(wrapper.find(".employee-admin-hero").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("MODULE CONTROL");
    expect(layout.classes()).toContain("employee-admin-grid");
    expect(wrapper.find('[data-testid="employee-list-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-detail-only-mode"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-detail-workspace"]').exists()).toBe(false);
    expect(listSection.classes()).toContain("employee-admin-list-panel");

    expect(filterToolbar.find('[data-testid="employee-search-select"]').exists()).toBe(true);
    expect(filterToolbar.text()).toContain("Search");
    expect(filterToolbar.text()).toContain("Advanced filters");
    expect(filterToolbar.text()).not.toContain("Status");
    expect(filterToolbar.text()).not.toContain("Default branch");
    expect(filterToolbar.text()).not.toContain("Default mandate");
    expect(filterToolbar.text()).not.toContain("Include archived");

    const headerText = wrapper.get('[data-testid="employee-list-section"]').find(".employee-admin-panel__header").text();
    expect(headerText).toContain("Import / Export");
    expect(headerText).toContain("Create employee file");
    expect(wrapper.findAll('[data-testid="employee-list-row"]')).toHaveLength(2);
    expect(wrapper.get('[data-testid="employee-list-rows"]').text()).toContain("P-2000 · Markus Neumann");
    expect(wrapper.get('[data-testid="employee-list-rows"]').text()).toContain("P-2001 · Leon Yilmaz");
    expect(wrapper.findAll('[data-testid="employee-list-row-avatar"]')).toHaveLength(2);
    expect(wrapper.findAll('[data-testid="employee-list-row-avatar"]')[0]?.text()).toBe("MN");
    expect(wrapper.findAll('[data-testid="employee-list-row-avatar"]')[1]?.text()).toBe("LY");
    const firstRow = wrapper.findAll('[data-testid="employee-list-row"]')[0];
    expect(firstRow?.classes()).toContain("employee-admin-employee-row");
    expect(firstRow?.find(".employee-admin-employee-row__body").exists()).toBe(true);
    expect(firstRow?.find(".employee-admin-employee-row__line--primary").text()).toContain("P-2000 · Markus Neumann");
    expect(firstRow?.find(".employee-admin-employee-row__meta").text()).toContain("markus.neumann@example.test");
    expect(wrapper.get('[data-testid="employee-list-header-import-export"]').classes()).toContain("employee-admin-header-action");
    expect(wrapper.get('[data-testid="employee-list-header-new-employee"]').classes()).toContain("employee-admin-header-action");
  });

  it("shows a cached employee photo thumbnail in the list row after the detail photo was loaded", async () => {
    const { createObjectURLMock } = stubEmployeePhotoObjectUrls("blob:markus-photo");
    apiMocks.getEmployeePhotoMock.mockResolvedValue({
      document_id: "photo-document-1",
      relation_type: "employee_photo",
      label: null,
      title: "Markus photo",
      document_type_key: "employee_photo",
      file_name: "markus.png",
      content_type: "image/png",
      current_version_no: 3,
      linked_at: "2026-04-01T08:00:00Z",
    });
    apiMocks.downloadEmployeeDocumentMock.mockResolvedValue({
      blob: new Blob(["photo"], { type: "image/png" }),
    });

    const wrapper = await mountEmployeeAdmin();
    await openFirstEmployeeWorkspace(wrapper);
    expect(createObjectURLMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.downloadEmployeeDocumentMock).toHaveBeenCalledWith(
      "tenant-1",
      "photo-document-1",
      3,
      "token-1",
    );
    expect(wrapper.get('[data-testid="employee-dashboard-photo-image"]').attributes("src")).toBe("blob:markus-photo");

    await wrapper.get('[data-testid="employee-detail-back-to-list"]').trigger("click");
    await settle();

    const rows = wrapper.findAll('[data-testid="employee-list-row"]');
    expect(rows).toHaveLength(2);
    expect(rows[0]?.find('[data-testid="employee-list-row-avatar-image"]').attributes("src")).toBe("blob:markus-photo");
    expect(rows[0]?.find('[data-testid="employee-list-row-avatar"]').text()).toBe("");
    expect(rows[1]?.find('[data-testid="employee-list-row-avatar-image"]').exists()).toBe(false);
    expect(rows[1]?.find('[data-testid="employee-list-row-avatar"]').text()).toBe("LY");
  });

  it("keeps initials fallback in the employee list when no photo has been loaded", async () => {
    const wrapper = await mountEmployeeAdmin();

    const avatars = wrapper.findAll('[data-testid="employee-list-row-avatar"]');
    expect(avatars).toHaveLength(2);
    expect(wrapper.find('[data-testid="employee-list-row-avatar-image"]').exists()).toBe(false);
    expect(avatars[0]?.text()).toBe("MN");
    expect(avatars[1]?.text()).toBe("LY");
  });

  it("falls back to initials when a cached employee list photo fails to load", async () => {
    stubEmployeePhotoObjectUrls("blob:broken-markus-photo");
    apiMocks.getEmployeePhotoMock.mockResolvedValue({
      document_id: "photo-document-1",
      relation_type: "employee_photo",
      label: null,
      title: "Broken Markus photo",
      document_type_key: "employee_photo",
      file_name: "markus.png",
      content_type: "image/png",
      current_version_no: 3,
      linked_at: "2026-04-01T08:00:00Z",
    });
    apiMocks.downloadEmployeeDocumentMock.mockResolvedValue({
      blob: new Blob(["broken-photo"], { type: "image/png" }),
    });

    const wrapper = await mountEmployeeAdmin();
    await openFirstEmployeeWorkspace(wrapper);
    await wrapper.get('[data-testid="employee-detail-back-to-list"]').trigger("click");
    await settle();

    const firstRowImage = wrapper.findAll('[data-testid="employee-list-row"]')[0]?.get('[data-testid="employee-list-row-avatar-image"]');
    await firstRowImage?.trigger("error");
    await settle();

    expect(wrapper.findAll('[data-testid="employee-list-row"]')[0]?.find('[data-testid="employee-list-row-avatar-image"]').exists()).toBe(false);
    expect(wrapper.findAll('[data-testid="employee-list-row-avatar"]')[0]?.text()).toBe("MN");
  });

  it("filters the visible employee list live while typing in the main search input", async () => {
    const wrapper = await mountEmployeeAdmin();
    apiMocks.listEmployeesMock.mockClear();

    const searchInput = wrapper.get('[data-testid="employee-search-select-input"]');
    await searchInput.setValue("P-2001");
    await settle();
    expect(apiMocks.listEmployeesMock).not.toHaveBeenCalled();
    expect(wrapper.findAll('[data-testid="employee-list-row"]')).toHaveLength(1);
    expect(wrapper.get('[data-testid="employee-list-rows"]').text()).toContain("Leon Yilmaz");
    expect(wrapper.get('[data-testid="employee-list-rows"]').text()).not.toContain("Markus Neumann");

    await searchInput.setValue("example.test");
    await settle();
    expect(wrapper.findAll('[data-testid="employee-list-row"]')).toHaveLength(1);
    expect(wrapper.get('[data-testid="employee-list-rows"]').text()).toContain("Markus Neumann");
    expect(wrapper.get('[data-testid="employee-list-rows"]').text()).not.toContain("Leon Yilmaz");

    await searchInput.setValue("missing");
    await settle();
    expect(wrapper.find('[data-testid="employee-list-empty-state"]').exists()).toBe(true);

    await searchInput.setValue("");
    await settle();
    expect(wrapper.findAll('[data-testid="employee-list-row"]')).toHaveLength(2);
  });

  it("opens advanced filters in a dialog, applies removed filters, and keeps the applied state visible", async () => {
    const wrapper = await mountEmployeeAdmin();

    await wrapper.get('[data-testid="employee-advanced-filters-open"]').trigger("click");
    await settle();

    const dialog = wrapper.get('[data-testid="employee-advanced-filters-dialog"]');
    expect(dialog.text()).toContain("Additional filters");
    expect(dialog.text()).toContain("Status");
    expect(dialog.text()).toContain("Default branch");
    expect(dialog.text()).toContain("Default mandate");
    expect(dialog.text()).toContain("Include archived");

    await dialog.get('[data-testid="employee-advanced-filters-search"]').setValue("mark");
    await dialog.get('[data-testid="employee-advanced-filters-status"]').setValue("active");
    await dialog.get('[data-testid="employee-advanced-filters-default-branch"]').setValue("branch-1");
    await settle();
    await dialog.get('[data-testid="employee-advanced-filters-default-mandate"]').setValue("mandate-1");
    await dialog.get('[data-testid="employee-advanced-filters-include-archived"]').setValue(true);

    apiMocks.listEmployeesMock.mockClear();
    await dialog.get('[data-testid="employee-advanced-filters-apply"]').trigger("submit");
    await settle();

    expect(apiMocks.listEmployeesMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        default_branch_id: "branch-1",
        default_mandate_id: "mandate-1",
        include_archived: true,
        search: "mark",
        status: "active",
      }),
    );
    expect(wrapper.find('[data-testid="employee-advanced-filters-dialog"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="employee-search-select-input"]').element as HTMLInputElement).value).toBe("mark");
    expect(wrapper.findAll('[data-testid="employee-list-row"]')).toHaveLength(1);
    expect(wrapper.get('[data-testid="employee-list-rows"]').text()).toContain("Markus Neumann");

    await wrapper.get('[data-testid="employee-advanced-filters-open"]').trigger("click");
    await settle();
    const reopenedDialog = wrapper.get('[data-testid="employee-advanced-filters-dialog"]');
    expect((reopenedDialog.get('[data-testid="employee-advanced-filters-status"]').element as HTMLSelectElement).value).toBe("active");
    expect((reopenedDialog.get('[data-testid="employee-advanced-filters-default-branch"]').element as HTMLSelectElement).value).toBe("branch-1");
    expect((reopenedDialog.get('[data-testid="employee-advanced-filters-default-mandate"]').element as HTMLSelectElement).value).toBe("mandate-1");
    expect((reopenedDialog.get('[data-testid="employee-advanced-filters-include-archived"]').element as HTMLInputElement).checked).toBe(true);

    await reopenedDialog.get('[data-testid="employee-advanced-filters-cancel"]').trigger("click");
    await settle();
    expect(wrapper.find('[data-testid="employee-advanced-filters-dialog"]').exists()).toBe(false);
  });

  it("moves import and export controls into a header-triggered modal without changing functionality", async () => {
    const wrapper = await mountEmployeeAdmin();

    await wrapper.get('[data-testid="employee-list-header-import-export"]').trigger("click");
    await settle();

    const importExportModal = wrapper.get('[data-testid="employee-import-export-modal"]');
    expect(importExportModal.find('input[type="file"]').exists()).toBe(true);
    expect(importExportModal.find("textarea").exists()).toBe(true);
    expect(importExportModal.text()).toContain("Load import file");
    expect(importExportModal.text()).toContain("Dry run");
    expect(importExportModal.text()).toContain("Import execute");
    expect(importExportModal.text()).toContain("Export employees");

    await wrapper.get('[data-testid="employee-import-export-close"]').trigger("click");
    await settle();
    expect(wrapper.find('[data-testid="employee-import-export-modal"]').exists()).toBe(false);
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
    await wrapper.get('[data-testid="employee-list-row"]').trigger("click");
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
    await openFirstEmployeeWorkspace(wrapper);

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
    await openFirstEmployeeWorkspace(wrapper);

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

  it("does not trigger employee reloads from live search without a token or read permission", async () => {
    authStoreState.accessToken = "";
    authStoreState.effectiveAccessToken = "";
    const missingTokenWrapper = await mountEmployeeAdmin();
    apiMocks.listEmployeesMock.mockClear();

    await missingTokenWrapper.get('[data-testid="employee-search-select-input"]').setValue("mark");
    expect(apiMocks.listEmployeesMock).not.toHaveBeenCalled();
    expect(missingTokenWrapper.findAll('[data-testid="employee-list-row"]')).toHaveLength(0);

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
    await openFirstEmployeeWorkspace(wrapper);

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

    expect(wrapper.find('[data-testid="employee-list-only-mode"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-detail-only-mode"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="employee-detail-back-to-list"]').classes()).toContain("employee-admin-back-button");
    expect(detailTabLabels(wrapper)).toEqual(["Overview"]);
    expect(wrapper.find('[data-testid="employee-tab-dashboard"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="employee-tab-overview"]').classes()).toContain("active");
    expect(wrapper.get('[data-testid="employee-overview-section-file"]').text()).toContain("employeeAdmin.form.title");
    expect(wrapper.get('[data-testid="employee-overview-section-file"]').find('input[required]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-overview-section-nav"]').exists()).toBe(false);
  });

  it("renders Overview nav and section cards with private visibility controlled by permission", async () => {
    const wrapper = await mountEmployeeAdmin();
    await wrapper.get('[data-testid="employee-list-row"]').trigger("click");
    await settle();
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
    await openFirstEmployeeWorkspace(dispatcherWrapper);
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
    await openFirstEmployeeWorkspace(wrapper);
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
    await openFirstEmployeeWorkspace(wrapper);

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
    await openFirstEmployeeWorkspace(wrapper);
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
    await openFirstEmployeeWorkspace(wrapper);

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
    await openFirstEmployeeWorkspace(wrapper);

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
    await openFirstEmployeeWorkspace(wrapper);
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
    await openFirstEmployeeWorkspace(wrapper);
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
    await openFirstEmployeeWorkspace(wrapper);
    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();

    const overview = wrapper.get('[data-testid="employee-overview-onepage"]');
    expect(overview.find(".employee-admin-editor-intro").exists()).toBe(false);
    expect(overview.findAll(".employee-admin-overview-section-card")).toHaveLength(11);
    expect(overview.findAll(".employee-admin-overview-section-card__header").length).toBeGreaterThanOrEqual(11);
  });

  it("removes static explanatory lead copy while keeping functional Overview hints", async () => {
    const wrapper = await mountEmployeeAdmin();
    await openFirstEmployeeWorkspace(wrapper);
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
    expect(apiMocks.getEmployeeMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="employee-list-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-detail-workspace"]').exists()).toBe(false);

    await wrapper.get('[data-testid="employee-list-header-import-export"]').trigger("click");
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

    await wrapper.get('[data-testid="employee-import-export-close"]').trigger("click");
    await settle();
    await wrapper.get('[data-testid="employee-list-row"]').trigger("click");
    await settle();

    expect(apiMocks.getEmployeeMock).toHaveBeenCalledWith("tenant-1", "employee-markus", "token-1");
    expect(wrapper.find('[data-testid="employee-list-only-mode"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="employee-detail-only-mode"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="employee-detail-workspace"]').text()).toContain("Markus Neumann");
    expect(wrapper.get(".employee-admin-detail-header-actions").exists()).toBe(true);
    expect(wrapper.get('[data-testid="employee-detail-back-to-list"]').classes()).toContain("employee-admin-back-button");
    expect(wrapper.get(".employee-admin-detail-header-actions").find('[data-testid="status-badge"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="employee-detail-tabs"]').text()).toMatch(/Dashboard[\s\S]*Overview/);
    expect(wrapper.get('[data-testid="employee-detail-tabs"]').text()).not.toContain("Profile photo");
    expect(wrapper.get('[data-testid="employee-detail-tabs"]').text()).not.toContain("Documents");
    expect(wrapper.get('[data-testid="employee-detail-tabs"]').text()).not.toContain("Qualifications");
    expect(wrapper.get('[data-testid="employee-tab-dashboard"]').classes()).toContain("active");
    expect(wrapper.get('[data-testid="employee-dashboard-hero"]').text()).toContain("Markus Neumann");
    expect(wrapper.find('[data-testid="employee-dashboard-calendar"]').exists()).toBe(true);

    await wrapper.get('[data-testid="employee-tab-overview"]').trigger("click");
    await settle();
    expect(wrapper.get('[data-testid="employee-tab-overview"]').classes()).toContain("active");
    expect(wrapper.find('[data-testid="employee-overview-section-nav"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-overview-section-app-access"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-overview-section-documents"]').exists()).toBe(true);
    await wrapper.get('[data-testid="employee-overview-nav-documents"]').trigger("click");
    await settle();
    expect(wrapper.get('[data-testid="employee-overview-nav-documents"]').classes()).toContain("employee-admin-overview-nav__link--active");

    await wrapper.get('[data-testid="employee-detail-back-to-list"]').trigger("click");
    await settle();
    expect(wrapper.find('[data-testid="employee-list-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-detail-workspace"]').exists()).toBe(false);

    await clickButtonByText(wrapper, "Create employee file");
    await settle();
    expect(wrapper.find('[data-testid="employee-list-only-mode"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="employee-detail-workspace"]').text()).toContain("Create employee");
    expect(wrapper.find('[data-testid="employee-tab-dashboard"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="employee-tab-overview"]').classes()).toContain("active");
    expect(wrapper.find('[data-testid="employee-overview-section-nav"]').exists()).toBe(false);
  });
});
