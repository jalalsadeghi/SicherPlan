// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';

import CustomerNewPlanAssignmentsStep from './customer-new-plan-assignments-step.vue';
import type { CustomerNewPlanWizardState } from './new-plan-wizard.types';

const staffingMocks = vi.hoisted(() => ({
  applyAssignmentStepMock: vi.fn(),
  getAssignmentStepSnapshotMock: vi.fn(),
  listAssignmentStepCandidatesMock: vi.fn(),
  listTeamsMock: vi.fn(),
  previewAssignmentStepApplyMock: vi.fn(),
}));

const employeeMocks = vi.hoisted(() => ({
  listEmployeeGroupsMock: vi.fn(),
  listFunctionTypesMock: vi.fn(),
  listQualificationTypesMock: vi.fn(),
}));

vi.mock('#/locales', () => ({
  $t: (key: string, params?: Record<string, unknown>) =>
    params ? `${key}:${JSON.stringify(params)}` : key,
}));

vi.mock('#/sicherplan-legacy/api/planningStaffing', () => ({
  applyAssignmentStep: staffingMocks.applyAssignmentStepMock,
  getAssignmentStepSnapshot: staffingMocks.getAssignmentStepSnapshotMock,
  listAssignmentStepCandidates: staffingMocks.listAssignmentStepCandidatesMock,
  listTeams: staffingMocks.listTeamsMock,
  previewAssignmentStepApply: staffingMocks.previewAssignmentStepApplyMock,
}));

vi.mock('#/sicherplan-legacy/api/employeeAdmin', () => ({
  listEmployeeGroups: employeeMocks.listEmployeeGroupsMock,
  listFunctionTypes: employeeMocks.listFunctionTypesMock,
  listQualificationTypes: employeeMocks.listQualificationTypesMock,
}));

function baseWizardState(): CustomerNewPlanWizardState {
  return {
    current_step: 'assignments',
    customer_id: 'customer-1',
    order_id: 'order-1',
    planning_entity_id: 'site-1',
    planning_entity_type: 'site',
    planning_mode_code: 'site',
    planning_record_id: 'record-1',
    shift_plan_id: 'plan-1',
    series_id: 'series-1',
    step_state: {
      'order-details': { completed: true, dirty: false, error: '', loading: false },
      'order-scope-documents': { completed: true, dirty: false, error: '', loading: false },
      'planning-record-overview': { completed: true, dirty: false, error: '', loading: false },
      'planning-record-documents': { completed: true, dirty: false, error: '', loading: false },
      'shift-plan': { completed: true, dirty: false, error: '', loading: false },
      'series-exceptions': { completed: true, dirty: false, error: '', loading: false },
      'demand-groups': { completed: true, dirty: false, error: '', loading: false },
      'assignments': { completed: false, dirty: false, error: '', loading: false },
    },
  };
}

