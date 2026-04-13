// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent } from "vue";

const sessionState = vi.hoisted(() => ({
  accessToken: "token-1",
  role: "dispatcher",
  tenantId: "tenant-1",
}));

const mocks = vi.hoisted(() => ({
  assignStaffingMock: vi.fn(async () => ({
    tenant_id: "tenant-1",
    shift_id: "shift-1",
    assignment_id: "assignment-new",
    outcome_code: "assigned",
    validation_codes: [],
    conflict_code: null,
    assignment: null,
  })),
  createDemandGroupMock: vi.fn(async () => ({
    id: "dg-new",
    tenant_id: "tenant-1",
    shift_id: "shift-1",
    function_type_id: "func-1",
    qualification_type_id: null,
    min_qty: 1,
    target_qty: 2,
    mandatory_flag: true,
    sort_order: 100,
    remark: null,
    status: "active",
    version_no: 1,
    created_at: "2026-04-05T08:00:00Z",
    updated_at: "2026-04-05T08:00:00Z",
    archived_at: null,
  })),
  createTeamMock: vi.fn(async () => ({
    id: "team-planning-new",
    tenant_id: "tenant-1",
    planning_record_id: "planning-1",
    shift_id: null,
    name: "Planung Alpha",
    role_label: null,
    status: "active",
    version_no: 1,
    notes: null,
    members: [],
  })),
  createTeamMemberMock: vi.fn(async () => ({
    id: "member-new",
    tenant_id: "tenant-1",
    team_id: "team-planning-new",
    employee_id: "employee-1",
    subcontractor_worker_id: null,
    role_label: "Lead",
    is_team_lead: true,
    valid_from: "2026-04-05T08:00:00Z",
    valid_to: null,
    status: "active",
    version_no: 1,
    notes: null,
  })),
  createAssignmentValidationOverrideMock: vi.fn(async () => ({})),
  ensureSessionReadyMock: vi.fn(async () => true),
  listAssignmentValidationOverridesMock: vi.fn(async () => []),
  listDemandGroupsMock: vi.fn(async () => [
    {
      id: "dg-1",
      tenant_id: "tenant-1",
      shift_id: "shift-1",
      function_type_id: "func-1",
      qualification_type_id: null,
      min_qty: 1,
      target_qty: 2,
      mandatory_flag: true,
      sort_order: 100,
      remark: null,
      status: "active",
      version_no: 1,
      created_at: "2026-04-05T08:00:00Z",
      updated_at: "2026-04-05T08:00:00Z",
      archived_at: null,
    },
  ]),
  listShiftOutputsMock: vi.fn(async () => []),
  listStaffingBoardMock: vi.fn(async () => [
    {
      id: "shift-1",
      tenant_id: "tenant-1",
      planning_record_id: "planning-1",
      shift_plan_id: "plan-1",
      order_id: "order-1",
      order_no: "ORD-1",
      planning_record_name: "Planning 1",
      planning_mode_code: "site",
      workforce_scope_code: "internal",
      starts_at: "2026-04-05T08:00:00Z",
      ends_at: "2026-04-05T16:00:00Z",
      shift_type_code: "site_day",
      release_state: "draft",
      status: "active",
      location_text: "Berlin",
      meeting_point: "Gate A",
      demand_groups: [
        {
          id: "dg-1",
          shift_id: "shift-1",
          function_type_id: "func-1",
          qualification_type_id: "qual-1",
          min_qty: 1,
          target_qty: 2,
          mandatory_flag: true,
          assigned_count: 1,
          confirmed_count: 1,
          released_partner_qty: 0,
        },
      ],
      assignments: [
        {
          id: "assignment-1",
          shift_id: "shift-1",
          demand_group_id: "dg-1",
          team_id: "team-1",
          employee_id: "employee-1",
          subcontractor_worker_id: null,
          assignment_status_code: "assigned",
          assignment_source_code: "dispatcher",
          confirmed_at: null,
          version_no: 1,
        },
      ],
    },
  ]),
  listStaffingCoverageMock: vi.fn(async () => [
    {
      shift_id: "shift-1",
      planning_record_id: "planning-1",
      shift_plan_id: "plan-1",
      order_id: "order-1",
      order_no: "ORD-1",
      planning_record_name: "Planning 1",
      planning_mode_code: "site",
      workforce_scope_code: "internal",
      starts_at: "2026-04-05T08:00:00Z",
      ends_at: "2026-04-05T16:00:00Z",
      shift_type_code: "site_day",
      location_text: "Berlin",
      meeting_point: "Gate A",
      min_required_qty: 1,
      target_required_qty: 2,
      assigned_count: 1,
      confirmed_count: 1,
      released_partner_qty: 0,
      coverage_state: "yellow",
      demand_groups: [
        {
          demand_group_id: "dg-1",
          function_type_id: "func-1",
          qualification_type_id: "qual-1",
          min_qty: 1,
          target_qty: 2,
          assigned_count: 1,
          confirmed_count: 1,
          released_partner_qty: 0,
          coverage_state: "yellow",
        },
      ],
    },
  ]),
  listSubcontractorReleasesMock: vi.fn(async () => []),
  listFunctionTypesMock: vi.fn(async () => [
    {
      id: "func-1",
      tenant_id: "tenant-1",
      code: "SEC_GUARD",
      label: "Sicherheitsdienst",
      category: null,
      description: null,
      is_active: true,
      planning_relevant: true,
      status: "active",
      created_at: "2026-04-01T00:00:00Z",
      updated_at: "2026-04-01T00:00:00Z",
      archived_at: null,
      version_no: 1,
    },
  ]),
  listQualificationTypesMock: vi.fn(async () => [
    {
      id: "qual-1",
      tenant_id: "tenant-1",
      code: "G34A",
      label: "G34a",
      category: null,
      description: null,
      is_active: true,
      planning_relevant: true,
      compliance_relevant: true,
      expiry_required: false,
      default_validity_days: null,
      proof_required: false,
      status: "active",
      created_at: "2026-04-01T00:00:00Z",
      updated_at: "2026-04-01T00:00:00Z",
      archived_at: null,
      version_no: 1,
    },
  ]),
  listEmployeesMock: vi.fn(async () => [
    {
      id: "employee-1",
      tenant_id: "tenant-1",
      personnel_no: "E-1",
      first_name: "Alex",
      last_name: "Muster",
      preferred_name: null,
      work_email: null,
      mobile_phone: null,
      default_branch_id: null,
      default_mandate_id: null,
      hire_date: null,
      termination_date: null,
      status: "active",
      created_at: "2026-04-01T00:00:00Z",
      updated_at: "2026-04-01T00:00:00Z",
      archived_at: null,
      version_no: 1,
    },
  ]),
  listPlanningRecordsMock: vi.fn(async () => [
    {
      id: "planning-1",
      tenant_id: "tenant-1",
      order_id: "order-1",
      parent_planning_record_id: null,
      dispatcher_user_id: "user-1",
      planning_mode_code: "site",
      name: "Planning 1",
      planning_from: "2026-04-05",
      planning_to: "2026-04-06",
      release_state: "draft",
      released_at: null,
      status: "active",
      version_no: 1,
    },
  ]),
  getPlanningRecordMock: vi.fn(async () => ({
    id: "planning-1",
    tenant_id: "tenant-1",
    order_id: "order-1",
    parent_planning_record_id: null,
    dispatcher_user_id: "user-1",
    planning_mode_code: "site",
    name: "Planning 1",
    planning_from: "2026-04-05",
    planning_to: "2026-04-06",
    release_state: "draft",
    released_at: null,
    status: "active",
    version_no: 1,
    notes: null,
    order: null,
    event_detail: null,
    site_detail: null,
    trade_fair_detail: null,
    patrol_detail: null,
  })),
  listTeamMembersMock: vi.fn(async () => [
    {
      id: "member-1",
      tenant_id: "tenant-1",
      team_id: "team-1",
      employee_id: "employee-1",
      subcontractor_worker_id: null,
      role_label: "Lead",
      is_team_lead: true,
      valid_from: "2026-04-01T00:00:00Z",
      valid_to: null,
      status: "active",
      version_no: 1,
      notes: null,
    },
  ]),
  listTeamsMock: vi.fn(async () => [
    {
      id: "team-1",
      tenant_id: "tenant-1",
      planning_record_id: "planning-1",
      shift_id: null,
      name: "Planung Alpha",
      role_label: "Lead",
      status: "active",
      version_no: 1,
      notes: "Planungsteam",
      members: [{ id: "member-1" }],
    },
    {
      id: "team-shift-1",
      tenant_id: "tenant-1",
      planning_record_id: "planning-1",
      shift_id: "shift-1",
      name: "Schicht Bravo",
      role_label: "Lead",
      status: "active",
      version_no: 1,
      notes: null,
      members: [{ id: "member-1" }],
    },
  ]),
  listSubcontractorWorkersMock: vi.fn(async () => [
    {
      id: "worker-1",
      tenant_id: "tenant-1",
      subcontractor_id: "sub-1",
      worker_no: "W-1",
      first_name: "Pat",
      last_name: "Partner",
      preferred_name: null,
      email: null,
      mobile: null,
      status: "active",
      archived_at: null,
      version_no: 1,
    },
  ]),
  getAssignmentValidationsMock: vi.fn(async () => ({ blocking_count: 0, warning_count: 0, info_count: 0, issues: [] })),
  getShiftReleaseValidationsMock: vi.fn(async () => ({ blocking_count: 0, warning_count: 0, issues: [] })),
  previewShiftDispatchMessageMock: vi.fn(async () => null),
  queueShiftDispatchMessageMock: vi.fn(async () => ({ id: "dispatch-1" })),
  redirectToLoginMock: vi.fn(async () => {}),
  substituteStaffingMock: vi.fn(async () => ({
    tenant_id: "tenant-1",
    shift_id: "shift-1",
    assignment_id: "assignment-sub",
    outcome_code: "substituted",
    validation_codes: [],
    conflict_code: null,
    assignment: null,
  })),
  updateDemandGroupMock: vi.fn(async () => ({
    id: "dg-1",
    tenant_id: "tenant-1",
    shift_id: "shift-1",
    function_type_id: "func-1",
    qualification_type_id: null,
    min_qty: 2,
    target_qty: 2,
    mandatory_flag: true,
    sort_order: 100,
    remark: null,
    status: "active",
    version_no: 2,
    created_at: "2026-04-05T08:00:00Z",
    updated_at: "2026-04-05T09:00:00Z",
    archived_at: null,
  })),
  updateAssignmentMock: vi.fn(async () => ({
    id: "assignment-1",
    shift_id: "shift-1",
    demand_group_id: "dg-1",
    team_id: "team-shift-1",
    employee_id: "employee-1",
    subcontractor_worker_id: null,
    assignment_status_code: "assigned",
    assignment_source_code: "dispatcher",
    confirmed_at: null,
    version_no: 2,
  })),
  updateTeamMock: vi.fn(async () => ({
    id: "team-1",
    tenant_id: "tenant-1",
    planning_record_id: "planning-1",
    shift_id: null,
    name: "Planung Alpha",
    role_label: "Lead",
    status: "active",
    version_no: 2,
    notes: "Planungsteam",
    members: [],
  })),
  updateTeamMemberMock: vi.fn(async () => ({
    id: "member-1",
    tenant_id: "tenant-1",
    team_id: "team-1",
    employee_id: "employee-1",
    subcontractor_worker_id: null,
    role_label: "Lead",
    is_team_lead: true,
    valid_from: "2026-04-05T08:00:00Z",
    valid_to: null,
    status: "active",
    version_no: 2,
    notes: null,
  })),
  unassignStaffingMock: vi.fn(async () => ({
    tenant_id: "tenant-1",
    shift_id: "shift-1",
    assignment_id: "assignment-1",
    outcome_code: "unassigned",
    validation_codes: [],
    conflict_code: null,
    assignment: null,
  })),
}));

