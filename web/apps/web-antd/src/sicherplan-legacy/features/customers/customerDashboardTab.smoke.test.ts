// @vitest-environment happy-dom

import { describe, expect, it, vi, beforeEach } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent } from "vue";

import CustomerDashboardTab from "../../components/customers/CustomerDashboardTab.vue";

const planningStaffingMocks = vi.hoisted(() => ({
  listStaffingCoverageMock: vi.fn(),
}));

const planningOrdersMocks = vi.hoisted(() => ({
  listCustomerOrdersMock: vi.fn(),
}));

vi.mock("@/i18n", () => ({
  useI18n: () => ({
    locale: { value: "en-US" },
    t: (key: string, values?: Record<string, unknown>) => {
      if (values && "count" in values) {
        return `${key}:${values.count}`;
      }
      return key;
    },
  }),
}));

vi.mock("@/api/planningStaffing", () => ({
  listStaffingCoverage: planningStaffingMocks.listStaffingCoverageMock,
}));

vi.mock("@/api/planningOrders", () => ({
  listCustomerOrders: planningOrdersMocks.listCustomerOrdersMock,
}));

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

const DashboardCalendarPanelStub = defineComponent({
  name: "DashboardCalendarPanelStub",
  props: {
    cells: { type: Array, required: true },
    loading: { type: Boolean, default: false },
    loadingLabel: { type: String, default: "" },
    monthLabel: { type: String, required: true },
    summary: { type: Array, required: true },
    title: { type: String, required: true },
  },
  emits: ["shift-calendar", "toggle-day"],
  template:
    '<div class="dashboard-calendar-panel-stub sp-dashboard__calendar-card">{{ title }}|month={{ monthLabel }}|{{ cells.length }}|{{ summary.map((item) => `${item.label}:${item.value}`).join(\',\') }}|loading={{ loading ? loadingLabel : \'idle\' }}<strong class="calendar-month-label">{{ monthLabel }}</strong><button class="calendar-prev" @click="$emit(\'shift-calendar\', \'prev\')">Previous</button><button class="calendar-next" @click="$emit(\'shift-calendar\', \'next\')">Next</button><span v-if="loading" data-testid="customer-dashboard-calendar-loading-indicator" role="status" aria-live="polite">{{ loadingLabel }}</span><div class="sp-dashboard__calendar-grid" /></div>',
});

const baseCustomer = {
  id: "customer-1",
  tenant_id: "tenant-1",
  customer_number: "CU-1000",
  name: "Nord Security",
  status: "active",
  created_at: "2025-04-18T12:00:00Z",
};

function buildDashboard(overrides: Record<string, unknown> = {}) {
  return {
    customer_id: "customer-1",
    planning_summary: {
      total_plans_count: 7,
      latest_plans: [],
    },
    finance_summary: {
      visibility: "available",
      currency_code: "EUR",
      total_received_amount: "4500.00",
      semantic_label: "released_invoice_total",
    },
    calendar_items: [],
    ...overrides,
  };
}

function buildOrderListItem(overrides: Record<string, unknown> = {}) {
  return {
    id: "order-1",
    tenant_id: "tenant-1",
    customer_id: "customer-1",
    requirement_type_id: "requirement-1",
    patrol_route_id: null,
    order_no: "ORD-1",
    title: "Lobby coverage",
    service_category_code: "guarding",
    service_from: "2026-04-18",
    service_to: "2026-04-19",
    release_state: "released",
    released_at: "2026-04-17T10:00:00Z",
    status: "active",
    version_no: 1,
    ...overrides,
  };
}

function buildCoverageRow(overrides: Record<string, unknown> = {}) {
  return {
    shift_id: "shift-1",
    planning_record_id: "planning-1",
    shift_plan_id: "shift-plan-1",
    order_id: "order-1",
    order_no: "ORD-1",
    planning_record_name: "Planung A",
    planning_mode_code: "site",
    workforce_scope_code: "internal",
    starts_at: "2026-04-18T08:00:00Z",
    ends_at: "2026-04-18T16:00:00Z",
    shift_type_code: "day",
    location_text: "Koeln",
    meeting_point: null,
    min_required_qty: 1,
    target_required_qty: 2,
    assigned_count: 1,
    confirmed_count: 1,
    released_partner_qty: 0,
    coverage_state: "green",
    demand_groups: [],
    ...overrides,
  };
}

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

