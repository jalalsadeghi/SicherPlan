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
const createObjectUrlMock = vi.fn(() => "blob:customer-export");
const revokeObjectUrlMock = vi.fn();
const scrollIntoViewMock = vi.fn();
type IntersectionObserverCallbackRef = ((entries: IntersectionObserverEntry[]) => void) | null;
let intersectionObserverCallback: IntersectionObserverCallbackRef = null;

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
  downloadCustomerDocumentMock: vi.fn(),
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
  "customerAdmin.actions.advancedFilters": "Advanced filters",
  "customerAdmin.actions.applyFilters": "Apply filters",
  "customerAdmin.actions.archive": "Archive",
  "customerAdmin.actions.createAddress": "Create address",
  "customerAdmin.actions.createContact": "Create contact",
  "customerAdmin.actions.createNewContact": "Create new contact",
  "customerAdmin.actions.createNewAddress": "Create new address",
  "customerAdmin.actions.createPortalAccess": "Create portal access",
  "customerAdmin.actions.createSharedAddress": "Create shared address",
  "customerAdmin.actions.closeFilters": "Close filters",
  "customerAdmin.actions.edit": "Edit",
  "customerAdmin.actions.exportCustomers": "CSV export",
  "customerAdmin.actions.exportVCard": "vCard",
  "customerAdmin.actions.newCustomer": "New customer",
  "customerAdmin.actions.backToList": "Back to customer list",
  "customerAdmin.actions.newOrder": "New order",
  "customerAdmin.actions.refreshHistory": "Refresh history",
  "customerAdmin.actions.resetPortalAccessPassword": "Reset portal password",
  "customerAdmin.actions.search": "Search",
  "customerAdmin.contactAccess.addressesDescription": "Link and maintain customer addresses.",
  "customerAdmin.contactAccess.addressesTitle": "Addresses",
  "customerAdmin.contactAccess.contactsDescription": "Manage customer contact persons.",
  "customerAdmin.contactAccess.contactsTitle": "Contacts",
  "customerAdmin.contactAccess.portalDescription": "Control portal access and login history.",
  "customerAdmin.contactAccess.portalTitle": "Portal & Access",
  "customerAdmin.contacts.empty": "No contacts have been added yet.",
  "customerAdmin.contacts.primaryBadge": "Primary contact",
  "customerAdmin.contacts.registerEyebrow": "Register",
  "customerAdmin.contacts.registerTitle": "Existing contacts",
  "customerAdmin.contacts.standardBadge": "Contact",
  "customerAdmin.detail.emptyBody": "Choose a customer from the list or create a new record.",
  "customerAdmin.detail.emptyTitle": "No customer selected yet",
  "customerAdmin.detail.notFoundBody": "The requested customer is not available in the current list. Select a customer from the list.",
  "customerAdmin.detail.notFoundTitle": "Customer not found",
  "customerAdmin.detail.newTitle": "Create customer",
  "customerAdmin.detail.workspaceLead": "Workspace lead",
  "customerAdmin.detail.workspaceTitle": "Customer workspace",
  "customerAdmin.addresses.addressLinkEmpty": "No shared addresses are available for this type.",
  "customerAdmin.addresses.editorEyebrow": "Editor",
  "customerAdmin.addresses.editorTitle": "Create or update an address link",
  "customerAdmin.addresses.empty": "No addresses linked yet.",
  "customerAdmin.addresses.linkLead": "Link an existing shared address to this customer.",
  "customerAdmin.addresses.linkBadge": "Linked address",
  "customerAdmin.addresses.defaultBadge": "Default address",
  "customerAdmin.addresses.registerEyebrow": "Register",
  "customerAdmin.addresses.registerTitle": "Address register",
  "customerAdmin.feedback.documentId": "Document ID",
  "customerAdmin.feedback.addressRequired": "An address link needs a selected address.",
  "customerAdmin.feedback.contactRequired": "A contact needs at least a name.",
  "customerAdmin.feedback.exportDownloadFailed": "Export created, download failed",
  "customerAdmin.feedback.exportDownloadFallback": "Use the document ID to download the file from the document library.",
  "customerAdmin.feedback.exportDownloadStarted": "The download started.",
  "customerAdmin.feedback.exportReady": "Customer export created",
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
  "customerAdmin.filters.additionalTitle": "Additional filters",
  "customerAdmin.filters.includeArchived": "Include archived customers",
  "customerAdmin.filters.search": "Search",
  "customerAdmin.filters.searchCustomers": "Search customers",
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
  "customerAdmin.tabs.orders": "Orders",
  "customerAdmin.tabs.portal": "Portal",
  "customerAdmin.title": "Customers",
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
    downloadCustomerDocument: apiMocks.downloadCustomerDocumentMock,
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

const CustomerOrdersTabStub = defineComponent({
  name: "CustomerOrdersTabStub",
  props: {
    canStartNewOrder: { type: Boolean, default: false },
  },
  emits: ["edit-order", "start-new-order"],
  template: `
    <div data-testid="customer-orders-tab-stub">
      <button
        v-if="canStartNewOrder"
        data-testid="customer-orders-new-order"
        type="button"
        @click="$emit('start-new-order')"
      >
        New order
      </button>
      <button
        data-testid="customer-orders-edit-order"
        type="button"
        @click="$emit('edit-order', 'order-1')"
      >
        Edit order
      </button>
    </div>
  `,
});