function buildSnapshot(overrides: Record<string, unknown> = {}) {
  return {
    tenant_id: 'tenant-1',
    order: {
      order_id: 'order-1',
      order_no: 'ORD-100',
      customer_id: 'customer-1',
      planning_record_id: 'record-1',
      planning_record_name: 'Werk Nord',
      planning_mode_code: 'site',
    },
    shift_plan: {
      shift_plan_id: 'plan-1',
      shift_plan_name: 'Sommerplan',
      shift_series_id: 'series-1',
      shift_series_label: 'Tagdienst',
      workforce_scope_code: 'mixed',
      planning_from: '2026-06-01',
      planning_to: '2026-06-30',
      project_start: '2026-06-01',
      project_end: '2026-06-30',
      default_month: '2026-06-01',
      active_months: ['2026-06-01'],
    },
    generated_shift_count: 2,
    demand_group_summary_count: 1,
    editable_flag: true,
    lock_reason_codes: [],
    demand_group_summaries: [
      {
        signature_key: 'dg-1',
        function_type_id: 'fn-1',
        qualification_type_id: 'ql-1',
        min_qty: 1,
        target_qty: 2,
        mandatory_flag: true,
        sort_order: 1,
        remark: null,
        matched_shift_count: 2,
        assigned_count: 0,
        confirmed_count: 0,
        released_partner_qty: 0,
        remaining_open_qty: 2,
        coverage_state: 'yellow',
      },
    ],
    day_summaries: [
      {
        occurrence_date: '2026-06-01',
        total_shifts: 1,
        fully_covered_count: 0,
        warning_count: 1,
        blocked_count: 0,
        overall_state: 'yellow',
        active_flag: true,
      },
      {
        occurrence_date: '2026-06-02',
        total_shifts: 1,
        fully_covered_count: 0,
        warning_count: 0,
        blocked_count: 1,
        overall_state: 'setup_required',
        active_flag: true,
      },
    ],
    calendar_cells: [
      {
        shift_id: 'shift-1',
        demand_group_id: 'dg-row-1',
        occurrence_date: '2026-06-01',
        starts_at: '2026-06-01T08:00:00Z',
        ends_at: '2026-06-01T16:00:00Z',
        shift_type_code: 'day',
        function_type_id: 'fn-1',
        qualification_type_id: 'ql-1',
        min_qty: 1,
        target_qty: 2,
        assigned_count: 0,
        confirmed_count: 0,
        released_partner_qty: 0,
        remaining_open_qty: 2,
        coverage_state: 'yellow',
        editable_flag: true,
        existing_assignments: [],
      },
      {
        shift_id: 'shift-2',
        demand_group_id: 'dg-row-2',
        occurrence_date: '2026-06-02',
        starts_at: '2026-06-02T08:00:00Z',
        ends_at: '2026-06-02T16:00:00Z',
        shift_type_code: 'day',
        function_type_id: 'fn-1',
        qualification_type_id: 'ql-1',
        min_qty: 1,
        target_qty: 2,
        assigned_count: 0,
        confirmed_count: 0,
        released_partner_qty: 0,
        remaining_open_qty: 1,
        coverage_state: 'setup_required',
        editable_flag: true,
        existing_assignments: [],
      },
    ],
    candidates: [
      {
        actor_kind: 'employee',
        actor_id: 'employee-1',
        personnel_ref: 'E-100',
        first_name: 'Eva',
        last_name: 'Meyer',
        display_name: 'Eva Meyer',
        subcontractor_id: null,
        team_ids: ['team-1'],
        employee_group_ids: ['group-1'],
        qualification_match_flag: true,
        function_match_flag: true,
        eligible_day_count: 1,
        warning_day_count: 1,
        blocked_day_count: 1,
        availability_day_count: 1,
        conflict_day_count: 1,
        suitability_score: 88,
        top_reason_codes: [],
        day_statuses: [
          {
            shift_id: 'shift-1',
            demand_group_id: 'dg-row-1',
            occurrence_date: '2026-06-01',
            eligible_flag: true,
            warning_flag: false,
            reason_codes: [],
            warning_codes: [],
            validation_results: [],
          },
          {
            shift_id: 'shift-2',
            demand_group_id: 'dg-row-2',
            occurrence_date: '2026-06-02',
            eligible_flag: false,
            warning_flag: false,
            reason_codes: ['employee_absent'],
            warning_codes: [],
            validation_results: [],
          },
        ],
      },
    ],
    ...overrides,
  };
}

async function mountStep() {
  const wrapper = mount(CustomerNewPlanAssignmentsStep, {
    props: {
      accessToken: 'token-1',
      tenantId: 'tenant-1',
      wizardState: baseWizardState(),
    },
  });
  await flushPromises();
  await flushPromises();
  return wrapper;
}