function createRejectableThenable<T>() {
  const rejectionHandlers: Array<(reason: unknown) => unknown> = [];
  const finallyHandlers: Array<() => void> = [];
  const thenable = {
    catch(onRejected?: (reason: unknown) => unknown) {
      if (onRejected) {
        rejectionHandlers.push(onRejected);
      }
      return thenable;
    },
    finally(onFinally?: () => void) {
      if (onFinally) {
        finallyHandlers.push(onFinally);
      }
      return thenable;
    },
    reject(reason: unknown) {
      finallyHandlers.forEach((handler) => handler());
      rejectionHandlers.forEach((handler) => handler(reason));
    },
    then(_onResolved?: (value: T) => unknown, onRejected?: (reason: unknown) => unknown) {
      if (onRejected) {
        rejectionHandlers.push(onRejected);
      }
      return thenable;
    },
  };
  return thenable;
}

function mountComponent(props: Record<string, unknown> = {}) {
  return mount(CustomerDashboardTab, {
    props: {
      accessToken: "token-1",
      canReadCommercial: true,
      canWriteCommercial: true,
      canManageContacts: true,
      customer: baseCustomer as any,
      dashboard: buildDashboard() as any,
      error: "",
      loading: false,
      standing: {
        label: "A",
        tone: "good",
      },
      tenantId: "tenant-1",
      ...props,
    },
    global: {
      stubs: {
        Card: CardStub,
        EmptyState: EmptyStateStub,
        DashboardCalendarPanel: DashboardCalendarPanelStub,
      },
    },
  });
}

