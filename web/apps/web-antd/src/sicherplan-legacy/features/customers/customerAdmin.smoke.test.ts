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
  createCustomerAddressMock: vi.fn(),
  createCustomerAvailableAddressMock: vi.fn(),
  createCustomerContactMock: vi.fn(),
  createCustomerEmployeeBlockMock: vi.fn(),
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
  updateCustomerAddressMock: vi.fn(),
  updateCustomerContactMock: vi.fn(),
  updateCustomerEmployeeBlockMock: vi.fn(),
  updateCustomerPortalPrivacyMock: vi.fn(),
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
  "customerAdmin.actions.addAddress": "Add address",
  "customerAdmin.actions.addContact": "Add contact",
  "customerAdmin.actions.createAddress": "Create address",
  "customerAdmin.actions.createContact": "Create contact",
  "customerAdmin.actions.createPortalAccess": "Create portal access",
  "customerAdmin.actions.createSharedAddress": "Create shared address",
  "customerAdmin.actions.exportCustomers": "CSV export",
  "customerAdmin.actions.newCustomer": "New customer",
  "customerAdmin.actions.refreshHistory": "Refresh history",
  "customerAdmin.actions.resetPortalAccessPassword": "Reset portal password",
  "customerAdmin.actions.search": "Search",
  "customerAdmin.contactAccess.addressesDescription": "Link and maintain customer addresses.",
  "customerAdmin.contactAccess.addressesTitle": "Addresses",
  "customerAdmin.contactAccess.contactsDescription": "Manage customer contact persons.",
  "customerAdmin.contactAccess.contactsTitle": "Contacts",
  "customerAdmin.contactAccess.portalDescription": "Control portal access and login history.",
  "customerAdmin.contactAccess.portalTitle": "Portal & Access",
  "customerAdmin.detail.emptyBody": "Choose a customer from the list or create a new record.",
  "customerAdmin.detail.newTitle": "Create customer",
  "customerAdmin.detail.workspaceLead": "Workspace lead",
  "customerAdmin.detail.workspaceTitle": "Customer workspace",
  "customerAdmin.fields.address": "Address",
  "customerAdmin.fields.addressType": "Address type",
  "customerAdmin.fields.effectiveFrom": "Effective from",
  "customerAdmin.fields.email": "Email",
  "customerAdmin.fields.employeeId": "Employee ID",
  "customerAdmin.fields.fullName": "Full name",
  "customerAdmin.fields.lifecycleStatus": "Status",
  "customerAdmin.fields.locale": "Locale",
  "customerAdmin.fields.reason": "Reason",
  "customerAdmin.fields.temporaryPassword": "Temporary password",
  "customerAdmin.fields.username": "Username",
  "customerAdmin.filters.allStatuses": "All statuses",
  "customerAdmin.filters.includeArchived": "Include archived customers",
  "customerAdmin.filters.search": "Search",
  "customerAdmin.filters.searchPlaceholder": "Number or name",
  "customerAdmin.history.empty": "No history entries.",
  "customerAdmin.portal.title": "Portal controls and releases",
  "customerAdmin.portalAccess.title": "Credentials and login enablement",
  "customerAdmin.portalAccess.contactPlaceholder": "Select a contact",
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
  "customerAdmin.tabs.addresses": "Addresses",
  "customerAdmin.tabs.commercial": "Commercial",
  "customerAdmin.tabs.contactAccess": "Contacts & Access",
  "customerAdmin.tabs.contacts": "Contacts",
  "customerAdmin.tabs.dashboard": "Dashboard",
  "customerAdmin.tabs.employeeBlocks": "Employee blocks",
  "customerAdmin.tabs.history": "History",
  "customerAdmin.tabs.overview": "Overview",
  "customerAdmin.tabs.plans": "Plans",
  "customerAdmin.tabs.portal": "Portal",
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
    createCustomerAddress: apiMocks.createCustomerAddressMock,
    createCustomerAvailableAddress: apiMocks.createCustomerAvailableAddressMock,
    createCustomerContact: apiMocks.createCustomerContactMock,
    createCustomerEmployeeBlock: apiMocks.createCustomerEmployeeBlockMock,
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
    updateCustomerAddress: apiMocks.updateCustomerAddressMock,
    updateCustomerContact: apiMocks.updateCustomerContactMock,
    updateCustomerEmployeeBlock: apiMocks.updateCustomerEmployeeBlockMock,
    updateCustomerPortalPrivacy: apiMocks.updateCustomerPortalPrivacyMock,
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
  emits: ["select-tab"],
  template: `
    <div data-testid="customer-dashboard-tab-stub">
      {{ customer ? customer.id : "" }}
      <button data-testid="dashboard-select-contacts" type="button" @click="$emit('select-tab', 'contacts')">Contacts</button>
      <button data-testid="dashboard-select-addresses" type="button" @click="$emit('select-tab', 'addresses')">Addresses</button>
      <button data-testid="dashboard-select-portal" type="button" @click="$emit('select-tab', 'portal')">Portal</button>
    </div>
  `,
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

