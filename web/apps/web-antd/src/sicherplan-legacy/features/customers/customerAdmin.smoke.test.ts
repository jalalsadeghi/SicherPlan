// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import { defineComponent, reactive } from "vue";

import CustomerAdminView from "../../views/CustomerAdminView.vue";
import { moduleRegistry } from "../../../views/sicherplan/module-registry";

const routeState = reactive({
  meta: {} as Record<string, unknown>,
  query: {} as Record<string, unknown>,
});

const routerPushMock = vi.fn();
const routerReplaceMock = vi.fn();
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
  exportCustomersMock: vi.fn(),
  getCustomerCommercialProfileMock: vi.fn(),
  getCustomerDashboardMock: vi.fn(),
  getCustomerMock: vi.fn(),
  getCustomerPortalPrivacyMock: vi.fn(),
  getCustomerReferenceDataMock: vi.fn(),
  listCustomerAvailableAddressesMock: vi.fn(),
  listCustomerEmployeeBlocksMock: vi.fn(),
  listCustomerHistoryMock: vi.fn(),
  listCustomerPortalAccessMock: vi.fn(),
  listCustomerPortalLoginHistoryMock: vi.fn(),
  listCustomersMock: vi.fn(),
}));

const portalAccessMocks = vi.hoisted(() => ({
  createCustomerPortalAccessMock: vi.fn(),
  listCustomerPortalAccessMock: vi.fn(),
  resetCustomerPortalAccessPasswordMock: vi.fn(),
  unlinkCustomerPortalAccessMock: vi.fn(),
  updateCustomerPortalAccessStatusMock: vi.fn(),
}));

const employeeAdminMocks = vi.hoisted(() => ({
  bootstrapEmployeeCatalogSamplesMock: vi.fn(),
}));

const translations: Record<string, string> = {
  "customerAdmin.actions.cancel": "Cancel",
  "customerAdmin.actions.exportCustomers": "CSV export",
  "customerAdmin.actions.newCustomer": "New customer",
  "customerAdmin.actions.search": "Search",
  "customerAdmin.detail.emptyBody": "Choose a customer from the list or create a new record.",
  "customerAdmin.detail.newTitle": "Create customer",
  "customerAdmin.detail.workspaceLead": "Workspace lead",
  "customerAdmin.detail.workspaceTitle": "Customer workspace",
  "customerAdmin.filters.allStatuses": "All statuses",
  "customerAdmin.filters.includeArchived": "Include archived customers",
  "customerAdmin.filters.search": "Search",
  "customerAdmin.filters.searchPlaceholder": "Number or name",
  "customerAdmin.list.empty": "No customers match the current filters.",
  "customerAdmin.list.sidebarNavigationHint": "Use the sidebar customer links to open a customer dashboard.",
  "customerAdmin.searchResults.eyebrow": "Customer search",
  "customerAdmin.searchResults.empty": "No matching customers were found for the current filters.",
  "customerAdmin.searchResults.lead": "Select a result to open that customer's dashboard directly.",
  "customerAdmin.searchResults.loading": "Searching customers...",
  "customerAdmin.searchResults.title": "Matching customers",
  "customerAdmin.status.active": "Active",
  "customerAdmin.status.archived": "Archived",
  "customerAdmin.status.inactive": "Inactive",
  "customerAdmin.summary.none": "None",
};

vi.mock("@/i18n", () => ({
  useI18n: () => ({
    t: (key: string) => translations[key] ?? key,
  }),
}));