describe("CustomerDashboardTab", () => {
  beforeEach(() => {
    planningStaffingMocks.listStaffingCoverageMock.mockReset();
    planningStaffingMocks.listStaffingCoverageMock.mockResolvedValue([]);
    planningOrdersMocks.listCustomerOrdersMock.mockReset();
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([]);
  });

  it("renders restricted finance state without leaking amounts", () => {
    const wrapper = mountComponent({
      dashboard: buildDashboard({
        finance_summary: {
          visibility: "restricted",
          currency_code: null,
          total_received_amount: null,
          semantic_label: null,
        },
      }),
    });

    expect(wrapper.get('[data-testid="customer-dashboard-kpi-finance"]').text()).toContain(
      "customerAdmin.dashboard.financeRestricted",
    );
    expect(wrapper.get('[data-testid="customer-dashboard-kpi-finance"]').text()).not.toContain("4500.00");
    expect(wrapper.get('[data-testid="customer-dashboard-kpi-finance"]').attributes("data-tone")).toBe("restricted");
  });

  it("renders unavailable finance state cleanly when no finance data exists", () => {
    const wrapper = mountComponent({
      dashboard: buildDashboard({
        finance_summary: {
          visibility: "available",
          currency_code: null,
          total_received_amount: null,
          semantic_label: "released_invoice_total",
        },
      }),
    });

    expect(wrapper.get('[data-testid="customer-dashboard-kpi-finance"]').text()).toContain(
      "customerAdmin.dashboard.financeUnavailable",
    );
    expect(wrapper.get('[data-testid="customer-dashboard-kpi-finance"]').attributes("data-tone")).toBe("warn");
  });

  it("renders available finance state with the positive tone shell", () => {
    const wrapper = mountComponent({
      dashboard: buildDashboard({
        finance_summary: {
          visibility: "available",
          currency_code: "EUR",
          total_received_amount: "4500.00",
          semantic_label: "released_invoice_total",
        },
      }),
    });

    expect(wrapper.get('[data-testid="customer-dashboard-kpi-finance"]').attributes("data-tone")).toBe("good");
    expect(wrapper.get('[data-testid="customer-dashboard-kpi-finance"]').text()).toContain(
      "customerAdmin.dashboard.financeLabels.released_invoice_total",
    );
  });

  it("maps standing tone to lifecycle-driven good, warn, and bad shells", async () => {
    const wrapper = mountComponent({
      standing: {
        label: "A",
        tone: "good",
      },
    });

    expect(wrapper.get('[data-testid="customer-dashboard-kpi-standing"]').attributes("data-tone")).toBe("good");

    await wrapper.setProps({
      standing: {
        label: "Review",
        tone: "warn",
      },
    });
    expect(wrapper.get('[data-testid="customer-dashboard-kpi-standing"]').attributes("data-tone")).toBe("warn");

    await wrapper.setProps({
      standing: {
        label: "Archived",
        tone: "bad",
      },
    });
    expect(wrapper.get('[data-testid="customer-dashboard-kpi-standing"]').attributes("data-tone")).toBe("bad");
  });

  it("renders empty orders/plans cards and empty calendar states cleanly", async () => {
    const wrapper = mountComponent({
      dashboard: buildDashboard({
        planning_summary: {
          total_plans_count: 0,
          latest_plans: [],
        },
        calendar_items: [],
      }),
    });
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-dashboard-orders-empty"]').text()).toContain(
      "customerAdmin.dashboard.latestOrdersEmptyTitle",
    );
    expect(wrapper.get('[data-testid="customer-dashboard-orders-empty"]').text()).toContain(
      "customerAdmin.dashboard.latestOrdersEmptyBody",
    );
    expect(wrapper.get('[data-testid="customer-dashboard-plans-empty"]').text()).toContain(
      "customerAdmin.dashboard.latestPlansEmptyTitle",
    );
    expect(wrapper.text()).toContain("customerAdmin.dashboard.latestPlansEmptyTitle");
    expect(wrapper.text()).toContain("customerAdmin.dashboard.latestPlansEmptyBody");
    expect(wrapper.get(".dashboard-calendar-panel-stub").text()).toContain("customerAdmin.dashboard.calendarTitle");
    expect(wrapper.text()).not.toContain("customerAdmin.dashboard.calendarEmptyTitle");
    expect(wrapper.text()).not.toContain("customerAdmin.dashboard.calendarEmptyBody");
  });

  it("renders the second row as latest orders and latest plans with equal-height card hooks", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([
      buildOrderListItem(),
      buildOrderListItem({
        id: "order-2",
        order_no: "ORD-2",
        title: "Night patrol",
        service_from: "2026-04-21",
        service_to: "2026-04-22",
        release_state: "release_ready",
      }),
    ]);

    const wrapper = mountComponent({
      dashboard: buildDashboard({
        planning_summary: {
          total_plans_count: 2,
          latest_plans: [
            {
              id: "plan-1",
              order_id: "order-1",
              order_no: "ORD-1",
              label: "Plan Released",
              status: "released",
              planning_mode_code: "site",
              planning_from: "2026-04-18",
              planning_to: "2026-04-19",
              released_at: "2026-04-17T10:00:00Z",
            },
          ],
        },
      }),
    });
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-dashboard-second-row"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-dashboard-orders-card"]').text()).toContain(
      "customerAdmin.dashboard.latestOrdersTitle",
    );
    expect(wrapper.get('[data-testid="customer-dashboard-plans-card"]').text()).toContain(
      "customerAdmin.dashboard.latestPlansTitle",
    );
    expect(wrapper.get('[data-testid="customer-dashboard-orders-card"]').classes()).toContain(
      "customer-dashboard-tab__panel--equal",
    );
    expect(wrapper.get('[data-testid="customer-dashboard-plans-card"]').classes()).toContain(
      "customer-dashboard-tab__panel--equal",
    );
    expect(wrapper.findAll('[data-testid="customer-dashboard-orders-row"]')).toHaveLength(2);
    expect(wrapper.findAll('[data-testid="customer-dashboard-plans-row"]')).toHaveLength(1);
    expect(wrapper.text()).not.toContain("customerAdmin.dashboard.quickActionsTitle");
    expect(wrapper.text()).not.toContain("customerAdmin.dashboard.quickActionsEyebrow");
  });

  it("renders up to five latest orders sorted by service window", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockResolvedValue([
      buildOrderListItem({ id: "order-1", order_no: "ORD-1", service_from: "2026-04-18" }),
      buildOrderListItem({ id: "order-2", order_no: "ORD-2", service_from: "2026-04-19" }),
      buildOrderListItem({ id: "order-3", order_no: "ORD-3", service_from: "2026-04-20" }),
      buildOrderListItem({ id: "order-4", order_no: "ORD-4", service_from: "2026-04-21" }),
      buildOrderListItem({ id: "order-5", order_no: "ORD-5", service_from: "2026-04-22" }),
      buildOrderListItem({ id: "order-6", order_no: "ORD-6", service_from: "2026-04-23" }),
    ]);

    const wrapper = mountComponent();
    await flushPromises();

    const rows = wrapper.findAll('[data-testid="customer-dashboard-orders-row"]');
    expect(rows).toHaveLength(5);
    expect(rows[0]?.text()).toContain("ORD-6");
    expect(rows[4]?.text()).toContain("ORD-2");
    expect(wrapper.text()).not.toContain("ORD-1");
    expect(planningOrdersMocks.listCustomerOrdersMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({ customer_id: "customer-1" }),
    );
  });

  it("renders up to five latest plans in the plans card", async () => {
    const wrapper = mountComponent({
      dashboard: buildDashboard({
        planning_summary: {
          total_plans_count: 6,
          latest_plans: [1, 2, 3, 4, 5, 6].map((index) => ({
            id: `plan-${index}`,
            order_id: `order-${index}`,
            order_no: `ORD-${index}`,
            label: `Plan ${index}`,
            status: index === 1 ? "released" : "draft",
            planning_mode_code: "site",
            planning_from: `2026-04-${String(index).padStart(2, "0")}`,
            planning_to: `2026-04-${String(index + 1).padStart(2, "0")}`,
            released_at: index === 1 ? "2026-04-01T10:00:00Z" : null,
          })),
        },
      }),
    });
    await flushPromises();

    const rows = wrapper.findAll('[data-testid="customer-dashboard-plans-row"]');
    expect(rows).toHaveLength(5);
    expect(wrapper.text()).toContain("ORD-1");
    expect(wrapper.text()).toContain("ORD-5");
    expect(wrapper.text()).not.toContain("ORD-6 · Plan 6");
  });

  it("shows a clean orders empty state when latest orders cannot be loaded", async () => {
    planningOrdersMocks.listCustomerOrdersMock.mockRejectedValue(new Error("boom"));

    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-dashboard-orders-empty"]').text()).toContain(
      "customerAdmin.dashboard.latestOrdersEmptyTitle",
    );
    expect(wrapper.get('[data-testid="customer-dashboard-orders-empty"]').text()).toContain(
      "customerAdmin.dashboard.latestOrdersLoadError",
    );
  });

  it("renders status badges for latest plans with release-state tones", () => {
    const wrapper = mountComponent({
      dashboard: buildDashboard({
        planning_summary: {
          total_plans_count: 3,
          latest_plans: [
            {
              id: "plan-1",
              order_id: "order-1",
              order_no: "ORD-1",
              label: "Plan Released",
              status: "released",
              planning_mode_code: "site",
              planning_from: "2026-04-18",
              planning_to: "2026-04-19",
              released_at: "2026-04-17T10:00:00Z",
            },
            {
              id: "plan-2",
              order_id: "order-2",
              order_no: "ORD-2",
              label: "Plan Ready",
              status: "release_ready",
              planning_mode_code: "site",
              planning_from: "2026-04-20",
              planning_to: "2026-04-21",
              released_at: null,
            },
            {
              id: "plan-3",
              order_id: "order-3",
              order_no: "ORD-3",
              label: "Plan Draft",
              status: "draft",
              planning_mode_code: "site",
              planning_from: "2026-04-22",
              planning_to: "2026-04-23",
              released_at: null,
            },
          ],
        },
      }),
    });

    const tags = wrapper.findAll(".customer-dashboard-tab__status-tag");
    expect(tags).toHaveLength(3);
    expect(tags[0]?.attributes("data-tone")).toBe("good");
    expect(tags[1]?.attributes("data-tone")).toBe("warn");
    expect(tags[2]?.attributes("data-tone")).toBe("warn");
  });

  it("falls back safely for unknown latest-plan statuses", () => {
    const wrapper = mountComponent({
      dashboard: buildDashboard({
        planning_summary: {
          total_plans_count: 1,
          latest_plans: [
            {
              id: "plan-1",
              order_id: "order-1",
              order_no: "ORD-1",
              label: "Plan Unknown",
              status: "unknown_state",
              planning_mode_code: "site",
              planning_from: "2026-04-18",
              planning_to: "2026-04-19",
              released_at: null,
            },
          ],
        },
      }),
    });

    const tag = wrapper.get(".customer-dashboard-tab__status-tag");
    expect(tag.attributes("data-tone")).toBe("neutral");
    expect(tag.text()).toContain("unknown_state");
  });

  it("no longer reads plan rows as calendar shift items", async () => {
    const wrapper = mountComponent({
      dashboard: buildDashboard({
        calendar_items: [
          {
            id: "planning-record:1",
            source_type: "planning_record",
            source_ref_id: "planning-1",
            order_id: "order-1",
            planning_record_id: "planning-1",
            title: "Legacy planning row",
            starts_at: "2026-04-18T00:00:00Z",
            ends_at: "2026-04-19T00:00:00Z",
            status: "released",
          },
        ],
      }),
    });
    await flushPromises();

    const calendarProps = wrapper.getComponent(DashboardCalendarPanelStub).props("cells") as Array<Record<string, unknown>>;
    expect(calendarProps.every((cell) => (cell.shiftCount as number) === 0)).toBe(true);
    expect(wrapper.text()).not.toContain("customerAdmin.dashboard.calendarEmptyTitle");
  });

  it("populates shiftCount and orderCount from customer-scoped staffing coverage", async () => {
    planningStaffingMocks.listStaffingCoverageMock.mockResolvedValue([
      buildCoverageRow({ shift_id: "shift-1", order_id: "order-1" }),
      buildCoverageRow({ shift_id: "shift-2", order_id: "order-2", starts_at: "2026-04-18T18:00:00Z", ends_at: "2026-04-18T22:00:00Z", coverage_state: "yellow" }),
    ]);

    const wrapper = mountComponent();
    await flushPromises();

    const calendarProps = wrapper.getComponent(DashboardCalendarPanelStub).props("cells") as Array<Record<string, unknown>>;
    const populatedCell = calendarProps.find((cell) => (cell.shiftCount as number) === 2);
    expect(populatedCell).toBeTruthy();
    expect(populatedCell?.orderCount).toBe(2);
    expect(wrapper.text()).toContain("customerAdmin.dashboard.calendarSummary.shifts");
    expect(wrapper.text()).toContain("customerAdmin.dashboard.calendarSummary.atRisk");
  });

  it("keeps the dashboard free of the removed quick-actions section for read-only commercial users", () => {
    const wrapper = mountComponent({
      canReadCommercial: true,
      canWriteCommercial: false,
    });

    expect(wrapper.text()).not.toContain("customerAdmin.actions.addInvoiceParty");
    expect(wrapper.text()).not.toContain("customerAdmin.dashboard.quickActionsTitle");
    expect(wrapper.text()).not.toContain("customerAdmin.dashboard.quickActionsEyebrow");
  });

  it("updates dashboard cards when the selected customer changes", async () => {
    planningStaffingMocks.listStaffingCoverageMock.mockResolvedValue([buildCoverageRow()]);
    const wrapper = mountComponent({
      customer: {
        ...baseCustomer,
        id: "customer-1",
        created_at: "2025-04-18T12:00:00Z",
      } as any,
      dashboard: buildDashboard({
        planning_summary: {
          total_plans_count: 7,
          latest_plans: [],
        },
      }),
    });

    await wrapper.setProps({
      customer: {
        ...baseCustomer,
        id: "customer-2",
        created_at: "2026-04-10T12:00:00Z",
      } as any,
      dashboard: buildDashboard({
        customer_id: "customer-2",
        planning_summary: {
          total_plans_count: 2,
          latest_plans: [],
        },
      }) as any,
    });
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-dashboard-kpi-plans"]').text()).toContain("2");
    expect(wrapper.get('[data-testid="customer-dashboard-kpi-tenure"]').text()).not.toContain(
      "customerAdmin.dashboard.tenureYears",
    );
    expect(planningStaffingMocks.listStaffingCoverageMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({ customer_id: "customer-2" }),
    );
  });

  it("reloads coverage when the visible month changes", async () => {
    planningStaffingMocks.listStaffingCoverageMock.mockResolvedValue([buildCoverageRow()]);
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get(".calendar-next").trigger("click");
    await flushPromises();

    expect(planningStaffingMocks.listStaffingCoverageMock).toHaveBeenCalledTimes(2);
    const firstFilters = planningStaffingMocks.listStaffingCoverageMock.mock.calls[0]?.[2];
    const secondFilters = planningStaffingMocks.listStaffingCoverageMock.mock.calls[1]?.[2];
    expect(firstFilters.customer_id).toBe("customer-1");
    expect(secondFilters.customer_id).toBe("customer-1");
    expect(secondFilters.date_from).not.toBe(firstFilters.date_from);
  });

  it("keeps the calendar panel mounted while the next month is loading", async () => {
    const firstRequest = createDeferred<Array<ReturnType<typeof buildCoverageRow>>>();
    const secondRequest = createDeferred<Array<ReturnType<typeof buildCoverageRow>>>();
    planningStaffingMocks.listStaffingCoverageMock
      .mockImplementationOnce(() => firstRequest.promise)
      .mockImplementationOnce(() => secondRequest.promise);

    const wrapper = mountComponent();
    const initialMonthLabel = wrapper.getComponent(DashboardCalendarPanelStub).props("monthLabel") as string;

    expect(wrapper.get(".dashboard-calendar-panel-stub").text()).toContain("loading=workspace.loading.processing");

    firstRequest.resolve([buildCoverageRow()]);
    await flushPromises();

    expect(wrapper.get(".dashboard-calendar-panel-stub").text()).toContain("loading=idle");

    await wrapper.get(".calendar-next").trigger("click");
    const nextMonthLabel = wrapper.getComponent(DashboardCalendarPanelStub).props("monthLabel") as string;

    expect(wrapper.find(".dashboard-calendar-panel-stub").exists()).toBe(true);
    expect(nextMonthLabel).not.toBe(initialMonthLabel);
    expect(wrapper.get('[data-testid="customer-dashboard-calendar-loading-indicator"]').text()).toBe(
      "workspace.loading.processing",
    );
    expect(wrapper.find(".sp-dashboard__calendar-grid").exists()).toBe(true);
    expect(wrapper.find(".sicherplan-loading-overlay").exists()).toBe(false);
    expect(wrapper.find(".sp-dashboard__calendar-card").classes()).not.toContain("is-loading");
    expect(wrapper.find(".sp-dashboard__calendar-card").classes()).not.toContain("is-dimmed");
    expect(wrapper.find('[data-testid="customer-dashboard-calendar-loading"]').exists()).toBe(false);

    secondRequest.resolve([buildCoverageRow({ shift_id: "shift-2", order_id: "order-2" })]);
    await flushPromises();

    expect(wrapper.get(".dashboard-calendar-panel-stub").text()).toContain("loading=idle");
    expect(wrapper.find('[data-testid="customer-dashboard-calendar-loading-indicator"]').exists()).toBe(false);
  });

  it("does not replace the calendar panel or accept stale data after quick next-previous navigation", async () => {
    const currentMonthDate = new Date();
    const nextMonthDate = new Date(currentMonthDate.getFullYear(), currentMonthDate.getMonth() + 1, 18, 8, 0, 0, 0);
    const initialRow = buildCoverageRow({
      shift_id: "shift-current",
      order_id: "order-current",
      starts_at: new Date(currentMonthDate.getFullYear(), currentMonthDate.getMonth(), 18, 8, 0, 0, 0).toISOString(),
      ends_at: new Date(currentMonthDate.getFullYear(), currentMonthDate.getMonth(), 18, 16, 0, 0, 0).toISOString(),
    });
    const nextMonthRow = buildCoverageRow({
      shift_id: "shift-next",
      order_id: "order-next",
      starts_at: nextMonthDate.toISOString(),
      ends_at: new Date(nextMonthDate.getFullYear(), nextMonthDate.getMonth(), 18, 16, 0, 0, 0).toISOString(),
    });
    const nextMonthRequest = createDeferred<Array<ReturnType<typeof buildCoverageRow>>>();

    planningStaffingMocks.listStaffingCoverageMock
      .mockResolvedValueOnce([initialRow])
      .mockImplementationOnce(() => nextMonthRequest.promise);

    const wrapper = mountComponent();
    await flushPromises();

    const initialMonthLabel = wrapper.getComponent(DashboardCalendarPanelStub).props("monthLabel") as string;
    const initialCells = wrapper.getComponent(DashboardCalendarPanelStub).props("cells") as Array<Record<string, unknown>>;
    expect(initialCells.some((cell) => (cell.shiftCount as number) === 1)).toBe(true);

    await wrapper.get(".calendar-next").trigger("click");
    await wrapper.get(".calendar-prev").trigger("click");
    await flushPromises();

    expect(wrapper.find(".dashboard-calendar-panel-stub").exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-dashboard-calendar-loading"]').exists()).toBe(false);
    expect(wrapper.find(".sicherplan-loading-overlay").exists()).toBe(false);
    expect(wrapper.getComponent(DashboardCalendarPanelStub).props("monthLabel")).toBe(initialMonthLabel);

    nextMonthRequest.resolve([nextMonthRow]);
    await flushPromises();

    expect(wrapper.getComponent(DashboardCalendarPanelStub).props("monthLabel")).toBe(initialMonthLabel);
    const finalCells = wrapper.getComponent(DashboardCalendarPanelStub).props("cells") as Array<Record<string, unknown>>;
    expect(finalCells.some((cell) => (cell.shiftCount as number) === 1)).toBe(true);
    expect(planningStaffingMocks.listStaffingCoverageMock).toHaveBeenCalledTimes(2);
  });

  it("shows the calendar API error state when coverage loading fails", async () => {
    const initialRow = buildCoverageRow();
    const failingRequest = createRejectableThenable<Array<ReturnType<typeof buildCoverageRow>>>();
    planningStaffingMocks.listStaffingCoverageMock
      .mockResolvedValueOnce([initialRow])
      .mockImplementationOnce(() => failingRequest as never);

    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get(".calendar-next").trigger("click");
    expect(wrapper.find('[data-testid="customer-dashboard-calendar-loading-indicator"]').exists()).toBe(true);
    expect(wrapper.find(".sp-dashboard__calendar-grid").exists()).toBe(true);

    failingRequest.reject(new Error("boom"));
    await flushPromises();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-dashboard-calendar-error"]').text()).toContain(
      "customerAdmin.dashboard.calendarLoadError",
    );
    expect(wrapper.find('[data-testid="customer-dashboard-calendar-loading-indicator"]').exists()).toBe(false);
    expect(wrapper.find(".dashboard-calendar-panel-stub").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("customerAdmin.dashboard.calendarEmptyTitle");
  });

  it("keeps the dashboard KPI labels stable while tone styling changes", () => {
    const wrapper = mountComponent();

    expect(wrapper.get('[data-testid="customer-dashboard-kpi-finance"]').text()).toContain(
      "customerAdmin.dashboard.kpis.finance",
    );
    expect(wrapper.get('[data-testid="customer-dashboard-kpi-standing"]').text()).toContain(
      "customerAdmin.dashboard.kpis.standing",
    );
  });
});
