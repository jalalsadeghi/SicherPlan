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
  });

  it("suppresses the inner hero in embedded mode but keeps workspace tabs", () => {
    const wrapper = mount(PlanningShiftsAdminView, {
      props: {
        embedded: true,
      },
    });

    expect(wrapper.find(".planning-shifts-hero").exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-shifts-tabs"]').exists()).toBe(true);
  });
});
