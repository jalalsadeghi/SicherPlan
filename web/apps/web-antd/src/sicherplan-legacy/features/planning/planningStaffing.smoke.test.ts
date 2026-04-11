// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";

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
      shift_id: "shift-1",
      name: "Alpha",
      role_label: "Lead",
      status: "active",
      version_no: 1,
      notes: null,
      members: [{ id: "member-1" }],
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
  createDemandGroup: mocks.createDemandGroupMock,
  createAssignmentValidationOverride: mocks.createAssignmentValidationOverrideMock,
  generateShiftOutput: vi.fn(async () => ({})),
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
  updateDemandGroup: mocks.updateDemandGroupMock,
  PlanningStaffingApiError: class PlanningStaffingApiError extends Error {
    messageKey = "";
  },
}));

vi.mock("@/api/planningOrders", () => ({
  listPlanningRecords: mocks.listPlanningRecordsMock,
}));

vi.mock("@/api/employeeAdmin", () => ({
  listFunctionTypes: mocks.listFunctionTypesMock,
  listQualificationTypes: mocks.listQualificationTypesMock,
}));

async function mountView() {
  const { default: PlanningStaffingCoverageView } = await import("../../views/PlanningStaffingCoverageView.vue");
  const wrapper = mount(PlanningStaffingCoverageView);
  await flushPromises();
  return wrapper;
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
    expect(wrapper.find('[data-testid="planning-staffing-demand-group-editor"]').exists()).toBe(true);
  });

  it("creates a demand group inline from the setup-required state", async () => {
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

    await wrapper.get('[data-testid="planning-staffing-demand-group-function-type"]').setValue("func-1");
    await wrapper.get('[data-testid="planning-staffing-demand-group-save"]').trigger("click");
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
});