const baseReferenceData = {
  legal_forms: [],
  classifications: [
    {
      id: "classification-vip",
      code: "VIP",
      label: "VIP customer",
      description: null,
      is_active: true,
      status: "active",
      archived_at: null,
    },
  ],
  rankings: [],
  customer_statuses: [],
  branches: [
    {
      id: "branch-cgn",
      code: "CGN",
      name: "Cologne branch",
    },
  ],
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
    classification_lookup_id: "classification-vip",
    customer_status_lookup_id: null,
    default_branch_id: "branch-cgn",
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

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, reject, resolve };
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
        CustomerOrdersTab: CustomerOrdersTabStub,
        SicherPlanLoadingOverlay: SicherPlanLoadingOverlayStub,
        StatusBadge: StatusBadgeStub,
      },
    },
  });
  mountedWrappers.push(wrapper);
  await settle();
  return wrapper;
}

function mountCustomerAdminWithoutSettling() {
  const wrapper = mount(CustomerAdminView, {
    global: {
      stubs: {
        CustomerDashboardTab: CustomerDashboardTabStub,
        CustomerOrdersTab: CustomerOrdersTabStub,
        SicherPlanLoadingOverlay: SicherPlanLoadingOverlayStub,
        StatusBadge: StatusBadgeStub,
      },
    },
  });
  mountedWrappers.push(wrapper);
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
    routerReplaceMock.mockImplementation(async (location: { query?: Record<string, unknown> }) => {
      if (location?.query) {
        routeState.query = { ...location.query };
      }
    });
    showFeedbackToastMock.mockReset();
    createObjectUrlMock.mockClear();
    revokeObjectUrlMock.mockClear();
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: createObjectUrlMock,
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: revokeObjectUrlMock,
    });
    scrollIntoViewMock.mockReset();
    HTMLElement.prototype.scrollIntoView = scrollIntoViewMock;
    intersectionObserverCallback = null;
    class MockIntersectionObserver {
      callback: IntersectionObserverCallback;
      constructor(callback: IntersectionObserverCallback) {
        this.callback = callback;
        intersectionObserverCallback = (entries) => this.callback(entries as IntersectionObserverEntry[], this as unknown as IntersectionObserver);
      }
      disconnect() {}
      observe() {}
      unobserve() {}
      takeRecords() {
        return [];
      }
      root = null;
      rootMargin = "";
      thresholds = [];
    }
    Object.defineProperty(window, "IntersectionObserver", {
      configurable: true,
      value: MockIntersectionObserver,
    });

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
    apiMocks.downloadCustomerDocumentMock.mockReset();
    apiMocks.downloadCustomerDocumentMock.mockResolvedValue({
      blob: new Blob(["customer_number,name\nK-0001,Alpha Security\n"], { type: "text/csv" }),
      fileName: "customers.csv",
    });
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
      job_id: "job-1",
      row_count: 1,
      tenant_id: "tenant-1",
      version_no: 1,
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

  it("lands on a list-first customer page without auto-opening the first customer", async () => {
    const wrapper = await mountCustomerAdmin();

    expect(wrapper.find('[data-testid="customer-list-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-detail-only-mode"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-page-context-label"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-page-context-label-full-title"]').exists()).toBe(false);
    expect(routeState.meta.title).toBe("Customers");
    expect(wrapper.find('[data-testid="customer-list-section"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-search-select"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-advanced-filters-open"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-header-export"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-header-new-customer"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-section"] input[type="checkbox"]').exists()).toBe(false);
    expect(wrapper.findAll('[data-testid="customer-list-row"]')).toHaveLength(1);
    expect(wrapper.get('[data-testid="customer-list-row-name"]').text()).toContain("Alpha Security");
    expect(wrapper.get('[data-testid="customer-list-row-number"]').text()).toContain("K-0001");
    expect(wrapper.get('[data-testid="customer-list-row"]').text()).toContain("Cologne branch");
    expect(wrapper.get('[data-testid="customer-list-row"]').text()).toContain("VIP customer");
    expect(wrapper.find('[data-testid="customer-list-row-status"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-detail-workspace"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-detail-tabs"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-dashboard-tab-stub"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-detail-empty-state"]').exists()).toBe(false);

    const searchInput = wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]');
    await searchInput.setValue("Rhein");

    expect(searchInput.element.value).toBe("Rhein");
    expect(wrapper.find('[data-testid="customer-search-suggestions"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-search-results-modal"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain("Use the sidebar customer links to open a customer dashboard.");
  });

  it("opens a customer workspace only after clicking a customer row and updates the selected route", async () => {
    const wrapper = await mountCustomerAdmin();
    apiMocks.getCustomerMock.mockClear();
    routerReplaceMock.mockClear();

    await wrapper.get('[data-testid="customer-list-row"]').trigger("click");
    await settle();

    expect(apiMocks.getCustomerMock).toHaveBeenCalledWith("tenant-1", "customer-default", "token-1");
    expect(routerReplaceMock).toHaveBeenCalledWith(
      expect.objectContaining({
        query: expect.objectContaining({
          customer_id: "customer-default",
          tab: "dashboard",
        }),
      }),
    );
    expect(wrapper.find('[data-testid="customer-detail-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-section"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-detail-workspace"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-page-context-label"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-page-context-label-full-title"]').exists()).toBe(false);
    expect(routeState.meta.title).toBe("Alpha Security");
    expect(routeState.meta.title).not.toBe("Customers");
    expect(`${routeState.meta.title}`).not.toContain("...");
    expect(wrapper.get('[data-testid="customer-detail-title"]').text()).toBe("Alpha Security");
    expect(wrapper.get('[data-testid="customer-detail-title"]').classes()).toContain("customer-admin-detail-title");
    expect(wrapper.get('[data-testid="customer-detail-workspace"]').text()).toContain("Workspace lead");
    expect(wrapper.get('[data-testid="customer-back-to-list"]').classes()).toContain("customer-admin-back-button");
    expect(wrapper.get('[data-testid="customer-detail-workspace"] .status-badge-stub').text()).toBe("active");
    expect(wrapper.get('[data-testid="customer-dashboard-tab-stub"]').text()).toContain("customer-default");
  });

  it("truncates long customer names only in the upper context label while preserving the full detail title", async () => {
    const longName = "RheinForum International Security Services Operations GmbH West Region";
    routeState.query = {
      customer_id: "customer-default",
      tab: "dashboard",
    };
    apiMocks.listCustomersMock.mockResolvedValueOnce([
      buildCustomerListItem("customer-default", longName, "K-0001", "active"),
    ]);
    apiMocks.getCustomerMock.mockResolvedValueOnce(buildCustomerRead("customer-default", longName, "K-0001"));

    const wrapper = await mountCustomerAdmin();

    expect(wrapper.find('[data-testid="customer-page-context-label"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-page-context-label-full-title"]').exists()).toBe(false);
    expect(routeState.meta.title).toBe("RheinForum International Security...");
    expect(routeState.meta.title).not.toBe(longName);
    expect(wrapper.get('[data-testid="customer-detail-title"]').text()).toBe(longName);
  });

  it("filters visible customer rows directly by name without suggestions or modal", async () => {
    apiMocks.listCustomersMock.mockResolvedValueOnce([
      buildCustomerListItem("customer-default", "Alpha Security", "K-0001", "active"),
      buildCustomerListItem("customer-rhein", "RheinForum Köln", "K-1000", "active"),
      buildCustomerListItem("customer-hafen", "HafenKontor Köln", "K-1001", "active"),
    ]);
    const wrapper = await mountCustomerAdmin();
    apiMocks.listCustomersMock.mockClear();

    const searchInput = wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]');
    expect(wrapper.findAll('[data-testid="customer-list-row"]')).toHaveLength(3);

    await searchInput.setValue("Rhein");
    await settle();

    expect(apiMocks.listCustomersMock).not.toHaveBeenCalled();
    expect(wrapper.findAll('[data-testid="customer-list-row"]')).toHaveLength(1);
    expect(wrapper.text()).toContain("RheinForum Köln");
    expect(wrapper.text()).not.toContain("Alpha Security");
    expect(wrapper.find('[data-testid="customer-search-suggestions"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-search-results-modal"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain("Use the sidebar customer links to open a customer dashboard.");
  });

  it("filters visible customer rows by customer number and restores the full list when cleared", async () => {
    apiMocks.listCustomersMock.mockResolvedValueOnce([
      buildCustomerListItem("customer-default", "Alpha Security", "K-0001", "active"),
      buildCustomerListItem("customer-rhein", "RheinForum Köln", "K-1000", "active"),
      buildCustomerListItem("customer-hafen", "HafenKontor Köln", "K-1001", "active"),
    ]);
    const wrapper = await mountCustomerAdmin();
    apiMocks.listCustomersMock.mockClear();

    const searchInput = wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]');
    await searchInput.setValue("K-1001");
    await settle();

    expect(apiMocks.listCustomersMock).not.toHaveBeenCalled();
    expect(wrapper.findAll('[data-testid="customer-list-row"]')).toHaveLength(1);
    expect(wrapper.get('[data-testid="customer-list-row-name"]').text()).toContain("HafenKontor Köln");

    await searchInput.setValue("");
    await settle();

    expect(wrapper.findAll('[data-testid="customer-list-row"]')).toHaveLength(3);
    expect(wrapper.find('[data-testid="customer-search-suggestions"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-search-results-modal"]').exists()).toBe(false);
  });

  it("opens advanced filters with synchronized search and applies filters to the list", async () => {
    const wrapper = await mountCustomerAdmin();
    apiMocks.listCustomersMock.mockClear();
    apiMocks.getCustomerMock.mockClear();

    await wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]').setValue("Rhein");
    await wrapper.get('[data-testid="customer-advanced-filters-open"]').trigger("click");
    await settle();

    expect(wrapper.find('[data-testid="customer-advanced-filters-dialog"]').exists()).toBe(true);
    expect(wrapper.get<HTMLInputElement>('[data-testid="customer-advanced-filters-search"]').element.value).toBe("Rhein");
    await wrapper.get<HTMLSelectElement>('[data-testid="customer-advanced-filters-status"]').setValue("active");
    await wrapper.get<HTMLSelectElement>('[data-testid="customer-advanced-filters-default-branch"]').setValue("branch-cgn");
    await wrapper.get<HTMLInputElement>('[data-testid="customer-advanced-filters-include-archived"]').setValue(true);
    await wrapper.get('[data-testid="customer-advanced-filters-dialog"] form').trigger("submit");
    await settle();

    expect(apiMocks.listCustomersMock.mock.calls.at(-1)?.[2]).toMatchObject({
      default_branch_id: "branch-cgn",
      include_archived: true,
      lifecycle_status: "active",
      search: "Rhein",
    });
    expect(apiMocks.getCustomerMock).not.toHaveBeenCalled();
    expect(wrapper.get('[data-testid="customer-list-row-name"]').text()).toContain("RheinForum Köln");
    expect(wrapper.find('[data-testid="customer-advanced-filters-dialog"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-detail-workspace"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-dashboard-tab-stub"]').exists()).toBe(false);
  });

  it("closes advanced filters on cancel without applying staged filters", async () => {
    const wrapper = await mountCustomerAdmin();
    apiMocks.listCustomersMock.mockClear();

    await wrapper.get('[data-testid="customer-advanced-filters-open"]').trigger("click");
    await settle();
    await wrapper.get<HTMLSelectElement>('[data-testid="customer-advanced-filters-status"]').setValue("archived");
    await wrapper.get('[data-testid="customer-advanced-filters-cancel"]').trigger("click");
    await settle();

    expect(wrapper.find('[data-testid="customer-advanced-filters-dialog"]').exists()).toBe(false);
    expect(apiMocks.listCustomersMock).not.toHaveBeenCalled();
  });

  it("closes advanced filters with Escape like the existing customer modals", async () => {
    const wrapper = await mountCustomerAdmin();

    await wrapper.get('[data-testid="customer-advanced-filters-open"]').trigger("click");
    await settle();
    expect(wrapper.find('[data-testid="customer-advanced-filters-dialog"]').exists()).toBe(true);

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await settle();

    expect(wrapper.find('[data-testid="customer-advanced-filters-dialog"]').exists()).toBe(false);
  });

  it("shows the local empty state for unknown search values without stale rows or modal results", async () => {
    apiMocks.listCustomersMock.mockResolvedValueOnce([
      buildCustomerListItem("customer-default", "Alpha Security", "K-0001", "active"),
      buildCustomerListItem("customer-rhein", "RheinForum Köln", "K-1000", "active"),
    ]);
    const wrapper = await mountCustomerAdmin();
    apiMocks.listCustomersMock.mockClear();

    const searchInput = wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]');
    await searchInput.setValue("Rhein");
    await settle();
    expect(wrapper.text()).toContain("RheinForum Köln");

    await searchInput.setValue("unknown");
    await settle();

    expect(apiMocks.listCustomersMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="customer-list-empty-state"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-search-suggestions"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-search-results-modal"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain("RheinForum Köln");
  });

  it("passes include_archived through advanced filter requests", async () => {
    const wrapper = await mountCustomerAdmin();
    apiMocks.listCustomersMock.mockClear();

    await wrapper.get('[data-testid="customer-advanced-filters-open"]').trigger("click");
    await settle();
    const includeArchived = wrapper.get<HTMLInputElement>('[data-testid="customer-advanced-filters-include-archived"]');
    await includeArchived.setValue(true);
    await wrapper.get<HTMLInputElement>('[data-testid="customer-advanced-filters-search"]').setValue("Rhein");
    await wrapper.get('[data-testid="customer-advanced-filters-dialog"] form').trigger("submit");
    await settle();

    expect(apiMocks.listCustomersMock.mock.calls.at(-1)?.[2]).toMatchObject({
      search: "Rhein",
      include_archived: true,
    });

    await wrapper.get('[data-testid="customer-advanced-filters-open"]').trigger("click");
    await settle();
    await wrapper.get<HTMLInputElement>('[data-testid="customer-advanced-filters-include-archived"]').setValue(false);
    await wrapper.get('[data-testid="customer-advanced-filters-dialog"] form').trigger("submit");
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

  it("shows the full workspace overlay only during the initial blocking customer bootstrap", async () => {
    const initialList = deferred<ReturnType<typeof buildCustomerListItem>[]>();
    apiMocks.listCustomersMock.mockReturnValue(initialList.promise);

    const wrapper = mountCustomerAdminWithoutSettling();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-loading-overlay"]').attributes("data-busy")).toBe("true");

    initialList.resolve([buildCustomerListItem("customer-default", "Alpha Security", "K-0001", "active")]);
    await settle();

    expect(wrapper.get('[data-testid="customer-loading-overlay"]').attributes("data-busy")).toBe("false");
    expect(wrapper.find('[data-testid="customer-list-row"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-detail-workspace"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-dashboard-tab-stub"]').exists()).toBe(false);
  });

  it("does not activate the full overlay for background search, same-record detail refresh, or session reconciliation", async () => {
    apiMocks.listCustomersMock.mockResolvedValueOnce([
      buildCustomerListItem("customer-default", "Alpha Security", "K-0001", "active"),
      buildCustomerListItem("customer-rhein", "RheinForum Köln", "K-1000", "active"),
    ]);
    const wrapper = await mountCustomerAdmin();
    expect(wrapper.get('[data-testid="customer-loading-overlay"]').attributes("data-busy")).toBe("false");

    apiMocks.listCustomersMock.mockClear();
    const searchInput = wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]');
    await searchInput.setValue("Rhein");
    await settle();
    expect(wrapper.get('[data-testid="customer-loading-overlay"]').attributes("data-busy")).toBe("false");
    expect(apiMocks.listCustomersMock).not.toHaveBeenCalled();

    const refreshedCustomer = deferred<ReturnType<typeof buildCustomerRead>>();
    apiMocks.getCustomerMock.mockReturnValueOnce(refreshedCustomer.promise);
    await wrapper.get('[data-testid="customer-list-row"]').trigger("click");
    await flushPromises();
    expect(wrapper.get('[data-testid="customer-loading-overlay"]').attributes("data-busy")).toBe("false");
    refreshedCustomer.resolve(buildCustomerRead("customer-rhein", "RheinForum Köln", "K-1000"));
    await settle();
    expect(wrapper.find('[data-testid="customer-detail-workspace"]').exists()).toBe(true);

    authStoreState.isSessionResolving = true;
    await settle();
    expect(wrapper.get('[data-testid="customer-loading-overlay"]').attributes("data-busy")).toBe("false");
    expect(wrapper.find('[data-testid="customer-detail-workspace"]').exists()).toBe(true);
    authStoreState.isSessionResolving = false;
  });

  it("shows a controlled empty state for an invalid customer_id without auto-selecting another customer", async () => {
    routeState.query = {
      customer_id: "customer-missing",
      tab: "dashboard",
    };
    const wrapper = await mountCustomerAdmin();

    expect(wrapper.find('[data-testid="customer-detail-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-section"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-dashboard-tab-stub"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-detail-empty-state"]').text()).toContain("Customer not found");
    expect(wrapper.find('[data-testid="customer-back-to-list"]').exists()).toBe(true);
  });

  it("returns from an invalid customer route to the list-only fallback", async () => {
    routeState.query = {
      customer_id: "customer-missing",
      tab: "dashboard",
    };
    const wrapper = await mountCustomerAdmin();

    await wrapper.get('[data-testid="customer-back-to-list"]').trigger("click");
    await settle();

    expect(routerReplaceMock).toHaveBeenCalledWith({ query: {} });
    expect(wrapper.find('[data-testid="customer-list-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-section"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-detail-workspace"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-dashboard-tab-stub"]').exists()).toBe(false);
  });

  it("returns to list-first state when customer_id is removed from the route", async () => {
    const wrapper = await mountSelectedCustomer("dashboard");
    expect(wrapper.find('[data-testid="customer-dashboard-tab-stub"]').exists()).toBe(true);

    routeState.query = {};
    await settle();

    expect(wrapper.find('[data-testid="customer-list-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-row"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-detail-workspace"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-dashboard-tab-stub"]').exists()).toBe(false);
  });

  it("returns from selected detail mode to list-only mode through the back action", async () => {
    const wrapper = await mountSelectedCustomer("dashboard");

    expect(wrapper.find('[data-testid="customer-detail-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-section"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-back-to-list"]').classes()).toContain("customer-admin-back-button");

    await wrapper.get('[data-testid="customer-back-to-list"]').trigger("click");
    await settle();

    expect(routerReplaceMock).toHaveBeenCalledWith({ query: {} });
    expect(wrapper.find('[data-testid="customer-list-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-section"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-detail-workspace"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-page-context-label"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-page-context-label-full-title"]').exists()).toBe(false);
    expect(routeState.meta.title).toBe("Customers");
  });

  it("does not activate the full overlay while nested contact saves and same-customer refreshes are pending", async () => {
    const wrapper = await mountSelectedCustomer("contact_access");
    expect(wrapper.get('[data-testid="customer-loading-overlay"]').attributes("data-busy")).toBe("false");

    const contactPanel = wrapper.get('[data-testid="customer-contacts-access-section-contacts"]');
    await contactPanel.get('[data-testid="customer-contact-register-create"]').trigger("click");
    await settle();
    const contactModal = wrapper.get('[data-testid="customer-contact-editor-modal"]');
    await contactModal.get<HTMLInputElement>('input[required]').setValue("Ada Lovelace");
    await contactModal.get<HTMLInputElement>('input[type="email"]').setValue("ada@example.test");

    const contactSave = deferred<Record<string, never>>();
    apiMocks.createCustomerContactMock.mockReturnValueOnce(contactSave.promise);
    await contactModal.get("form").trigger("submit");
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-loading-overlay"]').attributes("data-busy")).toBe("false");
    expect(wrapper.find('[data-testid="customer-tab-panel-contact-access"]').exists()).toBe(true);

    const detailRefresh = deferred<ReturnType<typeof buildCustomerRead>>();
    apiMocks.getCustomerMock.mockReturnValueOnce(detailRefresh.promise);
    contactSave.resolve({});
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-loading-overlay"]').attributes("data-busy")).toBe("false");
    expect(wrapper.find('[data-testid="customer-tab-panel-contact-access"]').exists()).toBe(true);

    detailRefresh.resolve(buildCustomerRead("customer-default", "Alpha Security", "K-0001"));
    await settle();

    expect(wrapper.get('[data-testid="customer-loading-overlay"]').attributes("data-busy")).toBe("false");
    expect(wrapper.find('[data-testid="customer-tab-panel-contact-access"]').exists()).toBe(true);
  });

  it("keeps route-based customer selection working in detail-only mode", async () => {
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

    const wrapper = await mountCustomerAdmin();

    expect(apiMocks.getCustomerMock).toHaveBeenCalledWith("tenant-1", "customer-rhein", "token-1");
    expect(wrapper.find('[data-testid="customer-detail-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-section"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-page-context-label"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-page-context-label-full-title"]').exists()).toBe(false);
    expect(routeState.meta.title).toBe("RheinForum Köln");
    expect(wrapper.get('[data-testid="customer-dashboard-tab-stub"]').text()).toContain("customer-rhein");
  });

  it("keeps export and new customer actions in list-only mode", async () => {
    const wrapper = await mountCustomerAdmin();
    apiMocks.exportCustomersMock.mockClear();

    const filterToolbar = wrapper.get(".customer-admin-filter-toolbar");
    expect(filterToolbar.text()).toContain("Advanced filters");
    expect(filterToolbar.text()).not.toContain("CSV export");
    expect(filterToolbar.text()).not.toContain("New customer");

    await wrapper.get('[data-testid="customer-list-header-export"]').trigger("click");
    await settle();
    expect(apiMocks.exportCustomersMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        include_archived: false,
        tenant_id: "tenant-1",
      }),
    );
    expect(apiMocks.downloadCustomerDocumentMock).toHaveBeenCalledWith(
      "tenant-1",
      "doc-1",
      1,
      "token-1",
      "customers.csv",
    );
    expect(createObjectUrlMock).toHaveBeenCalledWith(expect.any(Blob));
    expect(revokeObjectUrlMock).toHaveBeenCalledWith("blob:customer-export");
    expect(showFeedbackToastMock).toHaveBeenCalledWith(expect.objectContaining({
      message: expect.stringContaining("The download started."),
      title: "Customer export created",
      tone: "success",
    }));

    await wrapper.get('[data-testid="customer-list-header-new-customer"]').trigger("click");
    await settle();
    expect(wrapper.find('[data-testid="customer-detail-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-section"]').exists()).toBe(false);
    expect(wrapper.text()).toContain("Create customer");
  });

  it("shows a clear fallback message when customer export download fails after creation", async () => {
    const wrapper = await mountCustomerAdmin();
    apiMocks.downloadCustomerDocumentMock.mockRejectedValueOnce(new Error("download failed"));
    showFeedbackToastMock.mockClear();

    await wrapper.get('[data-testid="customer-list-header-export"]').trigger("click");
    await settle();

    expect(apiMocks.exportCustomersMock).toHaveBeenCalled();
    expect(apiMocks.downloadCustomerDocumentMock).toHaveBeenCalled();
    expect(createObjectUrlMock).not.toHaveBeenCalled();
    expect(showFeedbackToastMock).toHaveBeenCalledWith(expect.objectContaining({
      message: expect.stringContaining("Use the document ID to download the file from the document library."),
      title: "Export created, download failed",
      tone: "warning",
    }));
    expect(showFeedbackToastMock.mock.calls.at(-1)?.[0].message).toContain("doc-1");
  });

  it("exports and downloads with active search and advanced filter state", async () => {
    const wrapper = await mountCustomerAdmin();

    await wrapper.get<HTMLInputElement>('[data-testid="customer-search-select-input"]').setValue("Rhein");
    await wrapper.get('[data-testid="customer-advanced-filters-open"]').trigger("click");
    await settle();
    await wrapper.get<HTMLInputElement>('[data-testid="customer-advanced-filters-include-archived"]').setValue(true);
    await wrapper.get('[data-testid="customer-advanced-filters-dialog"] form').trigger("submit");
    await settle();

    apiMocks.exportCustomersMock.mockClear();
    apiMocks.downloadCustomerDocumentMock.mockClear();

    await wrapper.get('[data-testid="customer-list-header-export"]').trigger("click");
    await settle();

    expect(apiMocks.exportCustomersMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        include_archived: true,
        search: "Rhein",
        tenant_id: "tenant-1",
      }),
    );
    expect(apiMocks.downloadCustomerDocumentMock).toHaveBeenCalledWith(
      "tenant-1",
      "doc-1",
      1,
      "token-1",
      "customers.csv",
    );
  });

  it("returns from new customer cancel to the list-first state when no selected route exists", async () => {
    const wrapper = await mountCustomerAdmin();

    await clickButtonByText(wrapper, "New customer");
    await settle();
    expect(wrapper.find('[data-testid="customer-detail-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-section"]').exists()).toBe(false);
    expect(wrapper.text()).toContain("Create customer");

    await clickButtonByText(wrapper, "Cancel");
    await settle();

    expect(wrapper.find('[data-testid="customer-list-only-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-list-row"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-detail-workspace"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-dashboard-tab-stub"]').exists()).toBe(false);
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

  it("renders contact access with employee-overview style section nav and one section container per area", async () => {
    const wrapper = await mountSelectedCustomer("contact_access");

    const html = wrapper.html();
    const contactAccessPanel = wrapper.get('[data-testid="customer-tab-panel-contact-access"]');
    const onePageLayout = wrapper.get('[data-testid="customer-contacts-access-layout"]');
    const nav = wrapper.get('[data-testid="customer-contacts-access-nav"]');
    const contentShell = onePageLayout.get(".customer-admin-contact-access-content");
    const contactsSection = wrapper.get('[data-testid="customer-contacts-access-section-contacts"]');
    const addressesSection = wrapper.get('[data-testid="customer-contacts-access-section-addresses"]');
    const portalSection = wrapper.get('[data-testid="customer-contacts-access-section-portal"]');
    const directLayoutChildren = Array.from(onePageLayout.element.children).map((child) =>
      child.getAttribute("data-testid"),
    );
    expect(directLayoutChildren).toEqual([
      "customer-contacts-access-nav",
      null,
    ]);
    expect(contentShell.classes()).toContain("customer-admin-contact-access-content");
    expect(nav.text()).toContain("Contacts");
    expect(nav.text()).toContain("Addresses");
    expect(nav.text()).toContain("Portal & Access");
    expect(wrapper.findAll(".customer-admin-contact-access-nav__link")).toHaveLength(3);
    expect(wrapper.get('[data-testid="customer-contacts-access-nav-contacts"]').attributes("aria-current")).toBe("true");
    expect(contactsSection.classes()).toContain("customer-admin-contact-access-section-card");
    expect(addressesSection.classes()).toContain("customer-admin-contact-access-section-card");
    expect(portalSection.classes()).toContain("customer-admin-contact-access-section-card");
    expect(contactsSection.text()).toContain("Contacts");
    expect(contactsSection.text()).toContain("Manage customer contact persons.");
    expect(addressesSection.text()).toContain("Addresses");
    expect(addressesSection.text()).toContain("Link and maintain customer addresses.");
    expect(portalSection.text()).toContain("Portal & Access");
    expect(portalSection.text()).toContain("Control portal access and login history.");
    expect(contactAccessPanel.findAll(".customer-admin-editor-intro")).toHaveLength(0);
    expect(contactAccessPanel.text()).not.toContain("Contact maintenance");
    expect(contactAccessPanel.text()).not.toContain("Address links");
    expect(contactAccessPanel.text()).not.toContain("Portal controls and releases");
    expect(wrapper.find('[data-testid="customer-tab-panel-contacts"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-tab-panel-addresses"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-tab-panel-portal"]').exists()).toBe(true);
    expect(contactsSection.find('[data-testid="customer-tab-panel-contacts"]').exists()).toBe(true);
    expect(addressesSection.find('[data-testid="customer-tab-panel-addresses"]').exists()).toBe(true);
    expect(portalSection.find('[data-testid="customer-tab-panel-portal"]').exists()).toBe(true);
    expect(contactsSection.find('[data-testid="customer-tab-panel-addresses"]').exists()).toBe(false);
    expect(addressesSection.find('[data-testid="customer-tab-panel-portal"]').exists()).toBe(false);
    expect(portalSection.find('[data-testid="customer-tab-panel-contacts"]').exists()).toBe(false);
    expect(contactsSection.findAll(".customer-admin-form-section")).toHaveLength(1);
    expect(addressesSection.findAll(".customer-admin-form-section")).toHaveLength(1);
    expect(portalSection.findAll(".customer-admin-form-section").length).toBeGreaterThanOrEqual(2);
    expect(contactsSection.find('[data-testid="customer-contact-editor-modal"]').exists()).toBe(false);
    expect(contactsSection.text()).toContain("Create new contact");
    expect(addressesSection.find('[data-testid="customer-address-editor-modal"]').exists()).toBe(false);
    expect(addressesSection.text()).toContain("Create new address");
    expect(html.indexOf('data-testid="customer-tab-panel-contact-access"')).toBeLessThan(
      html.indexOf('data-testid="customer-contacts-access-layout"'),
    );
    expect(html.indexOf('data-testid="customer-contacts-access-section-contacts"')).toBeLessThan(
      html.indexOf('data-testid="customer-contacts-access-section-addresses"'),
    );
    expect(html.indexOf('data-testid="customer-contacts-access-section-addresses"')).toBeLessThan(
      html.indexOf('data-testid="customer-contacts-access-section-portal"'),
    );

    await wrapper.get('[data-testid="customer-contacts-access-nav-portal"]').trigger("click");
    await settle();
    expect(wrapper.get('[data-testid="customer-contacts-access-nav-portal"]').attributes("aria-current")).toBe("true");
    expect(onePageLayout.get(".customer-admin-contact-access-content").classes()).toContain("customer-admin-contact-access-content");
    expect(onePageLayout.find('[data-testid="customer-contacts-access-nav"]').exists()).toBe(true);
  });

  it("keeps the left nav interactive like Employees Overview on click", async () => {
    const wrapper = await mountSelectedCustomer("contact_access");

    await wrapper.get('[data-testid="customer-contacts-access-nav-addresses"]').trigger("click");
    await settle();

    expect(wrapper.get('[data-testid="customer-contacts-access-nav-addresses"]').attributes("aria-current")).toBe("true");
  });

  it("renders Orders as the customer detail tab label and no longer shows Plans", async () => {
    const wrapper = await mountSelectedCustomer("orders");

    const ordersTab = wrapper.get('[data-testid="customer-tab-orders"]');
    expect(ordersTab.text()).toBe("Orders");
    expect(ordersTab.classes()).toContain("active");
    expect(wrapper.find('[data-testid="customer-tab-plans"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-orders-tab-stub"]').exists()).toBe(true);
    expect(wrapper.text()).not.toContain("Plans");
  });

  it("routes the Orders tab New order CTA to the customer order workspace with customer context", async () => {
    const wrapper = await mountSelectedCustomer("orders");

    await wrapper.get('[data-testid="customer-orders-new-order"]').trigger("click");
    await settle();

    expect(routerPushMock).toHaveBeenCalledWith({
      name: "SicherPlanCustomerOrderWorkspace",
      query: {
        customer_id: "customer-default",
      },
    });
    expect(routerPushMock.mock.calls.at(-1)?.[0]).not.toMatchObject({
      path: "/admin/customers/new-plan",
    });
    expect(routerPushMock.mock.calls.at(-1)?.[0]?.query).not.toHaveProperty("order_id");
    expect(wrapper.text()).toContain("New order");
    expect(wrapper.text()).not.toContain("New plan");
  });

  it("routes explicit order edits to the customer order workspace with order context", async () => {
    const wrapper = await mountSelectedCustomer("orders");

    await wrapper.get('[data-testid="customer-orders-edit-order"]').trigger("click");
    await settle();

    expect(routerPushMock).toHaveBeenCalledWith({
      name: "SicherPlanCustomerOrderWorkspace",
      query: {
        customer_id: "customer-default",
        order_id: "order-1",
        order_mode: "edit",
        step: "order-details",
      },
    });
    expect(routerPushMock.mock.calls.at(-1)?.[0]).not.toMatchObject({
      path: "/admin/customers/new-plan",
    });
  });

  it("keeps contact creation working from the merged contact access tab", async () => {
    const wrapper = await mountSelectedCustomer("contact_access");

    const contactPanel = wrapper.get('[data-testid="customer-contacts-access-section-contacts"]');
    expect(contactPanel.text()).toContain("Mira Contact");
    await contactPanel.get('[data-testid="customer-contact-register-create"]').trigger("click");
    await settle();
    const modal = wrapper.get('[data-testid="customer-contact-editor-modal"]');
    await modal.get<HTMLInputElement>('input[required]').setValue("Ada Lovelace");
    await modal.get<HTMLInputElement>('input[type="email"]').setValue("ada@example.test");
    await modal.get("form").trigger("submit");
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
    expect(wrapper.find('[data-testid="customer-contact-editor-modal"]').exists()).toBe(false);
  });

  it("opens the same contact editor modal for edit mode and keeps validation errors inside it", async () => {
    const wrapper = await mountSelectedCustomer("contact_access");

    const contactPanel = wrapper.get('[data-testid="customer-contacts-access-section-contacts"]');
    await clickButtonByTextWithin(contactPanel, "Edit");
    await settle();

    const modal = wrapper.get('[data-testid="customer-contact-editor-modal"]');
    const inputs = modal.findAll("input");
    expect(inputs[0]!.element.value).toBe("Mira Contact");

    await inputs[0]!.setValue("");
    await modal.get("form").trigger("submit");
    await settle();

    expect(wrapper.get('[data-testid="customer-contact-editor-error"]').text()).toContain("A contact needs at least a name.");
    expect(wrapper.find('[data-testid="customer-contact-editor-modal"]').exists()).toBe(true);

    await inputs[0]!.setValue("Mira Contact Updated");
    await modal.get("form").trigger("submit");
    await settle();

    expect(apiMocks.updateCustomerContactMock).toHaveBeenCalledWith(
      "tenant-1",
      "customer-default",
      "contact-1",
      "token-1",
      expect.objectContaining({
        full_name: "Mira Contact Updated",
        version_no: 1,
      }),
    );
    expect(wrapper.find('[data-testid="customer-contact-editor-modal"]').exists()).toBe(false);
  });

  it("keeps address creation and shared-address modal behavior working from contact access", async () => {
    const wrapper = await mountSelectedCustomer("contact_access");

    const addressPanel = wrapper.get('[data-testid="customer-contacts-access-section-addresses"]');
    expect(addressPanel.text()).toContain("Alte Strasse 1");
    await addressPanel.get('[data-testid="customer-address-register-create"]').trigger("click");
    await settle();
    const addressModal = wrapper.get('[data-testid="customer-address-editor-modal"]');
    await addressModal.get<HTMLSelectElement>("select").setValue("address-option-2");
    await addressModal.get("form").trigger("submit");
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
    expect(wrapper.find('[data-testid="customer-address-editor-modal"]').exists()).toBe(false);

    await addressPanel.get('[data-testid="customer-address-register-create"]').trigger("click");
    await settle();
    const addressEditModal = wrapper.get('[data-testid="customer-address-editor-modal"]');
    await clickButtonByTextWithin(addressEditModal, "Create shared address");
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

  it("opens the same address editor modal for edit mode and keeps validation errors inside it", async () => {
    const wrapper = await mountSelectedCustomer("contact_access");

    const addressPanel = wrapper.get('[data-testid="customer-contacts-access-section-addresses"]');
    await clickButtonByTextWithin(addressPanel, "Edit");
    await settle();

    const modal = wrapper.get('[data-testid="customer-address-editor-modal"]');
    const select = modal.get("select");
    expect((select.element as HTMLSelectElement).value).toBe("address-option-1");

    await select.setValue("");
    await modal.get("form").trigger("submit");
    await settle();

    expect(wrapper.get('[data-testid="customer-address-editor-error"]').text()).toContain("An address link needs a selected address.");
    expect(wrapper.find('[data-testid="customer-address-editor-modal"]').exists()).toBe(true);

    await select.setValue("address-option-1");
    await modal.get("form").trigger("submit");
    await settle();

    expect(apiMocks.updateCustomerAddressMock).toHaveBeenCalledWith(
      "tenant-1",
      "customer-default",
      "customer-address-1",
      "token-1",
      expect.objectContaining({
        address_id: "address-option-1",
        version_no: 1,
      }),
    );
    expect(wrapper.find('[data-testid="customer-address-editor-modal"]').exists()).toBe(false);
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

    const portalCard = wrapper.get('[data-testid="customer-contacts-access-section-portal"]');
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

  it("normalizes legacy plans route state to the Orders tab without a blank panel", async () => {
    const wrapper = await mountSelectedCustomer("plans");

    expect(wrapper.get('[data-testid="customer-tab-orders"]').classes()).toContain("active");
    expect(wrapper.find('[data-testid="customer-orders-tab-stub"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-tab-plans"]').exists()).toBe(false);
    expect(wrapper.text()).toContain("Orders");
    expect(wrapper.text()).not.toContain("Plans");
  });
});