vi.mock("#/store", () => ({
  useAuthStore: () => ({
    clearSessionState: vi.fn(),
    redirectToLogin: mocks.redirectToLoginMock,
  }),
}));

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => ({
    effectiveAccessToken: sessionState.accessToken,
    effectiveRole: sessionState.role,
    effectiveTenantScopeId: sessionState.tenantId,
    tenantScopeId: sessionState.tenantId,
    accessToken: sessionState.accessToken,
    refreshToken: "refresh-1",
    sessionUser: { id: "user-1" },
    syncFromPrimarySession: vi.fn(),
    ensureSessionReady: mocks.ensureSessionReadyMock,
    clearSession: vi.fn(),
  }),
}));

vi.mock("@/stores/locale", () => ({
  useLocaleStore: () => ({
    locale: "de",
  }),
}));

vi.mock("@/api/planningStaffing", () => ({
  assignStaffing: mocks.assignStaffingMock,
  createTeam: mocks.createTeamMock,
  createTeamMember: mocks.createTeamMemberMock,
  createDemandGroup: mocks.createDemandGroupMock,
  createAssignmentValidationOverride: mocks.createAssignmentValidationOverrideMock,
  generateShiftOutput: vi.fn(async () => ({})),
  getTeam: vi.fn(async () => ({
    id: "team-1",
    tenant_id: "tenant-1",
    planning_record_id: "planning-1",
    shift_id: null,
    name: "Planung Alpha",
    role_label: "Lead",
    status: "active",
    version_no: 1,
    notes: "Planungsteam",
    members: [],
  })),
  getAssignmentValidations: mocks.getAssignmentValidationsMock,
  getShiftReleaseValidations: mocks.getShiftReleaseValidationsMock,
  listAssignmentValidationOverrides: mocks.listAssignmentValidationOverridesMock,
  listDemandGroups: mocks.listDemandGroupsMock,
  listShiftOutputs: mocks.listShiftOutputsMock,
  listStaffingBoard: mocks.listStaffingBoardMock,
  listStaffingCoverage: mocks.listStaffingCoverageMock,
  listSubcontractorReleases: mocks.listSubcontractorReleasesMock,
  listTeamMembers: mocks.listTeamMembersMock,
  listTeams: mocks.listTeamsMock,
  previewShiftDispatchMessage: mocks.previewShiftDispatchMessageMock,
  queueShiftDispatchMessage: mocks.queueShiftDispatchMessageMock,
  substituteStaffing: mocks.substituteStaffingMock,
  unassignStaffing: mocks.unassignStaffingMock,
  updateAssignment: mocks.updateAssignmentMock,
  updateDemandGroup: mocks.updateDemandGroupMock,
  updateTeam: mocks.updateTeamMock,
  updateTeamMember: mocks.updateTeamMemberMock,
  PlanningStaffingApiError: class PlanningStaffingApiError extends Error {
    messageKey = "";
  },
}));

