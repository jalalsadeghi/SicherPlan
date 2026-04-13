// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent, h } from "vue";

import PlanningShiftsAdminView from "../../views/PlanningShiftsAdminView.vue";

const {
  createShiftSeriesExceptionMock,
  createShiftPlanMock,
  createShiftSeriesMock,
  createShiftTemplateMock,
  ensureSessionReadyMock,
  redirectToLoginMock,
  showFeedbackToastMock,
  listShiftTypeOptionsMock,
  listShiftTemplatesMock,
  getShiftTemplateMock,
  getShiftPlanMock,
  listShiftPlansMock,
  listShiftSeriesMock,
  getShiftSeriesMock,
  listShiftSeriesExceptionsMock,
  listShiftsMock,
  getShiftMock,
  getShiftReleaseDiagnosticsMock,
  updateShiftPlanMock,
  updateShiftSeriesExceptionMock,
  updateShiftSeriesMock,
  updateShiftTemplateMock,
} = vi.hoisted(() => ({
  createShiftSeriesExceptionMock: vi.fn(async () => ({ id: "exception-1" })),
  createShiftPlanMock: vi.fn(async () => ({ id: "plan-1" })),
  createShiftSeriesMock: vi.fn(async () => ({ id: "series-1" })),
  createShiftTemplateMock: vi.fn(async () => ({ id: "template-1" })),
  updateShiftPlanMock: vi.fn(async () => ({})),
  updateShiftSeriesExceptionMock: vi.fn(async () => ({})),
  updateShiftSeriesMock: vi.fn(async () => ({})),
  updateShiftTemplateMock: vi.fn(async () => ({})),
  ensureSessionReadyMock: vi.fn(async () => ({ id: "user-1" })),
  redirectToLoginMock: vi.fn(async () => {}),
  showFeedbackToastMock: vi.fn(),
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
    override_break_minutes: 45,
    override_shift_type_code: "site_night",
    override_meeting_point: "South gate",
    override_location_text: "Berlin South",
    customer_visible_flag: true,
    subcontractor_visible_flag: false,
    stealth_mode_flag: null,
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
  getShiftPlanMock: vi.fn(async () => ({
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
}));

vi.mock("@/api/planningShifts", () => ({
  copyShiftSlice: vi.fn(async () => ({})),
  createShift: vi.fn(async () => ({ id: "shift-1" })),
  createShiftPlan: createShiftPlanMock,
  createShiftSeries: createShiftSeriesMock,
  createShiftSeriesException: createShiftSeriesExceptionMock,
  createShiftTemplate: createShiftTemplateMock,
  generateShiftSeries: vi.fn(async () => ({})),
  getShift: getShiftMock,
  getShiftPlan: getShiftPlanMock,
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
  updateShiftPlan: updateShiftPlanMock,
  updateShiftSeriesException: updateShiftSeriesExceptionMock,
  updateShiftSeries: updateShiftSeriesMock,
  updateShiftTemplate: updateShiftTemplateMock,
  updateShiftVisibility: vi.fn(async () => ({})),
  PlanningShiftsApiError: class PlanningShiftsApiError extends Error {
    messageKey = "";
  },
}));

vi.mock("@/composables/useSicherPlanFeedback", () => ({
  useSicherPlanFeedback: () => ({
    showFeedbackToast: showFeedbackToastMock,
  }),
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
    effectiveTenantScopeId: "tenant-1",
    effectiveAccessToken: "token-1",
    tenantScopeId: "tenant-1",
    accessToken: "token-1",
    refreshToken: "refresh-1",
    sessionUser: { id: "user-1" },
    syncFromPrimarySession: vi.fn(),
    ensureSessionReady: ensureSessionReadyMock,
    clearSession: vi.fn(),
  }),
}));

vi.mock("#/store", () => ({
  useAuthStore: () => ({
    clearSessionState: vi.fn(),
    redirectToLogin: redirectToLoginMock,
  }),
}));

vi.mock("@/stores/locale", () => ({
  useLocaleStore: () => ({
    locale: "en",
  }),
}));

vi.mock("ant-design-vue", () => ({
  Modal: defineComponent({
    name: "AntdModalStub",
    props: {
      open: {
        type: Boolean,
        default: false,
      },
      title: {
        type: String,
        default: "",
      },
    },
    setup(props, { slots }) {
      return () =>
        props.open
          ? h("section", { class: "ant-modal-stub" }, [
              props.title ? h("h3", props.title) : null,
              slots.default?.(),
            ])
          : null;
    },
  }),
}));

function mountView(options: Record<string, unknown> = {}) {
  return mount(PlanningShiftsAdminView, {
    ...(options as object),
  });
}

describe("PlanningShiftsAdminView", () => {
  beforeEach(() => {
    createShiftSeriesExceptionMock.mockClear();
    createShiftPlanMock.mockClear();
    createShiftSeriesMock.mockClear();
    createShiftTemplateMock.mockClear();
    updateShiftPlanMock.mockClear();
    updateShiftSeriesExceptionMock.mockClear();
    updateShiftSeriesMock.mockClear();
    updateShiftTemplateMock.mockClear();
    ensureSessionReadyMock.mockClear();
    redirectToLoginMock.mockClear();
    showFeedbackToastMock.mockClear();
    getShiftPlanMock.mockClear();
    listShiftSeriesMock.mockClear();
    listShiftsMock.mockClear();
    listShiftPlansMock.mockReset();
    listShiftPlansMock.mockResolvedValue([
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
    ]);
  });

  it("mounts without setup crash and renders shift-planning sections", () => {
    const wrapper = mountView();

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
    const wrapper = mountView({
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
    const wrapper = mountView();
    await flushPromises();

    expect(wrapper.text()).toContain("Select planning record");
    expect(wrapper.text()).toContain("All visibility states");
    expect(wrapper.text()).toContain("All release states");
    expect(listShiftTypeOptionsMock).toHaveBeenCalledWith("tenant-1", "token-1");
    expect(wrapper.html()).not.toMatch(/Shift type<\/span><input/);

    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    expect(wrapper.text()).toContain("Plan 1");
    expect((wrapper.get('[data-testid="planning-shifts-series-plan-select"]').element as HTMLSelectElement).value).toBe("plan-1");
    expect(wrapper.find('[data-testid="planning-shifts-series-modal"]').exists()).toBe(false);

    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-panel__header .cta-button').trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("Select shift template");
    expect((wrapper.get('[data-testid="planning-shifts-series-modal-save"]').element as HTMLButtonElement).disabled).toBe(false);
    expect(wrapper.html()).not.toContain('data-testid="planning-shifts-weekday-picker"');

    const recurrenceSelect = wrapper
      .findAll('[data-testid="planning-shifts-series-modal"] select')
      .find((entry) => entry.element.outerHTML.includes("Daily") && entry.element.outerHTML.includes("Weekly"));
    await recurrenceSelect?.setValue("weekly");

    expect(wrapper.html()).toContain('data-testid="planning-shifts-weekday-picker"');
  });

  it("shows a visible explanation and keeps series save disabled when no shift plan is selected", async () => {
    listShiftPlansMock.mockResolvedValueOnce([]);

    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();

    expect(wrapper.get('[data-testid="planning-shifts-series-context"]').text()).toContain("No Shift Plan is available yet");
    expect((wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-panel__header .cta-button').element as HTMLButtonElement).disabled).toBe(true);
  });

  it("lets the operator change the active shift plan from inside the series workflow", async () => {
    listShiftPlansMock.mockResolvedValueOnce([
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
      {
        id: "plan-2",
        tenant_id: "tenant-1",
        planning_record_id: "planning-1",
        name: "Plan 2",
        workforce_scope_code: "mixed",
        planning_from: "2026-04-08",
        planning_to: "2026-04-14",
        status: "active",
        version_no: 1,
      },
    ]);
    getShiftPlanMock.mockResolvedValueOnce({
      id: "plan-2",
      tenant_id: "tenant-1",
      planning_record_id: "planning-1",
      name: "Plan 2",
      workforce_scope_code: "mixed",
      planning_from: "2026-04-08",
      planning_to: "2026-04-14",
      remarks: "",
      version_no: 1,
    });

    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-series-plan-select"]').setValue("plan-2");
    await flushPromises();

    expect(getShiftPlanMock).toHaveBeenCalledWith("tenant-1", "plan-2", "token-1");
    expect(listShiftSeriesMock).toHaveBeenCalledWith("tenant-1", "plan-2", "token-1");
    expect(wrapper.get('[data-testid="planning-shifts-series-context"]').text()).toContain("Plan 2");
  });

  it("opens the template modal from the new-template action and removes the old inline editor", async () => {
    const wrapper = mountView();
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-tab-panel-templates"] form').exists()).toBe(false);

    await wrapper.get('[data-testid="planning-shifts-create-template"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-template-modal"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("New shift template");
    expect(wrapper.find('[data-testid="planning-shifts-template-modal-save"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="planning-shifts-template-modal-cancel"]').exists()).toBe(true);
  });

  it("opens the plan modal from the new-plan action and removes the old inline editor", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-tab-panel-plans"] form').exists()).toBe(false);
    const headerActions = wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-panel__header');
    expect(headerActions.text()).toContain("Refresh");
    expect(headerActions.text()).toContain("New shift plan");

    await wrapper.get('[data-testid="planning-shifts-create-plan"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-plan-modal"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("New shift plan");
    expect(wrapper.find('[data-testid="planning-shifts-plan-modal-save"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="planning-shifts-plan-modal-cancel"]').exists()).toBe(true);
  });

  it("opens the plan modal in edit mode from a plan row and preserves plan selection", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-row').trigger("click");
    await flushPromises();

    expect(getShiftPlanMock).toHaveBeenCalledWith("tenant-1", "plan-1", "token-1");
    expect(wrapper.find('[data-testid="planning-shifts-plan-modal"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Edit shift plan");
    expect((wrapper.get('[data-testid="planning-shifts-plan-modal"] input').element as HTMLInputElement).value).toBe("Plan 1");

    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();
    expect(wrapper.get('[data-testid="planning-shifts-series-context"]').text()).toContain("Plan 1");
  });

  it("opens the series modal from the new-series action and removes the old inline editor", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-tab-panel-series"] form').exists()).toBe(false);

    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-panel__header .cta-button').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-series-modal"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("New series");
    expect(wrapper.find('[data-testid="planning-shifts-series-modal-save"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="planning-shifts-series-modal-cancel"]').exists()).toBe(true);
  });

  it("opens the series modal in edit mode from a series row and keeps exception workflow inline", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-row').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-row').trigger("click");
    await flushPromises();

    expect(getShiftSeriesMock).toHaveBeenCalledWith("tenant-1", "series-1", "token-1");
    expect(wrapper.find('[data-testid="planning-shifts-series-modal"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Edit series");
    expect((wrapper.get('[data-testid="planning-shifts-series-modal"] textarea').element as HTMLTextAreaElement).value).toBe("Series detail note");
    expect(wrapper.text()).toContain("Series exceptions");
  });

  it("closes the series modal on cancel without clearing the selected series", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-row').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-row').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-series-modal-cancel"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-series-modal"]').exists()).toBe(false);
    expect(wrapper.text()).toContain("Series exceptions");
  });

  it("closes the plan modal on cancel", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-create-plan"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-plan-modal-cancel"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-plan-modal"]').exists()).toBe(false);
  });

  it("opens the template modal in edit mode from a template row and keeps legacy shift type values visible", async () => {
    const wrapper = mountView();
    await flushPromises();

    await wrapper.get(".planning-orders-row").trigger("click");
    await flushPromises();

    expect(getShiftTemplateMock).toHaveBeenCalledWith("tenant-1", "template-1", "token-1");
    expect(wrapper.find('[data-testid="planning-shifts-template-modal"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Edit shift template");
    expect((wrapper.get('[data-testid="planning-shifts-template-modal"] textarea').element as HTMLTextAreaElement).value).toBe("Template detail note");
    expect(
      wrapper
        .findAll('[data-testid="planning-shifts-template-modal"] input')
        .some((entry) => (entry.element as HTMLInputElement).value === "Berlin Mitte"),
    ).toBe(true);
    const templateSelect = wrapper.findAll('[data-testid="planning-shifts-template-modal"] select').at(0);
    expect(templateSelect?.html()).toContain("day (legacy)");
    expect((templateSelect?.element as HTMLSelectElement).value).toBe("day");
  });

  it("closes the template modal on cancel", async () => {
    const wrapper = mountView();
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-create-template"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-template-modal-cancel"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-template-modal"]').exists()).toBe(false);
  });

  it("closes the template modal after a successful save", async () => {
    const wrapper = mountView();
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-create-template"]').trigger("click");
    await flushPromises();

    const modalInputs = wrapper.findAll('[data-testid="planning-shifts-template-modal"] input');
    await modalInputs.at(0)?.setValue("TPL-NEW");
    await modalInputs.at(1)?.setValue("New template");
    await modalInputs.at(2)?.setValue("08:00");
    await modalInputs.at(3)?.setValue("16:00");
    await wrapper.findAll('[data-testid="planning-shifts-template-modal"] select').at(0)?.setValue("site_day");
    await wrapper.get('[data-testid="planning-shifts-template-modal"]').trigger("submit");
    await flushPromises();

    expect(createShiftTemplateMock).toHaveBeenCalled();
    expect(wrapper.find('[data-testid="planning-shifts-template-modal"]').exists()).toBe(false);
  });

  it("lists existing series exceptions and loads them back into the editor", async () => {
    const wrapper = mountView();
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
    expect((wrapper.find('[data-testid="planning-shifts-tab-panel-series"] textarea').element as HTMLTextAreaElement).value).toBe("Exception detail note");
    expect((wrapper.get('[data-testid="planning-shifts-exception-override-break"]').element as HTMLInputElement).value).toBe("45");
    expect((wrapper.get('[data-testid="planning-shifts-exception-override-shift-type"]').element as HTMLSelectElement).value).toBe("site_night");
    expect((wrapper.get('[data-testid="planning-shifts-exception-customer-visibility"]').element as HTMLSelectElement).value).toBe("yes");
    expect((wrapper.get('[data-testid="planning-shifts-exception-subcontractor-visibility"]').element as HTMLSelectElement).value).toBe("no");
    expect((wrapper.get('[data-testid="planning-shifts-exception-stealth-visibility"]').element as HTMLSelectElement).value).toBe("inherit");
  });

  it("keeps the exception form minimal in skip mode", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-row').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-row').trigger("click");
    await flushPromises();

    expect((wrapper.get('[data-testid="planning-shifts-exception-action"]').element as HTMLSelectElement).value).toBe("skip");
    expect(wrapper.text()).not.toContain("Override break minutes");
    expect(wrapper.find('[data-testid="planning-shifts-exception-override-break"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-shifts-exception-override-shift-type"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-shifts-exception-customer-visibility"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-shifts-exception-subcontractor-visibility"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-shifts-exception-stealth-visibility"]').exists()).toBe(false);
  });

  it("shows the full override field set for override exceptions", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-row').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-row').trigger("click");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-exception-action"]').setValue("override");
    await flushPromises();

    expect(wrapper.text()).toContain("Override break minutes");
    expect(wrapper.text()).toContain("Override shift type");
    expect(wrapper.text()).toContain("Override meeting point");
    expect(wrapper.text()).toContain("Override location text");
    expect(wrapper.find('[data-testid="planning-shifts-exception-override-break"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="planning-shifts-exception-override-shift-type"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="planning-shifts-exception-customer-visibility"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="planning-shifts-exception-subcontractor-visibility"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="planning-shifts-exception-stealth-visibility"]').exists()).toBe(true);
  });

  it("preserves nullable visibility flags and clears override-only fields when switching back to skip", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-row').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-row').trigger("click");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-exception-action"]').setValue("override");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-exception-customer-visibility"]').setValue("yes");
    await wrapper.get('[data-testid="planning-shifts-exception-subcontractor-visibility"]').setValue("no");
    await wrapper.get('[data-testid="planning-shifts-exception-stealth-visibility"]').setValue("inherit");
    await wrapper.get('[data-testid="planning-shifts-exception-override-break"]').setValue("15");
    await wrapper.get('[data-testid="planning-shifts-exception-override-shift-type"]').setValue("site_day");

    await wrapper.get('[data-testid="planning-shifts-exception-action"]').setValue("skip");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-exception-override-break"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-shifts-exception-customer-visibility"]').exists()).toBe(false);

    await wrapper.get('[data-testid="planning-shifts-exception-action"]').setValue("override");
    await flushPromises();

    expect((wrapper.get('[data-testid="planning-shifts-exception-customer-visibility"]').element as HTMLSelectElement).value).toBe("inherit");
    expect((wrapper.get('[data-testid="planning-shifts-exception-subcontractor-visibility"]').element as HTMLSelectElement).value).toBe("inherit");
    expect((wrapper.get('[data-testid="planning-shifts-exception-stealth-visibility"]').element as HTMLSelectElement).value).toBe("inherit");
    expect((wrapper.get('[data-testid="planning-shifts-exception-override-break"]').element as HTMLInputElement).value).toBe("");
    expect((wrapper.get('[data-testid="planning-shifts-exception-override-shift-type"]').element as HTMLSelectElement).value).toBe("");
  });

  it("submits override exception payloads with nullable visibility flags and reused shift-type options", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-row').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-row').trigger("click");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-exception-action"]').setValue("override");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-exception-date"]').setValue("2026-04-05");
    await wrapper.get('[data-testid="planning-shifts-exception-override-start"]').setValue("09:00");
    await wrapper.get('[data-testid="planning-shifts-exception-override-end"]').setValue("17:00");
    await wrapper.get('[data-testid="planning-shifts-exception-override-break"]').setValue("30");
    await wrapper.get('[data-testid="planning-shifts-exception-override-shift-type"]').setValue("site_night");
    await wrapper.get('[data-testid="planning-shifts-exception-override-meeting-point"]').setValue("Gate B");
    await wrapper.get('[data-testid="planning-shifts-exception-override-location-text"]').setValue("Berlin West");
    await wrapper.get('[data-testid="planning-shifts-exception-customer-visibility"]').setValue("yes");
    await wrapper.get('[data-testid="planning-shifts-exception-subcontractor-visibility"]').setValue("no");
    await wrapper.get('[data-testid="planning-shifts-exception-stealth-visibility"]').setValue("inherit");

    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] form').trigger("submit");
    await flushPromises();

    expect(createShiftSeriesExceptionMock).toHaveBeenCalledWith(
      "tenant-1",
      "series-1",
      "token-1",
      expect.objectContaining({
        exception_date: "2026-04-05",
        action_code: "override",
        override_break_minutes: 30,
        override_shift_type_code: "site_night",
        override_meeting_point: "Gate B",
        override_location_text: "Berlin West",
        customer_visible_flag: true,
        subcontractor_visible_flag: false,
        stealth_mode_flag: null,
      }),
    );
  });

  it("keeps the created shift plan selected when switching to the series tab", async () => {
    listShiftPlansMock.mockResolvedValue([
      {
        id: "plan-99",
        tenant_id: "tenant-1",
        planning_record_id: "planning-1",
        name: "Fresh plan",
        workforce_scope_code: "mixed",
        planning_from: "2026-04-02",
        planning_to: "2026-04-06",
        status: "active",
        version_no: 1,
      },
    ]);
    createShiftPlanMock.mockResolvedValueOnce({ id: "plan-99" });
    getShiftPlanMock.mockResolvedValueOnce({
      id: "plan-99",
      tenant_id: "tenant-1",
      planning_record_id: "planning-1",
      name: "Fresh plan",
      workforce_scope_code: "mixed",
      planning_from: "2026-04-02",
      planning_to: "2026-04-06",
      remarks: "",
      version_no: 1,
    });

    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-create-plan"]').trigger("click");
    await flushPromises();

    const planInputs = wrapper.findAll('[data-testid="planning-shifts-plan-modal"] input');
    await planInputs.at(0)?.setValue("Fresh plan");
    await planInputs.at(1)?.setValue("2026-04-02");
    await planInputs.at(2)?.setValue("2026-04-06");
    await wrapper.get('[data-testid="planning-shifts-plan-modal"]').trigger("submit");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-plan-modal"]').exists()).toBe(false);
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();

    expect(createShiftPlanMock).toHaveBeenCalled();
    expect(wrapper.get('[data-testid="planning-shifts-series-context"]').text()).toContain("Fresh plan");
    expect((wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-panel__header .cta-button').element as HTMLButtonElement).disabled).toBe(false);
  });

  it("closes the plan modal after a successful edit save", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-row').trigger("click");
    await flushPromises();

    const planInputs = wrapper.findAll('[data-testid="planning-shifts-plan-modal"] input');
    await planInputs.at(0)?.setValue("Plan 1 updated");
    await wrapper.get('[data-testid="planning-shifts-plan-modal"]').trigger("submit");
    await flushPromises();

    expect(updateShiftPlanMock).toHaveBeenCalledWith(
      "tenant-1",
      "plan-1",
      "token-1",
      expect.objectContaining({ name: "Plan 1 updated" }),
    );
    expect(wrapper.find('[data-testid="planning-shifts-plan-modal"]').exists()).toBe(false);
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();
    expect((wrapper.get('[data-testid="planning-shifts-series-plan-select"]').element as HTMLSelectElement).value).toBe("plan-1");
    expect(wrapper.get('[data-testid="planning-shifts-series-context"]').text()).toContain("Plan 1");
  });

  it("shows a clear error and avoids the API call when series save runs without a selected shift plan", async () => {
    listShiftPlansMock.mockResolvedValueOnce([]);

    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    expect((wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-panel__header .cta-button').element as HTMLButtonElement).disabled).toBe(true);

    expect(createShiftSeriesMock).not.toHaveBeenCalled();
    expect(wrapper.get('[data-testid="planning-shifts-series-context"]').text()).toContain("No Shift Plan is available yet. Create one in the Shift Plans tab first.");
  });

  it("uses the selected shift plan id for a valid series creation request", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-panel__header .cta-button').trigger("click");
    await flushPromises();

    const textInputs = wrapper
      .findAll('[data-testid="planning-shifts-series-modal"] input')
      .filter((entry) => entry.attributes("type") !== "number");
    await wrapper.findAll('[data-testid="planning-shifts-series-modal"] select').at(0)?.setValue("template-1");
    await textInputs.at(0)?.setValue("Weekday follow-up");
    await textInputs.at(2)?.setValue("2026-04-01");
    await textInputs.at(3)?.setValue("2026-04-05");
    await wrapper.get('[data-testid="planning-shifts-series-modal"]').trigger("submit");
    await flushPromises();

    expect(createShiftSeriesMock).toHaveBeenCalledWith(
      "tenant-1",
      "plan-1",
      "token-1",
      expect.objectContaining({
        tenant_id: "tenant-1",
        shift_plan_id: "plan-1",
        shift_template_id: "template-1",
        label: "Weekday follow-up",
      }),
    );
    expect(wrapper.find('[data-testid="planning-shifts-series-modal"]').exists()).toBe(false);
  });

  it("closes the series modal after a successful edit save while preserving the selected series", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-plans"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-row').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] .planning-orders-row').trigger("click");
    await flushPromises();

    const seriesInputs = wrapper.findAll('[data-testid="planning-shifts-series-modal"] input');
    await seriesInputs.at(0)?.setValue("Weekday series updated");
    await wrapper.get('[data-testid="planning-shifts-series-modal"]').trigger("submit");
    await flushPromises();

    expect(updateShiftSeriesMock).toHaveBeenCalledWith(
      "tenant-1",
      "series-1",
      "token-1",
      expect.objectContaining({ label: "Weekday series updated" }),
    );
    expect(wrapper.find('[data-testid="planning-shifts-series-modal"]').exists()).toBe(false);
    expect(wrapper.text()).toContain("Series exceptions");
  });

  it("shows release diagnostics for the selected shift", async () => {
    const wrapper = mountView();
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

  it("shows the active shift plan selector in the shifts tab too", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-shifts"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-shifts-shifts-plan-select"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="planning-shifts-shifts-plan-select"]').element as HTMLSelectElement).value).toBe("plan-1");
  });

  it("recovers the session and refreshes the active tab when the page becomes visible again", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();
    listShiftSeriesMock.mockClear();

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });

    document.dispatchEvent(new Event("visibilitychange"));
    await flushPromises();

    expect(ensureSessionReadyMock).toHaveBeenCalled();
    expect(listShiftSeriesMock).toHaveBeenCalledWith("tenant-1", "plan-1", "token-1");
    wrapper.unmount();
  });
});