describe('CustomerNewPlanAssignmentsStep', () => {
  beforeEach(() => {
    staffingMocks.applyAssignmentStepMock.mockReset();
    staffingMocks.getAssignmentStepSnapshotMock.mockReset();
    staffingMocks.listAssignmentStepCandidatesMock.mockReset();
    staffingMocks.listTeamsMock.mockReset();
    staffingMocks.previewAssignmentStepApplyMock.mockReset();
    employeeMocks.listEmployeeGroupsMock.mockReset();
    employeeMocks.listFunctionTypesMock.mockReset();
    employeeMocks.listQualificationTypesMock.mockReset();

    staffingMocks.listTeamsMock.mockResolvedValue([{ id: 'team-1', name: 'Alpha', status: 'active', members: [] }]);
    employeeMocks.listEmployeeGroupsMock.mockResolvedValue([{ id: 'group-1', name: 'Nord', status: 'active', archived_at: null }]);
    employeeMocks.listFunctionTypesMock.mockResolvedValue([{ id: 'fn-1', label: 'Objektschutz', code: 'OBJ', status: 'active', archived_at: null }]);
    employeeMocks.listQualificationTypesMock.mockResolvedValue([{ id: 'ql-1', label: '§34a', code: '34A', status: 'active', archived_at: null }]);
  });

  it('renders the left candidate rail and right calendar from the backend snapshot', async () => {
    staffingMocks.getAssignmentStepSnapshotMock.mockResolvedValueOnce(buildSnapshot());

    const wrapper = await mountStep();

    expect(wrapper.get('[data-testid="customer-new-plan-assignments-filters"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-new-plan-assignments-candidate-rail"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-new-plan-assignments-calendar"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-new-plan-assignments-candidate-employee-1"]').text()).toContain('Eva Meyer');
    expect(wrapper.get('[data-testid="customer-new-plan-assignments-day-2026-06-01"]').text()).toContain('0/2');
    expect(staffingMocks.getAssignmentStepSnapshotMock).toHaveBeenCalledTimes(1);
    expect(staffingMocks.listAssignmentStepCandidatesMock).not.toHaveBeenCalled();
  });

  it('loads candidates once after the first snapshot when the backend does not include them yet', async () => {
    staffingMocks.getAssignmentStepSnapshotMock.mockResolvedValueOnce(buildSnapshot({ candidates: [] }));
    staffingMocks.listAssignmentStepCandidatesMock.mockResolvedValueOnce({
      tenant_id: 'tenant-1',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      generated_shift_count: 2,
      candidates: buildSnapshot().candidates,
    });

    const wrapper = await mountStep();

    expect(staffingMocks.getAssignmentStepSnapshotMock).toHaveBeenCalledTimes(1);
    expect(staffingMocks.listAssignmentStepCandidatesMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-assignments-candidate-employee-1"]').text()).toContain('Eva Meyer');
  });

  it('uses the candidate endpoint for filter-only changes instead of reloading the snapshot', async () => {
    staffingMocks.getAssignmentStepSnapshotMock.mockResolvedValueOnce(buildSnapshot());
    staffingMocks.listAssignmentStepCandidatesMock.mockResolvedValue({
      tenant_id: 'tenant-1',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      generated_shift_count: 2,
      candidates: buildSnapshot().candidates,
    });

    const wrapper = await mountStep();
    await wrapper.get('[data-testid="customer-new-plan-assignments-team"]').setValue('team-1');
    await flushPromises();

    expect(staffingMocks.getAssignmentStepSnapshotMock).toHaveBeenCalledTimes(1);
    expect(staffingMocks.listAssignmentStepCandidatesMock).toHaveBeenCalledTimes(1);
    expect(staffingMocks.listAssignmentStepCandidatesMock).toHaveBeenCalledWith(
      'tenant-1',
      'token-1',
      expect.objectContaining({
        demand_group_match: expect.objectContaining({ function_type_id: 'fn-1' }),
        team_id: 'team-1',
      }),
    );
  });

  it('switches demand-group context without reloading the full snapshot', async () => {
    staffingMocks.getAssignmentStepSnapshotMock.mockResolvedValueOnce(buildSnapshot({
      demand_group_summaries: [
        buildSnapshot().demand_group_summaries[0],
        {
          ...buildSnapshot().demand_group_summaries[0],
          signature_key: 'dg-2',
          function_type_id: 'fn-2',
          qualification_type_id: null,
          sort_order: 2,
        },
      ],
    }));
    staffingMocks.listAssignmentStepCandidatesMock.mockResolvedValue({
      tenant_id: 'tenant-1',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      generated_shift_count: 2,
      candidates: [],
    });

    const wrapper = await mountStep();
    await wrapper.get('[data-testid="customer-new-plan-assignments-demand-group"]').setValue('dg-2');
    await flushPromises();

    expect(staffingMocks.getAssignmentStepSnapshotMock).toHaveBeenCalledTimes(1);
    expect(staffingMocks.listAssignmentStepCandidatesMock).toHaveBeenCalledTimes(1);
    expect(staffingMocks.listAssignmentStepCandidatesMock).toHaveBeenCalledWith(
      'tenant-1',
      'token-1',
      expect.objectContaining({
        demand_group_match: expect.objectContaining({ function_type_id: 'fn-2', sort_order: 2 }),
      }),
    );
  });

  it('assigns a candidate through preview + apply and reloads the snapshot', async () => {
    staffingMocks.getAssignmentStepSnapshotMock
      .mockResolvedValueOnce(buildSnapshot())
      .mockResolvedValueOnce(buildSnapshot({
        demand_group_summaries: [
          {
            ...buildSnapshot().demand_group_summaries[0],
            assigned_count: 1,
            remaining_open_qty: 1,
          },
        ],
        calendar_cells: [
          {
            ...buildSnapshot().calendar_cells[0],
            assigned_count: 1,
            remaining_open_qty: 1,
            existing_assignments: [
              {
                assignment_id: 'assignment-1',
                shift_id: 'shift-1',
                demand_group_id: 'dg-row-1',
                assignment_status_code: 'assigned',
                actor_kind: 'employee',
                actor_id: 'employee-1',
                personnel_ref: 'E-100',
                display_name: 'Eva Meyer',
                team_id: 'team-1',
              },
            ],
          },
          buildSnapshot().calendar_cells[1],
        ],
      }));
    staffingMocks.previewAssignmentStepApplyMock.mockResolvedValue({
      tenant_id: 'tenant-1',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      actor_kind: 'employee',
      actor_id: 'employee-1',
      requested_count: 2,
      accepted_count: 1,
      rejected_count: 1,
      created_assignment_ids: [],
      results: [],
    });
    staffingMocks.applyAssignmentStepMock.mockResolvedValue({
      tenant_id: 'tenant-1',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      actor_kind: 'employee',
      actor_id: 'employee-1',
      requested_count: 2,
      accepted_count: 1,
      rejected_count: 1,
      created_assignment_ids: ['assignment-1'],
      results: [],
    });

    const wrapper = await mountStep();
    await wrapper.get('[data-testid="customer-new-plan-assignments-assign-employee-1"]').trigger('click');
    await flushPromises();
    await flushPromises();

    expect(staffingMocks.previewAssignmentStepApplyMock).toHaveBeenCalledWith(
      'tenant-1',
      'token-1',
      expect.objectContaining({
        employee_id: 'employee-1',
        target_shift_ids: ['shift-1', 'shift-2'],
      }),
    );
    expect(staffingMocks.applyAssignmentStepMock).toHaveBeenCalled();
    expect(wrapper.get('[data-testid="customer-new-plan-assignments-message"]').text()).toContain('assignmentsAppliedSummary');
    expect(wrapper.emitted('step-completion')?.some(([stepId, completed]) => stepId === 'assignments' && completed === true)).toBe(true);
  });

  it('returns success from submitCurrentStep when persisted assignments already exist', async () => {
    staffingMocks.getAssignmentStepSnapshotMock
      .mockResolvedValueOnce(buildSnapshot({
        demand_group_summaries: [
          {
            ...buildSnapshot().demand_group_summaries[0],
            assigned_count: 2,
            remaining_open_qty: 0,
          },
        ],
      }))
      .mockResolvedValueOnce(buildSnapshot({
        demand_group_summaries: [
          {
            ...buildSnapshot().demand_group_summaries[0],
            assigned_count: 2,
            remaining_open_qty: 0,
          },
        ],
      }));

    const wrapper = await mountStep();
    const result = await (wrapper.vm as unknown as { submitCurrentStep: () => Promise<unknown> }).submitCurrentStep();

    expect(result).toMatchObject({
      completedStepId: 'assignments',
      success: true,
    });
  });
});