vi.mock("@/api/planningOrders", () => ({
  getPlanningRecord: mocks.getPlanningRecordMock,
  listPlanningRecords: mocks.listPlanningRecordsMock,
}));

vi.mock("@/api/employeeAdmin", () => ({
  listEmployees: mocks.listEmployeesMock,
  listFunctionTypes: mocks.listFunctionTypesMock,
  listQualificationTypes: mocks.listQualificationTypesMock,
}));

vi.mock("@/api/subcontractors", () => ({
  listSubcontractorWorkers: mocks.listSubcontractorWorkersMock,
}));

vi.mock("ant-design-vue", async () => {
  const actual = await vi.importActual<typeof import("ant-design-vue")>("ant-design-vue");
  return {
    ...actual,
    Modal: defineComponent({
      props: {
        open: { type: Boolean, default: false },
        title: { type: String, default: "" },
      },
      emits: ["cancel", "update:open"],
      template: `
        <div v-if="open" class="modal-stub">
          <strong class="modal-stub__title">{{ title }}</strong>
          <slot />
        </div>
      `,
    }),
  };
});

async function mountView() {
  const { default: PlanningStaffingCoverageView } = await import("../../views/PlanningStaffingCoverageView.vue");
  const wrapper = mount(PlanningStaffingCoverageView);
  await flushPromises();
  return wrapper;
}

