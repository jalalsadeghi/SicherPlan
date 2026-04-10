// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent, h } from "vue";

import PlanningShiftsAdminView from "../../views/PlanningShiftsAdminView.vue";

const {
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
  updateShiftTemplateMock,
} = vi.hoisted(() => ({
  createShiftPlanMock: vi.fn(async () => ({ id: "plan-1" })),
  createShiftSeriesMock: vi.fn(async () => ({ id: "series-1" })),
  createShiftTemplateMock: vi.fn(async () => ({ id: "template-1" })),
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
  createShiftSeriesException: vi.fn(async () => ({ id: "exception-1" })),
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
  updateShiftPlan: vi.fn(async () => ({})),
  updateShiftSeriesException: vi.fn(async () => ({})),
  updateShiftSeries: vi.fn(async () => ({})),
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
    createShiftPlanMock.mockClear();
    createShiftSeriesMock.mockClear();
    createShiftTemplateMock.mockClear();
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
    expect(wrapper.text()).toContain("Select shift template");
    expect(wrapper.text()).toContain("Plan 1");
    expect((wrapper.get('[data-testid="planning-shifts-series-plan-select"]').element as HTMLSelectElement).value).toBe("plan-1");
    expect((wrapper.get('[data-testid="planning-shifts-tab-panel-series"] button[type="submit"]').element as HTMLButtonElement).disabled).toBe(false);
    expect(wrapper.html()).not.toContain('data-testid="planning-shifts-weekday-picker"');

    const recurrenceSelect = wrapper
      .findAll("select")
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
    expect((wrapper.get('[data-testid="planning-shifts-tab-panel-series"] button[type="submit"]').element as HTMLButtonElement).disabled).toBe(true);
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
    expect((wrapper.findAll('[data-testid="planning-shifts-tab-panel-series"] textarea').at(1)?.element as HTMLTextAreaElement).value).toBe("Exception detail note");
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
    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] .planning-orders-panel__header .cta-button').trigger("click");
    await flushPromises();

    const planInputs = wrapper.findAll('[data-testid="planning-shifts-tab-panel-plans"] input');
    await planInputs.at(0)?.setValue("Fresh plan");
    await planInputs.at(1)?.setValue("2026-04-02");
    await planInputs.at(2)?.setValue("2026-04-06");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-plans"] form').trigger("submit");
    await flushPromises();

    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();

    expect(createShiftPlanMock).toHaveBeenCalled();
    expect(wrapper.get('[data-testid="planning-shifts-series-context"]').text()).toContain("Fresh plan");
    expect((wrapper.get('[data-testid="planning-shifts-tab-panel-series"] button[type="submit"]').element as HTMLButtonElement).disabled).toBe(false);
  });

  it("shows a clear error and avoids the API call when series save runs without a selected shift plan", async () => {
    listShiftPlansMock.mockResolvedValueOnce([]);

    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] form').trigger("submit");
    await flushPromises();

    expect(createShiftSeriesMock).not.toHaveBeenCalled();
    expect(showFeedbackToastMock).toHaveBeenCalledWith(
      expect.objectContaining({
        tone: "error",
        message: "A series can only be saved after a Shift Plan is selected.",
      }),
    );
  });

  it("uses the selected shift plan id for a valid series creation request", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.get('[data-testid="planning-shifts-tab-series"]').trigger("click");
    await flushPromises();

    const textInputs = wrapper
      .findAll('[data-testid="planning-shifts-tab-panel-series"] input')
      .filter((entry) => entry.attributes("type") !== "number");
    await wrapper.findAll('[data-testid="planning-shifts-tab-panel-series"] select').at(1)?.setValue("template-1");
    await textInputs.at(0)?.setValue("Weekday follow-up");
    await textInputs.at(2)?.setValue("2026-04-01");
    await textInputs.at(3)?.setValue("2026-04-05");
    await wrapper.get('[data-testid="planning-shifts-tab-panel-series"] form').trigger("submit");
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
