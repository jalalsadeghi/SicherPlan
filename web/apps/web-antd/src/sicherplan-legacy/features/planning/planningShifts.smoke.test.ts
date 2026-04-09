// @vitest-environment happy-dom

import { describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";

import PlanningShiftsAdminView from "../../views/PlanningShiftsAdminView.vue";

const {
  listShiftTypeOptionsMock,
  listShiftTemplatesMock,
  getShiftTemplateMock,
  listShiftPlansMock,
  listShiftSeriesMock,
  getShiftSeriesMock,
  listShiftSeriesExceptionsMock,
  listShiftsMock,
  getShiftMock,
  getShiftReleaseDiagnosticsMock,
} = vi.hoisted(() => ({
  listShiftTypeOptionsMock: vi.fn(async () => [
    { code: "site_day", label: "Site Day" },
    { code: "site_night", label: "Site Night" },
  ]),
  listShiftTemplatesMock: vi.fn(async () => [
  {
    id: "template-1",
    tenant_id: "tenant-1",
    code: "TPL-1",
    label: "Day shift",
    local_start_time: "08:00:00",
    local_end_time: "16:00:00",
    default_break_minutes: 30,
    shift_type_code: "day",
    status: "active",
    version_no: 1,
  },
  ]),
  getShiftTemplateMock: vi.fn(async () => ({
  id: "template-1",
  tenant_id: "tenant-1",
  code: "TPL-1",
  label: "Day shift",
  local_start_time: "08:00:00",
  local_end_time: "16:00:00",
  default_break_minutes: 30,
  shift_type_code: "day",
  meeting_point: "Gate A",
  location_text: "Berlin Mitte",
  notes: "Template detail note",
  status: "active",
  version_no: 1,
  })),
  listShiftPlansMock: vi.fn(async () => [
  {
    id: "plan-1",
    tenant_id: "tenant-1",
    planning_record_id: "planning-1",
    name: "Plan 1",
    workforce_scope_code: "internal",
    planning_from: "2026-04-01",
    planning_to: "2026-04-07",
    status: "active",
    version_no: 1,
  },
  ]),
  listShiftSeriesMock: vi.fn(async () => [
  {
    id: "series-1",
    tenant_id: "tenant-1",
    shift_plan_id: "plan-1",
    shift_template_id: "template-1",
    label: "Weekday series",
    recurrence_code: "weekly",
    interval_count: 1,
    weekday_mask: "1111100",
    timezone: "Europe/Berlin",
    date_from: "2026-04-01",
    date_to: "2026-04-07",
    release_state: "draft",
    customer_visible_flag: false,
    subcontractor_visible_flag: false,
    stealth_mode_flag: false,
    status: "active",
    version_no: 1,
  },
  ]),
  getShiftSeriesMock: vi.fn(async () => ({
  id: "series-1",
  tenant_id: "tenant-1",
  shift_plan_id: "plan-1",
  shift_template_id: "template-1",
  label: "Weekday series",
  recurrence_code: "weekly",
  interval_count: 1,
  weekday_mask: "1010100",
  timezone: "Europe/Berlin",
  date_from: "2026-04-01",
  date_to: "2026-04-07",
  release_state: "draft",
  customer_visible_flag: false,
  subcontractor_visible_flag: false,
  stealth_mode_flag: false,
  status: "active",
  version_no: 1,
  default_break_minutes: 25,
  shift_type_code: "day",
  meeting_point: "North gate",
  location_text: "Berlin Mitte",
  notes: "Series detail note",
  exceptions: [],
  })),
  listShiftSeriesExceptionsMock: vi.fn(async () => [
  {
    id: "exception-1",
    tenant_id: "tenant-1",
    shift_series_id: "series-1",
    exception_date: "2026-04-03",
    action_code: "override",
    override_local_start_time: "10:00:00",
    override_local_end_time: "18:00:00",
    notes: "Exception detail note",
    version_no: 1,
  },
  ]),
  listShiftsMock: vi.fn(async () => [
  {
    id: "shift-1",
    tenant_id: "tenant-1",
    shift_plan_id: "plan-1",
    shift_series_id: "series-1",
    occurrence_date: "2026-04-02",
    starts_at: "2026-04-02T08:00:00Z",
    ends_at: "2026-04-02T16:00:00Z",
    break_minutes: 30,
    shift_type_code: "day",
    location_text: "Berlin Mitte",
    meeting_point: "Gate A",
    release_state: "draft",
    customer_visible_flag: false,
    subcontractor_visible_flag: false,
    stealth_mode_flag: false,
    source_kind_code: "manual",
    status: "active",
    version_no: 1,
  },
  ]),
  getShiftMock: vi.fn(async () => ({
  id: "shift-1",
  tenant_id: "tenant-1",
  shift_plan_id: "plan-1",
  shift_series_id: "series-1",
  occurrence_date: "2026-04-02",
  starts_at: "2026-04-02T08:00:00Z",
  ends_at: "2026-04-02T16:00:00Z",
  break_minutes: 30,
  shift_type_code: "day",
  location_text: "Berlin Mitte",
  meeting_point: "Gate A",
  release_state: "draft",
  customer_visible_flag: false,
  subcontractor_visible_flag: false,
  stealth_mode_flag: false,
  source_kind_code: "manual",
  status: "active",
  version_no: 1,
  notes: "Shift detail note",
  released_at: null,
  released_by_user_id: null,
  created_at: "2026-04-01T08:00:00Z",
  updated_at: "2026-04-01T08:00:00Z",
  created_by_user_id: "user-1",
  updated_by_user_id: "user-1",
  archived_at: null,
  })),
  getShiftReleaseDiagnosticsMock: vi.fn(async () => ({
  tenant_id: "tenant-1",
  shift_id: "shift-1",
  release_state: "draft",
  customer_visible_flag: false,
  subcontractor_visible_flag: false,
  employee_visible: false,
  blocking_count: 1,
  warning_count: 1,
  issues: [
    { scope: "shift", code: "missing_assignment", severity: "blocking", message: "Assignments missing" },
    { scope: "shift", code: "note", severity: "warning", message: "Review meeting point" },
  ],
  })),
}));

vi.mock("@/api/planningShifts", () => ({
  copyShiftSlice: vi.fn(async () => ({})),
  createShift: vi.fn(async () => ({ id: "shift-1" })),
  createShiftPlan: vi.fn(async () => ({ id: "plan-1" })),
  createShiftSeries: vi.fn(async () => ({ id: "series-1" })),
  createShiftSeriesException: vi.fn(async () => ({ id: "exception-1" })),
  createShiftTemplate: vi.fn(async () => ({ id: "template-1" })),
  generateShiftSeries: vi.fn(async () => ({})),
  getShift: getShiftMock,
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
  getShiftReleaseDiagnostics: getShiftReleaseDiagnosticsMock,
  getShiftSeries: getShiftSeriesMock,
  getShiftTemplate: getShiftTemplateMock,
  listBoardShifts: vi.fn(async () => []),
  listShiftPlans: listShiftPlansMock,
  listShiftSeries: listShiftSeriesMock,
  listShiftSeriesExceptions: listShiftSeriesExceptionsMock,
  listShiftTypeOptions: listShiftTypeOptionsMock,
  listShiftTemplates: listShiftTemplatesMock,
  listShifts: listShiftsMock,
  setShiftReleaseState: vi.fn(async () => ({})),
  updateShift: vi.fn(async () => ({})),
  updateShiftPlan: vi.fn(async () => ({})),
  updateShiftSeriesException: vi.fn(async () => ({})),
  updateShiftSeries: vi.fn(async () => ({})),
  updateShiftTemplate: vi.fn(async () => ({})),
  updateShiftVisibility: vi.fn(async () => ({})),
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
    await flushPromises();

    expect(wrapper.text()).toContain("Select planning record");
    expect(wrapper.text()).toContain("All visibility states");
    expect(wrapper.text()).toContain("All release states");
    expect(listShiftTypeOptionsMock).toHaveBeenCalledWith("tenant-1", "token-1");
    expect(wrapper.html()).not.toMatch(/Shift type<\/span><input/);

    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    expect(wrapper.text()).toContain("Select shift template");
    expect(wrapper.html()).not.toContain('data-testid="planning-shifts-weekday-picker"');

    const recurrenceSelect = wrapper
      .findAll("select")
      .find((entry) => entry.element.outerHTML.includes("Daily") && entry.element.outerHTML.includes("Weekly"));
    await recurrenceSelect?.setValue("weekly");

    expect(wrapper.html()).toContain('data-testid="planning-shifts-weekday-picker"');
  });

  it("keeps legacy shift type values visible in the controlled select", async () => {
    const wrapper = mount(PlanningShiftsAdminView);
    await flushPromises();

    await wrapper.get(".planning-orders-row").trigger("click");
    await flushPromises();

    const templateSelect = wrapper.findAll('[data-testid="planning-shifts-tab-panel-templates"] select').at(0);
    expect(templateSelect?.html()).toContain("day (legacy)");
    expect((templateSelect?.element as HTMLSelectElement).value).toBe("day");
  });

  it("loads full template detail instead of using the list row only", async () => {
    const wrapper = mount(PlanningShiftsAdminView);
    await flushPromises();

    await wrapper.get(".planning-orders-row").trigger("click");
    await flushPromises();

    expect(getShiftTemplateMock).toHaveBeenCalledWith("tenant-1", "template-1", "token-1");
    expect((wrapper.get('[data-testid="planning-shifts-tab-panel-templates"] textarea').element as HTMLTextAreaElement).value).toBe("Template detail note");
    expect(
      wrapper
        .findAll('[data-testid="planning-shifts-tab-panel-templates"] input')
        .some((entry) => (entry.element as HTMLInputElement).value === "Berlin Mitte"),
    ).toBe(true);
  });

  it("lists existing series exceptions and loads them back into the editor", async () => {
    const wrapper = mount(PlanningShiftsAdminView);
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-row').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-row').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-form .planning-orders-row').trigger("click");
    await flushPromises();

    expect(getShiftSeriesMock).toHaveBeenCalledWith("tenant-1", "series-1", "token-1");
    expect(listShiftSeriesExceptionsMock).toHaveBeenCalledWith("tenant-1", "series-1", "token-1");
    expect(wrapper.text()).toContain("Series exceptions");
    expect(wrapper.text()).toContain("2026-04-03");
    expect((wrapper.findAll('[data-testid="planning-shifts-tab-panel-series"] textarea').at(1)?.element as HTMLTextAreaElement).value).toBe("Exception detail note");
  });

  it("shows release diagnostics for the selected shift", async () => {
    const wrapper = mount(PlanningShiftsAdminView);
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-row').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-shifts"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-shifts"] .planning-orders-row').trigger("click");
    await flushPromises();

    expect(getShiftMock).toHaveBeenCalledWith("tenant-1", "shift-1", "token-1");
    expect(getShiftReleaseDiagnosticsMock).toHaveBeenCalledWith("tenant-1", "shift-1", "token-1");
    expect(wrapper.find('[data-testid="planning-shifts-release-panel"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Assignments missing");
    expect(wrapper.text()).toContain("Review meeting point");
  });
});
