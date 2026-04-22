// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent } from "vue";

import CustomerOrdersTab from "../../components/customers/CustomerOrdersTab.vue";

const planningOrdersMocks = vi.hoisted(() => ({
  getCustomerOrderMock: vi.fn(),
  listCustomerOrdersMock: vi.fn(),
  listPlanningRecordsMock: vi.fn(),
}));

const translations: Record<string, string> = {
  "customerAdmin.actions.newOrder": "New order",
  "customerAdmin.filters.search": "Search",
  "customerAdmin.orders.emptyBody": "No matching orders are currently available for this customer.",
  "customerAdmin.orders.emptyTitle": "No orders found",
  "customerAdmin.orders.errorBody": "Customer orders are currently unavailable.",
  "customerAdmin.orders.errorTitle": "Orders could not be loaded",
  "customerAdmin.orders.rawReleaseState": "Release state",
  "customerAdmin.orders.detail.attachments": "Attachments",
  "customerAdmin.orders.detail.close": "Close",
  "customerAdmin.orders.detail.createdAt": "Created",
  "customerAdmin.orders.detail.customer": "Customer",
  "customerAdmin.orders.detail.errorBody": "Order details could not be loaded.",
  "customerAdmin.orders.detail.errorTitle": "Order details unavailable",
  "customerAdmin.orders.detail.eyebrow": "Order preview",
  "customerAdmin.orders.detail.loading": "Loading order details...",
  "customerAdmin.orders.detail.noAttachments": "No attachments linked.",
  "customerAdmin.orders.detail.notes": "Notes",
  "customerAdmin.orders.detail.patrolRoute": "Patrol route",
  "customerAdmin.orders.detail.releasedAt": "Released at",
  "customerAdmin.orders.detail.requirementType": "Requirement type",
  "customerAdmin.orders.detail.securityConcept": "Security concept",
  "customerAdmin.orders.detail.serviceCategory": "Service category",
  "customerAdmin.orders.detail.serviceFrom": "Service from",
  "customerAdmin.orders.detail.serviceTo": "Service to",
  "customerAdmin.orders.detail.title": "Order details",
  "customerAdmin.orders.detail.updatedAt": "Updated",
  "customerAdmin.orders.registrationDate": "Registered",
  "customerAdmin.orders.releaseDate": "Released",
  "customerAdmin.orders.searchPlaceholder": "Search by order title or order number",
  "customerAdmin.orders.sort.createdAtAsc": "Registration date asc",
  "customerAdmin.orders.sort.createdAtDesc": "Registration date desc",
  "customerAdmin.orders.sort.executionEndAsc": "Execution end asc",
  "customerAdmin.orders.sort.executionEndDesc": "Execution end desc",
  "customerAdmin.orders.sort.executionStartAsc": "Execution start asc",
  "customerAdmin.orders.sort.executionStartDesc": "Execution start desc",
  "customerAdmin.orders.sort.releaseDateAsc": "Release date asc",
  "customerAdmin.orders.sort.releaseDateDesc": "Release date desc",
  "customerAdmin.orders.sort.status": "Status",
  "customerAdmin.orders.sortLabel": "Sort",
};

vi.mock("@/i18n", () => ({
  useI18n: () => ({
    locale: { value: "de-DE" },
    t: (key: string) => translations[key] ?? key,
  }),
}));

vi.mock("@/api/planningOrders", async () => {
  const actual = await vi.importActual<typeof import("@/api/planningOrders")>("@/api/planningOrders");
  return {
    ...actual,
    getCustomerOrder: planningOrdersMocks.getCustomerOrderMock,
    listCustomerOrders: planningOrdersMocks.listCustomerOrdersMock,
    listPlanningRecords: planningOrdersMocks.listPlanningRecordsMock,
  };
});

const CardStub = defineComponent({
  name: "CardStub",
  template: '<div class="card-stub"><slot /></div>',
});

const EmptyStateStub = defineComponent({
  name: "EmptyStateStub",
  props: {
    title: { type: String, required: true },
    description: { type: String, required: true },
  },
  template: '<div class="empty-state-stub"><strong>{{ title }}</strong><span>{{ description }}</span></div>',
});

