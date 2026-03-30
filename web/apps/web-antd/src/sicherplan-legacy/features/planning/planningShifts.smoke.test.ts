// @vitest-environment happy-dom

import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";

import PlanningShiftsAdminView from "../../views/PlanningShiftsAdminView.vue";

vi.mock("@/api/planningShifts", () => ({
  copyShiftSlice: vi.fn(async () => ({})),
  createShift: vi.fn(async () => ({ id: "shift-1" })),
  createShiftPlan: vi.fn(async () => ({ id: "plan-1" })),
  createShiftSeries: vi.fn(async () => ({ id: "series-1" })),
  createShiftSeriesException: vi.fn(async () => ({ id: "exception-1" })),
  createShiftTemplate: vi.fn(async () => ({ id: "template-1" })),
  generateShiftSeries: vi.fn(async () => ({})),
  getShiftPlan: vi.fn(async () => ({
    id: "plan-1",
    tenant_id: "tenant-1",
    planning_record_id: "planning-1",
    name: "Plan 1",
    workforce_scope_code: "internal",
    planning_from: "2026-04-01",
    planning_to: "2026-04-02",
    remarks: "",
    version_no: 1,
  })),
  listBoardShifts: vi.fn(async () => []),
  listShiftPlans: vi.fn(async () => []),
  listShiftSeries: vi.fn(async () => []),
  listShiftTemplates: vi.fn(async () => []),
  listShifts: vi.fn(async () => []),
  updateShift: vi.fn(async () => ({})),
  updateShiftPlan: vi.fn(async () => ({})),
  updateShiftSeries: vi.fn(async () => ({})),
  updateShiftTemplate: vi.fn(async () => ({})),
  PlanningShiftsApiError: class PlanningShiftsApiError extends Error {
    messageKey = "";
  },
}));

vi.mock("@/api/planningOrders", () => ({
  listPlanningRecords: vi.fn(async () => [
    {
      id: "planning-1",
      tenant_id: "tenant-1",
      order_id: "order-1",
      parent_planning_record_id: null,
      dispatcher_user_id: null,
      planning_mode_code: "site",
      name: "Planning Record 1",
      planning_from: "2026-04-01",
      planning_to: "2026-04-07",
      release_state: "draft",
      released_at: null,
      status: "active",
      version_no: 1,
    },
  ]),
}));

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    effectiveRole: "tenant_admin",
    tenantScopeId: "tenant-1",
    accessToken: "token-1",
  }),
}));

vi.mock("@/stores/locale", () => ({
  useLocaleStore: () => ({
    locale: "en",
  }),
}));

describe("PlanningShiftsAdminView", () => {
  it("mounts without setup crash and renders shift-planning sections", () => {
    const wrapper = mount(PlanningShiftsAdminView);

    expect(wrapper.text()).toContain("Shift templates");
    expect(wrapper.text()).toContain("Shift plans");
    expect(wrapper.text()).toContain("Series and exceptions");
    expect(wrapper.text()).toContain("Concrete shifts");
    expect(wrapper.text()).toContain("Board preview");
    expect(wrapper.text()).not.toContain("Tenant scope");
    expect(wrapper.text()).not.toContain("Bearer token");
    expect(wrapper.text()).not.toContain("Remember scope and token");
  });

  it("suppresses the inner hero in embedded mode but keeps workspace tabs", () => {
    const wrapper = mount(PlanningShiftsAdminView, {
      props: {
        embedded: true,
      },
    });

    expect(wrapper.find(".planning-shifts-hero").exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-shifts-tabs"]').exists()).toBe(true);
    expect(wrapper.text()).not.toContain("Shift planning");
    expect(wrapper.text()).not.toContain("Shift plans, templates, series, and concrete shifts");
    expect(wrapper.text()).not.toContain("Tenant scope");
    expect(wrapper.text()).not.toContain("Bearer token");
  });

  it("renders structured planning-shifts controls instead of the old raw text fields", async () => {
    const wrapper = mount(PlanningShiftsAdminView);

    expect(wrapper.text()).toContain("Select planning record");
    expect(wrapper.text()).toContain("All visibility states");
    expect(wrapper.text()).toContain("All release states");

    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    expect(wrapper.text()).toContain("Select shift template");
    expect(wrapper.html()).not.toContain('data-testid="planning-shifts-weekday-picker"');

    const recurrenceSelect = wrapper
      .findAll("select")
      .find((entry) => entry.element.outerHTML.includes("Daily") && entry.element.outerHTML.includes("Weekly"));
    await recurrenceSelect?.setValue("weekly");

    expect(wrapper.html()).toContain('data-testid="planning-shifts-weekday-picker"');
  });
});
