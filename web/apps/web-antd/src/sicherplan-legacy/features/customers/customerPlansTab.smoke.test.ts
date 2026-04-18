// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent } from "vue";

import CustomerPlansTab from "../../components/customers/CustomerPlansTab.vue";

const planningOrdersMocks = vi.hoisted(() => ({
  listPlanningRecordsMock: vi.fn(),
}));

vi.mock("@/i18n", () => ({
  useI18n: () => ({
    locale: { value: "de-DE" },
    t: (key: string) => key,
  }),
}));

vi.mock("@/api/planningOrders", async () => {
  const actual = await vi.importActual<typeof import("@/api/planningOrders")>("@/api/planningOrders");
  return {
    ...actual,
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

function buildPlan(overrides: Record<string, unknown> = {}) {
  return {
    id: "plan-1",
    tenant_id: "tenant-1",
    order_id: "order-1",
    parent_planning_record_id: null,
    dispatcher_user_id: null,
    planning_mode_code: "site",
    name: "Plan Alpha",
    planning_from: "2026-05-10",
    planning_to: "2026-05-12",
    release_state: "released",
    released_at: "2026-05-01T10:00:00Z",
    created_at: "2026-04-01T08:00:00Z",
    status: "active",
    version_no: 1,
    ...overrides,
  };
}

function mountComponent(props: Record<string, unknown> = {}) {
  return mount(CustomerPlansTab, {
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

describe("CustomerPlansTab", () => {
  beforeEach(() => {
    planningOrdersMocks.listPlanningRecordsMock.mockReset();
    planningOrdersMocks.listPlanningRecordsMock.mockResolvedValue([]);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders empty state cleanly", async () => {
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.text()).toContain("customerAdmin.plans.emptyTitle");
    expect(wrapper.text()).toContain("customerAdmin.plans.emptyBody");
  });

  it("debounces search and sends server-backed planning-record filters", async () => {
    vi.useFakeTimers();
    planningOrdersMocks.listPlanningRecordsMock.mockResolvedValue([buildPlan()]);

    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-plans-search"]').setValue("Alpha");
    vi.advanceTimersByTime(249);
    expect(planningOrdersMocks.listPlanningRecordsMock).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(1);
    await flushPromises();
    expect(planningOrdersMocks.listPlanningRecordsMock).toHaveBeenCalledTimes(2);
    expect(planningOrdersMocks.listPlanningRecordsMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        customer_id: "customer-1",
        search: "Alpha",
      }),
    );
    vi.useRealTimers();
  });

  it("changes rendered order when sort changes", async () => {
    planningOrdersMocks.listPlanningRecordsMock.mockResolvedValue([
      buildPlan({ id: "plan-1", name: "Older", created_at: "2026-04-01T08:00:00Z" }),
      buildPlan({ id: "plan-2", name: "Newer", created_at: "2026-05-01T08:00:00Z" }),
    ]);

    const wrapper = mountComponent();
    await flushPromises();

    const initialRows = wrapper.findAll(".customer-plans-tab__row strong").map((node) => node.text());
    expect(initialRows).toEqual(["Newer", "Older"]);

    await wrapper.get('[data-testid="customer-plans-sort"]').setValue("createdAtAsc");
    const sortedRows = wrapper.findAll(".customer-plans-tab__row strong").map((node) => node.text());
    expect(sortedRows).toEqual(["Older", "Newer"]);
  });

  it("uses truthful display-state tones derived from release state and planning window", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-05-12T12:00:00Z"));
    planningOrdersMocks.listPlanningRecordsMock.mockResolvedValue([
      buildPlan({ id: "plan-upcoming", name: "Upcoming", planning_from: "2099-05-10", planning_to: "2099-05-12", release_state: "released" }),
      buildPlan({ id: "plan-ready", name: "Ready", release_state: "release_ready" }),
      buildPlan({ id: "plan-draft", name: "Draft", release_state: "draft" }),
      buildPlan({ id: "plan-in-progress", name: "In progress", planning_from: "2026-05-10", planning_to: "2026-05-12", release_state: "released" }),
      buildPlan({ id: "plan-completed", name: "Completed", planning_from: "2020-01-01", planning_to: "2020-01-02", release_state: "released" }),
      buildPlan({ id: "plan-archived", name: "Archived", status: "archived", release_state: "released" }),
    ]);

    const wrapper = mountComponent();
    await flushPromises();

    const rows = wrapper.findAll(".customer-plans-tab__row");
    expect(rows.some((row) => row.attributes("data-state") === "upcoming" && row.attributes("data-tone") === "good")).toBe(true);
    expect(rows.some((row) => row.attributes("data-state") === "release_ready" && row.attributes("data-tone") === "warn")).toBe(true);
    expect(rows.some((row) => row.attributes("data-state") === "draft" && row.attributes("data-tone") === "warn")).toBe(true);
    expect(rows.some((row) => row.attributes("data-state") === "in_progress" && row.attributes("data-tone") === "good")).toBe(true);
    expect(rows.some((row) => row.attributes("data-state") === "completed" && row.attributes("data-tone") === "neutral")).toBe(true);
    expect(rows.some((row) => row.attributes("data-state") === "archived" && row.attributes("data-tone") === "muted")).toBe(true);
  });

  it("falls back to a neutral unknown status without breaking the row contract", async () => {
    planningOrdersMocks.listPlanningRecordsMock.mockResolvedValue([
      buildPlan({ id: "plan-unknown", name: "Unknown", release_state: "qa_hold" }),
    ]);

    const wrapper = mountComponent();
    await flushPromises();

    const row = wrapper.get(".customer-plans-tab__row");
    expect(row.attributes("data-state")).toBe("neutral");
    expect(row.attributes("data-tone")).toBe("neutral");
    expect(wrapper.text()).toContain("qa_hold");
  });

  it("refreshes the plans list when the selected customer changes", async () => {
    planningOrdersMocks.listPlanningRecordsMock.mockResolvedValue([buildPlan()]);
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.setProps({ customerId: "customer-2" });
    await flushPromises();

    expect(planningOrdersMocks.listPlanningRecordsMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({ customer_id: "customer-2" }),
    );
  });

  it("ignores stale slower results after switching customers", async () => {
    let resolveFirst: (value: ReturnType<typeof buildPlan>[]) => void = () => undefined;
    let resolveSecond: (value: ReturnType<typeof buildPlan>[]) => void = () => undefined;
    planningOrdersMocks.listPlanningRecordsMock
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

    resolveSecond([buildPlan({ id: "plan-2", name: "Customer Two" })]);
    await flushPromises();
    expect(wrapper.text()).toContain("Customer Two");

    resolveFirst([buildPlan({ id: "plan-1", name: "Customer One" })]);
    await flushPromises();
    expect(wrapper.text()).toContain("Customer Two");
    expect(wrapper.text()).not.toContain("Customer One");
  });

  it("keeps created-at sorting truthful and deterministic when timestamps tie", async () => {
    planningOrdersMocks.listPlanningRecordsMock.mockResolvedValue([
      buildPlan({ id: "plan-2", name: "Bravo", created_at: "2026-04-01T08:00:00Z" }),
      buildPlan({ id: "plan-1", name: "Alpha", created_at: "2026-04-01T08:00:00Z" }),
    ]);

    const wrapper = mountComponent();
    await flushPromises();

    const rows = wrapper.findAll(".customer-plans-tab__row strong").map((node) => node.text());
    expect(rows).toEqual(["Alpha", "Bravo"]);
  });

  it("renders an explicit error state when planning-record loading fails", async () => {
    planningOrdersMocks.listPlanningRecordsMock.mockRejectedValue(new Error("boom"));
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.text()).toContain("customerAdmin.plans.errorTitle");
    expect(wrapper.text()).toContain("customerAdmin.plans.errorBody");
  });
});