function buildCustomerRead(id: string, name: string, customerNumber: string, overrides: Record<string, unknown> = {}) {
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
    ...overrides,
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

async function mountSelectedCustomer(tab = "dashboard") {
  routeState.query = {
    customer_id: "customer-default",
    tab,
  };
  return mountCustomerAdmin();
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

    apiMocks.createCustomerAddressMock.mockReset();
    apiMocks.createCustomerAddressMock.mockResolvedValue({});
    apiMocks.createCustomerAvailableAddressMock.mockReset();
    apiMocks.createCustomerAvailableAddressMock.mockResolvedValue({
      id: "address-option-new",
      street_line_1: "Neue Strasse 1",
      street_line_2: null,
      postal_code: "50667",
      city: "Koeln",
      state: null,
      country_code: "DE",
    });
    apiMocks.createCustomerContactMock.mockReset();
    apiMocks.createCustomerContactMock.mockResolvedValue({});
    apiMocks.createCustomerEmployeeBlockMock.mockReset();
    apiMocks.createCustomerEmployeeBlockMock.mockResolvedValue({});
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
      return buildCustomerRead("customer-default", "Alpha Security", "K-0001", {
        contacts: [
          {
            id: "contact-1",
            tenant_id: "tenant-1",
            customer_id: "customer-default",
            full_name: "Mira Contact",
            title: null,
            function_label: null,
            email: "mira@example.test",
            phone: null,
            mobile: null,
            is_primary_contact: true,
            is_billing_contact: false,
            user_id: null,
            notes: null,
            status: "active",
            version_no: 1,
            archived_at: null,
          },
        ],
        addresses: [
          {
            id: "customer-address-1",
            tenant_id: "tenant-1",
            customer_id: "customer-default",
            address_id: "address-option-1",
            address_type: "billing",
            label: "Billing",
            is_default: true,
            status: "active",
            version_no: 1,
            archived_at: null,
            address: {
              id: "address-option-1",
              street_line_1: "Alte Strasse 1",
              street_line_2: null,
              postal_code: "50667",
              city: "Koeln",
              state: null,
              country_code: "DE",
            },
          },
        ],
      });
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
    apiMocks.listCustomerAvailableAddressesMock.mockResolvedValue([
      {
        id: "address-option-2",
        street_line_1: "Neue Strasse 2",
        street_line_2: null,
        postal_code: "50667",
        city: "Koeln",
        state: null,
        country_code: "DE",
      },
    ]);
    apiMocks.listCustomerPortalAccessMock.mockReset();
    apiMocks.listCustomerPortalAccessMock.mockResolvedValue([]);
    apiMocks.exportCustomersMock.mockReset();
    apiMocks.exportCustomersMock.mockResolvedValue({
      document_id: "doc-1",
      file_name: "customers.csv",
    });
    apiMocks.updateCustomerAddressMock.mockReset();
    apiMocks.updateCustomerAddressMock.mockResolvedValue({});
    apiMocks.updateCustomerContactMock.mockReset();
    apiMocks.updateCustomerContactMock.mockResolvedValue({});
    apiMocks.updateCustomerEmployeeBlockMock.mockReset();
    apiMocks.updateCustomerEmployeeBlockMock.mockResolvedValue({});
    apiMocks.updateCustomerPortalPrivacyMock.mockReset();
    apiMocks.updateCustomerPortalPrivacyMock.mockResolvedValue({
      customer_id: "customer-default",
      person_names_released: true,
      person_names_released_at: "2026-04-21T08:00:00Z",
      person_names_released_by_user_id: "user-1",
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

  it("renders contact access as the only contacts-addresses-portal top-level tab with right-side history links", async () => {
    const wrapper = await mountSelectedCustomer("contact_access");

    const contactAccessTab = wrapper.get('[data-testid="customer-tab-contact_access"]');
    expect(contactAccessTab.text()).toContain("Contacts & Access");
    expect(contactAccessTab.classes()).toContain("customer-admin-tab");
    expect(contactAccessTab.classes()).toContain("active");
    expect(wrapper.find('[data-testid="customer-tab-contacts"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-tab-addresses"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-tab-portal"]').exists()).toBe(false);

    const historyTab = wrapper.get('[data-testid="customer-tab-history"]');
    const employeeBlocksTab = wrapper.get('[data-testid="customer-tab-employee_blocks"]');
    expect(historyTab.classes()).toContain("customer-admin-tab-link");
    expect(historyTab.classes()).not.toContain("customer-admin-tab");
    expect(employeeBlocksTab.classes()).toContain("customer-admin-tab-link");

    await historyTab.trigger("click");
    await settle();
    expect(wrapper.get('[data-testid="customer-tab-history"]').classes()).toContain("active");
    expect(wrapper.get('[data-testid="customer-tab-history"]').attributes("aria-current")).toBe("page");
    expect(wrapper.find('[data-testid="customer-tab-panel-history"]').exists()).toBe(true);

    await employeeBlocksTab.trigger("click");
    await settle();
    expect(wrapper.get('[data-testid="customer-tab-employee_blocks"]').classes()).toContain("active");
    expect(wrapper.get('[data-testid="customer-tab-employee_blocks"]').attributes("aria-current")).toBe("page");
    expect(wrapper.find('[data-testid="customer-tab-panel-employee-blocks"]').exists()).toBe(true);
  });

  it("renders contacts, addresses, and portal sections stacked inside contact access", async () => {
    const wrapper = await mountSelectedCustomer("contact_access");

    const html = wrapper.html();
    const contactAccessPanel = wrapper.get('[data-testid="customer-tab-panel-contact-access"]');
    const contactsCard = wrapper.get('[data-testid="customer-contact-access-card-contacts"]');
    const addressesCard = wrapper.get('[data-testid="customer-contact-access-card-addresses"]');
    const portalCard = wrapper.get('[data-testid="customer-contact-access-card-portal"]');
    const directCardTestIds = Array.from(contactAccessPanel.element.children).map((child) =>
      child.getAttribute("data-testid"),
    );
    expect(directCardTestIds).toEqual([
      "customer-contact-access-card-contacts",
      "customer-contact-access-card-addresses",
      "customer-contact-access-card-portal",
    ]);
    expect(contactsCard.classes()).toContain("customer-admin-contact-access-card");
    expect(addressesCard.classes()).toContain("customer-admin-contact-access-card");
    expect(portalCard.classes()).toContain("customer-admin-contact-access-card");
    expect(contactsCard.text()).toContain("Contacts");
    expect(contactsCard.text()).toContain("Manage customer contact persons.");
    expect(addressesCard.text()).toContain("Addresses");
    expect(addressesCard.text()).toContain("Link and maintain customer addresses.");
    expect(portalCard.text()).toContain("Portal & Access");
    expect(portalCard.text()).toContain("Control portal access and login history.");
    expect(contactAccessPanel.findAll(".customer-admin-editor-intro")).toHaveLength(0);
    expect(contactAccessPanel.text()).not.toContain("Contact maintenance");
    expect(contactAccessPanel.text()).not.toContain("Address links");
    expect(contactAccessPanel.text()).not.toContain("Portal controls and releases");
    expect(wrapper.find('[data-testid="customer-tab-panel-contacts"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-tab-panel-addresses"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-tab-panel-portal"]').exists()).toBe(true);
    expect(contactsCard.find('[data-testid="customer-tab-panel-contacts"]').exists()).toBe(true);
    expect(addressesCard.find('[data-testid="customer-tab-panel-addresses"]').exists()).toBe(true);
    expect(portalCard.find('[data-testid="customer-tab-panel-portal"]').exists()).toBe(true);
    expect(contactsCard.find('[data-testid="customer-tab-panel-addresses"]').exists()).toBe(false);
    expect(addressesCard.find('[data-testid="customer-tab-panel-portal"]').exists()).toBe(false);
    expect(portalCard.find('[data-testid="customer-tab-panel-contacts"]').exists()).toBe(false);
    expect(html.indexOf('data-testid="customer-tab-panel-contact-access"')).toBeLessThan(
      html.indexOf('data-testid="customer-tab-panel-contacts"'),
    );
    expect(html.indexOf('data-testid="customer-tab-panel-contacts"')).toBeLessThan(
      html.indexOf('data-testid="customer-tab-panel-addresses"'),
    );
    expect(html.indexOf('data-testid="customer-tab-panel-addresses"')).toBeLessThan(
      html.indexOf('data-testid="customer-tab-panel-portal"'),
    );
  });

  it("keeps contact creation working from the merged contact access tab", async () => {
    const wrapper = await mountSelectedCustomer("contact_access");

    const contactPanel = wrapper.get('[data-testid="customer-contact-access-card-contacts"]');
    expect(contactPanel.text()).toContain("Mira Contact");
    await contactPanel.get<HTMLInputElement>('input[required]').setValue("Ada Lovelace");
    await contactPanel.get<HTMLInputElement>('input[type="email"]').setValue("ada@example.test");
    await contactPanel.get("form").trigger("submit");
    await settle();

    expect(apiMocks.createCustomerContactMock).toHaveBeenCalledWith(
      "tenant-1",
      "customer-default",
      "token-1",
      expect.objectContaining({
        tenant_id: "tenant-1",
        customer_id: "customer-default",
        full_name: "Ada Lovelace",
        email: "ada@example.test",
      }),
    );
  });

  it("keeps address creation and shared-address modal behavior working from contact access", async () => {
    const wrapper = await mountSelectedCustomer("contact_access");

    const addressPanel = wrapper.get('[data-testid="customer-contact-access-card-addresses"]');
    expect(addressPanel.text()).toContain("Alte Strasse 1");
    await addressPanel.get<HTMLSelectElement>("select").setValue("address-option-2");
    await addressPanel.get("form").trigger("submit");
    await settle();

    expect(apiMocks.createCustomerAddressMock).toHaveBeenCalledWith(
      "tenant-1",
      "customer-default",
      "token-1",
      expect.objectContaining({
        tenant_id: "tenant-1",
        customer_id: "customer-default",
        address_id: "address-option-2",
        address_type: "billing",
      }),
    );

    await clickButtonByTextWithin(addressPanel, "Create shared address");
    await settle();
    const modal = wrapper.get('[data-testid="customer-address-directory-create-modal"]');
    const inputs = modal.findAll("input");
    await inputs[0]!.setValue("Neue Strasse 1");
    await inputs[2]!.setValue("50667");
    await inputs[3]!.setValue("Koeln");
    await inputs[4]!.setValue("DE");
    await clickButtonByTextWithin(modal, "Create shared address");
    await settle();

    expect(apiMocks.createCustomerAvailableAddressMock).toHaveBeenCalledWith(
      "tenant-1",
      "customer-default",
      "token-1",
      expect.objectContaining({
        street_line_1: "Neue Strasse 1",
        postal_code: "50667",
        city: "Koeln",
        country_code: "DE",
      }),
    );
  });

  it("keeps portal privacy, portal access, password reset, and login history visible in contact access", async () => {
    portalAccessMocks.createCustomerPortalAccessMock.mockResolvedValue({ temporary_password: "Temp-1" });
    portalAccessMocks.resetCustomerPortalAccessPasswordMock.mockResolvedValue({ temporary_password: "Temp-2" });
    portalAccessMocks.listCustomerPortalAccessMock.mockResolvedValue([
      {
        user_id: "portal-user-1",
        contact_id: "contact-1",
        contact_name: "Mira Contact",
        username: "mira",
        email: "mira@example.test",
        status: "active",
        last_login_at: "2026-04-20T08:00:00Z",
      },
    ]);
    const wrapper = await mountSelectedCustomer("contact_access");

    const portalCard = wrapper.get('[data-testid="customer-contact-access-card-portal"]');
    const portalPanel = wrapper.get('[data-testid="customer-tab-panel-portal"]');
    expect(portalCard.text()).toContain("Portal & Access");
    expect(portalCard.text()).toContain("Control portal access and login history.");
    expect(portalPanel.find('[data-testid="customer-portal-access-section"]').exists()).toBe(true);
    expect(portalPanel.text()).toContain("Credentials and login enablement");
    expect(portalPanel.text()).toContain("customerAdmin.loginHistory.title");

    await clickButtonByTextWithin(portalPanel, "Create portal access");
    await settle();
    expect(wrapper.find('[data-testid="customer-portal-access-create-modal"]').exists()).toBe(true);
    await wrapper.get<HTMLSelectElement>('[data-testid="customer-portal-access-create-modal"] select').setValue("contact-1");
    await clickButtonByTextWithin(wrapper.get('[data-testid="customer-portal-access-create-modal"]'), "Create portal access");
    await settle();
    expect(portalAccessMocks.createCustomerPortalAccessMock).toHaveBeenCalledWith(
      "tenant-1",
      "customer-default",
      "token-1",
      expect.objectContaining({
        contact_id: "contact-1",
        customer_id: "customer-default",
        tenant_id: "tenant-1",
      }),
    );

    await clickButtonByText(wrapper, "Reset portal password");
    await settle();
    expect(wrapper.find('[data-testid="customer-portal-access-password-modal"]').exists()).toBe(true);
  });

  it("keeps history refresh and employee block creation working from right-side links", async () => {
    const wrapper = await mountSelectedCustomer("dashboard");

    await wrapper.get('[data-testid="customer-tab-history"]').trigger("click");
    await settle();
    expect(wrapper.find('[data-testid="customer-tab-panel-history"]').exists()).toBe(true);
    apiMocks.listCustomerHistoryMock.mockClear();
    await clickButtonByText(wrapper, "Refresh history");
    await settle();
    expect(apiMocks.listCustomerHistoryMock).toHaveBeenCalledWith("tenant-1", "customer-default", "token-1");

    await wrapper.get('[data-testid="customer-tab-employee_blocks"]').trigger("click");
    await settle();
    expect(wrapper.find('[data-testid="customer-tab-panel-employee-blocks"]').exists()).toBe(true);
    const employeePanel = wrapper.get('[data-testid="customer-tab-panel-employee-blocks"]');
    const inputs = employeePanel.findAll("input");
    await inputs[0]!.setValue("employee-1");
    await inputs[1]!.setValue("Do not schedule");
    await inputs[2]!.setValue("2026-04-21");
    await employeePanel.get("form").trigger("submit");
    await settle();
    expect(apiMocks.createCustomerEmployeeBlockMock).toHaveBeenCalledWith(
      "tenant-1",
      "customer-default",
      "token-1",
      expect.objectContaining({
        tenant_id: "tenant-1",
        customer_id: "customer-default",
        employee_id: "employee-1",
        reason: "Do not schedule",
        effective_from: "2026-04-21",
      }),
    );
  });

  it("maps dashboard legacy quick-action tab ids to contact access", async () => {
    const wrapper = await mountSelectedCustomer("dashboard");

    for (const testId of ["dashboard-select-contacts", "dashboard-select-addresses", "dashboard-select-portal"]) {
      await wrapper.get(`[data-testid="${testId}"]`).trigger("click");
      await settle();
      expect(wrapper.get('[data-testid="customer-tab-contact_access"]').classes()).toContain("active");
      expect(wrapper.find('[data-testid="customer-tab-panel-contact-access"]').exists()).toBe(true);
      await wrapper.get('[data-testid="customer-tab-dashboard"]').trigger("click");
      await settle();
    }
  });

  it("normalizes legacy direct route tabs to contact access without a blank panel", async () => {
    for (const legacyTabId of ["contacts", "addresses", "portal"]) {
      const wrapper = await mountSelectedCustomer(legacyTabId);

      expect(wrapper.get('[data-testid="customer-tab-contact_access"]').classes()).toContain("active");
      expect(wrapper.find('[data-testid="customer-tab-panel-contact-access"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="customer-tab-panel-contacts"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="customer-tab-panel-addresses"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="customer-tab-panel-portal"]').exists()).toBe(true);

      wrapper.unmount();
    }
  });
});
