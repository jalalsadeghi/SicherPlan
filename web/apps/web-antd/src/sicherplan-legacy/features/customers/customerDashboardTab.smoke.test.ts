// @vitest-environment happy-dom

import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { defineComponent } from "vue";

import CustomerDashboardTab from "../../components/customers/CustomerDashboardTab.vue";

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
    title: { type: String, required: true },
  },
  template: '<div class="dashboard-calendar-panel-stub">{{ title }}|{{ cells.length }}</div>',
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

function mountComponent(props: Record<string, unknown> = {}) {
  return mount(CustomerDashboardTab, {
    props: {
      canReadCommercial: true,
      canWriteCommercial: true,
      canManageContacts: true,
      customer: baseCustomer as any,
      dashboard: buildDashboard(),
      error: "",
      loading: false,
      standing: {
        label: "A",
        tone: "good",
      },
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
  });

  it("renders empty latest-plans and empty calendar states cleanly", () => {
    const wrapper = mountComponent({
      dashboard: buildDashboard({
        planning_summary: {
          total_plans_count: 0,
          latest_plans: [],
        },
        calendar_items: [],
      }),
    });

    expect(wrapper.text()).toContain("customerAdmin.dashboard.latestPlansEmptyTitle");
    expect(wrapper.text()).toContain("customerAdmin.dashboard.latestPlansEmptyBody");
    expect(wrapper.text()).toContain("customerAdmin.dashboard.calendarEmptyTitle");
    expect(wrapper.text()).toContain("customerAdmin.dashboard.calendarEmptyBody");
    expect(wrapper.get(".dashboard-calendar-panel-stub").text()).toContain("customerAdmin.dashboard.calendarTitle");
  });

  it("keeps commercial navigation visible for read users but hides invoice-party creation without write permission", () => {
    const wrapper = mountComponent({
      canReadCommercial: true,
      canWriteCommercial: false,
    });

    expect(wrapper.text()).toContain("customerAdmin.tabs.commercial");
    expect(wrapper.text()).not.toContain("customerAdmin.actions.addInvoiceParty");
  });

  it("updates dashboard cards when the selected customer changes", async () => {
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
      },
      dashboard: buildDashboard({
        customer_id: "customer-2",
        planning_summary: {
          total_plans_count: 2,
          latest_plans: [],
        },
      }),
    });

    expect(wrapper.get('[data-testid="customer-dashboard-kpi-plans"]').text()).toContain("2");
    expect(wrapper.get('[data-testid="customer-dashboard-kpi-tenure"]').text()).not.toContain(
      "customerAdmin.dashboard.tenureYears",
    );
  });
});