function buildOrder(overrides: Record<string, unknown> = {}) {
  return {
    id: "order-1",
    tenant_id: "tenant-1",
    customer_id: "customer-1",
    requirement_type_id: "security-service",
    patrol_route_id: null,
    order_no: "O-1001",
    title: "Order Alpha",
    service_category_code: "guarding",
    service_from: "2026-05-10",
    service_to: "2026-05-12",
    release_state: "released",
    released_at: "2026-05-01T10:00:00Z",
    created_at: "2026-04-01T08:00:00Z",
    updated_at: "2026-04-02T08:00:00Z",
    archived_at: null,
    released_by_user_id: "user-1",
    security_concept_text: "Main gate concept",
    notes: "VIP entry note",
    attachments: [],
    status: "active",
    version_no: 1,
    ...overrides,
  };
}

function deferred<T>() {
  let resolve: (value: T) => void = () => undefined;
  let reject: (reason?: unknown) => void = () => undefined;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, reject, resolve };
}

function mountComponent(props: Record<string, unknown> = {}) {
  return mount(CustomerOrdersTab, {
    props: {
      accessToken: "token-1",
      customerId: "customer-1",
      tenantId: "tenant-1",
      ...props,
    },
    global: {
      stubs: {
        Card: CardStub,
        EmptyState: EmptyStateStub,
      },
    },
  });
}