vi.mock("vue-router", () => ({
  useRoute: () => routeState,
  useRouter: () => ({
    push: routerPushMock,
    replace: routerReplaceMock,
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

vi.mock("@/api/employeeAdmin", async () => {
  const actual = await vi.importActual<typeof import("@/api/employeeAdmin")>("@/api/employeeAdmin");
  return {
    ...actual,
    bootstrapEmployeeCatalogSamples: employeeAdminMocks.bootstrapEmployeeCatalogSamplesMock,
  };
});

vi.mock("#/api/sicherplan/customer-portal-access", async () => {
  const actual = await vi.importActual<typeof import("#/api/sicherplan/customer-portal-access")>(
    "#/api/sicherplan/customer-portal-access",
  );
  return {
    ...actual,
    createCustomerPortalAccess: portalAccessMocks.createCustomerPortalAccessMock,
    listCustomerPortalAccess: portalAccessMocks.listCustomerPortalAccessMock,
    resetCustomerPortalAccessPassword: portalAccessMocks.resetCustomerPortalAccessPasswordMock,
    unlinkCustomerPortalAccess: portalAccessMocks.unlinkCustomerPortalAccessMock,
    updateCustomerPortalAccessStatus: portalAccessMocks.updateCustomerPortalAccessStatusMock,
  };
});

vi.mock("@/api/customers", async () => {
  const actual = await vi.importActual<typeof import("@/api/customers")>("@/api/customers");
  return {
    ...actual,
    exportCustomers: apiMocks.exportCustomersMock,
    getCustomer: apiMocks.getCustomerMock,
    getCustomerCommercialProfile: apiMocks.getCustomerCommercialProfileMock,
    getCustomerDashboard: apiMocks.getCustomerDashboardMock,
    getCustomerPortalPrivacy: apiMocks.getCustomerPortalPrivacyMock,
    getCustomerReferenceData: apiMocks.getCustomerReferenceDataMock,
    listCustomerAvailableAddresses: apiMocks.listCustomerAvailableAddressesMock,
    listCustomerEmployeeBlocks: apiMocks.listCustomerEmployeeBlocksMock,
    listCustomerHistory: apiMocks.listCustomerHistoryMock,
    listCustomerPortalAccess: apiMocks.listCustomerPortalAccessMock,
    listCustomerPortalLoginHistory: apiMocks.listCustomerPortalLoginHistoryMock,
    listCustomers: apiMocks.listCustomersMock,
  };
});

const SicherPlanLoadingOverlayStub = defineComponent({
  name: "SicherPlanLoadingOverlayStub",
  props: {
    busy: { type: Boolean, default: false },
    text: { type: String, default: "" },
  },
  template: `
    <div data-testid="customer-loading-overlay" :data-busy="busy ? 'true' : 'false'">
      <slot />
    </div>
  `,
});

const StatusBadgeStub = defineComponent({
  name: "StatusBadgeStub",
  props: {
    status: { type: String, default: "" },
  },
  template: '<span class="status-badge-stub">{{ status }}</span>',
});

const CustomerDashboardTabStub = defineComponent({
  name: "CustomerDashboardTabStub",
  props: {
    customer: { type: Object, default: null },
  },
  template: '<div data-testid="customer-dashboard-tab-stub">{{ customer ? customer.id : "" }}</div>',
});

const CustomerPlansTabStub = defineComponent({
  name: "CustomerPlansTabStub",
  template: '<div data-testid="customer-plans-tab-stub" />',
});

const baseReferenceData = {
  legal_forms: [],
  classifications: [],
  rankings: [],
  customer_statuses: [],
  branches: [],
  mandates: [],
  invoice_layouts: [],
  function_types: [],
  qualification_types: [],
};

function buildCustomerListItem(id: string, name: string, customerNumber: string, status = "active") {
  return {
    id,
    tenant_id: "tenant-1",
    customer_number: customerNumber,
    name,
    status,
    version_no: 1,
  };
}

function buildCustomerRead(id: string, name: string, customerNumber: string) {
  return {
    ...buildCustomerListItem(id, name, customerNumber),
    legal_name: null,
    external_ref: null,
    legal_form_lookup_id: null,
    classification_lookup_id: null,
    ranking_lookup_id: null,
    customer_status_lookup_id: null,
    default_branch_id: null,
    default_mandate_id: null,
    notes: null,
    created_at: "2026-04-01T08:00:00Z",
    updated_at: "2026-04-01T08:00:00Z",
    portal_person_names_released: false,
    portal_person_names_released_at: null,
    portal_person_names_released_by_user_id: null,
    archived_at: null,
    contacts: [],
    addresses: [],
  };
}

function buildCommercialProfile() {
  return {
    billing_profile: null,
    invoice_parties: [],
    rate_cards: [],
    rate_lines: [],
    surcharge_rules: [],
  };
}

function buildDashboard(customerId: string) {
  return {
    customer_id: customerId,
    planning_summary: {
      total_plans_count: 0,
      latest_plans: [],
    },
    finance_summary: {
      visibility: "available",
      total_received_amount: null,
      currency_code: null,
      semantic_label: null,
    },
    calendar_items: [],
  };
}

function createListCustomersImplementation() {
  return vi.fn(async (_tenantId: string, _accessToken: string, params: Record<string, unknown>) => {
    const search = `${params.search ?? ""}`.trim().toLowerCase();
    if (search === "rhein") {
      return [buildCustomerListItem("customer-rhein", "RheinForum Köln", "K-1000", "active")];
    }
    if (search === "unknown") {
      return [];
    }
    if (search) {
      return [
        buildCustomerListItem("customer-rhein", "RheinForum Köln", "K-1000", "active"),
        buildCustomerListItem("customer-hafen", "HafenKontor Köln", "K-1001", "active"),
      ].filter((customer) => customer.name.toLowerCase().includes(search));
    }
    return [buildCustomerListItem("customer-default", "Alpha Security", "K-0001", "active")];
  });
}

async function settle() {
  await flushPromises();
  await flushPromises();
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

const mountedWrappers: VueWrapper[] = [];

async function mountCustomerAdmin() {
  const wrapper = mount(CustomerAdminView, {
    global: {
      stubs: {
        CustomerDashboardTab: CustomerDashboardTabStub,
        CustomerPlansTab: CustomerPlansTabStub,
        SicherPlanLoadingOverlay: SicherPlanLoadingOverlayStub,
        StatusBadge: StatusBadgeStub,
      },
    },
  });
  mountedWrappers.push(wrapper);
  await settle();
  return wrapper;
}

describe("CustomerAdminView search dialog", () => {
  beforeEach(() => {
    routeState.meta = {};
    routeState.query = {};
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
    routerReplaceMock.mockReset();
    showFeedbackToastMock.mockReset();

    apiMocks.getCustomerReferenceDataMock.mockReset();
    apiMocks.getCustomerReferenceDataMock.mockResolvedValue(baseReferenceData);
    apiMocks.listCustomersMock.mockReset();
    apiMocks.listCustomersMock.mockImplementation(createListCustomersImplementation());
    apiMocks.getCustomerMock.mockReset();
    apiMocks.getCustomerMock.mockImplementation(async (_tenantId: string, customerId: string) => {
      if (customerId === "customer-rhein") {
        return buildCustomerRead("customer-rhein", "RheinForum Köln", "K-1000");
      }
      if (customerId === "customer-hafen") {
        return buildCustomerRead("customer-hafen", "HafenKontor Köln", "K-1001");
      }
      return buildCustomerRead("customer-default", "Alpha Security", "K-0001");
    });
    apiMocks.getCustomerDashboardMock.mockReset();
    apiMocks.getCustomerDashboardMock.mockImplementation(async (_tenantId: string, customerId: string) => {
      return buildDashboard(customerId);
    });
    apiMocks.getCustomerCommercialProfileMock.mockReset();
    apiMocks.getCustomerCommercialProfileMock.mockResolvedValue(buildCommercialProfile());
    apiMocks.listCustomerHistoryMock.mockReset();
    apiMocks.listCustomerHistoryMock.mockResolvedValue([]);
    apiMocks.listCustomerPortalLoginHistoryMock.mockReset();
    apiMocks.listCustomerPortalLoginHistoryMock.mockResolvedValue([]);
    apiMocks.listCustomerEmployeeBlocksMock.mockReset();
    apiMocks.listCustomerEmployeeBlocksMock.mockResolvedValue({
      customer_id: "customer-default",
      capability: {
        directory_available: true,
        employee_reference_mode: "directory",
        message_key: "ok",
      },
      items: [],
    });
    apiMocks.getCustomerPortalPrivacyMock.mockReset();
    apiMocks.getCustomerPortalPrivacyMock.mockResolvedValue({
      customer_id: "customer-default",
      person_names_released: false,
      person_names_released_at: null,
      person_names_released_by_user_id: null,
    });
    apiMocks.listCustomerAvailableAddressesMock.mockReset();
    apiMocks.listCustomerAvailableAddressesMock.mockResolvedValue([]);
    apiMocks.listCustomerPortalAccessMock.mockReset();
    apiMocks.listCustomerPortalAccessMock.mockResolvedValue([]);
    apiMocks.exportCustomersMock.mockReset();
    apiMocks.exportCustomersMock.mockResolvedValue({
      document_id: "doc-1",
      file_name: "customers.csv",
    });

    portalAccessMocks.createCustomerPortalAccessMock.mockReset();
    portalAccessMocks.listCustomerPortalAccessMock.mockReset();
    portalAccessMocks.listCustomerPortalAccessMock.mockResolvedValue([]);
    portalAccessMocks.resetCustomerPortalAccessPasswordMock.mockReset();
    portalAccessMocks.unlinkCustomerPortalAccessMock.mockReset();
    portalAccessMocks.updateCustomerPortalAccessStatusMock.mockReset();
    employeeAdminMocks.bootstrapEmployeeCatalogSamplesMock.mockReset();
  });

  afterEach(() => {
    while (mountedWrappers.length) {
      mountedWrappers.pop()?.unmount();
    }
  });

  it("keeps the module control hidden for customers only via the registry flag", () => {
    expect(moduleRegistry.customers?.showPageIntro).toBe(false);
    expect(moduleRegistry["planning-orders"]?.showPageIntro).toBeUndefined();
  });

  it("renders the search-select control and removes the sidebar helper sentence", async () => {
    const wrapper = await mountCustomerAdmin();

    expect(wrapper.find('[data-testid="customer-list-section"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-search-select"]').exists()).toBe(true);

    const searchInput = wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]');
    await searchInput.setValue("Rhein");

    expect(searchInput.element.value).toBe("Rhein");
    expect(wrapper.text()).not.toContain("Use the sidebar customer links to open a customer dashboard.");
  });

  it("opens the customer search dialog from Search and shows matching results", async () => {
    const wrapper = await mountCustomerAdmin();
    apiMocks.listCustomersMock.mockClear();

    await wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]').setValue("Rhein");
    await clickButtonByText(wrapper, "Search");
    await settle();

    const lastCall = apiMocks.listCustomersMock.mock.calls.at(-1);
    expect(lastCall?.[2]).toMatchObject({ search: "Rhein" });
    expect(wrapper.find('[data-testid="customer-search-results-modal"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("RheinForum Köln");
    expect(wrapper.text()).not.toContain("Use the sidebar customer links to open a customer dashboard.");
  });

  it("selects a search result, closes the dialog, loads the customer, and routes to dashboard", async () => {
    const wrapper = await mountCustomerAdmin();
    apiMocks.listCustomersMock.mockClear();
    apiMocks.getCustomerMock.mockClear();
    routerReplaceMock.mockClear();

    await wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]').setValue("Rhein");
    await clickButtonByText(wrapper, "Search");
    await settle();

    await wrapper.get('[data-testid="customer-search-result-row"]').trigger("click");
    await settle();

    expect(wrapper.find('[data-testid="customer-search-results-modal"]').exists()).toBe(false);
    expect(apiMocks.getCustomerMock).toHaveBeenCalledWith("tenant-1", "customer-rhein", "token-1");
    expect(routerReplaceMock).toHaveBeenCalledWith(
      expect.objectContaining({
        query: expect.objectContaining({
          customer_id: "customer-rhein",
          tab: "dashboard",
        }),
      }),
    );
    expect(wrapper.get('[data-testid="customer-dashboard-tab-stub"]').text()).toContain("customer-rhein");
  });

  it("shows the empty state for unknown search values without stale results", async () => {
    const wrapper = await mountCustomerAdmin();
    apiMocks.listCustomersMock.mockClear();

    await wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]').setValue("Rhein");
    await clickButtonByText(wrapper, "Search");
    await settle();
    expect(wrapper.text()).toContain("RheinForum Köln");

    await wrapper.get('[data-testid="customer-search-result-close"]').trigger("click");
    await settle();

    await wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]').setValue("unknown");
    await clickButtonByText(wrapper, "Search");
    await settle();

    expect(wrapper.find('[data-testid="customer-search-result-empty"]').exists()).toBe(true);
    expect(wrapper.text()).not.toContain("RheinForum Köln");
  });

  it("passes include_archived through the search dialog requests", async () => {
    const wrapper = await mountCustomerAdmin();
    apiMocks.listCustomersMock.mockClear();

    const includeArchived = wrapper.get<HTMLInputElement>('[data-testid="customer-list-section"] input[type="checkbox"]');
    await includeArchived.setValue(true);
    await wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]').setValue("Rhein");
    await clickButtonByText(wrapper, "Search");
    await settle();

    expect(apiMocks.listCustomersMock.mock.calls.at(-1)?.[2]).toMatchObject({
      search: "Rhein",
      include_archived: true,
    });

    await includeArchived.setValue(false);
    await clickButtonByText(wrapper, "Search");
    await settle();

    expect(apiMocks.listCustomersMock.mock.calls.at(-1)?.[2]).toMatchObject({
      search: "Rhein",
      include_archived: false,
    });
  });

  it("does not fetch customer search results without scope, token, or read permission", async () => {
    authStoreState.activeRole = "tenant_admin";
    authStoreState.effectiveTenantScopeId = "";
    authStoreState.tenantScopeId = "";
    authStoreState.accessToken = "";
    authStoreState.effectiveAccessToken = "";
    apiMocks.listCustomersMock.mockClear();

    const wrapper = await mountCustomerAdmin();

    expect(apiMocks.listCustomersMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="customer-list-section"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-search-results-modal"]').exists()).toBe(false);
  });

  it("keeps export, new customer, and route-based customer selection working", async () => {
    routeState.query = {
      customer_id: "customer-rhein",
      tab: "dashboard",
    };
    apiMocks.listCustomersMock.mockImplementation(async (_tenantId: string, _accessToken: string, params: Record<string, unknown>) => {
      const search = `${params.search ?? ""}`.trim().toLowerCase();
      if (search) {
        return [buildCustomerListItem("customer-rhein", "RheinForum Köln", "K-1000", "active")];
      }
      return [buildCustomerListItem("customer-rhein", "RheinForum Köln", "K-1000", "active")];
    });
    apiMocks.getCustomerMock.mockClear();
    apiMocks.exportCustomersMock.mockClear();

    const wrapper = await mountCustomerAdmin();

    expect(apiMocks.getCustomerMock).toHaveBeenCalledWith("tenant-1", "customer-rhein", "token-1");
    await clickButtonByText(wrapper, "CSV export");
    await settle();
    expect(apiMocks.exportCustomersMock).toHaveBeenCalled();

    await clickButtonByText(wrapper, "New customer");
    await settle();
    expect(wrapper.text()).toContain("Create customer");
  });
});