async function clickDetailTab(wrapper: Awaited<ReturnType<typeof mountView>>, tabId: string) {
  await wrapper.get(`#planning-staffing-tab-${tabId}`).trigger("click");
  await flushPromises();
}

describe("PlanningStaffingCoverageView", () => {
  beforeEach(() => {
    sessionState.role = "dispatcher";
    sessionState.tenantId = "tenant-1";
    sessionState.accessToken = "token-1";
    for (const mock of Object.values(mocks)) {
      mock.mockClear();
    }
    mocks.ensureSessionReadyMock.mockResolvedValue(true);
    mocks.listPlanningRecordsMock.mockResolvedValue([
      {
        id: "planning-1",
        tenant_id: "tenant-1",
        order_id: "order-1",
        parent_planning_record_id: null,
        dispatcher_user_id: "user-1",
        planning_mode_code: "site",
        name: "Planning 1",
        planning_from: "2026-04-05",
        planning_to: "2026-04-06",
        release_state: "draft",
        released_at: null,
        status: "active",
        version_no: 1,
      },
    ]);
    mocks.listStaffingCoverageMock.mockResolvedValue([
      {
        shift_id: "shift-1",
        planning_record_id: "planning-1",
        shift_plan_id: "plan-1",
        order_id: "order-1",
        order_no: "ORD-1",
        planning_record_name: "Planning 1",
        planning_mode_code: "site",
        workforce_scope_code: "internal",
        starts_at: "2026-04-05T08:00:00Z",
        ends_at: "2026-04-05T16:00:00Z",
        shift_type_code: "site_day",
        location_text: "Berlin",
        meeting_point: "Gate A",
        min_required_qty: 1,
        target_required_qty: 2,
        assigned_count: 1,
        confirmed_count: 1,
        released_partner_qty: 0,
        coverage_state: "yellow",
        demand_groups: [
          {
            demand_group_id: "dg-1",
            function_type_id: "func-1",
            qualification_type_id: "qual-1",
            min_qty: 1,
            target_qty: 2,
            assigned_count: 1,
            confirmed_count: 1,
            released_partner_qty: 0,
            coverage_state: "yellow",
          },
        ],
      },
    ]);
    mocks.listStaffingBoardMock.mockResolvedValue([
      {
        id: "shift-1",
        tenant_id: "tenant-1",
        planning_record_id: "planning-1",
        shift_plan_id: "plan-1",
        order_id: "order-1",
        order_no: "ORD-1",
        planning_record_name: "Planning 1",
        planning_mode_code: "site",
        workforce_scope_code: "internal",
        starts_at: "2026-04-05T08:00:00Z",
        ends_at: "2026-04-05T16:00:00Z",
        shift_type_code: "site_day",
        release_state: "draft",
        status: "active",
        location_text: "Berlin",
        meeting_point: "Gate A",
        demand_groups: [
          {
            id: "dg-1",
            shift_id: "shift-1",
            function_type_id: "func-1",
            qualification_type_id: "qual-1",
            min_qty: 1,
            target_qty: 2,
            mandatory_flag: true,
            assigned_count: 1,
            confirmed_count: 1,
            released_partner_qty: 0,
          },
        ],
        assignments: [
          {
            id: "assignment-1",
            shift_id: "shift-1",
            demand_group_id: "dg-1",
            team_id: "team-1",
            employee_id: "employee-1",
            subcontractor_worker_id: null,
            assignment_status_code: "assigned",
            assignment_source_code: "dispatcher",
            confirmed_at: null,
            version_no: 1,
          },
        ],
      },
    ]);
  });

  it("renders from session context without manual token inputs", async () => {
    const wrapper = await mountView();
    const firstPanel = wrapper.findAll(".planning-staffing-panel")[0];

    expect(wrapper.find('[data-testid="planning-staffing-workspace"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="planning-staffing-planning-record-select"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="planning-staffing-refresh"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Filter und Scope");
    expect(wrapper.text()).toContain("Planungsdatensatz");
    expect(wrapper.text()).toContain("Planungsmodus auswaehlen");
    expect(wrapper.text()).toContain("Workforce-Scope auswaehlen");
    expect(wrapper.text()).toContain("Bestaetigungsstatus auswaehlen");
    expect(wrapper.text()).not.toContain("Planungsdatensatz-ID");
    expect(wrapper.text()).not.toContain("Coverage lesen");
    expect(wrapper.text()).not.toContain("Staffing schreiben");
    expect(wrapper.text()).not.toContain("Override erfassen");
    expect(wrapper.text()).not.toContain("Staffing-Validierungen");
    expect(wrapper.text()).not.toContain("Sessionbasierter Scope");
    expect(wrapper.text()).not.toContain("Bearer-Token");
    expect(firstPanel?.text()).not.toContain("Mitarbeiterverwaltung oeffnen");
    expect(firstPanel?.text()).not.toContain("Subunternehmerverwaltung oeffnen");
    expect(mocks.listStaffingCoverageMock).toHaveBeenCalledWith("tenant-1", "token-1", expect.any(Object));
    expect(mocks.listFunctionTypesMock).toHaveBeenCalledWith("tenant-1", "token-1");
    expect(mocks.listQualificationTypesMock).toHaveBeenCalledWith("tenant-1", "token-1");
  });

  it("hides the staffing workspace behind permission gating for controller_qm", async () => {
    sessionState.role = "controller_qm";

    const wrapper = await mountView();

    expect(wrapper.text()).toContain("Berechtigung fehlt");
    expect(wrapper.find('[data-testid="planning-staffing-assign-action"]').exists()).toBe(false);
  });

  it("runs assign, unassign, and substitute through the real staffing commands and refreshes coverage", async () => {
    const wrapper = await mountView();
    await wrapper.get('[data-testid="planning-staffing-assign-action"]').trigger("click");
    expect(mocks.assignStaffingMock).not.toHaveBeenCalled();

    await wrapper.get('[data-testid="planning-staffing-team-select"]').setValue("team-1");
    await wrapper.get('[data-testid="planning-staffing-member-select"]').setValue("member-1");
    await wrapper.get('[data-testid="planning-staffing-assign-action"]').trigger("click");
    await flushPromises();

    expect(mocks.assignStaffingMock).toHaveBeenCalledTimes(1);
    expect(mocks.assignStaffingMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        team_id: "team-1",
        employee_id: "employee-1",
        subcontractor_worker_id: null,
        confirmed_at: null,
      }),
    );
    expect(mocks.listStaffingCoverageMock.mock.calls.length).toBeGreaterThan(1);

    await wrapper.get('[data-testid="planning-staffing-unassign-action"]').trigger("click");
    await flushPromises();
    expect(mocks.unassignStaffingMock).toHaveBeenCalledTimes(1);

    await wrapper.get('[data-testid="planning-staffing-team-select"]').setValue("team-1");
    await wrapper.get('[data-testid="planning-staffing-member-select"]').setValue("member-1");
    await wrapper.get('[data-testid="planning-staffing-substitute-action"]').trigger("click");
    await flushPromises();
    expect(mocks.substituteStaffingMock).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).not.toContain("Sofort bestaetigen");
    expect(mocks.listStaffingBoardMock.mock.calls.length).toBeGreaterThan(1);
  });

  it("sends confirmed_at only for assign when confirmation-at-creation is checked", async () => {
    mocks.listStaffingBoardMock.mockResolvedValueOnce([
      {
        id: "shift-1",
        tenant_id: "tenant-1",
        planning_record_id: "planning-1",
        shift_plan_id: "plan-1",
        order_id: "order-1",
        order_no: "ORD-1",
        planning_record_name: "Planning 1",
        planning_mode_code: "site",
        workforce_scope_code: "internal",
        starts_at: "2026-04-05T08:00:00Z",
        ends_at: "2026-04-05T16:00:00Z",
        shift_type_code: "site_day",
        release_state: "draft",
        status: "active",
        location_text: "Berlin",
        meeting_point: "Gate A",
        demand_groups: [
          {
            id: "dg-1",
            shift_id: "shift-1",
            function_type_id: "func-1",
            qualification_type_id: "qual-1",
            min_qty: 1,
            target_qty: 2,
            mandatory_flag: true,
            assigned_count: 0,
            confirmed_count: 0,
            released_partner_qty: 0,
          },
        ],
        assignments: [],
      },
    ]);

    const wrapper = await mountView();

    expect(wrapper.text()).toContain("Zuweisung jetzt als bestaetigt anlegen");
    expect(wrapper.text()).toContain("Aktiviert setzt beim Zuweisen sofort einen Bestaetigungszeitpunkt.");

    await wrapper.get('[data-testid="planning-staffing-team-select"]').setValue("team-1");
    await wrapper.get('[data-testid="planning-staffing-member-select"]').setValue("member-1");
    await wrapper.get('[data-testid="planning-staffing-confirm-now"]').setValue(true);
    await wrapper.get('[data-testid="planning-staffing-assign-action"]').trigger("click");
    await flushPromises();

    expect(mocks.assignStaffingMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        confirmed_at: expect.any(String),
        employee_id: "employee-1",
      }),
    );
  });

  it("hides the confirmation-at-creation control when acting on an existing assignment", async () => {
    const wrapper = await mountView();

    expect(wrapper.text()).not.toContain("Zuweisung jetzt als bestaetigt anlegen");
    expect(wrapper.text()).not.toContain("Aktiviert setzt beim Zuweisen sofort einen Bestaetigungszeitpunkt.");
  });

  it("treats team as optional context and keeps assignment actor concrete", async () => {
    const wrapper = await mountView();
    const actorKindSelect = wrapper.get('[data-testid="planning-staffing-actor-kind-select"]');

    expect(actorKindSelect.html()).not.toContain('value="team"');
    expect(wrapper.text()).toContain("Team bleibt kontextbezogen.");

    await wrapper.get('[data-testid="planning-staffing-member-select"]').setValue("member-1");
    await wrapper.get('[data-testid="planning-staffing-assign-action"]').trigger("click");
    await flushPromises();

    expect(mocks.assignStaffingMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        team_id: null,
        employee_id: "employee-1",
        subcontractor_worker_id: null,
      }),
    );
  });

  it("shows a setup-required state instead of a normal staffing warning when a shift has no demand groups", async () => {
    mocks.listStaffingBoardMock.mockResolvedValueOnce([
      {
        id: "shift-1",
        tenant_id: "tenant-1",
        planning_record_id: "planning-1",
        shift_plan_id: "plan-1",
        order_id: "order-1",
        order_no: "ORD-1",
        planning_record_name: "Planning 1",
        planning_mode_code: "site",
        workforce_scope_code: "internal",
        starts_at: "2026-04-05T08:00:00Z",
        ends_at: "2026-04-05T16:00:00Z",
        shift_type_code: "site_day",
        release_state: "draft",
        status: "active",
        location_text: "Berlin",
        meeting_point: "Gate A",
        demand_groups: [],
        assignments: [],
      },
    ]);
    mocks.listStaffingCoverageMock.mockResolvedValueOnce([
      {
        shift_id: "shift-1",
        planning_record_id: "planning-1",
        shift_plan_id: "plan-1",
        order_id: "order-1",
        order_no: "ORD-1",
        planning_record_name: "Planning 1",
        planning_mode_code: "site",
        workforce_scope_code: "internal",
        starts_at: "2026-04-05T08:00:00Z",
        ends_at: "2026-04-05T16:00:00Z",
        shift_type_code: "site_day",
        location_text: "Berlin",
        meeting_point: "Gate A",
        min_required_qty: 0,
        target_required_qty: 0,
        assigned_count: 0,
        confirmed_count: 0,
        released_partner_qty: 0,
        coverage_state: "yellow",
        demand_groups: [],
      },
    ]);
    mocks.listDemandGroupsMock.mockResolvedValueOnce([]);

    const wrapper = await mountView();

    expect(wrapper.text()).toContain("Setup noetig");
    expect(wrapper.text()).toContain("Demand-Group-Setup fehlt");
    expect(wrapper.text()).toContain("Diese Schicht ist im Coverage sichtbar, kann aber erst staffed werden");
    expect(wrapper.text()).toContain("Staffing-Aktionen sind blockiert, bis die Schicht mindestens eine Demand Group hat.");
    expect(wrapper.get('[data-testid="planning-staffing-assign-action"]').attributes("disabled")).toBeDefined();
    expect(wrapper.get('[data-testid="planning-staffing-substitute-action"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('[data-testid="planning-staffing-demand-group-editor"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-staffing-demand-group-start-create"]').exists()).toBe(true);
  });

  it("creates a demand group from the setup-required state through the modal", async () => {
    mocks.listStaffingBoardMock.mockResolvedValueOnce([
      {
        id: "shift-1",
        tenant_id: "tenant-1",
        planning_record_id: "planning-1",
        shift_plan_id: "plan-1",
        order_id: "order-1",
        order_no: "ORD-1",
        planning_record_name: "Planning 1",
        planning_mode_code: "site",
        workforce_scope_code: "internal",
        starts_at: "2026-04-05T08:00:00Z",
        ends_at: "2026-04-05T16:00:00Z",
        shift_type_code: "site_day",
        release_state: "draft",
        status: "active",
        location_text: "Berlin",
        meeting_point: "Gate A",
        demand_groups: [],
        assignments: [],
      },
    ]);
    mocks.listStaffingCoverageMock.mockResolvedValueOnce([
      {
        shift_id: "shift-1",
        planning_record_id: "planning-1",
        shift_plan_id: "plan-1",
        order_id: "order-1",
        order_no: "ORD-1",
        planning_record_name: "Planning 1",
        planning_mode_code: "site",
        workforce_scope_code: "internal",
        starts_at: "2026-04-05T08:00:00Z",
        ends_at: "2026-04-05T16:00:00Z",
        shift_type_code: "site_day",
        location_text: "Berlin",
        meeting_point: "Gate A",
        min_required_qty: 0,
        target_required_qty: 0,
        assigned_count: 0,
        confirmed_count: 0,
        released_partner_qty: 0,
        coverage_state: "yellow",
        demand_groups: [],
      },
    ]);
    mocks.listDemandGroupsMock.mockResolvedValueOnce([]);

    const wrapper = await mountView();

    await wrapper.get('[data-testid="planning-staffing-demand-group-start-create"]').trigger("click");
    await flushPromises();

    expect(wrapper.get(".modal-stub__title").text()).toContain("Demand Group anlegen");
    expect(wrapper.find('[data-testid="planning-staffing-demand-group-editor"]').exists()).toBe(true);
    await wrapper.get('[data-testid="planning-staffing-demand-group-function-type"]').setValue("func-1");
    await flushPromises();
    await wrapper.get('[data-testid="planning-staffing-demand-group-editor"]').trigger("submit");
    await flushPromises();

    expect(mocks.createDemandGroupMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        tenant_id: "tenant-1",
        shift_id: "shift-1",
        function_type_id: "func-1",
        qualification_type_id: null,
      }),
    );
    expect(mocks.listStaffingBoardMock.mock.calls.length).toBeGreaterThan(1);
    expect(wrapper.find('[data-testid="planning-staffing-demand-group-editor"]').exists()).toBe(false);
  });

  it("maps planning-record select change and clear back to filters.planning_record_id", async () => {
    const wrapper = await mountView();
    const selects = wrapper.findAllComponents({ name: "ASelect" });
    const planningRecordSelect = selects[0]!;

    planningRecordSelect.vm.$emit("change", "planning-1");
    await flushPromises();
    await wrapper.get('[data-testid="planning-staffing-refresh"]').trigger("click");

    expect(mocks.listStaffingCoverageMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({ planning_record_id: "planning-1" }),
    );

    planningRecordSelect.vm.$emit("clear");
    await flushPromises();
    await wrapper.get('[data-testid="planning-staffing-refresh"]').trigger("click");

    expect(mocks.listStaffingCoverageMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({ planning_record_id: "" }),
    );
  });

  it("shows demand and staffing as the default detail tab while keeping summary metrics visible", async () => {
    const wrapper = await mountView();

    expect(wrapper.get('[data-testid="planning-staffing-detail-tabs"]').text()).toContain("Bedarf und Staffing");
    expect(wrapper.find('[data-testid="planning-staffing-tab-panel-demand-staffing"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="planning-staffing-tab-panel-validations"]').exists()).toBe(false);
    expect(wrapper.text()).toContain("Min: 1");
    expect(wrapper.text()).toContain("Ziel: 2");
    expect(wrapper.get('[data-testid="planning-staffing-demand-group-list"]').text()).toContain("Sicherheitsdienst · G34a");
    expect(wrapper.get('[data-testid="planning-staffing-tab-panel-demand-staffing"]').text()).not.toContain("func-1 · qual-1");
    expect(wrapper.get('[data-testid="planning-staffing-tab-panel-demand-staffing"]').html()).toContain(">Sicherheitsdienst · G34a<");
    expect(wrapper.find('[data-testid="planning-staffing-demand-group-editor"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-staffing-demand-group-edit-selected"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-staffing-demand-group-start-create"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="planning-staffing-assign-action"]').exists()).toBe(true);
  });

  it("opens the demand-group modal in edit mode when a list row is clicked", async () => {
    const wrapper = await mountView();

    await wrapper.get(".planning-staffing-demand-group").trigger("click");
    await flushPromises();

    expect(wrapper.get(".modal-stub__title").text()).toContain("Demand Group bearbeiten");
    expect(wrapper.find('[data-testid="planning-staffing-demand-group-editor"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="planning-staffing-demand-group-function-type"]').element as HTMLSelectElement).value).toBe("func-1");
    expect(wrapper.get('[data-testid="planning-staffing-demand-group-editor"]').text()).toContain("Demand Group als verpflichtend markieren");
    expect(wrapper.find('[data-testid="planning-staffing-demand-group-modal-cancel"]').exists()).toBe(true);
  });

  it("updates a demand group from the modal after clicking a row", async () => {
    const wrapper = await mountView();

    await wrapper.get(".planning-staffing-demand-group").trigger("click");
    await flushPromises();
    await wrapper.get('input[type="number"]').setValue("2");
    await flushPromises();
    await wrapper.get('[data-testid="planning-staffing-demand-group-editor"]').trigger("submit");
    await flushPromises();

    expect(mocks.updateDemandGroupMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      "dg-1",
      expect.objectContaining({
        min_qty: 2,
      }),
    );
    expect(wrapper.find('[data-testid="planning-staffing-demand-group-editor"]').exists()).toBe(false);
  });

  it("switches to validations without hiding the always-visible shift summary", async () => {
    mocks.getShiftReleaseValidationsMock.mockResolvedValueOnce({
      blocking_count: 1,
      warning_count: 0,
      info_count: 0,
      issues: [{ rule_code: "minimum_staffing", severity: "block", message_key: "validation.minimum_staffing", override_allowed: false, demand_group_id: null }],
    } as any);

    const wrapper = await mountView();
    await clickDetailTab(wrapper, "validations");

    expect(wrapper.get('[data-testid="planning-staffing-tab-panel-validations"]').text()).toContain("Release-Validierungen");
    expect(wrapper.text()).toContain("Min: 1");
    expect(wrapper.text()).toContain("Bestaetigt: 1");
    expect(wrapper.find('[data-testid="planning-staffing-tab-panel-demand-staffing"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-staffing-assign-action"]').exists()).toBe(false);
    expect(wrapper.text()).toContain("Mindestbesetzung nicht erreicht");
  });

  it("shows outputs and dispatch content under the outputs tab", async () => {
    mocks.listShiftOutputsMock.mockResolvedValueOnce([
      {
        document_id: "doc-1",
        title: "Einsatzplan intern",
        variant_code: "internal",
        audience_code: "internal",
        file_name: "einsatzplan.pdf",
      },
    ] as any);

    const wrapper = await mountView();
    await clickDetailTab(wrapper, "outputs_dispatch");

    expect(wrapper.get('[data-testid="planning-staffing-tab-panel-outputs-dispatch"]').text()).toContain("Einsatzplaene und Protokolle");
    expect(wrapper.text()).toContain("Dispatch-Nachrichten");
    expect(wrapper.text()).toContain("Einsatzplan intern");
    expect(wrapper.find('[data-testid="planning-staffing-tab-panel-demand-staffing"]').exists()).toBe(false);
  });

  it("creates a planning-level team for the selected planning record", async () => {
    const wrapper = await mountView();
    await clickDetailTab(wrapper, "teams_releases");

    await wrapper.get('[data-testid="planning-staffing-create-planning-team"]').trigger("click");
    await flushPromises();
    expect((wrapper.get('[data-testid="planning-staffing-team-planning-record"]').element as HTMLInputElement).value).toBe("Planning 1");
    expect(wrapper.get('[data-testid="planning-staffing-team-editor"]').text()).toContain("ID: planning-1");
    await wrapper.get('[data-testid="planning-staffing-team-name"]').setValue("Planung Alpha");
    await wrapper.get('[data-testid="planning-staffing-team-lead-member"]').setValue("employee-1");
    await wrapper.get('[data-testid="planning-staffing-team-editor"]').trigger("submit");
    await flushPromises();

    expect(mocks.listTeamsMock).toHaveBeenCalledWith("tenant-1", "token-1", { planning_record_id: "planning-1" });
    expect(mocks.createTeamMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        tenant_id: "tenant-1",
        planning_record_id: "planning-1",
        shift_id: null,
        name: "Planung Alpha",
      }),
    );
    expect(mocks.createTeamMemberMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        team_id: "team-planning-new",
        employee_id: "employee-1",
        subcontractor_worker_id: null,
        is_team_lead: true,
      }),
    );
  });

  it("keeps planning-team creation available from planning-record context without a selected shift", async () => {
    mocks.listStaffingCoverageMock.mockResolvedValue([]);
    mocks.listStaffingBoardMock.mockResolvedValue([]);

    const wrapper = await mountView();
    const selects = wrapper.findAllComponents({ name: "ASelect" });
    const planningRecordSelect = selects[0]!;

    planningRecordSelect.vm.$emit("change", "planning-1");
    await flushPromises();
    await wrapper.get('[data-testid="planning-staffing-refresh"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-staffing-planning-context-panel"]').exists()).toBe(true);
    expect(wrapper.text()).toContain("Planungskontext ohne Schichtauswahl");
    expect(mocks.listTeamsMock).toHaveBeenLastCalledWith("tenant-1", "token-1", { planning_record_id: "planning-1" });

    await wrapper.get('[data-testid="planning-staffing-create-planning-team-context"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-staffing-team-name"]').setValue("Planung Ohne Schicht");
    await wrapper.get('[data-testid="planning-staffing-team-editor"]').trigger("submit");
    await flushPromises();

    expect(mocks.createTeamMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        planning_record_id: "planning-1",
        shift_id: null,
        name: "Planung Ohne Schicht",
      }),
    );
  });

  it("resolves and replaces the planning-record UUID with the planning-record name in the team modal when only the id is known initially", async () => {
    mocks.listStaffingCoverageMock.mockResolvedValue([]);
    mocks.listStaffingBoardMock.mockResolvedValue([]);
    mocks.listPlanningRecordsMock.mockResolvedValue([]);

    const wrapper = await mountView();
    const selects = wrapper.findAllComponents({ name: "ASelect" });
    const planningRecordSelect = selects[0]!;

    planningRecordSelect.vm.$emit("change", "planning-1");
    await flushPromises();
    await wrapper.get('[data-testid="planning-staffing-refresh"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-staffing-create-planning-team-context"]').trigger("click");
    await flushPromises();

    expect((wrapper.get('[data-testid="planning-staffing-team-planning-record"]').element as HTMLInputElement).value).toBe("Planning 1");
    expect(wrapper.get('[data-testid="planning-staffing-team-editor"]').text()).toContain("ID: planning-1");
    expect(mocks.getPlanningRecordMock).toHaveBeenCalledWith("tenant-1", "planning-1", "token-1");
    expect((wrapper.get('[data-testid="planning-staffing-team-planning-record"]').element as HTMLInputElement).value).not.toBe("planning-1");
  });

  it("does not expose planning-team creation when no planning-record context exists", async () => {
    mocks.listStaffingCoverageMock.mockResolvedValueOnce([]);
    mocks.listStaffingBoardMock.mockResolvedValueOnce([]);

    const wrapper = await mountView();
    await wrapper.get('[data-testid="planning-staffing-refresh"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="planning-staffing-planning-context-panel"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="planning-staffing-create-planning-team-context"]').exists()).toBe(false);
    expect(mocks.createTeamMock).not.toHaveBeenCalled();
  });

  it("creates a shift team with the selected shift context", async () => {
    const wrapper = await mountView();
    await clickDetailTab(wrapper, "teams_releases");

    await wrapper.get('[data-testid="planning-staffing-create-shift-team"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-staffing-team-name"]').setValue("Schicht Bravo");
    await wrapper.get('[data-testid="planning-staffing-team-editor"]').trigger("submit");
    await flushPromises();

    expect(mocks.createTeamMock).toHaveBeenLastCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        planning_record_id: "planning-1",
        shift_id: "shift-1",
        name: "Schicht Bravo",
      }),
    );
  });

  it("creates a team member with role_label for the selected team", async () => {
    const wrapper = await mountView();
    await clickDetailTab(wrapper, "teams_releases");

    expect(wrapper.text()).toContain("Planung Alpha");

    await wrapper.get('[data-testid="planning-staffing-create-team-member"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="planning-staffing-team-member-role-label"]').setValue("Springer");
    await wrapper.get('[data-testid="planning-staffing-team-member-member"]').setValue("employee-1");
    await wrapper.get('[data-testid="planning-staffing-team-member-editor"]').trigger("submit");
    await flushPromises();

    expect(mocks.createTeamMemberMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      expect.objectContaining({
        team_id: "team-1",
        employee_id: "employee-1",
        subcontractor_worker_id: null,
        role_label: "Springer",
      }),
    );
  });

  it("links the selected assignment to a planning or shift team through assignment patching", async () => {
    const wrapper = await mountView();
    await clickDetailTab(wrapper, "assignments");

    expect(wrapper.text()).toContain("Planung Alpha");
    await wrapper.get('[data-testid="planning-staffing-assignment-team-select"]').setValue("team-shift-1");
    await wrapper.get('[data-testid="planning-staffing-assignment-team-save"]').trigger("click");
    await flushPromises();

    expect(mocks.updateAssignmentMock).toHaveBeenCalledWith(
      "tenant-1",
      "token-1",
      "assignment-1",
      { team_id: "team-shift-1", version_no: 1 },
    );
  });
});