describe("CustomerOrdersTab", () => {
  beforeEach(() => {
    planningOrdersMocks.getCustomerOrderMock.mockReset();
    planningOrdersMocks.getCustomerOrderMock.mockResolvedValue(buildOrder());
    planningOrdersMocks.listCustomerOrdersMock.mockReset();
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([]);
    planningOrdersMocks.listPlanningRecordsMock.mockReset();
    planningOrdersMocks.listPlanningRecordsMock.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders empty state cleanly", async () => {
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-tab-panel-orders"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-orders-toolbar"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-orders-search"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-orders-sort"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-tab-panel-plans"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-plans-toolbar"]').exists()).toBe(false);
    expect(wrapper.text()).toContain("No orders found");
    expect(wrapper.text()).toContain("No matching orders are currently available for this customer.");
  });

  it("renders the toolbar with search first and sort second", async () => {
    const wrapper = mountComponent();
    await flushPromises();

    const toolbar = wrapper.get('[data-testid="customer-orders-toolbar"]');
    const fieldClasses = toolbar.findAll("label").map((node) => node.classes().join(" "));
    expect(fieldClasses).toEqual([
      "customer-orders-tab__field customer-orders-tab__field--search",
      "customer-orders-tab__field customer-orders-tab__field--sort",
    ]);
  });

  it("shows the New Order entry point only when explicitly allowed and emits the existing wizard action", async () => {
    const wrapper = mountComponent({ canStartNewOrder: true });
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-orders-new-order"]').text()).toBe("New order");
    await wrapper.get('[data-testid="customer-orders-new-order"]').trigger("click");
    expect(wrapper.emitted("start-new-order")).toHaveLength(1);

    const restrictedWrapper = mountComponent({ canStartNewOrder: false });
    await flushPromises();
    expect(restrictedWrapper.find('[data-testid="customer-orders-new-order"]').exists()).toBe(false);
  });

  it("debounces search and sends server-backed order filters", async () => {
    vi.useFakeTimers();
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([buildOrder()]);

    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-orders-search"]').setValue("Alpha");
    vi.advanceTimersByTime(249);
    expect(planningOrdersMocks.listCustomerOrdersMock).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(1);
    await flushPromises();
    expect(planningOrdersMocks.listCustomerOrdersMock).toHaveBeenCalledTimes(2);
    expect(planningOrdersMocks.listCustomerOrdersMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        customer_id: "customer-1",
        search: "Alpha",
      }),
    );
    expect(planningOrdersMocks.listPlanningRecordsMock).not.toHaveBeenCalled();
    vi.useRealTimers();
  });

  it("renders order identity, order dates, and order-centric search copy", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([
      buildOrder({
        order_no: "O-2042",
        title: "Museum night guarding",
        service_category_code: "event_security",
        service_from: "2026-06-10",
        service_to: "2026-06-12",
      }),
    ]);

    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-orders-search"]').attributes("placeholder")).toBe("Search by order title or order number");
    expect(wrapper.text()).toContain("Museum night guarding");
    expect(wrapper.text()).toContain("O-2042");
    expect(wrapper.text()).toContain("10.06.2026");
    expect(wrapper.text()).toContain("12.06.2026");
    expect(wrapper.text()).toContain("event_security");
    expect(wrapper.text()).not.toContain("Plan Alpha");
    expect(wrapper.text()).not.toContain("Search by plan name or order number");
  });

  it("opens a read-only detail modal from the card body and loads full order details", async () => {
    const detailRequest = deferred<ReturnType<typeof buildOrder>>();
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([
      buildOrder({
        id: "order-preview-1",
        order_no: "O-2042",
        title: "Museum night guarding",
      }),
      buildOrder({
        id: "order-preview-2",
        order_no: "O-2043",
        title: "Warehouse night guarding",
      }),
    ]);
    planningOrdersMocks.getCustomerOrderMock.mockReturnValue(detailRequest.promise);
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.findAll('[data-testid="customer-orders-card-open"]')[0]!.trigger("click");
    expect(wrapper.find('[data-testid="customer-orders-detail-modal"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-orders-detail-loading"]').text()).toContain("Loading order details...");

    detailRequest.resolve(buildOrder({
      id: "order-preview-1",
      order_no: "O-2042",
      title: "Museum night guarding",
      security_concept_text: "Guard the museum gates.",
      notes: "Use north entrance.",
      attachments: [{ current_version_no: 1, id: "doc-1", status: "active", tenant_id: "tenant-1", title: "Security concept PDF" }],
    }));
    await flushPromises();

    expect(planningOrdersMocks.getCustomerOrderMock).toHaveBeenCalledWith("tenant-1", "order-preview-1", "token-1");
    const modal = wrapper.get('[data-testid="customer-orders-detail-modal"]');
    expect(modal.attributes("role")).toBe("dialog");
    expect(modal.attributes("aria-modal")).toBe("true");
    expect(modal.text()).toContain("Museum night guarding");
    expect(modal.text()).toContain("O-2042");
    expect(modal.text()).toContain("Guard the museum gates.");
    expect(modal.text()).toContain("Use north entrance.");
    expect(modal.text()).toContain("Security concept PDF");

    await wrapper.get('[data-testid="customer-orders-detail-close"]').trigger("click");
    expect(wrapper.find('[data-testid="customer-orders-detail-modal"]').exists()).toBe(false);
  });

  it("closes by backdrop and reopens with a different order detail", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([
      buildOrder({ id: "order-preview-1", order_no: "O-2042", title: "Museum night guarding" }),
      buildOrder({ id: "order-preview-2", order_no: "O-2043", title: "Warehouse night guarding" }),
    ]);
    planningOrdersMocks.getCustomerOrderMock
      .mockResolvedValueOnce(buildOrder({ id: "order-preview-1", order_no: "O-2042", title: "Museum night guarding" }))
      .mockResolvedValueOnce(buildOrder({ id: "order-preview-2", order_no: "O-2043", title: "Warehouse night guarding" }));
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.findAll('[data-testid="customer-orders-card-open"]')[0]!.trigger("click");
    await flushPromises();
    expect(wrapper.get('[data-testid="customer-orders-detail-modal"]').text()).toContain("Museum night guarding");

    await wrapper.get(".customer-orders-tab__modal-backdrop").trigger("click");
    expect(wrapper.find('[data-testid="customer-orders-detail-modal"]').exists()).toBe(false);

    await wrapper.findAll('[data-testid="customer-orders-card-open"]')[1]!.trigger("click");
    await flushPromises();
    expect(planningOrdersMocks.getCustomerOrderMock).toHaveBeenLastCalledWith("tenant-1", "order-preview-2", "token-1");
    expect(wrapper.get('[data-testid="customer-orders-detail-modal"]').text()).toContain("Warehouse night guarding");
    expect(wrapper.get('[data-testid="customer-orders-detail-modal"]').text()).toContain("O-2043");
  });

  it("shows a deterministic modal error when order detail loading fails", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([buildOrder()]);
    planningOrdersMocks.getCustomerOrderMock.mockRejectedValue(new Error("boom"));
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-orders-card-open"]').trigger("click");
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-orders-detail-error"]').text()).toContain("Order details unavailable");
    expect(wrapper.get('[data-testid="customer-orders-detail-error"]').text()).toContain("Order details could not be loaded.");
  });

  it("emits edit-order from the explicit Edit button without opening the preview modal", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([buildOrder({ id: "order-edit-1" })]);
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-orders-card-edit"]').trigger("click");
    await flushPromises();

    expect(wrapper.emitted("edit-order")).toEqual([["order-edit-1"]]);
    expect(planningOrdersMocks.getCustomerOrderMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="customer-orders-detail-modal"]').exists()).toBe(false);
  });

  it("keeps search and sort behavior working before opening a filtered order preview", async () => {
    vi.useFakeTimers();
    planningOrdersMocks.listCustomerOrdersMock.mockImplementation(
      (_tenantId: string, _accessToken: string, filters: Record<string, unknown>) => {
        if (filters.search === "night") {
          return Promise.resolve([
            buildOrder({ id: "order-filter-older", title: "Night older", created_at: "2026-04-01T08:00:00Z" }),
            buildOrder({ id: "order-filter-newer", title: "Night newer", created_at: "2026-05-01T08:00:00Z" }),
          ]);
        }
        return Promise.resolve([buildOrder({ id: "order-day", title: "Day order" })]);
      },
    );
    planningOrdersMocks.getCustomerOrderMock.mockResolvedValue(
      buildOrder({ id: "order-filter-older", title: "Night older", order_no: "O-NIGHT-1" }),
    );
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-orders-search"]').setValue("night");
    vi.advanceTimersByTime(250);
    await flushPromises();
    await wrapper.get('[data-testid="customer-orders-sort"]').setValue("createdAtAsc");

    const sortedRows = wrapper.findAll(".customer-orders-tab__row strong").map((node) => node.text());
    expect(sortedRows).toEqual(["Night older", "Night newer"]);

    await wrapper.findAll('[data-testid="customer-orders-card-open"]')[0]!.trigger("click");
    await flushPromises();

    expect(planningOrdersMocks.listCustomerOrdersMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({ customer_id: "customer-1", search: "night" }),
    );
    expect(planningOrdersMocks.getCustomerOrderMock).toHaveBeenCalledWith("tenant-1", "order-filter-older", "token-1");
    expect(wrapper.get('[data-testid="customer-orders-detail-modal"]').text()).toContain("Night older");
    expect(wrapper.get('[data-testid="customer-orders-detail-modal"]').text()).toContain("O-NIGHT-1");
    vi.useRealTimers();
  });

  it("exposes order-based sort options instead of planning-record date fields", async () => {
    const wrapper = mountComponent();
    await flushPromises();

    const options = wrapper.findAll('[data-testid="customer-orders-sort"] option').map((option) => ({
      label: option.text(),
      value: option.attributes("value"),
    }));
    expect(options).toEqual([
      { value: "createdAtDesc", label: "Registration date desc" },
      { value: "createdAtAsc", label: "Registration date asc" },
      { value: "executionStartDesc", label: "Execution start desc" },
      { value: "executionStartAsc", label: "Execution start asc" },
      { value: "executionEndDesc", label: "Execution end desc" },
      { value: "executionEndAsc", label: "Execution end asc" },
      { value: "releaseDateDesc", label: "Release date desc" },
      { value: "releaseDateAsc", label: "Release date asc" },
      { value: "status", label: "Status" },
    ]);
  });

  it("changes rendered order when sort changes", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([
      buildOrder({ id: "order-1", title: "Older", created_at: "2026-04-01T08:00:00Z" }),
      buildOrder({ id: "order-2", title: "Newer", created_at: "2026-05-01T08:00:00Z" }),
    ]);

    const wrapper = mountComponent();
    await flushPromises();

    const initialRows = wrapper.findAll(".customer-orders-tab__row strong").map((node) => node.text());
    expect(initialRows).toEqual(["Newer", "Older"]);

    await wrapper.get('[data-testid="customer-orders-sort"]').setValue("createdAtAsc");
    const sortedRows = wrapper.findAll(".customer-orders-tab__row strong").map((node) => node.text());
    expect(sortedRows).toEqual(["Older", "Newer"]);
  });

  it("uses truthful display-state tones derived from release state and service window", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-05-12T12:00:00Z"));
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([
      buildOrder({ id: "order-upcoming", title: "Upcoming", service_from: "2099-05-10", service_to: "2099-05-12", release_state: "released" }),
      buildOrder({ id: "order-ready", title: "Ready", release_state: "release_ready" }),
      buildOrder({ id: "order-draft", title: "Draft", release_state: "draft" }),
      buildOrder({ id: "order-in-progress", title: "In progress", service_from: "2026-05-10", service_to: "2026-05-12", release_state: "released" }),
      buildOrder({ id: "order-completed", title: "Completed", service_from: "2020-01-01", service_to: "2020-01-02", release_state: "released" }),
      buildOrder({ id: "order-archived", title: "Archived", status: "archived", release_state: "released" }),
    ]);

    const wrapper = mountComponent();
    await flushPromises();

    const rows = wrapper.findAll(".customer-orders-tab__row");
    expect(rows.some((row) => row.attributes("data-state") === "upcoming" && row.attributes("data-tone") === "good")).toBe(true);
    expect(rows.some((row) => row.attributes("data-state") === "release_ready" && row.attributes("data-tone") === "warn")).toBe(true);
    expect(rows.some((row) => row.attributes("data-state") === "draft" && row.attributes("data-tone") === "warn")).toBe(true);
    expect(rows.some((row) => row.attributes("data-state") === "in_progress" && row.attributes("data-tone") === "good")).toBe(true);
    expect(rows.some((row) => row.attributes("data-state") === "completed" && row.attributes("data-tone") === "neutral")).toBe(true);
    expect(rows.some((row) => row.attributes("data-state") === "archived" && row.attributes("data-tone") === "muted")).toBe(true);
  });

  it("falls back to a neutral unknown status without breaking the row contract", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([
      buildOrder({ id: "order-unknown", title: "Unknown", release_state: "qa_hold" }),
    ]);

    const wrapper = mountComponent();
    await flushPromises();

    const row = wrapper.get(".customer-orders-tab__row");
    expect(row.attributes("data-state")).toBe("neutral");
    expect(row.attributes("data-tone")).toBe("neutral");
    expect(wrapper.text()).toContain("qa_hold");
  });

  it("refreshes the orders list when the selected customer changes", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([buildOrder()]);
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.setProps({ customerId: "customer-2" });
    await flushPromises();

    expect(planningOrdersMocks.listCustomerOrdersMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({ customer_id: "customer-2" }),
    );
  });

  it("ignores stale slower results after switching customers", async () => {
    let resolveFirst: (value: ReturnType<typeof buildOrder>[]) => void = () => undefined;
    let resolveSecond: (value: ReturnType<typeof buildOrder>[]) => void = () => undefined;
    planningOrdersMocks.listCustomerOrdersMock
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveFirst = resolve;
          }),
      )
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveSecond = resolve;
          }),
      );

    const wrapper = mountComponent();
    await wrapper.setProps({ customerId: "customer-2" });

    resolveSecond([buildOrder({ id: "order-2", title: "Customer Two" })]);
    await flushPromises();
    expect(wrapper.text()).toContain("Customer Two");

    resolveFirst([buildOrder({ id: "order-1", title: "Customer One" })]);
    await flushPromises();
    expect(wrapper.text()).toContain("Customer Two");
    expect(wrapper.text()).not.toContain("Customer One");
  });

  it("keeps created-at sorting truthful and deterministic when timestamps tie", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([
      buildOrder({ id: "order-2", title: "Bravo", order_no: "O-1002", created_at: "2026-04-01T08:00:00Z" }),
      buildOrder({ id: "order-1", title: "Alpha", order_no: "O-1001", created_at: "2026-04-01T08:00:00Z" }),
    ]);

    const wrapper = mountComponent();
    await flushPromises();

    const rows = wrapper.findAll(".customer-orders-tab__row strong").map((node) => node.text());
    expect(rows).toEqual(["Alpha", "Bravo"]);
  });

  it("renders an explicit error state when order loading fails", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockRejectedValue(new Error("boom"));
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.text()).toContain("Orders could not be loaded");
    expect(wrapper.text()).toContain("Customer orders are currently unavailable.");
  });
});
